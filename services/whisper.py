import io
import logging

from openai import AsyncOpenAI

from config import OPENAI_API_KEY

logger = logging.getLogger(__name__)
client = AsyncOpenAI(api_key=OPENAI_API_KEY)


async def transcribe_voice(voice_bytes: bytes) -> str | None:
    """Transcribe voice message bytes (OGG) via OpenAI Whisper.

    Returns transcribed text or None on error.
    """
    try:
        buf = io.BytesIO(voice_bytes)
        buf.name = "voice.ogg"
        response = await client.audio.transcriptions.create(
            model="whisper-1",
            file=buf,
            language="ru",
        )
        return response.text
    except Exception:
        logger.exception("Whisper transcription failed")
        return None
