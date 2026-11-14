import os
import uuid
import requests
from typing import Optional
from app.core.logging import logger

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DEFAULT_STATIC_AUDIO_DIR = os.path.join(BASE_DIR, "static", "audio")

class AudioService:
    """
    Unified Audio & Speech synthesis service.
    Decoupled from specific TTS vendors (ElevenLabs, gTTS, etc.).
    """

    def __init__(self, static_audio_dir: Optional[str] = None):
        self.static_audio_dir = static_audio_dir or DEFAULT_STATIC_AUDIO_DIR
        os.makedirs(self.static_audio_dir, exist_ok=True)

    def synthesize_to_file(self, text: str, lang_code: str = "en", filename: Optional[str] = None) -> Optional[str]:
        """
        Synthesizes text into an MP3 file and returns the file path.
        """
        if not text or not text.strip():
            return None

        clean_filename = filename or f"speech_{uuid.uuid4().hex[:12]}.mp3"
        filepath = os.path.join(self.static_audio_dir, clean_filename)

        # 1. Try ElevenLabs if explicitly configured and key present
        elevenlabs_key = os.environ.get("ELEVENLABS_API_KEY")
        voice_id = os.environ.get("ELEVENLABS_VOICE_ID")

        if elevenlabs_key and voice_id:
            try:
                url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
                headers = {
                    "xi-api-key": elevenlabs_key,
                    "Content-Type": "application/json",
                    "accept": "audio/mpeg"
                }
                payload = {
                    "text": text,
                    "model_id": "eleven_multilingual_v2",
                    "voice_settings": {"stability": 0.5, "similarity_boost": 0.75}
                }
                response = requests.post(url, json=payload, headers=headers, timeout=10)
                if response.status_code == 200:
                    with open(filepath, "wb") as f:
                        f.write(response.content)
                    return filepath
            except Exception as e:
                logger.warning("ElevenLabs synthesis failed, trying fallback", error=str(e))

        # 2. High-quality zero-cost Microsoft Edge Neural TTS
        try:
            import asyncio
            import edge_tts

            edge_voice = os.environ.get("EDGE_TTS_VOICE", "en-US-JennyNeural")
            if lang_code.startswith("hi"):
                edge_voice = "hi-IN-SwaraNeural"
            elif lang_code.startswith("in"):
                edge_voice = "en-IN-NeerjaNeural"

            async def run_edge_tts():
                communicate = edge_tts.Communicate(text, edge_voice)
                await communicate.save(filepath)

            asyncio.run(run_edge_tts())
            if os.path.exists(filepath) and os.path.getsize(filepath) > 0:
                return filepath
        except Exception as edge_err:
            logger.warning("Edge-TTS synthesis unavailable or failed, falling back to gTTS", error=str(edge_err))

        # 3. Secondary fallback to gTTS
        try:
            from gtts import gTTS
            tts = gTTS(text=text, lang=lang_code)
            tts.save(filepath)
            return filepath
        except Exception as e:
            logger.warning("gTTS synthesis unavailable or failed", error=str(e))

        return None

    def synthesize_speech_url(self, text: str, base_url: str = "", lang_code: str = "en") -> Optional[str]:
        """Synthesizes speech and returns a public URL for TwiML <Play> or web audio playback."""
        filepath = self.synthesize_to_file(text, lang_code=lang_code)
        if not filepath:
            return None

        filename = os.path.basename(filepath)
        clean_base = base_url.rstrip("/") if base_url else ""
        return f"{clean_base}/static/audio/{filename}"

# Global audio service
audio_service = AudioService()
