"""Kafka consumer handler tests — LLM nodes and producer mocked."""

import uuid
from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.kafka import consumer as consumer_mod
from app.models.interview import (
    Interview,
    InterviewLevel,
    InterviewStatus,
    Question,
    User,
)


@pytest.fixture
def session_factory(test_engine):
    return async_sessionmaker(test_engine, expire_on_commit=False)


@pytest.fixture(autouse=True)
def clear_states():
    consumer_mod._interview_states.clear()
    yield
    consumer_mod._interview_states.clear()


async def _make_interview(session_factory, status=InterviewStatus.pending):
    async with session_factory() as db:
        user = User(email=f"{uuid.uuid4().hex}@example.com", hashed_password="x")
        db.add(user)
        await db.flush()
        interview = Interview(
            user_id=user.id, topic="Python", level=InterviewLevel.junior, status=status
        )
        db.add(interview)
        await db.commit()
        return interview.id


def _fake_question(text="What is the GIL?"):
    async def fake_ask(state):
        return {
            "questions": [
                {
                    "id": str(uuid.uuid4()),
                    "text": text,
                    "answer": None,
                    "score": None,
                    "feedback": None,
                }
            ],
            "current_question_index": state["current_question_index"] + 1,
        }

    return fake_ask


async def test_handle_interview_started(session_factory):
    interview_id = str(await _make_interview(session_factory))

    with (
        patch.object(consumer_mod, "AsyncSessionLocal", session_factory),
        patch.object(consumer_mod, "ask_question_node", side_effect=_fake_question()),
        patch.object(consumer_mod, "publish", new_callable=AsyncMock) as publish_mock,
    ):
        await consumer_mod._handle_interview_started(
            {"interview_id": interview_id, "topic": "Python", "level": "junior"}
        )

    state = consumer_mod._interview_states[interview_id]
    assert state["questions"][0]["text"] == "What is the GIL?"

    topic, payload = publish_mock.call_args.args
    assert payload["type"] == "question"
    assert payload["interview_id"] == interview_id

    async with session_factory() as db:
        interview = await db.get(Interview, uuid.UUID(interview_id))
        assert interview.status == InterviewStatus.active


async def test_handle_interview_started_sanitizes_topic(session_factory):
    interview_id = str(await _make_interview(session_factory))

    with (
        patch.object(consumer_mod, "AsyncSessionLocal", session_factory),
        patch.object(consumer_mod, "ask_question_node", side_effect=_fake_question()),
        patch.object(consumer_mod, "publish", new_callable=AsyncMock),
    ):
        await consumer_mod._handle_interview_started(
            {"interview_id": interview_id, "topic": "Py\x00thon" + "x" * 500, "level": "junior"}
        )

    topic = consumer_mod._interview_states[interview_id]["topic"]
    assert "\x00" not in topic
    assert len(topic) <= 100


async def test_rebuild_state_from_db(session_factory):
    """Regression: _rebuild_state used QuestionRecord without importing it."""
    interview_id = await _make_interview(session_factory, status=InterviewStatus.active)
    async with session_factory() as db:
        db.add(
            Question(
                interview_id=interview_id, text="Q1", answer="A1", score=7.0, feedback="ok", order=1
            )
        )
        await db.commit()

    with patch.object(consumer_mod, "AsyncSessionLocal", session_factory):
        state = await consumer_mod._rebuild_state(str(interview_id))

    assert state is not None
    assert len(state["questions"]) == 1
    assert state["questions"][0]["text"] == "Q1"
    assert state["current_question_index"] == 1
    assert consumer_mod._interview_states[str(interview_id)] is state


async def test_handle_answer_evaluates_and_asks_next(session_factory):
    interview_id = await _make_interview(session_factory, status=InterviewStatus.active)
    question_id = str(uuid.uuid4())
    async with session_factory() as db:
        db.add(Question(id=uuid.UUID(question_id), interview_id=interview_id, text="Q1", order=1))
        await db.commit()

    consumer_mod._interview_states[str(interview_id)] = {
        "interview_id": str(interview_id),
        "topic": "Python",
        "level": "junior",
        "questions": [
            {"id": question_id, "text": "Q1", "answer": None, "score": None, "feedback": None}
        ],
        "current_question_index": 1,
        "max_questions": 5,
        "greeting_sent": True,
        "completed": False,
        "overall_score": None,
        "report": None,
        "error": None,
    }

    async def fake_evaluate(state):
        return {"questions": [{**q, "score": 8.0, "feedback": "Solid"} for q in state["questions"]]}

    with (
        patch.object(consumer_mod, "AsyncSessionLocal", session_factory),
        patch.object(consumer_mod, "evaluate_answer_node", side_effect=fake_evaluate),
        patch.object(consumer_mod, "ask_question_node", side_effect=_fake_question("Q2")),
        patch.object(consumer_mod, "publish", new_callable=AsyncMock) as publish_mock,
    ):
        await consumer_mod._handle_answer(
            {
                "interview_id": str(interview_id),
                "question_id": question_id,
                "answer": "An\x00swer " + "x" * 6000,
            }
        )

    # Answer sanitized before reaching state/DB
    answered = consumer_mod._interview_states[str(interview_id)]["questions"][0]
    assert "\x00" not in answered["answer"]
    assert len(answered["answer"]) <= 5000

    types = [call.args[1]["type"] for call in publish_mock.call_args_list]
    assert types == ["feedback", "question"]

    async with session_factory() as db:
        db_q = await db.get(Question, uuid.UUID(question_id))
        assert db_q.score == 8.0
        assert db_q.feedback == "Solid"
