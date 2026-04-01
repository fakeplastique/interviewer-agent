# MockAI — AI Mock Interview Platform

A full-stack, production-ready prototype for an AI-powered mock interview service.

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.12, FastAPI, SQLAlchemy (async) |
| AI Agent | LangGraph + LangChain + GPT-4o |
| Message Bus | Apache Kafka (via aiokafka) |
| Database | PostgreSQL 16 |
| Cache | Redis 7 |
| Frontend | Next.js 14 (App Router, TypeScript) |
| Auth | JWT (python-jose + bcrypt) |
| DevOps | Docker Compose |

## Architecture

```
Browser ←→ Next.js ←→ FastAPI REST
                           ↕ WebSocket (real-time)
                       Kafka Topics
                           ↕
                      LangGraph Agent
                       (GPT-4o)
                           ↕
                       PostgreSQL
```

### Kafka Topics
| Topic | Purpose |
|---|---|
| `interview.started` | Triggers agent initialization |
| `interview.answer` | Routes user answer to agent |
| `interview.feedback` | Agent → WebSocket → browser |
| `interview.completed` | Final report saved to DB |

## Quick Start

### 1. Configure environment
```bash
cp .env.example .env
# Add your OPENAI_API_KEY to .env
```

### 2. Start all services
```bash
docker compose up --build
```

### 3. Open the app
- **Frontend**: http://localhost:3000
- **API Docs**: http://localhost:8000/api/docs

## Development (without Docker)

### Backend
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

### Run tests
```bash
cd backend
pip install aiosqlite  # for SQLite test DB
pytest tests/ -v --cov=app --cov-report=term-missing
```

## Project Structure
```
interview-mocker/
├── backend/
│   ├── app/
│   │   ├── agent/          # LangGraph nodes, graph, state
│   │   ├── api/routes/     # FastAPI routers (auth, interviews, websocket)
│   │   ├── kafka/          # Producer & consumer
│   │   ├── models/         # SQLAlchemy ORM models
│   │   ├── schemas/        # Pydantic schemas
│   │   ├── db.py           # Async engine
│   │   ├── config.py       # Settings
│   │   └── main.py         # App entry point
│   └── tests/              # pytest test suite
└── frontend/
    └── src/
        ├── app/            # Next.js App Router pages
        ├── components/     # Shared UI components
        └── lib/            # API client, WebSocket, auth context
```

## Interview Flow
1. User creates an interview (topic + level)
2. Backend publishes `interview.started` to Kafka
3. LangGraph agent generates questions via GPT-4o
4. Each question is pushed to browser via WebSocket
5. User submits answer → `interview.answer` Kafka event
6. Agent evaluates answer, scores 0-10, gives feedback
7. After N questions → summarize node generates full report
8. `interview.completed` event persists final score to DB
