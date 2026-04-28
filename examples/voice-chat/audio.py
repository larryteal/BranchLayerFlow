"""Audio I/O + voice activity detection (VAD) helpers."""

import io
import os
from pathlib import Path
from typing import List, Optional

import numpy as np
import sounddevice as sd
import soundfile as sf
from openai import OpenAI


SAMPLE_RATE = 16000
SILENCE_RMS = 0.01
SILENCE_FRAMES = int(SAMPLE_RATE * 0.8)  # 0.8s of trailing silence

_client: Optional[OpenAI] = None


def _c() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    return _client


def record_until_silent(max_seconds: int = 15) -> np.ndarray:
    """Record from default mic until trailing silence is detected."""
    print("(listening...)", flush=True)
    chunks: List[np.ndarray] = []
    silent_run = 0
    with sd.InputStream(samplerate=SAMPLE_RATE, channels=1, dtype="float32") as stream:
        for _ in range(int(max_seconds * SAMPLE_RATE / 1024)):
            block, _ = stream.read(1024)
            chunks.append(block)
            rms = float(np.sqrt(np.mean(block ** 2)))
            if rms < SILENCE_RMS:
                silent_run += len(block)
                if silent_run > SILENCE_FRAMES and len(chunks) > 5:
                    break
            else:
                silent_run = 0
    return np.concatenate(chunks).flatten()


def transcribe(audio: np.ndarray) -> str:
    buf = io.BytesIO()
    sf.write(buf, audio, SAMPLE_RATE, format="WAV")
    buf.name = "speech.wav"
    buf.seek(0)
    return _c().audio.transcriptions.create(model="whisper-1", file=buf).text


def speak(text: str) -> None:
    resp = _c().audio.speech.create(model="tts-1", voice="alloy", input=text)
    buf = io.BytesIO(resp.read())
    audio, sr = sf.read(buf, dtype="float32")
    sd.play(audio, sr)
    sd.wait()
