"""Local voice features: speech-to-text (faster-whisper) and TTS (Piper).

Both run fully offline on CPU, consistent with the project's no-paid-API
constraint. Heavy libraries are imported inside the loaders so the rest of
the app works even when the voice dependencies are not installed; the
Streamlit layer caches the loaded models.
"""
from __future__ import annotations

import io
import re
import wave
from pathlib import Path

import requests

from . import config

_VOICES_REPO = "https://huggingface.co/rhasspy/piper-voices/resolve/main"


def clean_for_speech(text: str) -> str:
    """Markdown, [n] citations and URLs sound terrible when read aloud."""
    text = re.sub(r"\[([^\]]+)\]\(\s*[^)]*\)", r"\1", text)  # [label](url) -> label
    text = re.sub(r"\[\d+\]", "", text)  # [1] citation markers
    text = re.sub(r"https?://\S+", "", text)  # bare URLs
    text = re.sub(r"[*_#`]+", "", text)  # emphasis / headers / code marks
    text = re.sub(r"^\s*[-•]\s+", "", text, flags=re.MULTILINE)  # bullet dashes
    text = re.sub(r"[ \t]+", " ", text)
    return text.strip()


# --- Text-to-speech (Piper) ---


def _ensure_voice_files() -> Path:
    """Download the Piper voice (~60 MB, once) into data/voices/."""
    config.VOICES_DIR.mkdir(parents=True, exist_ok=True)
    lang, name, quality = config.PIPER_VOICE.split("-", 2)
    base = f"{_VOICES_REPO}/{lang.split('_')[0]}/{lang}/{name}/{quality}"
    for suffix in (".onnx", ".onnx.json"):
        target = config.VOICES_DIR / f"{config.PIPER_VOICE}{suffix}"
        if not target.exists():
            resp = requests.get(f"{base}/{config.PIPER_VOICE}{suffix}", timeout=300)
            resp.raise_for_status()
            target.write_bytes(resp.content)
    return config.VOICES_DIR / f"{config.PIPER_VOICE}.onnx"


def load_tts():
    from piper import PiperVoice  # heavy import, deferred

    return PiperVoice.load(str(_ensure_voice_files()))


def synthesize(tts, text: str) -> bytes:
    """Return WAV bytes for the given text."""
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as wav_file:
        tts.synthesize_wav(text, wav_file)
    return buffer.getvalue()


# --- Speech-to-text (faster-whisper) ---


def load_stt():
    from faster_whisper import WhisperModel  # heavy import, deferred

    return WhisperModel(config.WHISPER_MODEL, device="cpu", compute_type="int8")


def transcribe(stt, wav_bytes: bytes) -> str:
    """Transcribe recorded audio to French text."""
    segments, _info = stt.transcribe(
        io.BytesIO(wav_bytes), language="fr", vad_filter=True
    )
    return " ".join(seg.text.strip() for seg in segments).strip()
