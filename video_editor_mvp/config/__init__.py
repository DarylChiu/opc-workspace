"""
视频编辑器 MVP · 配置管理
统一管理路径、API Key、模型参数
"""
import os
import json

# 项目根目录
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

CONFIG = {
    # === 路径 ===
    'root': ROOT,
    'material_dir': '/Volumes/TOSHIBA EXT/Video/Raw Materials/Insta 360',
    'output_dir': '/Volumes/TOSHIBA EXT/Video/Masterpieces/Demo_video_auto_editor_output',
    'bgm_dir': os.path.join(ROOT, 'data', 'bgm'),
    'data_dir': os.path.join(ROOT, 'data'),
    'output_demo_dir': os.path.join(ROOT, 'output'),
    
    # === API Keys ===
    'openrouter_api_key': os.environ.get('OPENROUTER_API_KEY', ''),
    
    # === 模型 ===
    'gemini_model': 'google/gemini-2.5-flash',
    'asr_model': 'whisper-1',
    
    # === Pipeline ===
    'emotion_l1_enabled': True,    # Gemini 原生视频
    'emotion_l2_enabled': True,    # 对白情绪
    'emotion_l3_enabled': True,    # 视觉信号
    'emotion_l1_confidence_threshold': 0.7,
    'match_confidence_auto': 0.85,  # ≥85% 自动匹配
    'match_confidence_review': 0.70, # 70-84% 待确认
    
    # === 视频输出 ===
    'output_resolution_preview': '640x360',
    'output_resolution_final': '1920x1080',
    'output_fps': 30,
    'output_codec': 'h264',
    'output_aspect': '16:9',
    
    # === Syncthing ===
    'syncthing_output_dir': '/Volumes/TOSHIBA EXT/Video/Masterpieces/Demo_video_auto_editor_output',
    
    # === 清理 ===
    'preview_cleanup_days': 2,
    'demo_cleanup_days': 7,
}

# 加载 .env
env_path = os.path.join(ROOT, '.env')
if os.path.exists(env_path):
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                k, v = line.split('=', 1)
                os.environ[k.strip()] = v.strip().strip('"').strip("'")
    CONFIG['openrouter_api_key'] = os.environ.get('OPENROUTER_API_KEY', '')

def get(key, default=None):
    return CONFIG.get(key, default)

def get_path(key):
    path = CONFIG.get(key, '')
    os.makedirs(path, exist_ok=True)
    return path
