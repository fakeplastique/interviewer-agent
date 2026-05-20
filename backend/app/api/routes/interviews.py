"""Interview CRUD + session control routes."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_current_user
from app.config import settings
from app.db import get_db
from app.kafka.producer import publish
from app.models.interview import Interview, InterviewStatus, User
from app.schemas.interview import AnswerSubmit, InterviewCreate, InterviewOut

router = APIRouter(prefix="/interviews", tags=["interviews"])


@router.post("", response_model=InterviewOut, status_code=status.HTTP_201_CREATED)
async def create_interview(
    body: InterviewCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    interview = Interview(
        user_id=current_user.id,
        topic=body.topic,
        level=body.level,
    )
    db.add(interview)
    await db.flush()
    await db.refresh(interview)
    await db.refresh(interview, attribute_names=["questions"])
    return interview


@router.get("", response_model=list[InterviewOut])
async def list_interviews(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Interview)
        .where(Interview.user_id == current_user.id)
        .options(selectinload(Interview.questions))
        .order_by(Interview.created_at.desc())
    )
    return result.scalars().all()


@router.get("/{interview_id}", response_model=InterviewOut)
async def get_interview(
    interview_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Interview)
        .where(Interview.id == interview_id, Interview.user_id == current_user.id)
        .options(selectinload(Interview.questions))
    )
    interview = result.scalar_one_or_none()
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found")
    return interview


@router.post("/{interview_id}/start", response_model=InterviewOut)
async def start_interview(
    interview_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Interview)
        .where(Interview.id == interview_id, Interview.user_id == current_user.id)
        .options(selectinload(Interview.questions))
    )
    interview = result.scalar_one_or_none()
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found")
    if interview.status != InterviewStatus.pending:
        raise HTTPException(status_code=400, detail=f"Interview is already {interview.status}")

    await publish(
        settings.KAFKA_TOPIC_INTERVIEW_STARTED,
        {
            "interview_id": str(interview.id),
            "topic": interview.topic,
            "level": interview.level,
        },
    )
    return interview


@router.post("/{interview_id}/answer", response_model=dict)
async def submit_answer(
    interview_id: uuid.UUID,
    body: AnswerSubmit,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Interview).where(Interview.id == interview_id, Interview.user_id == current_user.id)
    )
    interview = result.scalar_one_or_none()
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found")
    if interview.status != InterviewStatus.active:
        raise HTTPException(status_code=400, detail="Interview is not active")

    await publish(
        settings.KAFKA_TOPIC_ANSWER,
        {
            "interview_id": str(interview_id),
            "question_id": str(body.question_id),
            "answer": body.answer,
        },
    )
    return {"status": "answer_received"}


@router.delete("/{interview_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_interview(
    interview_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Interview).where(Interview.id == interview_id, Interview.user_id == current_user.id)
    )
    interview = result.scalar_one_or_none()
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found")
    await db.delete(interview)
