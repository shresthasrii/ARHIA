import io
import os
import re
import wave
import tempfile
import logging
from typing import Optional
from pathlib import Path
from backend.config import settings

logger = logging.getLogger("ARHIEA.STT")

def normalize_transcription_text(text: str) -> str:
    """
    Cleans up and normalizes transcription artifacts:
    - Times: 12/7 AM -> 12:07 AM, 5.30 PM -> 5:30 PM, 9 am -> 9:00 AM
    - Spoken math: x square -> x^2, under root 16 -> sqrt(16), 3x square plus 5 -> 3x^2 + 5
    - Punctuation & dictation formatting
    """
    if not text:
        return ""
    
    t = text.strip()

    # 1. Clean leading speech fillers (uh, um, ah, err)
    t = re.sub(r'^(uh|um|ah|err|like)\s*,\s*', '', t, flags=re.IGNORECASE)
    t = re.sub(r'^(uh|um|ah|err)\s+', '', t, flags=re.IGNORECASE)

    # 2. Fix slash or dot time formats e.g. 12/7 AM, 12/07AM, 5.30 PM
    def fix_time_match(m):
        hh = m.group(1)
        mm = int(m.group(2))
        ampm = m.group(3) if m.group(3) else ""
        return f"{hh}:{mm:02d} {ampm.upper()}".strip()

    t = re.sub(r'\b(\d{1,2})[/.](\d{1,2})\s*(am|pm|AM|PM)\b', fix_time_match, t)
    t = re.sub(r'\b(\d{1,2})\s+(\d{1,2})\s*(am|pm|AM|PM)\b', fix_time_match, t)
    
    # Fix standalone 12/7 when representing hour/min
    def fix_slash_standalone(m):
        hh = int(m.group(1))
        mm = int(m.group(2))
        if 1 <= hh <= 12 and 0 <= mm <= 59:
            return f"{hh}:{mm:02d}"
        return m.group(0)

    t = re.sub(r'\b(\d{1,2})/(\d{1,2})\b', fix_slash_standalone, t)

    # Fix standalone hours like "at 9 am" -> "at 9:00 AM" (only when not already part of HH:MM)
    t = re.sub(r'(?<![:\d])\b(\d{1,2})\s*(am|pm)\b', lambda m: f"{m.group(1)}:00 {m.group(2).upper()}", t, flags=re.IGNORECASE)

    # 3. Spoken dictation punctuation commands
    t = re.sub(r'\s+(full stop|period)\b', '.', t, flags=re.IGNORECASE)
    t = re.sub(r'\s+comma\b', ',', t, flags=re.IGNORECASE)
    t = re.sub(r'\s+question mark\b', '?', t, flags=re.IGNORECASE)
    t = re.sub(r'\s+exclamation mark\b', '!', t, flags=re.IGNORECASE)

    # 4. Spoken/phonetic math artifacts and typos
    t = re.sub(r'\b(squre|squar|sqr)\b', 'square', t, flags=re.IGNORECASE)
    t = re.sub(r'\b(squred)\b', 'squared', t, flags=re.IGNORECASE)

    # Roots: "under root", "underroot", "square root of", "cube root of"
    t = re.sub(r'\bunder\s*root\s*(?:of\s+)?(\d+|[a-zA-Z])\b', r'sqrt(\1)', t, flags=re.IGNORECASE)
    t = re.sub(r'\bsquare\s*root\s*of\s+(\d+|[a-zA-Z])\b', r'sqrt(\1)', t, flags=re.IGNORECASE)
    t = re.sub(r'\bcube\s*root\s*of\s+(\d+|[a-zA-Z])\b', r'cbrt(\1)', t, flags=re.IGNORECASE)

    # Calculus: "d by dx" -> "d/dx"
    t = re.sub(r'\bd\s+by\s+d\s*x\b', 'd/dx', t, flags=re.IGNORECASE)

    # Powers: "x to the power of 4", "x raised to 3", "2 power 8"
    t = re.sub(r'(\b\d*[a-zA-Z]\b|\b\d+\b)\s*(?:to\s+the\s+power\s+(?:of\s+)?|power\s+|raised\s+to\s+(?:the\s+power\s+of\s+)?)\s*(\d+|[a-zA-Z])\b', r'\1^\2', t, flags=re.IGNORECASE)

    # Squares: "x square", "3x square", "x squared", "3x squared" -> "x^2", "3x^2"
    t = re.sub(r'(\b\d*[a-zA-Z]\b|\b\d+\b)\s+(?:square|squared)\b', r'\1^2', t, flags=re.IGNORECASE)

    # Cubes: "x cube", "3x cube", "x cubed" -> "x^3", "3x^3"
    t = re.sub(r'(\b\d*[a-zA-Z]\b|\b\d+\b)\s+(?:cube|cubed)\b', r'\1^3', t, flags=re.IGNORECASE)

    # Spoken operators between terms: "3x^2 plus 5" -> "3x^2 + 5"
    operator_replacements = [
        (r'(?<=\S)\s+plus\s+(?=\S)', ' + '),
        (r'(?<=\S)\s+minus\s+(?=\S)', ' - '),
        (r'(?<=\S)\s+(?:multiplied\s+by|into|times)\s+(?=\S)', ' * '),
        (r'(?<=\S)\s+divided\s+by\s+(?=\S)', ' / '),
        (r'(?<=\S)\s+(?:is\s+equal\s+to|equals|equal\s+to)\s+(?=\S)', ' = '),
    ]
    for pat, repl in operator_replacements:
        t = re.sub(pat, repl, t, flags=re.IGNORECASE)

    # Standalone math context conversions
    if any(c in t for c in ['^', '=', 'x', 'y', '+', '-', '*', '/']) or re.search(r'\b(solve|calculate|evaluate|find)\b', t, re.IGNORECASE):
        t = re.sub(r'\bplus\b', '+', t, flags=re.IGNORECASE)
        t = re.sub(r'\bminus\b', '-', t, flags=re.IGNORECASE)
        t = re.sub(r'\b(equals|equal to|is equal to)\b', '=', t, flags=re.IGNORECASE)

    t = re.sub(r'\s+', ' ', t).strip()
    return t

