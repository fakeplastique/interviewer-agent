"""FastAPI application entry point."""

import asyncio
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.character import router as character_router
from app.api.routes.interviews import router as interviews_router
from app.api.routes.tts import router as tts_router
from app.api.routes.users import router as auth_router
from app.api.routes.ws import router as ws_router
from app.api.routes.ws import run_ws_feedback_consumer
from app.config import settings
from app.db import init_db
from app.kafka.consumer import run_consumer
from app.kafka.producer import stop_producer

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s — %(message)s")
logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
        version="1.0.0",
        description="AI-powered mock interview service",
        docs_url="/api/docs",
        redoc_url="/api/redoc",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS.split(","),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(auth_router, prefix="/api/v1")
    app.include_router(interviews_router, prefix="/api/v1")
    app.include_router(tts_router, prefix="/api/v1")
    app.include_router(character_router, prefix="/api/v1")
    app.include_router(ws_router)

    @app.on_event("startup")
    async def startup():
        logger.info("Starting up...")
        await init_db()
        # Start Kafka consumers as background tasks
        asyncio.create_task(run_consumer())
        asyncio.create_task(run_ws_feedback_consumer())
        logger.info("Ready ✓")

    @app.on_event("shutdown")
    async def shutdown():
        logger.info("Shutting down...")
        await stop_producer()

    @app.get("/health", tags=["health"])
    async def health():
        return {"status": "ok", "service": settings.APP_NAME}

    return app


app = create_app()
