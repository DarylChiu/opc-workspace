"""
Emotion API 模块 — 三层情感漏斗
L1: Gemini 原生视频分析（主力）
L2: 对白情绪分析（补充）
L3: 视觉信号分析（补充）
+ 补漏机制
"""
import json, os, subprocess, tempfile, base64, time
import requests
import numpy as np
from config import CONFIG

OPENROUTER_KEY = CONFIG['openrouter_api_key']
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
GEMINI_MODEL = CONFIG['gemini_model']

def analyze_clip(video_path, start_sec, end_sec):
    """L1: Gemini 原生视频分析单个片段"""
    dur = end_sec - start_sec
    
    # 提取片段
    clip_path = tempfile.mktemp(suffix='.mp4')
    try:
        subprocess.run(['ffmpeg','-y','-ss',str(start_sec),'-i',video_path,
                       '-t',str(dur),'-c','copy',clip_path],
                      capture_output=True, timeout=15)
    except:
        # Fallback: use frames
        frames = extract_frames(video_path, start_sec, end_sec, max_frames=4)
        return analyze_with_frames(frames, dur, start_sec, end_sec)
    
    if not os.path.exists(clip_path) or os.path.getsize(clip_path) < 100:
        frames = extract_frames(video_path, start_sec, end_sec, max_frames=4)
        return analyze_with_frames(frames, dur, start_sec, end_sec)
    
    # 用 base64 video
    with open(clip_path, 'rb') as f:
        video_b64 = base64.b64encode(f.read()).decode()
    os.unlink(clip_path)
    
    prompt = f"""Analyze this {dur:.0f}s video clip.
Return JSON:
{{
  "primary_emotion": "Chinese emotion word (平静/愉悦/震撼/漫步/自由/好奇/生机/释放/叙述/期待/收束)",
  "secondary_emotions": ["emotion2"],
  "confidence": 0.0-1.0,
  "scene_description": "brief scene description",
  "scene_elements": ["element1", "element2"],
  "narrative_role": "角色 (开场/过渡/高潮/收束/叙述)",
  "color_palette": ["color1"],
  "motion_level": "low/medium/high",
  "brightness": "dark/normal/bright"
}}
Output ONLY valid JSON."""

    return _call_gemini(prompt, video_b64, dur, start_sec, end_sec)
    
def analyze_with_frames(frames, dur, start_sec, end_sec):
    """用关键帧做 Gemini 分析"""
    prompt = f"""Analyze these frames from a {dur:.0f}s video clip.
Return JSON:
{{
  "primary_emotion": "Chinese emotion",
  "secondary_emotions": ["emotion2"],
  "confidence": 0.0-1.0,
  "scene_description": "brief scene description",
  "scene_elements": ["element1"],
  "narrative_role": "叙事角色",
  "color_palette": ["color1"],
  "motion_level": "low/medium/high",
  "brightness": "dark/normal/bright"
}}
Output ONLY valid JSON."""

    return _call_gemini(prompt, frames[0] if frames else '', dur, start_sec, end_sec, is_image=True, extra_images=frames[1:])

def analyze_l2_dialogue(text):
    """L2: 对白情绪分析（如果有对白）"""
    if not text or len(text.strip()) < 3:
        return {'emotion': '', 'confidence': 0}
    
    if not OPENROUTER_KEY:
        return {'emotion': '未分析', 'confidence': 0}
    
    prompt = f"""Analyze the emotion in this dialogue: "{text}"
Return JSON: {{"emotion": "Chinese emotion", "confidence": 0.0-1.0, "intensity": "low/medium/high"}}
Output ONLY valid JSON."""

    try:
        r = requests.post(OPENROUTER_URL, headers={
            'Authorization': f'Bearer {OPENROUTER_KEY}',
            'Content-Type': 'application/json',
        }, json={
            'model': 'deepseek/deepseek-chat',
            'messages': [{'role': 'user', 'content': prompt}],
            'max_tokens': 200, 'temperature': 0.1,
        }, timeout=15)
        
        if r.status_code == 200:
            text = r.json()['choices'][0]['message']['content'].strip()
            text = text.removeprefix('```json').removeprefix('```').removesuffix('```').strip()
            return json.loads(text)
    except:
        pass
    
    return {'emotion': '', 'confidence': 0}

