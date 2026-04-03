import uuid
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr
from app.models.interview import InterviewLevel, InterviewStatus


# ── User ──────────────────────────────────────────────────────────────────────

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: Optional[str] = None


class UserOut(BaseModel):
    id: uuid.UUID
    email: str
    full_name: Optional[str] = None
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
    answer: Optional[str] = None
    score: Optional[float] = None
    feedback: Optional[str] = None
    order: int
    asked_at: datetime
    answered_at: Optional[datetime] = None

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
    score: Optional[float] = None
    report: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None
    questions: List[QuestionOut] = []

    model_config = {"from_attributes": True}


class AnswerSubmit(BaseModel):
    question_id: uuid.UUID
    answer: str


# ── WebSocket messages ────────────────────────────────────────────────────────

class WSMessage(BaseModel):
    type: str        # "question" | "feedback" | "completed" | "error"
    payload: dict
