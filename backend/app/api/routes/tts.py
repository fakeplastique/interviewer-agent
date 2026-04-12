from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel

from app.api.deps import get_current_user
from app.models.interview import User
from app.services.tts import text_to_speech
from app.config import settings

router = APIRouter(prefix="/tts", tags=["tts"])


class TTSRequest(BaseModel):
    text: str


@router.post("/speak")
async def speak(
    body: TTSRequest,
    current_user: User = Depends(get_current_user),
):
    if not settings.ELEVENLABS_API_KEY:
        raise HTTPException(status_code=503, detail="TTS not configured — set ELEVENLABS_API_KEY")
    try:
        audio = await text_to_speech(body.text)
        return Response(content=audio, media_type="audio/mpeg")
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"TTS service error: {e}")
