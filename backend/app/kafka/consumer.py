"""Kafka consumer — processes interview events and drives the LangGraph agent."""

import json
import logging
import uuid
from datetime import datetime

from aiokafka import AIOKafkaConsumer
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.agent.nodes import (
    ask_question_node,
    evaluate_answer_node,
    greet_node,
    should_continue,
    summarize_node,
)
from app.agent.state import InterviewState, QuestionRecord
from app.config import settings
from app.core.text import sanitize_text
from app.db import AsyncSessionLocal
from app.kafka.producer import publish
from app.models.interview import Interview, InterviewStatus, Question

logger = logging.getLogger(__name__)

# In-memory state store (replace with Redis for multi-instance deployment)
_interview_states: dict[str, InterviewState] = {}


async def _handle_interview_started(payload: dict) -> None:
    """Initialize state and send the first question."""
    interview_id = payload["interview_id"]
    state: InterviewState = {
        "interview_id": interview_id,
        "topic": sanitize_text(payload["topic"], max_length=100),
        "level": payload["level"],
        "questions": [],
        "current_question_index": 0,
        "max_questions": settings.MAX_QUESTIONS_PER_INTERVIEW,
        "greeting_sent": False,
        "completed": False,
        "overall_score": None,
        "report": None,
        "error": None,
    }
    state.update(await greet_node(state))
    state.update(await ask_question_node(state))
    _interview_states[interview_id] = state

    # Persist question to DB
    async with AsyncSessionLocal() as db:
        q = state["questions"][-1]
        db_q = Question(
            id=uuid.UUID(q["id"]),
            interview_id=uuid.UUID(interview_id),
            text=q["text"],
            order=state["current_question_index"],
        )
        db.add(db_q)
        interview = await db.get(Interview, uuid.UUID(interview_id))
        if interview:
            interview.status = InterviewStatus.active
        await db.commit()

    # Push question to frontend via feedback topic
    await publish(
        settings.KAFKA_TOPIC_FEEDBACK,
        {
            "interview_id": interview_id,
            "type": "question",
            "question_id": state["questions"][-1]["id"],
            "text": state["questions"][-1]["text"],
            "index": state["current_question_index"],
            "total": state["max_questions"],
        },
    )


async def _rebuild_state(interview_id: str) -> InterviewState | None:
    """Reconstruct in-memory state from the database after a backend restart."""
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Interview)
            .where(Interview.id == uuid.UUID(interview_id))
            .options(selectinload(Interview.questions))
        )
        interview = result.scalar_one_or_none()
        if not interview or interview.status not in (
            InterviewStatus.active,
            InterviewStatus.pending,
        ):
            return None

        questions: list[QuestionRecord] = [
            {
                "id": str(q.id),
                "text": q.text,
                "answer": q.answer,
                "score": q.score,
                "feedback": q.feedback,
            }
            for q in sorted(interview.questions, key=lambda q: q.order)
        ]

    state: InterviewState = {
        "interview_id": interview_id,
        "topic": interview.topic,
        "level": interview.level,
        "questions": questions,
        "current_question_index": len(questions),
        "max_questions": settings.MAX_QUESTIONS_PER_INTERVIEW,
        "greeting_sent": True,
        "completed": False,
        "overall_score": None,
        "report": None,
        "error": None,
    }
    _interview_states[interview_id] = state
    logger.info(
        "Rebuilt state for interview %s from DB (%d questions)", interview_id, len(questions)
    )
    return state


async def _handle_answer(payload: dict) -> None:
    """Inject answer into state, evaluate, then ask next or summarize."""
    interview_id = payload["interview_id"]
    question_id = payload["question_id"]
    answer = sanitize_text(payload["answer"], max_length=5000)

    state = _interview_states.get(interview_id)
    if not state:
        logger.warning("No state found for interview %s — rebuilding from DB", interview_id)
        state = await _rebuild_state(interview_id)
    if not state:
        logger.error("Could not recover state for interview %s", interview_id)
        return

    # Inject answer into the matching question
    state["questions"] = [
        {**q, "answer": answer} if q["id"] == question_id else q for q in state["questions"]
    ]

    # Persist answer
    async with AsyncSessionLocal() as db:
        db_q = await db.get(Question, uuid.UUID(question_id))
        if db_q:
            db_q.answer = answer
            db_q.answered_at = datetime.utcnow()
        await db.commit()

    # Evaluate
    updates = await evaluate_answer_node(state)
    state.update(updates)

    # Persist score + feedback
    evaluated_q = next((q for q in state["questions"] if q["id"] == question_id), None)
    if evaluated_q:
        async with AsyncSessionLocal() as db:
            db_q = await db.get(Question, uuid.UUID(question_id))
            if db_q:
                db_q.score = evaluated_q["score"]
                db_q.feedback = evaluated_q["feedback"]
            await db.commit()

        await publish(
            settings.KAFKA_TOPIC_FEEDBACK,
            {
                "interview_id": interview_id,
                "type": "feedback",
                "question_id": question_id,
                "score": evaluated_q["score"],
                "feedback": evaluated_q["feedback"],
            },
        )

    route = should_continue(state)
    if route == "ask_question":
        state.update(await ask_question_node(state))
        new_q = state["questions"][-1]
        async with AsyncSessionLocal() as db:
            db_q = Question(
                id=uuid.UUID(new_q["id"]),
                interview_id=uuid.UUID(interview_id),
                text=new_q["text"],
                order=state["current_question_index"],
            )
            db.add(db_q)
            await db.commit()

        await publish(
            settings.KAFKA_TOPIC_FEEDBACK,
            {
                "interview_id": interview_id,
                "type": "question",
                "question_id": new_q["id"],
                "text": new_q["text"],
                "index": state["current_question_index"],
                "total": state["max_questions"],
            },
        )
    else:
        state.update(await summarize_node(state))
        async with AsyncSessionLocal() as db:
            interview = await db.get(Interview, uuid.UUID(interview_id))
            if interview:
                interview.status = InterviewStatus.completed
                interview.score = state["overall_score"]
                interview.report = state["report"]
                interview.completed_at = datetime.utcnow()
            await db.commit()

        await publish(
            settings.KAFKA_TOPIC_COMPLETED,
            {
                "interview_id": interview_id,
                "type": "completed",
                "overall_score": state["overall_score"],
                "report": state["report"],
            },
        )
        _interview_states.pop(interview_id, None)


async def run_consumer() -> None:
    """Long-running Kafka consumer loop."""
    consumer = AIOKafkaConsumer(
        settings.KAFKA_TOPIC_INTERVIEW_STARTED,
        settings.KAFKA_TOPIC_ANSWER,
        bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
        group_id=settings.KAFKA_GROUP_ID,
        value_deserializer=lambda v: json.loads(v.decode("utf-8")),
        auto_offset_reset="earliest",
    )
    await consumer.start()
    logger.info("Kafka consumer started")
    try:
        async for msg in consumer:
            try:
                if msg.topic == settings.KAFKA_TOPIC_INTERVIEW_STARTED:
                    await _handle_interview_started(msg.value)
                elif msg.topic == settings.KAFKA_TOPIC_ANSWER:
                    await _handle_answer(msg.value)
            except Exception:
                logger.exception("Error processing Kafka message: %s", msg.value)
    finally:
        await consumer.stop()
        logger.info("Kafka consumer stopped")
