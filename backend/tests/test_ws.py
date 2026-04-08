"""WebSocket authorization tests (IDOR regression)."""

import uuid

import pytest

from app.api.deps import create_access_token
from app.api.routes.ws import WS_FORBIDDEN, WS_UNAUTHORIZED, authorize_ws
from app.models.interview import Interview, InterviewLevel, User


@pytest.fixture
async def owner_other_interview(db_session):
    owner = User(email=f"{uuid.uuid4().hex}@example.com", hashed_password="x")
    other = User(email=f"{uuid.uuid4().hex}@example.com", hashed_password="x")
    db_session.add_all([owner, other])
    await db_session.flush()
    interview = Interview(user_id=owner.id, topic="Python", level=InterviewLevel.junior)
    db_session.add(interview)
    await db_session.flush()
    return owner, other, interview


async def test_missing_token_rejected(db_session, owner_other_interview):
    _, _, interview = owner_other_interview
    assert await authorize_ws(None, str(interview.id), db_session) == WS_UNAUTHORIZED


async def test_garbage_token_rejected(db_session, owner_other_interview):
    _, _, interview = owner_other_interview
    assert await authorize_ws("not-a-jwt", str(interview.id), db_session) == WS_UNAUTHORIZED


async def test_foreign_interview_rejected(db_session, owner_other_interview):
    _, other, interview = owner_other_interview
    token = create_access_token(other.id)
    assert await authorize_ws(token, str(interview.id), db_session) == WS_FORBIDDEN


async def test_malformed_interview_id_rejected(db_session, owner_other_interview):
    owner, _, _ = owner_other_interview
    token = create_access_token(owner.id)
    assert await authorize_ws(token, "not-a-uuid", db_session) == WS_FORBIDDEN


async def test_owner_allowed(db_session, owner_other_interview):
    owner, _, interview = owner_other_interview
    token = create_access_token(owner.id)
    assert await authorize_ws(token, str(interview.id), db_session) is None