class STTService:
    def __init__(self):
        self.recognizer = None
        self.whisper_model = None
        self._init_recognizer()

    def _init_recognizer(self):
        try:
            import speech_recognition as sr
            self.recognizer = sr.Recognizer()
            self.recognizer.energy_threshold = 300
            self.recognizer.dynamic_energy_threshold = True
            logger.info("SpeechRecognition engine initialized.")
        except Exception as e:
            logger.warning(f"SpeechRecognition init notice: {e}")

    def _convert_to_wav_bytes(self, audio_bytes: bytes) -> Optional[bytes]:
        """Converts arbitrary audio bytes (WebM, MP3, OGG, raw PCM) into standard 16kHz mono WAV bytes."""
        if not audio_bytes:
            return None

        # Check if already a valid RIFF WAV header
        if len(audio_bytes) > 12 and audio_bytes[:4] == b"RIFF" and audio_bytes[8:12] == b"WAVE":
            return audio_bytes

        # Attempt conversion using pydub
        try:
            from pydub import AudioSegment
            seg = AudioSegment.from_file(io.BytesIO(audio_bytes))
            seg = seg.set_frame_rate(16000).set_channels(1).set_sample_width(2)
            out = io.BytesIO()
            seg.export(out, format="wav")
            return out.getvalue()
        except Exception as e:
            logger.debug(f"pydub audio conversion notice: {e}")

        # If already raw PCM, wrap in standard WAV header
        try:
            out = io.BytesIO()
            with wave.open(out, "wb") as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(16000)
                wf.writeframes(audio_bytes)
            return out.getvalue()
        except Exception as ex:
            logger.debug(f"Direct PCM wrap notice: {ex}")

        return audio_bytes

    def transcribe_audio_bytes(self, audio_bytes: bytes) -> str:
        """
        Transcribes audio bytes into clean, normalized text.
        Multi-tier pipeline:
        1. Google Speech Recognition via speech_recognition (Fast, robust, free)
        2. Local Faster-Whisper (if available and loaded)
        3. Normalization of math, times, and punctuation
        """
        if not audio_bytes or len(audio_bytes) < 100:
            return ""

        wav_bytes = self._convert_to_wav_bytes(audio_bytes)
        if not wav_bytes:
            return ""

        # Tier 1: SpeechRecognition (Google Free Speech Engine)
        if self.recognizer:
            try:
                import speech_recognition as sr
                with io.BytesIO(wav_bytes) as audio_file:
                    with sr.AudioFile(audio_file) as source:
                        audio_data = self.recognizer.record(source)
                        raw_text = self.recognizer.recognize_google(audio_data, language="en-US")
                        if raw_text and raw_text.strip():
                            clean = normalize_transcription_text(raw_text)
                            logger.info(f"Transcribed audio (Google STT): '{clean}'")
                            return clean
            except sr.UnknownValueError:
                logger.debug("Speech recognition: Audio unclear or silent.")
            except Exception as e:
                logger.debug(f"Google STT notice: {e}")

        # Tier 2: Faster-Whisper local model fallback
        try:
            if self.whisper_model is None:
                from faster_whisper import WhisperModel
                self.whisper_model = WhisperModel("tiny", device="cpu", compute_type="int8")

            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                tmp.write(wav_bytes)
                tmp_path = tmp.name

            segments, _ = self.whisper_model.transcribe(tmp_path, language="en")
            raw_text = " ".join([seg.text for seg in segments]).strip()

            try:
                os.remove(tmp_path)
            except Exception:
                pass

            if raw_text:
                clean = normalize_transcription_text(raw_text)
                logger.info(f"Transcribed audio (Faster-Whisper): '{clean}'")
                return clean
        except Exception as ex:
            logger.debug(f"Faster-Whisper fallback notice: {ex}")

        return ""

stt_service = STTService()
