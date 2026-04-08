"""Tests for LangGraph agent nodes — idiomatic LangGraph approach."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from langchain_core.messages import AIMessage

from app.agent.state import InterviewState
from app.agent.nodes import (
    greet_node,
    ask_question_node,
    evaluate_answer_node,
    summarize_node,
    should_continue,
    EvaluationResult,
    SummaryResult,
)


def make_state(**overrides) -> InterviewState:
    base: InterviewState = {
        "interview_id": "test-uuid",
        "topic": "Python",
        "level": "middle",
        "questions": [],
        "current_question_index": 0,
        "max_questions": 3,
        "greeting_sent": False,
        "completed": False,
        "overall_score": None,
        "report": None,
        "error": None,
    }
    base.update(overrides)
    return base


# ── greet ────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_greet_node():
    state = make_state()
    result = await greet_node(state)
    assert result["greeting_sent"] is True


# ── ask_question ─────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_ask_question_node():
    """_llm.ainvoke returns an AIMessage — standard LangGraph message type."""
    ai_msg = AIMessage(content="What is a Python decorator?")

    with patch("app.agent.nodes._llm") as mock_llm:
        mock_llm.ainvoke = AsyncMock(return_value=ai_msg)
        state = make_state()
        result = await ask_question_node(state)

    assert len(result["questions"]) == 1
    assert result["questions"][0]["text"] == "What is a Python decorator?"
    assert result["questions"][0]["answer"] is None
    assert result["current_question_index"] == 1


@pytest.mark.asyncio
async def test_ask_question_node_avoids_repeats():
    """When previous questions exist, their texts are sent as context."""
    ai_msg = AIMessage(content="Explain Python's GIL.")

    with patch("app.agent.nodes._llm") as mock_llm:
        mock_llm.ainvoke = AsyncMock(return_value=ai_msg)
        state = make_state(questions=[
            {"id": "q0", "text": "What is a decorator?", "answer": "...", "score": 7.0, "feedback": "Good"}
        ], current_question_index=1)
        result = await ask_question_node(state)

    # Second argument passed to ainvoke should contain the previous question
    call_messages = mock_llm.ainvoke.call_args[0][0]
    human_content = call_messages[-1].content
    assert "What is a decorator?" in human_content


# ── evaluate_answer ───────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_evaluate_answer_node():
    """_eval_chain.ainvoke returns an EvaluationResult Pydantic object."""
    eval_result = EvaluationResult(score=8.5, feedback="Good explanation of decorators.")

    state = make_state(questions=[{
        "id": "q1",
        "text": "What is a Python decorator?",
        "answer": "A decorator wraps a function to extend its behavior.",
        "score": None,
        "feedback": None,
    }])

    with patch("app.agent.nodes._eval_chain") as mock_chain:
        mock_chain.ainvoke = AsyncMock(return_value=eval_result)
        result = await evaluate_answer_node(state)

    updated = result["questions"][0]
    assert updated["score"] == 8.5
    assert "Good explanation" in updated["feedback"]


@pytest.mark.asyncio
async def test_evaluate_skips_when_no_unevaluated_answer():
    """No-op if all questions already have scores."""
    state = make_state(questions=[{
        "id": "q1", "text": "Q?", "answer": "A", "score": 7.0, "feedback": "ok"
    }])
    result = await evaluate_answer_node(state)
    assert result == {}


# ── summarize ─────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_summarize_node():
    """_summary_chain.ainvoke returns a SummaryResult Pydantic object."""
    summary_result = SummaryResult(overall_score=75.0, report="Solid Python knowledge.")

    state = make_state(questions=[
        {"id": "q1", "text": "Q1", "answer": "A1", "score": 7.0, "feedback": "Good"},
        {"id": "q2", "text": "Q2", "answer": "A2", "score": 8.0, "feedback": "Great"},
    ])

    with patch("app.agent.nodes._summary_chain") as mock_chain:
        mock_chain.ainvoke = AsyncMock(return_value=summary_result)
        result = await summarize_node(state)

    assert result["overall_score"] == 75.0
    assert result["completed"] is True
    assert "Solid" in result["report"]


# ── router ────────────────────────────────────────────────────────────────────────

def test_should_continue_keep_asking():
    state = make_state(current_question_index=2, max_questions=5)
    assert should_continue(state) == "ask_question"


def test_should_continue_summarize():
    state = make_state(current_question_index=5, max_questions=5)
    assert should_continue(state) == "summarize"
