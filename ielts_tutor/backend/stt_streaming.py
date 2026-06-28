"""
Google Speech-to-Text 流式转写
使用 REST API (v1/speech:recognize)
"""
import aiohttp
import base64
import logging

logger = logging.getLogger(__name__)
RATE = 16000


class GoogleSTTStreamer:
    def __init__(self, api_key: str, language="en-US"):
        self.api_key = api_key
        self.language = language
        self.buffer = b""

    def feed(self, audio_bytes: bytes):
        """累积 PCM 音频"""
        self.buffer += audio_bytes

    async def flush(self) -> str:
        """将累积音频发送到 Google STT，返回转写文本"""
        if len(self.buffer) < 3200:  # <0.1s
            self.buffer = b""
            return ""

        buf = self.buffer
        self.buffer = b""
        audio_b64 = base64.b64encode(buf).decode("ascii")

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
            async with aiohttp.ClientSession() as s:
                async with s.post(url, json=body,
                                  timeout=aiohttp.ClientTimeout(total=10)) as resp:
                    result = await resp.json()
        except Exception as e:
            logger.error(f"STT error: {e}")
            return ""

        try:
            text = result["results"][0]["alternatives"][0]["transcript"]
            logger.info(f"STT: {text}")
            return text
        except (KeyError, IndexError):
            logger.debug(f"STT no result: {result.get('error', 'no speech')}")
            return ""

    def close(self):
        self.buffer = b""
