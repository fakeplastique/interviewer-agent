"""LangGraph interview agent state definition."""

import operator
from typing import Annotated, TypedDict


class QuestionRecord(TypedDict):
    id: str
    text: str
    answer: str | None
    score: float | None
    feedback: str | None


class InterviewState(TypedDict):
    """Shared state passed between all LangGraph nodes."""

    interview_id: str
    topic: str
    level: str  # junior | middle | senior
    questions: Annotated[list[QuestionRecord], operator.add]
    current_question_index: int
    max_questions: int
    greeting_sent: bool
    completed: bool
    overall_score: float | None
    report: str | None
    error: str | None
