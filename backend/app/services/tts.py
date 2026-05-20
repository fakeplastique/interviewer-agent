import httpx

from app.config import settings


async def text_to_speech(text: str) -> bytes:
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{settings.ELEVENLABS_VOICE_ID}"

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            url,
            headers={
                "Accept": "audio/mpeg",
                "Content-Type": "application/json",
                "xi-api-key": settings.ELEVENLABS_API_KEY,
            },
            json={
                "text": text,
                "model_id": "eleven_multilingual_v2",
                "speed": 1.2,
                "voice_settings": {
                    "stability": 0.35,
                    "similarity_boost": 0.75,
                    "style": 0.75,
                    "use_speaker_boost": True,
                },
            },
        )
        response.raise_for_status()
        return response.content
