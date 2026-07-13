# Interview Mocker — AI-Powered Mock Interview Platform

An interactive web platform for practicing job interviews with an AI character. Built with Next.js, FastAPI, and LangGraph, powered by Anthropic's Claude API.

## Features

- **AI Interview Characters**: Realistic interviewer personalities that ask follow-up questions
- **Real-time Feedback**: WebSocket-powered speech bubbles and instant character responses
- **Text-to-Speech**: Natural speech synthesis with ElevenLabs integration
- **Interview Analytics**: Performance scoring and detailed feedback
- **Async-first Backend**: Built with FastAPI and Kafka for scalable real-time processing

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.12, FastAPI, asyncio |
| AI Agent | LangGraph + LangChain + Claude (Anthropic API) |
| Message Bus | Apache Kafka (via aiokafka) |
| Database | PostgreSQL (dev/prod), SQLite (tests only) |
| Speech | ElevenLabs TTS API |
| Frontend | Next.js 14 (App Router, TypeScript, React) |
| DevOps | Docker, Docker Compose, Railway |

## Architecture

```
Browser (Next.js) ←→ FastAPI REST API
      ↓                    ↓
   WebSocket          Kafka Producer
      ↑                    ↓
      └─ Kafka Consumer ←→ LangGraph Agent
                           (Claude)
                             ↓
                        PostgreSQL/SQLite
```

### Core Flows

**Interview Start**
1. User creates interview session
2. Backend publishes `interview.started` event to Kafka
3. LangGraph agent initializes with character context
4. First question generated via Claude API
5. Message streamed to browser via WebSocket

**User Response**
1. User answers question (text input)
2. Frontend sends answer via REST API
3. Backend publishes `interview.answer` event
4. Agent evaluates response and generates follow-up/feedback
5. Real-time updates pushed via WebSocket + optional TTS

**Interview Completion**
1. After configured question count, summarization node runs
2. Claude generates detailed feedback and score
3. Final report persisted to database
4. Results displayed to user with analytics

## Quick Start

### 1. Configure environment
```bash
cp .env.example .env
# Add your ANTHROPIC_API_KEY and ELEVENLABS_API_KEY
```

### 2. Start all services
```bash
docker compose up --build
```

### 3. Open the app
- **Frontend**: http://localhost:3000
- **API Docs**: http://localhost:8000/api/docs
- **Health Check**: http://localhost:8000/health

## Development (without Docker)

### Prerequisites
- Python 3.12+
- Node.js 20+
- Kafka (or use mock producer/consumer for testing)

### Backend
```bash
cd backend
pip install -r requirements-dev.txt
export ANTHROPIC_API_KEY=your_key_here
export ELEVENLABS_API_KEY=your_key_here
uvicorn app.main:app --reload --port 8000
```

### Frontend
```bash
cd frontend
npm install
npm run dev
# Opens http://localhost:3000
```

### Run tests
```bash
cd backend
pytest tests/ -v --cov=app --cov-report=term-missing

# Run evaluation tests (requires ANTHROPIC_API_KEY)
pytest tests/evals/ -m eval -v
```

## Project Structure
```
interview-mocker/
├── backend/
│   ├── app/
│   │   ├── agent/          # LangGraph interview agent
│   │   │   ├── graph.py    # Agentic loop
│   │   │   ├── nodes.py    # Question, evaluate, summarize
│   │   │   └── state.py    # Interview state schema
│   │   ├── api/
│   │   │   ├── routes/     # FastAPI routers
│   │   │   │   ├── interviews.py
│   │   │   │   ├── character.py
│   │   │   │   ├── tts.py
│   │   │   │   ├── users.py
│   │   │   │   └── ws.py   # WebSocket
│   │   │   └── deps.py     # Dependency injection
│   │   ├── kafka/          # Event streaming
│   │   │   ├── producer.py
│   │   │   └── consumer.py
│   │   ├── services/
│   │   │   ├── llm.py      # Anthropic chat clients
│   │   │   └── tts.py      # ElevenLabs TTS
│   │   ├── models/         # Domain models
│   │   ├── schemas/        # Pydantic schemas
│   │   ├── core/           # Utilities (logging, rate limiting)
│   │   ├── prompts/        # Interview character definitions
│   │   ├── db.py           # Database initialization
│   │   ├── config.py       # Settings
│   │   └── main.py         # Application factory
│   ├── requirements.txt    # Production deps
│   ├── requirements-dev.txt # Dev + test deps
│   └── tests/              # pytest test suite
├── frontend/
│   ├── src/
│   │   ├── app/            # Next.js App Router
│   │   │   ├── interview/  # Interview UI
│   │   │   ├── dashboard/  # Session browser
│   │   │   └── results/    # Interview report
│   │   ├── components/     # React components
│   │   │   ├── CharacterPanel.tsx
│   │   │   └── Navbar.tsx
│   │   └── lib/            # Client utilities
│   │       ├── ws.ts       # WebSocket manager
│   │       ├── api.ts      # HTTP client
│   │       └── auth.tsx    # Auth context
│   └── package.json
├── evals/                  # LLM evaluation configs
│   ├── *.config.yaml       # Promptfoo configs
│   └── datasets/           # Test data
├── docker-compose.yml
├── Dockerfile              # Frontend container
└── .env.example            # Configuration template
```

## Environment Variables

Required:
- `ANTHROPIC_API_KEY`: Claude API key from Anthropic
- `ELEVENLABS_API_KEY`: Text-to-speech API key

Optional:
- `ALLOWED_ORIGINS`: CORS origins (default: `http://localhost:3000`)
- `DATABASE_URL`: PostgreSQL connection string (defaults to a local Postgres instance; the test suite always uses in-memory SQLite regardless of this setting)
- `ENVIRONMENT`: `development` (default) or `production` — production rejects the default/short `SECRET_KEY`
- `KAFKA_BROKERS`: Kafka bootstrap servers
- `LLM_TIMEOUT_SECONDS`: API timeout (default: 30)
