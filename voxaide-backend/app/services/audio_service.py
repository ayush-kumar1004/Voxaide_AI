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

    def synthesize_to_file(
        self,
        text: str,
        lang_code: str = "en",
        filename: Optional[str] = None,
        voice_model: Optional[str] = None,
        provider: Optional[str] = None,
        elevenlabs_api_key: Optional[str] = None,
        elevenlabs_voice_id: Optional[str] = None
    ) -> Optional[str]:
        """
        Synthesizes text into an MP3 file using ElevenLabs (voice cloning) or Edge-TTS (zero-cost).
        """
        if not text or not text.strip():
            return None

        clean_filename = filename or f"speech_{uuid.uuid4().hex[:12]}.mp3"
        filepath = os.path.join(self.static_audio_dir, clean_filename)

        # 1. ElevenLabs Voice Cloning (if provider is elevenlabs, or custom keys passed, or env set)
        is_elevenlabs_requested = (provider == "elevenlabs") or bool(elevenlabs_voice_id)
        elevenlabs_key = elevenlabs_api_key or os.environ.get("ELEVENLABS_API_KEY")
        target_voice_id = elevenlabs_voice_id or (voice_model if is_elevenlabs_requested else None) or os.environ.get("ELEVENLABS_VOICE_ID")

        if is_elevenlabs_requested and elevenlabs_key and target_voice_id:
            try:
                url = f"https://api.elevenlabs.io/v1/text-to-speech/{target_voice_id}"
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
                response = requests.post(url, json=payload, headers=headers, timeout=12)
                if response.status_code == 200:
                    with open(filepath, "wb") as f:
                        f.write(response.content)
                    return filepath
                else:
                    logger.warning("ElevenLabs API returned non-200", status_code=response.status_code, body=response.text[:200])
            except Exception as e:
                logger.warning("ElevenLabs synthesis failed, trying Edge-TTS fallback", error=str(e))

        # 2. High-quality zero-cost Microsoft Edge Neural TTS
        try:
            import asyncio
            import edge_tts

            edge_voice = voice_model or os.environ.get("EDGE_TTS_VOICE", "en-US-JennyNeural")
            # If voice_model was an elevenlabs id, fall back to clean neural voice
            if len(edge_voice) < 30 and ("Neural" in edge_voice):
                pass
            elif lang_code.startswith("hi"):
                edge_voice = "hi-IN-SwaraNeural"
            elif lang_code.startswith("in"):
                edge_voice = "en-IN-NeerjaNeural"
            else:
                edge_voice = "en-US-JennyNeural"

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

    def synthesize_speech_url(
        self,
        text: str,
        base_url: str = "",
        lang_code: str = "en",
        voice_model: Optional[str] = None,
        provider: Optional[str] = None,
        elevenlabs_api_key: Optional[str] = None,
        elevenlabs_voice_id: Optional[str] = None
    ) -> Optional[str]:
        """Synthesizes speech and returns a public URL for TwiML or web audio playback."""
        filepath = self.synthesize_to_file(
            text=text,
            lang_code=lang_code,
            voice_model=voice_model,
            provider=provider,
            elevenlabs_api_key=elevenlabs_api_key,
            elevenlabs_voice_id=elevenlabs_voice_id
        )
        if not filepath:
            return None

        filename = os.path.basename(filepath)
        clean_base = base_url.rstrip("/") if base_url else ""
        return f"{clean_base}/static/audio/{filename}"

    def generate_preview(
        self,
        text: str,
        voice_model: str,
        provider: str = "edge-tts",
        elevenlabs_api_key: Optional[str] = None,
        base_url: str = ""
    ) -> Optional[str]:
        """Generates a short voice preview sample URL."""
        preview_sample = text or f"Hello! I am speaking with the {voice_model} voice model on VoxAide."
        return self.synthesize_speech_url(
            text=preview_sample,
            base_url=base_url,
            voice_model=voice_model,
            provider=provider,
            elevenlabs_api_key=elevenlabs_api_key,
            elevenlabs_voice_id=voice_model if provider == "elevenlabs" else None
        )

# Global audio service
audio_service = AudioService()
