import uuid
import enum
from datetime import datetime
from sqlalchemy import (
    Column, String, Float, Integer, DateTime, Enum, ForeignKey, Text
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, DeclarativeBase


class Base(DeclarativeBase):
    pass


class InterviewLevel(str, enum.Enum):
    junior = "junior"
    middle = "middle"
    senior = "senior"


class InterviewStatus(str, enum.Enum):
    pending = "pending"
    active = "active"
    completed = "completed"
    failed = "failed"


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    interviews = relationship("Interview", back_populates="user", cascade="all, delete-orphan")


class Interview(Base):
    __tablename__ = "interviews"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    topic = Column(String(100), nullable=False)   # e.g. "Python", "System Design"
    level = Column(Enum(InterviewLevel), nullable=False)
    status = Column(Enum(InterviewStatus), default=InterviewStatus.pending, nullable=False)
    score = Column(Float, nullable=True)           # 0–100 overall score
    report = Column(Text, nullable=True)           # AI-generated summary report
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    user = relationship("User", back_populates="interviews")
    questions = relationship("Question", back_populates="interview", cascade="all, delete-orphan",
                             order_by="Question.order")


class Question(Base):
    __tablename__ = "questions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    interview_id = Column(UUID(as_uuid=True), ForeignKey("interviews.id", ondelete="CASCADE"), nullable=False)
    text = Column(Text, nullable=False)
    answer = Column(Text, nullable=True)
    score = Column(Float, nullable=True)           # 0–10 per-question score
    feedback = Column(Text, nullable=True)         # AI feedback on this answer
    order = Column(Integer, nullable=False, default=0)
    asked_at = Column(DateTime, default=datetime.utcnow)
    answered_at = Column(DateTime, nullable=True)

    interview = relationship("Interview", back_populates="questions")
