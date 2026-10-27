"""
Voice input tool for ARIA.
Records microphone input and transcribes it locally using faster-whisper.
Runs 100% offline with zero cloud API keys required.
"""

import os
import tempfile
import threading
from typing import Optional
from aria.utils.logger import logger
from aria.config import config

_whisper_model = None
_model_lock = threading.Lock()


def get_whisper_model():
    """Lazily load faster-whisper model."""
    global _whisper_model
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        logger.warning("faster-whisper is not installed.")
        return None

    with _model_lock:
        if _whisper_model is None:
            logger.info(f"Loading Whisper model '{config.voice_model}' on CPU...")
            _whisper_model = WhisperModel(
                config.voice_model,
                device="cpu",
                compute_type="int8",  # Fast CPU inference
                download_root=str(config.memory_dir / "models"),
            )
        return _whisper_model


class VoiceRecorder:
    def __init__(self, sample_rate: int = 16000):
        self.sample_rate = sample_rate
        self.recording = False
        self._frames = []
        self._thread: Optional[threading.Thread] = None

    def start(self):
        """Start recording from microphone."""
        try:
            import sounddevice as sd
            import numpy as np
        except ImportError:
            logger.error("sounddevice or numpy not installed.")
            return False

        self._frames = []
        self.recording = True

        def _record():
            try:
                with sd.InputStream(samplerate=self.sample_rate, channels=1, dtype="float32") as stream:
                    while self.recording:
                        data, _ = stream.read(1024)
                        self._frames.append(data.copy())
            except Exception as e:
                logger.error(f"Recording error: {e}")
                self.recording = False

        self._thread = threading.Thread(target=_record, daemon=True)
        self._thread.start()
        logger.info("Voice recording started.")
        return True

    def stop_and_transcribe(self) -> str:
        """Stop recording and return transcribed text."""
        self.recording = False
        if self._thread:
            self._thread.join(timeout=2.0)

        if not self._frames:
            logger.warning("No audio frames recorded.")
            return ""

        try:
            import numpy as np
            import soundfile as sf
        except ImportError:
            return ""

        audio_data = np.concatenate(self._frames, axis=0)

        # Save to temporary WAV file
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            tmp_path = tmp.name

        try:
            sf.write(tmp_path, audio_data, self.sample_rate)
            model = get_whisper_model()
            if not model:
                return "Error: Whisper model not available."

            segments, info = model.transcribe(
                tmp_path,
                language=config.voice_language,
                beam_size=3,
                vad_filter=True,  # Filter out silence
            )
            text = " ".join([segment.text for segment in segments]).strip()
            logger.info(f"Transcribed audio: '{text}' (lang={info.language})")
            return text
        except Exception as e:
            logger.error(f"Transcription failed: {e}")
            return ""
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)


voice_recorder = VoiceRecorder()
