"""LangGraph interview agent state definition."""
from typing import TypedDict, List, Optional, Annotated
import operator


class QuestionRecord(TypedDict):
    id: str
    text: str
    answer: Optional[str]
    score: Optional[float]
    feedback: Optional[str]


class InterviewState(TypedDict):
    """Shared state passed between all LangGraph nodes."""
    interview_id: str
    topic: str
    level: str                              # junior | middle | senior
    questions: Annotated[List[QuestionRecord], operator.add]
    current_question_index: int
    max_questions: int
    greeting_sent: bool
    completed: bool
    overall_score: Optional[float]
    report: Optional[str]
    error: Optional[str]
