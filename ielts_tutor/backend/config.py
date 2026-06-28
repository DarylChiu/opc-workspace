"""
配置管理 - 从认证目录加载 API Key
"""
import os

def _read_key(path):
    """读取密钥文件，去除空白"""
    if os.path.exists(path):
        with open(path) as f:
            return f.read().strip()
    return ""

# Google Cloud API Keys
AUTH_DIR = os.path.expanduser("~/.openclaw/auth")
GOOGLE_STT_KEY = _read_key(os.path.join(AUTH_DIR, "google", "ielts_stt_2026.key"))
GOOGLE_TTS_KEY = _read_key(os.path.join(AUTH_DIR, "google", "ielts_tts_2026.key"))

# DeepSeek
# API Key: read from auth file or environment
DEEPSEEK_KEY = os.environ.get("DEEPSEEK_API_KEY") or _read_key(os.path.join(AUTH_DIR, "deepseek", "api.key"))
DEEPSEEK_BASE = "https://api.deepseek.com/v1"

# Qwen-Omni (Daryl 准备中)
QWEN_OMNI_KEY = _read_key(os.path.join(AUTH_DIR, "qwen", "omni_realtime.key"))

# Server
HOST = "0.0.0.0"
PORT = int(os.environ.get("PORT", 8767))
