"""
管线2 · Qwen-Omni Realtime 语音交互
阿里百炼 DashScope WebSocket 协议
"""
import asyncio
import json
import logging
import base64
import struct
from typing import AsyncIterator

logger = logging.getLogger(__name__)

# DashScope Realtime API（文档: help.aliyun.com/zh/model-studio/realtime）
# Workspace endpoint from CSV: ws-spzk3f7tb6hcawwn.cn-beijing.maas.aliyuncs.com
QWEN_WS_HOST = "ws-spzk3f7tb6hcawwn.cn-beijing.maas.aliyuncs.com"
QWEN_WS_URL = f"wss://{QWEN_WS_HOST}/api-ws/v1/realtime"
QWEN_MODEL = "qwen3.5-omni-flash-realtime"  # 当前默认: flash (无需白名单)
QWEN_MODEL_PLUS = "qwen3.5-omni-plus-realtime"  # 旗舰，需百炼控制台申请白名单


class QwenOmniClient:
    """
    Qwen-Omni Realtime 客户端
    
    流程:
    1. 建立 WebSocket 连接到 DashScope
    2. 发送 session.update 配置模型和行为
    3. 流式发送音频 (input_audio_buffer.append)
    4. 接收响应 (response.text.delta + response.audio.delta)
    5. 双向音频对话
    """

    def __init__(self, api_key: str, mode: str = "ielts_part1",
                 voice: str = "Ethan", language: str = "en-US",
                 model: str = None):
        self.api_key = api_key
        self.mode = mode
        self.voice = voice
        self.language = language
        self.model = model or QWEN_MODEL  # 允许外部指定模型
        self.ws = None
        self._session_id = None
        self._pending_events = asyncio.Queue()
        self._response_text = ""
        self._response_audio = b""

    # ── System prompts ──
    SYSTEM_PROMPTS = {
        "ielts_part1": (
            "You are Alex, a friendly IELTS Speaking examiner doing Part 1. "
            "Ask ONE question at a time about familiar topics. Keep responses very short — 1-2 sentences. "
            "React naturally to answers before moving to the next question. "
            "Vary your transitions. NEVER give scores. Be warm and conversational. "
            "Speak at a natural pace with clear pronunciation."
        ),
        "ielts_part2": (
            "You are an IELTS examiner doing Part 2. Give the topic card clearly. "
            "Let the candidate speak for 1-2 minutes. Ask 1-2 brief follow-up questions after. "
            "Keep your own words very minimal. The candidate should do most of the talking."
        ),
        "ielts_part3": (
            "You are an IELTS examiner doing Part 3 Discussion. "
            "Ask abstract questions. Follow up on answers. Challenge respectfully. "
            "Keep questions concise. NEVER give scores."
        ),
        "business_pitch": (
            "You are a business English coach for investor pitch practice. "
            "Simulate an investor. Ask typical investor questions. "
            "Give one brief, constructive tip after each answer. Stay professional."
        ),
        "free_talk": (
            "You are a friendly English conversation partner. "
            "Chat naturally. Respond with 2-3 sentences. "
            "Gently correct major grammar mistakes. Ask follow-up questions. Be encouraging."
        ),
    }

    async def connect(self) -> dict:
        """建立 WebSocket 连接并初始化会话"""
        import websockets
        import uuid

        ws_url = f"{QWEN_WS_URL}?model={self.model}"
        headers = {"Authorization": f"Bearer {self.api_key}"}
        self.ws = await websockets.connect(
            ws_url,
            additional_headers=headers,
            ping_interval=30,
            ping_timeout=10,
        )

        # Configure session（文档: help.aliyun.com/zh/model-studio/realtime）
        system_prompt = self.SYSTEM_PROMPTS.get(self.mode, self.SYSTEM_PROMPTS["free_talk"])
        session_config = {
            "event_id": f"event_{uuid.uuid4().hex[:21]}",
            "type": "session.update",
            "session": {
                "modalities": ["text", "audio"],
                "instructions": system_prompt,
                "voice": self.voice,
                "input_audio_format": "pcm",       # 16kHz PCM
                "output_audio_format": "pcm",      # 24kHz PCM 输出
            },
        }
        await self.ws.send(json.dumps(session_config))

        # Wait for session.created
        while True:
            msg = json.loads(await self.ws.recv())
            if msg.get("type") == "session.created":
                self._session_id = msg["session"]["id"]
                logger.info(f"Qwen-Omni session: {self._session_id}")
                return msg["session"]
            elif msg.get("type") == "error":
                raise Exception(f"Qwen-Omni error: {msg.get('error', {}).get('message', msg)}")

        return {}

    async def send_audio(self, pcm_chunk: bytes):
        """发送 PCM 音频块到 Qwen"""
        if not self.ws:
            return
        b64 = base64.b64encode(pcm_chunk).decode()
        msg = {"type": "input_audio_buffer.append", "audio": b64}
        await self.ws.send(json.dumps(msg))

    async def commit_audio(self):
        """通知 Qwen 音频缓冲区已就绪"""
        if not self.ws:
            return
        await self.ws.send(json.dumps({"type": "input_audio_buffer.commit"}))

    async def request_response(self):
        """请求 Qwen 生成响应"""
        if not self.ws:
            return
        await self.ws.send(json.dumps({"type": "response.create"}))

    async def receive_response(self) -> AsyncIterator[dict]:
        """接收 Qwen 的流式响应，yield 每个事件"""
        if not self.ws:
            return

        while True:
            try:
                msg = json.loads(await asyncio.wait_for(self.ws.recv(), timeout=15))
            except asyncio.TimeoutError:
                break

            msg_type = msg.get("type", "")

            # 文档定义的事件类型:
            # 文本+音频模式: response.audio_transcript.delta / response.audio_transcript.done
            # 仅文本模式: response.text.delta / response.text.done
            if msg_type == "response.audio_transcript.delta":
                yield {"type": "text", "data": msg.get("delta", "")}
            elif msg_type == "response.audio.delta":
                yield {"type": "audio", "data": msg.get("delta", "")}
            elif msg_type == "response.audio_transcript.done":
                yield {"type": "text_done", "text": msg.get("transcript", "")}
            elif msg_type == "response.audio.done":
                yield {"type": "audio_done"}
            elif msg_type == "response.done":
                break
            elif msg_type == "error":
                logger.error(f"Qwen error: {msg}")
                yield {"type": "error", "msg": str(msg)}
                break
            elif msg_type == "input_audio_buffer.speech_started":
                yield {"type": "speech_started"}
            elif msg_type == "input_audio_buffer.speech_stopped":
                yield {"type": "speech_stopped"}
            elif msg_type == "conversation.item.input_audio_transcription.completed":
                # 用户语音转写完成
                yield {"type": "user_transcript", "transcript": msg.get("transcript", "")}

    async def close(self):
        if self.ws:
            await self.ws.close()
            self.ws = None


