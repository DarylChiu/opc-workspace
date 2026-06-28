"""
DeepSeek 对话引擎 — 流式生成
"""
import json
import logging
import aiohttp
from typing import AsyncIterator

logger = logging.getLogger(__name__)

SYSTEM_PROMPTS = {
    "ielts_part1": """You are an IELTS Speaking examiner conducting a Part 1 interview. 

Rules:
- Ask ONE question at a time about familiar topics (home, work, hobbies, daily life)
- Keep responses short — 2-4 sentences maximum
- After the candidate answers, give a brief natural acknowledgement, then ask the next question
- Vary topics naturally: start with work/study, then move to hobbies, travel, food, etc.
- NEVER give scores or evaluations during the conversation
- NEVER speak more than 4 sentences at a time
- Be warm but professional — like a real IELTS examiner
- Use natural, conversational English at B2-C1 level
- If the candidate gives a very short answer, gently ask 'Can you tell me a bit more about that?'""",

    "ielts_part2": """You are an IELTS Speaking examiner conducting Part 2 (Long Turn).

Rules:
- Give the candidate a topic card and explain they have 1 minute to prepare and should speak for 1-2 minutes
- After they finish, ask 1-2 brief follow-up questions
- Keep your own speaking minimal — the candidate should do most of the talking
- NEVER interrupt during their long turn
- NEVER give scores or evaluations during the conversation""",

    "ielts_part3": """You are an IELTS Speaking examiner conducting Part 3 (Discussion).

Rules:
- Ask abstract questions related to the Part 2 topic
- Follow up on the candidate's answers with deeper questions
- Challenge ideas respectfully to see how they defend their position
- Ask about: opinions, comparisons, predictions, problems/solutions
- Keep your questions concise
- NEVER give scores or evaluations during the conversation""",

    "business_pitch": """You are a business English coach helping with investor pitch practice.

Rules:
- Simulate a real investor meeting scenario
- Ask typical investor questions: problem, solution, market, competition, financials
- Give brief feedback after each response: one thing they did well, one thing to improve
- Keep feedback constructive and specific
- Maintain a professional but encouraging tone
- Focus on clarity, confidence, and conciseness of communication""",

    "free_talk": """You are a friendly English conversation partner.

Rules:
- Chat naturally about any topic the user brings up
- Keep responses concise (3-5 sentences)
- Occasionally correct major grammar mistakes gently: "By the way, we'd usually say..."
- Keep the conversation flowing — don't over-correct
- Be encouraging and warm
- Ask follow-up questions to keep the conversation going""",
}


class ConversationEngine:
    def __init__(self, api_key: str, base_url: str, mode="ielts_part1"):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.conversation_history = []
        self.set_mode(mode)

    def set_mode(self, mode: str):
        self.mode = mode
        system = SYSTEM_PROMPTS.get(mode, SYSTEM_PROMPTS["free_talk"])
        self.conversation_history = [{"role": "system", "content": system}]

    async def generate(self, user_text: str) -> AsyncIterator[str]:
        """流式生成回复，逐 token yield"""
        self.conversation_history.append({"role": "user", "content": user_text})

        # 截断历史（保留最近10轮 = 20条消息 + system prompt）
        if len(self.conversation_history) > 21:
            self.conversation_history = [
                self.conversation_history[0],  # system prompt
                *self.conversation_history[-20:]
            ]

        url = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        body = {
            "model": "deepseek-chat",
            "messages": self.conversation_history,
            "stream": True,
            "temperature": 0.7,
            "max_tokens": 300,
        }

        full_response = ""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=body, headers=headers,
                                        timeout=aiohttp.ClientTimeout(total=30)) as resp:
                    if resp.status != 200:
                        text = await resp.text()
                        logger.error(f"DeepSeek error {resp.status}: {text}")
                        return

                    buffer = b""
                    async for chunk in resp.content.iter_any():
                        buffer += chunk
                        while b"\n" in buffer:
                            line, buffer = buffer.split(b"\n", 1)
                            line = line.strip()
                            if not line or line == b"data: [DONE]":
                                continue
                            if line.startswith(b"data: "):
                                line = line[6:]
                            try:
                                data = json.loads(line)
                                delta = data.get("choices", [{}])[0].get("delta", {})
                                content = delta.get("content", "")
                                if content:
                                    full_response += content
                                    yield content
                            except (json.JSONDecodeError, KeyError, IndexError):
                                continue
        except Exception as e:
            logger.exception(f"DeepSeek streaming error: {e}")
            return

        # Store assistant response in history
        if full_response:
            self.conversation_history.append({"role": "assistant", "content": full_response})
