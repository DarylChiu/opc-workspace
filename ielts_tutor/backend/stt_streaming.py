"""
Google Speech-to-Text 流式转写
使用 REST API (v1/speech:recognize) + streaming 模式
"""
import json
import logging
import aiohttp
import asyncio

logger = logging.getLogger(__name__)

RATE = 16000  # sample rate


class GoogleSTTStreamer:
    """简易流式 STT —— 累积音频，周期性请求识别"""

    def __init__(self, api_key: str, language="en-US"):
        self.api_key = api_key
        self.language = language
        self.buffer = b""
        self.last_partial = ""
        self.last_full = ""
        self.utterance_complete = False
        self._silence_frames = 0

    def feed(self, audio_bytes: bytes) -> str | None:
        """喂入PCM音频数据，返回当前部分识别文本"""
        self.buffer += audio_bytes
        self._silence_frames = 0
        return None  # don't send partials on every chunk (too noisy)

    def is_utterance_complete(self, silence_frames: int = 0) -> bool:
        """外部可喂入静音帧数来决定是否断句"""
        self._silence_frames += silence_frames
        # 累积 >0.8s (12 frames at 16kHz/20ms) 且 buffer > 0.5s
        min_bytes = RATE * 0.5 * 2  # 0.5s of 16-bit mono = 16000 bytes
        if self._silence_frames > 12 and len(self.buffer) > min_bytes:
            return True
        return False

    async def flush(self) -> str:
        """发送累积音频到 Google STT，返回完整文本"""
        if len(self.buffer) < 3200:  # <0.1s
            self.buffer = b""
            self.utterance_complete = False
            return ""

        audio_b64 = _encode_b64(self.buffer)
        self.buffer = b""
        self.utterance_complete = False

        url = f"https://speech.googleapis.com/v1/speech:recognize?key={self.api_key}"
        body = {
            "config": {
                "encoding": "LINEAR16",
                "sampleRateHertz": RATE,
                "languageCode": self.language,
                "enableAutomaticPunctuation": True,
                "model": "latest_short",
            },
            "audio": {"content": audio_b64},
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=body, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                    result = await resp.json()
        except Exception as e:
            logger.error(f"STT request failed: {e}")
            return ""

        if "results" in result:
            text = result["results"][0]["alternatives"][0]["transcript"]
            self.last_full = text
            return text

        return ""

    def close(self):
        self.buffer = b""
        self.utterance_complete = False


def _encode_b64(data: bytes) -> str:
    import base64
    return base64.b64encode(data).decode("ascii")
