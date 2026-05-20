import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr

from app.models.interview import InterviewLevel, InterviewStatus

# ── User ──────────────────────────────────────────────────────────────────────


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str | None = None


class UserOut(BaseModel):
    id: uuid.UUID
    email: str
    full_name: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


# ── Question ──────────────────────────────────────────────────────────────────


class QuestionOut(BaseModel):
    id: uuid.UUID
    text: str
    answer: str | None = None
    score: float | None = None
    feedback: str | None = None
    order: int
    asked_at: datetime
    answered_at: datetime | None = None

    model_config = {"from_attributes": True}


# ── Interview ─────────────────────────────────────────────────────────────────


class InterviewCreate(BaseModel):
    topic: str
    level: InterviewLevel


class InterviewOut(BaseModel):
    id: uuid.UUID
    topic: str
    level: InterviewLevel
    status: InterviewStatus
    score: float | None = None
    report: str | None = None
    created_at: datetime
    completed_at: datetime | None = None
    questions: list[QuestionOut] = []

    model_config = {"from_attributes": True}


class AnswerSubmit(BaseModel):
    question_id: uuid.UUID
    answer: str


# ── WebSocket messages ────────────────────────────────────────────────────────


class WSMessage(BaseModel):
    type: str  # "question" | "feedback" | "completed" | "error"
    payload: dict
