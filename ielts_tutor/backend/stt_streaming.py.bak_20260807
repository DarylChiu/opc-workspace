"""
Streaming STT using faster-whisper (CTranslate2 backend)
- Model loaded once, persists across calls (no subprocess overhead)
- Single-pass: transcribe on flush, with VAD auto-segmentation for speed
- Partial transcripts via segment callback for real-time display
"""

import logging
import os
import numpy as np
from faster_whisper import WhisperModel

logger = logging.getLogger("stt-streaming")

# Global model (loaded once)
# 延迟优化 P0 (2026-07-15): small.en+beam5 → base.en+beam1 → small.en+beam1
#   实测(20s音频): base.en b1≈1004ms, small.en b1≈1522ms, small.en b5≈6317ms
#   口音识别微调(2026-07-15): base.en→small.en 只+~500ms, 口音能力明显回升
#   可回退: export IELTS_STT_MODEL=base.en / IELTS_STT_BEAM=5
_model = None
_model_size = os.environ.get("IELTS_STT_MODEL", "small.en")
_beam_size = int(os.environ.get("IELTS_STT_BEAM", "1"))
_device = "auto"
_compute_type = "auto"  # CoreML on M4

def get_model():
    global _model
    if _model is None:
        logger.info(f"STT: loading {_model_size} ({_device}/{_compute_type})...")
        _model = WhisperModel(_model_size, device=_device, compute_type=_compute_type)
        logger.info(f"STT: model loaded")
    return _model


class StreamingTranscriber:
    """Per-connection transcriber with incremental audio buffering.
    
    Accumulates audio chunks during speech, then transcribes on flush.
    Uses VAD-based segmentation for fast, accurate results.
    """

    def __init__(self):
        self._model = get_model()
        self._buffer = b""

    def feed(self, pcm_bytes: bytes):
        self._buffer += pcm_bytes

    @property
    def buffer_duration_s(self) -> float:
        return len(self._buffer) / 32000

    def transcribe(self, on_partial=None) -> tuple[str, float]:
        """Transcribe accumulated audio. Returns (text, confidence).
        
        If on_partial is provided, it's called with each segment text
        as it becomes available (streaming partial results).
        """
        if not self._buffer or len(self._buffer) < 1600:
            return "", 0.0

        audio = np.frombuffer(self._buffer, dtype=np.int16).astype(np.float32) / 32768.0

        try:
            segments, info = self._model.transcribe(
                audio,
                beam_size=_beam_size,
                vad_filter=True,
                vad_parameters=dict(
                    threshold=0.5,
                    min_speech_duration_ms=250,
                    min_silence_duration_ms=600,  # longer silence tolerance
                    speech_pad_ms=400,  # more padding around speech
                ),
                compression_ratio_threshold=4.0,  # relaxed — avoid truncating long sentences
                no_speech_threshold=0.4,  # more permissive
            )

            all_segments = []
            total_logprob = 0.0
            count = 0

            for seg in segments:
                t = seg.text.strip()
                if t:
                    all_segments.append(t)
                    total_logprob += seg.avg_logprob
                    count += 1
                    if on_partial:
                        on_partial(t)

            text = " ".join(all_segments).strip()
            confidence = min(1.0, max(0.0, (total_logprob / max(count, 1)) / 3.0 + 0.5))

            logger.info(f"STT[{_model_size} b{_beam_size}]: {text[:80]} (conf={confidence:.2f}, {count} segments, {self.buffer_duration_s:.1f}s audio)")
            return text, confidence

        except Exception as e:
            logger.error(f"STT error: {e}")
            return "", 0.0

    def reset(self):
        """Clear buffer for next utterance."""
        self._buffer = b""
