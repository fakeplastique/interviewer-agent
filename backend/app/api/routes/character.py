import json
import logging
from typing import Literal

from anthropic import AsyncAnthropic
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse  # noqa: F401 — resolved at runtime via starlette
from pydantic import BaseModel, Field

from app.api.deps import get_current_user
from app.config import settings
from app.models.interview import User
from app.prompts import Prompt, get_prompt

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/character", tags=["character"])
_client = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)


class ReactRequest(BaseModel):
    question: str
    answer: str = Field(max_length=5000)
    feedback: str
    score: float = Field(ge=0, le=10)
    lang: Literal["ua"] = "ua"


class ReactResponse(BaseModel):
    text: str


def _pick_prompt(positive: bool) -> Prompt:
    return get_prompt("character.positive.ua" if positive else "character.negative.ua")


def _build_user_message(body: ReactRequest) -> str:
    return (
        f"<question>{body.question}</question>\n"
        f"<candidate_answer>{body.answer}</candidate_answer>\n"
        f"<score>{body.score}/10</score>\n"
        f"<evaluator_feedback>{body.feedback}</evaluator_feedback>"
    )


@router.post("/react/stream")
async def react_stream(
    body: ReactRequest,
    current_user: User = Depends(get_current_user),
):
    prompt = _pick_prompt(body.score > 5)

    async def generate():
        try:
            async with _client.messages.stream(
                model=settings.ANTHROPIC_MODEL,
                max_tokens=prompt.params["max_tokens"],
                temperature=prompt.params["temperature"],
                system=prompt.template,
                messages=[{"role": "user", "content": _build_user_message(body)}],
            ) as stream:
                async for token in stream.text_stream:
                    yield f"data: {json.dumps({'token': token})}\n\n"
        except Exception:
            logger.exception("Character reaction generation failed")
            yield f"data: {json.dumps({'error': 'generation_failed'})}\n\n"
        finally:
            yield "data: [DONE]\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"X-Accel-Buffering": "no", "Cache-Control": "no-cache"},
    )
