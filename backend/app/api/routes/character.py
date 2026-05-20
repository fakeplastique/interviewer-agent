import json

from anthropic import AsyncAnthropic
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse  # noqa: F401 — resolved at runtime via starlette
from pydantic import BaseModel

from app.api.deps import get_current_user
from app.config import settings
from app.models.interview import User

router = APIRouter(prefix="/character", tags=["character"])
_client = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)


class ReactRequest(BaseModel):
    question: str
    answer: str
    feedback: str
    score: float
    lang: str = "pl"


class ReactResponse(BaseModel):
    text: str


def _pick_prompt(lang: str, positive: bool) -> str:
    prompts = {
        ("pl", True): settings.CHARACTER_SYSTEM_PROMPT_POSITIVE_PL,
        ("pl", False): settings.CHARACTER_SYSTEM_PROMPT_NEGATIVE_PL,
        ("ua", True): settings.CHARACTER_SYSTEM_PROMPT_POSITIVE_UA,
        ("ua", False): settings.CHARACTER_SYSTEM_PROMPT_NEGATIVE_UA,
    }
    return prompts.get((lang, positive), settings.CHARACTER_SYSTEM_PROMPT_POSITIVE_PL)


def _build_user_message(body: ReactRequest) -> str:
    return (
        f"Question: {body.question}\n"
        f"Candidate's answer: {body.answer}\n"
        f"Score: {body.score}/10\n"
        f"Evaluator feedback: {body.feedback}"
    )


@router.post("/react/stream")
async def react_stream(
    body: ReactRequest,
    current_user: User = Depends(get_current_user),
):
    prompt = _pick_prompt(body.lang, body.score > 5)

    async def generate():
        try:
            async with _client.messages.stream(
                model=settings.ANTHROPIC_MODEL,
                max_tokens=200,
                system=prompt,
                messages=[{"role": "user", "content": _build_user_message(body)}],
            ) as stream:
                async for token in stream.text_stream:
                    yield f"data: {json.dumps({'token': token})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
        finally:
            yield "data: [DONE]\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"X-Accel-Buffering": "no", "Cache-Control": "no-cache"},
    )
