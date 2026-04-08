"""Tests for Interview API endpoints."""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_register_and_login(client: AsyncClient):
    resp = await client.post(
        "/api/v1/auth/register",
        json={"email": "user1@test.com", "password": "pass123", "full_name": "Alice"},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["email"] == "user1@test.com"

    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "user1@test.com", "password": "pass123"},
    )
    assert resp.status_code == 200
    assert "access_token" in resp.json()


@pytest.mark.asyncio
async def test_create_interview(client: AsyncClient, auth_headers: dict):
    resp = await client.post(
        "/api/v1/interviews",
        json={"topic": "Python", "level": "middle"},
        headers=auth_headers,
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["topic"] == "Python"
    assert data["level"] == "middle"
    assert data["status"] == "pending"


@pytest.mark.asyncio
async def test_list_interviews(client: AsyncClient, auth_headers: dict):
    # Create two interviews
    for topic in ["Python", "System Design"]:
        await client.post(
            "/api/v1/interviews",
            json={"topic": topic, "level": "junior"},
            headers=auth_headers,
        )

    resp = await client.get("/api/v1/interviews", headers=auth_headers)
    assert resp.status_code == 200
    assert len(resp.json()) >= 2


@pytest.mark.asyncio
async def test_get_interview(client: AsyncClient, auth_headers: dict):
    create_resp = await client.post(
        "/api/v1/interviews",
        json={"topic": "FastAPI", "level": "senior"},
        headers=auth_headers,
    )
    interview_id = create_resp.json()["id"]

    resp = await client.get(f"/api/v1/interviews/{interview_id}", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["id"] == interview_id


@pytest.mark.asyncio
async def test_start_interview_publishes_kafka(client: AsyncClient, auth_headers: dict):
    create_resp = await client.post(
        "/api/v1/interviews",
        json={"topic": "Algorithms", "level": "junior"},
        headers=auth_headers,
    )
    interview_id = create_resp.json()["id"]

    resp = await client.post(
        f"/api/v1/interviews/{interview_id}/start", headers=auth_headers
    )
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_get_interview_not_found(client: AsyncClient, auth_headers: dict):
    import uuid
    fake_id = str(uuid.uuid4())
    resp = await client.get(f"/api/v1/interviews/{fake_id}", headers=auth_headers)
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_unauthorized_access(client: AsyncClient):
    resp = await client.get("/api/v1/interviews")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_health_endpoint(client: AsyncClient):
    resp = await client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"
