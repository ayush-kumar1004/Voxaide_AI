import os
import uuid
import requests
from typing import Optional
from app.core.logging import logger

class AudioService:
    """
    Unified Audio & Speech synthesis service.
    Decoupled from specific TTS vendors (ElevenLabs, gTTS, etc.).
    """

    def __init__(self, static_audio_dir: str = "static/audio"):
        self.static_audio_dir = static_audio_dir
        os.makedirs(self.static_audio_dir, exist_ok=True)

    def synthesize_to_file(self, text: str, lang_code: str = "en", filename: Optional[str] = None) -> Optional[str]:
        """
        Synthesizes text into an MP3 file and returns the file path.
        """
        if not text or not text.strip():
            return None

        clean_filename = filename or f"speech_{uuid.uuid4().hex[:12]}.mp3"
        filepath = os.path.join(self.static_audio_dir, clean_filename)

        # 1. Try ElevenLabs if configured
        elevenlabs_key = os.environ.get("ELEVENLABS_API_KEY")
        voice_id = os.environ.get("ELEVENLABS_VOICE_ID", "21m00Tcm4TlvDq8ikWAM")

        if elevenlabs_key:
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

        # 2. Fallback to gTTS
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
