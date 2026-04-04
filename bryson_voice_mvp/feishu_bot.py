#!/usr/bin/env python3
"""
飞书Bot入口 - MVP方案B
用户点击"开始口语练习"时生成语音对话页面链接
"""

import os
import uuid
import json
from datetime import datetime

# 配置
BASE_URL = "https://yourapp.com"  # 临时，需要替换为实际URL
SESSION_EXPIRE_HOURS = 24

class FeishuBotMVP:
    def __init__(self):
        self.active_sessions = {}  # 会话ID -> 创建时间
        
    def handle_start_command(self) -> dict:
        """
        处理"开始口语练习"命令
        返回飞书机器人响应消息
        """
        # 生成唯一会话ID
        session_id = str(uuid.uuid4())[:8]
        self.active_sessions[session_id] = datetime.now()
        
        # 生成访问链接（本地测试用localhost:8000）
        voice_page_url = f"http://localhost:8000/voice-chat/{session_id}"
        
        return {
            "msg_type": "interactive",
            "card": {
                "config": {
                    "wide_screen_mode": True,
                    "enable_forward": False
                },
                "header": {
                    "title": {
                        "tag": "plain_text",
                        "content": "🎤 Bryson口语练习室"
                    },
                    "template": "blue"
                },
                "elements": [
                    {
                        "tag": "div",
                        "text": {
                            "tag": "lark_md",
                            "content": "**🏃‍♂️ 点击下方按钮立即开始**\n\n准备好和Bryson进行实时英语对话了吗？点击进入语音聊天室开始练习。"
                        }
                    },
                    {
                        "tag": "action",
                        "actions": [
                            {
                                "tag": "button",
                                "text": {
                                    "tag": "plain_text",
                                    "content": "立即开始"
                                },
                                "type": "primary",
                                "multi_url": {
                                    "url": voice_page_url,
                                    "pc_url": voice_page_url,
                                    "android_url": voice_page_url,
                                    "ios_url": voice_page_url
                                }
                            }
                        ]
                    },
                    {
                        "tag": "note",
                        "elements": [
                            {
                                "tag": "plain_text",
                                "content": "⚠️ 提示：语音聊天需要麦克风和扬声器权限\n🟢 连接状态：准备就绪"
                            }
                        ]
                    }
                ]
            }
        }

if __name__ == "__main__":
    bot = FeishuBotMVP()
    
    # 测试生成响应
    response = bot.handle_start_command()
    print(json.dumps(response, indent=2, ensure_ascii=False))
    print("\n✅ 飞书Bot MVP入口已就绪")