def analyze_l3_visual(video_path, start_sec, end_sec):
    """L3: 视觉信号分析（颜色、亮度、运动量）"""
    dur = end_sec - start_sec
    
    # 提取样本帧
    frames = extract_frames_raw(video_path, start_sec, end_sec, max_frames=8)
    if not frames:
        return {'brightness': 0.5, 'color_variance': 0, 'motion_estimate': 'low'}
    
    # 分析
    brightnesses = []
    color_vars = []
    for frame in frames:
        # 简易亮度/颜色分析
        h, w = frame.shape[:2]
        gray = np.mean(frame) if len(frame.shape) == 2 else np.mean(frame, axis=2)
        brightnesses.append(np.mean(gray) / 255.0)
        
        if len(frame.shape) == 3:
            color_vars.append(np.std(frame.reshape(-1, 3), axis=0).mean() / 128.0)
    
    avg_brightness = float(np.mean(brightnesses))
    avg_color_var = float(np.mean(color_vars)) if color_vars else 0
    
    # 运动估算：亮度变化量
    motion = 'low'
    if len(brightnesses) > 1:
        changes = [abs(brightnesses[i] - brightnesses[i-1]) for i in range(1, len(brightnesses))]
        avg_change = np.mean(changes)
        if avg_change > 0.08: motion = 'high'
        elif avg_change > 0.04: motion = 'medium'
    
    return {
        'brightness': round(avg_brightness, 3),
        'brightness_label': 'bright' if avg_brightness > 0.6 else 'dark' if avg_brightness < 0.3 else 'normal',
        'color_variance': round(avg_color_var, 3),
        'motion_estimate': motion,
    }

def extract_frames(video_path, start_sec, end_sec, max_frames=4):
    """提取关键帧 (base64)"""
    dur = end_sec - start_sec
    frames = []
    interval = max(1, dur / (max_frames + 1))
    for i in range(max_frames):
        t = start_sec + interval * (i + 0.5)
        tmp = tempfile.mktemp(suffix='.jpg')
        try:
            subprocess.run(['ffmpeg','-y','-ss',str(t),'-i',video_path,
                           '-vframes','1','-q:v','5','-s','640x360',tmp],
                          capture_output=True, timeout=8)
            if os.path.exists(tmp):
                with open(tmp, 'rb') as f:
                    frames.append(base64.b64encode(f.read()).decode())
                os.unlink(tmp)
        except:
            if os.path.exists(tmp): os.unlink(tmp)
    return frames

def extract_frames_raw(video_path, start_sec, end_sec, max_frames=8):
    """提取原始帧 (numpy arrays) 用于 L3 分析"""
    try:
        import cv2
        cap = cv2.VideoCapture(video_path)
        dur = end_sec - start_sec
        interval = max(0.5, dur / (max_frames + 1))
        frames = []
        for i in range(max_frames):
            t = start_sec + interval * i
            cap.set(cv2.CAP_PROP_POS_MSEC, t * 1000)
            ret, frame = cap.read()
            if ret:
                frames.append(cv2.resize(frame, (160, 90)))
        cap.release()
        return frames
    except:
        return []

def _call_gemini(prompt, media_b64, dur, start_sec, end_sec, is_image=False, extra_images=None):
    if not OPENROUTER_KEY:
        return {'ok': False, 'error': 'API Key 未配置'}
    
    content = [{"type": "text", "text": prompt}]
    
    if is_image:
        content.append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{media_b64}"}})
        if extra_images:
            for img in extra_images:
                content.append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img}"}})
    
    try:
        r = requests.post(OPENROUTER_URL, headers={
            'Authorization': f'Bearer {OPENROUTER_KEY}',
            'Content-Type': 'application/json',
        }, json={
            'model': GEMINI_MODEL,
            'messages': [{'role': 'user', 'content': content}],
            'max_tokens': 1000, 'temperature': 0.3,
        }, timeout=60)
        
        if r.status_code != 200:
            return {'ok': False, 'error': f'API {r.status_code}', 'start_sec': start_sec, 'end_sec': end_sec}
        
        text = r.json()['choices'][0]['message']['content'].strip()
        text = text.removeprefix('```json').removeprefix('```').removesuffix('```').strip()
        result = json.loads(text)
        return {'ok': True, 'start_sec': start_sec, 'end_sec': end_sec, **result}
    except Exception as e:
        return {'ok': False, 'error': str(e), 'start_sec': start_sec, 'end_sec': end_sec}