# ── Bridge: frontend WebSocket ↔ Qwen-Omni ──
class QwenOmniBridge:
    """
    在前端 WebSocket 和 Qwen-Omni 之间桥接音频流
    
    前端 ─WebSocket─→ Bridge ─Qwen WS─→ Qwen-Omni
    """

    def __init__(self, qwen_api_key: str, mode: str = "ielts_part1"):
        self.client = QwenOmniClient(api_key=qwen_api_key, mode=mode)
        self.mode = mode

    async def start(self):
        await self.client.connect()

    async def handle_audio(self, pcm_chunk: bytes):
        """转发音频到 Qwen"""
        await self.client.send_audio(pcm_chunk)

    async def flush_and_respond(self) -> AsyncIterator[dict]:
        """提交音频并获取 Qwen 回复"""
        await self.client.commit_audio()
        await self.client.request_response()

        full_text = ""
        full_audio = b""

        async for event in self.client.receive_response():
            if event["type"] == "text":
                full_text += event["data"]
                yield {"type": "text_delta", "data": event["data"]}
            elif event["type"] == "audio":
                full_audio += base64.b64decode(event["data"])
                yield {"type": "audio_delta", "data": event["data"]}
            elif event["type"] == "text_done":
                yield {"type": "response_text", "text": full_text}
            elif event["type"] == "audio_done":
                yield {"type": "response_audio_done"}
            elif event["type"] == "speech_started":
                yield {"type": "vad_speech_started"}
            elif event["type"] == "speech_stopped":
                yield {"type": "vad_speech_stopped"}

    async def close(self):
        await self.client.close()
