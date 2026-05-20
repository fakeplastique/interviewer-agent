import logging
import uuid
from typing import Any

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, Field

from app.agent.state import InterviewState, QuestionRecord
from app.config import settings

logger = logging.getLogger(__name__)

# ── LLM singleton ────────────────────────────────────────────────────────────────
#   temperature=0 для evaluate/summarize — детермінований JSON
#   temperature=0.8 для ask_question — різноманітні питання

_llm = ChatAnthropic(
    model=settings.ANTHROPIC_MODEL,
    api_key=settings.ANTHROPIC_API_KEY,
)


# ── Pydantic-схеми для structured output ────────────────────────────────────────


class EvaluationResult(BaseModel):
    """Результат оцінки однієї відповіді кандидата."""

    score: float = Field(ge=0, le=10, description="Score from 0 to 10")
    feedback: str = Field(description="Constructive 2-3 sentence feedback")


class SummaryResult(BaseModel):
    """Фінальний звіт після всього інтерв'ю."""

    overall_score: float = Field(ge=0, le=100, description="Overall score 0-100")
    report: str = Field(description="3-5 sentence performance summary")


# ── Спеціалізовані LLM-chains через .with_structured_output() ───────────────────
#   Повертають типізований Pydantic-об'єкт, не рядок

_eval_chain = _llm.with_structured_output(EvaluationResult)
_summary_chain = _llm.with_structured_output(SummaryResult)


# ── Prompts ──────────────────────────────────────────────────────────────────────

QUESTION_SYSTEM = (
    "You are a professional technical interviewer. "
    "Generate ONE open-ended interview question for a {level} {topic} developer. "
    "The question must probe genuine understanding, not memorized facts. "
    "Return ONLY the question text."
)

EVALUATE_SYSTEM = (
    "You are evaluating a technical interview answer. " "Topic: {topic} | Candidate level: {level}"
)

SUMMARIZE_SYSTEM = (
    "You are summarizing a completed technical interview session. "
    "Topic: {topic} | Candidate level: {level}. "
    "Evaluate overall performance based on all questions and answers below."
)


# ── LangGraph nodes ──────────────────────────────────────────────────────────────


async def greet_node(state: InterviewState) -> dict[str, Any]:
    """Стартовий вузол — позначає що привітання надіслано."""
    logger.info(
        "greet_node | interview=%s topic=%s level=%s",
        state["interview_id"],
        state["topic"],
        state["level"],
    )
    return {"greeting_sent": True}


async def ask_question_node(state: InterviewState) -> dict[str, Any]:
    """Генерує наступне питання через ChatAnthropic і додає його до стану."""
    if state["questions"]:
        prev = "\n".join(f"- {q['text']}" for q in state["questions"])
        human_content = f"Already asked:\n{prev}\n\nGenerate a different question."
    else:
        human_content = "Generate the first question."

    messages = [
        SystemMessage(content=QUESTION_SYSTEM.format(level=state["level"], topic=state["topic"])),
        HumanMessage(content=human_content),
    ]

    response = await _llm.ainvoke(messages)
    question_text: str = response.content.strip()

    new_question: QuestionRecord = {
        "id": str(uuid.uuid4()),
        "text": question_text,
        "answer": None,
        "score": None,
        "feedback": None,
    }
    logger.info(
        "ask_question_node | q#%d: %.80s",
        state["current_question_index"] + 1,
        question_text,
    )
    return {
        "questions": [new_question],
        "current_question_index": state["current_question_index"] + 1,
    }


async def evaluate_answer_node(state: InterviewState) -> dict[str, Any]:
    """
    Оцінює останню відповідь кандидата.
    Використовує .with_structured_output(EvaluationResult) —
    LangGraph сам парсить і валідує JSON через Pydantic.
    """
    target = next(
        (q for q in reversed(state["questions"]) if q.get("answer") and q.get("score") is None),
        None,
    )
    if target is None:
        logger.warning("evaluate_answer_node: no unevaluated answer found")
        return {}

    messages = [
        SystemMessage(content=EVALUATE_SYSTEM.format(topic=state["topic"], level=state["level"])),
        HumanMessage(
            content=(f"Question: {target['text']}\n\n" f"Candidate's answer: {target['answer']}")
        ),
    ]

    result: EvaluationResult = await _eval_chain.ainvoke(messages)

    logger.info(
        "evaluate_answer_node | q_id=%s score=%.1f",
        target["id"],
        result.score,
    )

    updated_questions = [
        {**q, "score": result.score, "feedback": result.feedback} if q["id"] == target["id"] else q
        for q in state["questions"]
    ]
    return {"questions": updated_questions}


async def summarize_node(state: InterviewState) -> dict[str, Any]:
    """
    Генерує фінальний звіт.
    Використовує .with_structured_output(SummaryResult).
    """
    qa_block = "\n\n".join(
        f"Q{i}: {q['text']}\n"
        f"A: {q.get('answer') or 'No answer'}\n"
        f"Score: {q.get('score', 'N/A')}/10"
        for i, q in enumerate(state["questions"], 1)
    )

    messages = [
        SystemMessage(content=SUMMARIZE_SYSTEM.format(topic=state["topic"], level=state["level"])),
        HumanMessage(content=qa_block),
    ]

    result: SummaryResult = await _summary_chain.ainvoke(messages)

    logger.info(
        "summarize_node | interview=%s overall_score=%.1f",
        state["interview_id"],
        result.overall_score,
    )
    return {
        "overall_score": result.overall_score,
        "report": result.report,
        "completed": True,
    }


# ── Conditional edge (router) ────────────────────────────────────────────────────


def should_continue(state: InterviewState) -> str:
    """Роутер після evaluate_answer: продовжувати чи підсумовувати."""
    if state["current_question_index"] >= state["max_questions"]:
        return "summarize"
    return "ask_question"
