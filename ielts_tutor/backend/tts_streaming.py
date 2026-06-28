"""
Google TTS 流式合成
按句子切分，逐段合成并 yield base64 MP3
"""
import json
import base64
import logging
import re
import aiohttp
from typing import AsyncIterator

logger = logging.getLogger(__name__)

VOICE_CONFIG = {
    "en-US": {
        "name": "en-US-Journey-O",
        "gender": "FEMALE",
        "rate": 0.95,
    }
}


class GoogleTTSStreamer:
    def __init__(self, api_key: str, language="en-US", voice_name=None):
        self.api_key = api_key
        self.language = language
        self.voice = voice_name or VOICE_CONFIG.get(language, {}).get("name", "en-US-Journey-O")

    async def synthesize(self, text: str) -> AsyncIterator[str]:
        """将文本按句子切分，逐句合成，yield base64 MP3 chunk"""
        sentences = _split_sentences(text)
        if not sentences:
            return

        url = f"https://texttospeech.googleapis.com/v1/text:synthesize?key={self.api_key}"
        rate = VOICE_CONFIG.get(self.language, {}).get("rate", 1.0)

        for sentence in sentences:
            if not sentence.strip():
                continue

            body = {
                "input": {"text": sentence},
                "voice": {
                    "languageCode": self.language,
                    "name": self.voice,
                },
                "audioConfig": {
                    "audioEncoding": "MP3",
                    "speakingRate": rate,
                    "pitch": 0,
                },
            }

            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(url, json=body,
                                            timeout=aiohttp.ClientTimeout(total=5)) as resp:
                        result = await resp.json()
            except Exception as e:
                logger.error(f"TTS request failed: {e}")
                continue

            if "audioContent" in result:
                yield result["audioContent"]

    async def synthesize_full(self, text: str) -> str:
        """合成完整文本为单个 base64 MP3"""
        url = f"https://texttospeech.googleapis.com/v1/text:synthesize?key={self.api_key}"
        rate = VOICE_CONFIG.get(self.language, {}).get("rate", 1.0)

        body = {
            "input": {"text": text},
            "voice": {"languageCode": self.language, "name": self.voice},
            "audioConfig": {"audioEncoding": "MP3", "speakingRate": rate, "pitch": 0},
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=body,
                                    timeout=aiohttp.ClientTimeout(total=10)) as resp:
                result = await resp.json()

        return result.get("audioContent", "")


def _split_sentences(text: str) -> list[str]:
    """按句子边界切分，保留标点"""
    parts = re.split(r'(?<=[.!?])\s+', text.strip())
    # 过滤太短的片段，合并到前一个句子
    result = []
    for p in parts:
        if len(p.split()) <= 2 and result:
            result[-1] += " " + p
        else:
            result.append(p)
    return result
