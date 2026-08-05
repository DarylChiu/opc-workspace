"""
ASR + Scene API 模块
对白检测 / Gemini 场景切分 + 情绪预标注
"""
import json, os, subprocess, tempfile, time, base64, shutil
import requests
from config import CONFIG

# 绝对路径解析：launchd 环境 PATH 极简，找不到 ffmpeg/ffprobe
FFPROBE = shutil.which('ffprobe') or '/opt/homebrew/bin/ffprobe'
FFMPEG = shutil.which('ffmpeg') or '/opt/homebrew/bin/ffmpeg'

OPENROUTER_KEY = CONFIG['openrouter_api_key']
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
GEMINI_MODEL = CONFIG['gemini_model']

def detect_dialogue(video_path):
    """检测视频是否有可识别对白"""
    try:
        # 提取音频样本
        tmp = tempfile.mktemp(suffix='.wav')
        subprocess.run([FFMPEG,'-y','-i',video_path,'-ss','5','-t','15',
                       '-vn','-acodec','pcm_s16le','-ar','16000','-ac','1',tmp],
                      capture_output=True, timeout=15)
        
        if not os.path.exists(tmp) or os.path.getsize(tmp) < 1000:
            return {'has_dialogue': False, 'reason': '音频提取失败'}
        
        # 用 Whisper 做对白检测
        import whisper
        model = whisper.load_model("base")
        result = model.transcribe(tmp, language='en', fp16=False)
        
        os.unlink(tmp)
        
        text = result['text'].strip()
        return {
            'has_dialogue': len(text) > 5,
            'text': text if len(text) > 5 else '',
            'reason': '有对白' if len(text) > 5 else '无可识别对白'
        }
    except Exception as e:
        return {'has_dialogue': False, 'reason': str(e)}

def detect_scenes(video_path):
    """Gemini 场景切分 + 情绪预标注"""
    if not OPENROUTER_KEY:
        return {'ok': False, 'error': 'API Key 未配置'}
    
    duration = get_video_duration(video_path)
    
    # 提取关键帧用于场景检测
    frames = extract_keyframes(video_path, max_frames=5)
    
    prompt = f"""Analyze this video ({duration:.0f}s). 
Return JSON with these fields:
1. "scenes": array of scene segments with "start_sec", "end_sec", "description", "emotion_tags" (array of emotions in Chinese: 平静/愉悦/震撼/漫步/自由/好奇/生机/释放/叙述/期待/收束), "confidence" (0-1)
2. "has_dialogue": boolean
3. "dominant_emotion": primary emotion
4. "scene_elements": key visual elements

Example output format:
{{"scenes":[{{"start_sec":0,"end_sec":15,"description":"白色建筑全景","emotion_tags":["好奇","平静"],"confidence":0.82}}],"has_dialogue":false,"dominant_emotion":"平静","scene_elements":["建筑","天空","海面"]}}

IMPORTANT: Output ONLY valid JSON, no markdown, no code blocks."""

    content = [{"type": "text", "text": prompt}]
    for frame_b64 in frames:
        content.append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{frame_b64}"}})
    
    try:
        r = requests.post(OPENROUTER_URL, headers={
            'Authorization': f'Bearer {OPENROUTER_KEY}',
            'Content-Type': 'application/json',
        }, json={
            'model': GEMINI_MODEL,
            'messages': [{'role': 'user', 'content': content}],
            'max_tokens': 2000,
            'temperature': 0.3,
        }, timeout=60)
        
        if r.status_code != 200:
            return {'ok': False, 'error': f'API error {r.status_code}: {r.text[:200]}'}
        
        text = r.json()['choices'][0]['message']['content']
        # 清理可能的 markdown
        text = text.strip().removeprefix('```json').removeprefix('```').removesuffix('```').strip()
        result = json.loads(text)
        return {'ok': True, 'scenes': result.get('scenes', []), 
                'dominant_emotion': result.get('dominant_emotion', ''),
                'scene_elements': result.get('scene_elements', []),
                'has_dialogue': result.get('has_dialogue', False)}
    except Exception as e:
        return {'ok': False, 'error': str(e)}

def get_video_duration(path):
    """获取视频时长（秒），format 缺失时回退到视频流 duration/nb_frames。"""
    try:
        r = subprocess.run([FFPROBE,'-v','quiet','-print_format','json',
                           '-show_format','-show_streams', path],
                          capture_output=True, text=True, timeout=15)
        data = json.loads(r.stdout or '{}')
        dur = 0.0
        try:
            dur = float(data.get('format', {}).get('duration', 0) or 0)
        except Exception:
            dur = 0.0
        if dur <= 0:
            for s in data.get('streams', []):
                try:
                    d = float(s.get('duration', 0) or 0)
                except Exception:
                    d = 0.0
                if d > 0:
                    dur = d
                    break
        if dur <= 0:
            for s in data.get('streams', []):
                if s.get('codec_type') == 'video':
                    try:
                        nb = s.get('nb_frames')
                        num, den = map(float, s.get('avg_frame_rate', '0/0').split('/'))
                        if nb and num and den:
                            dur = float(nb) * den / num
                    except Exception:
                        pass
                    break
        return round(dur, 1) if dur > 0 else 0
    except:
        return 0

def extract_keyframes(video_path, max_frames=5):
    """从视频中提取关键帧（base64）"""
    dur = get_video_duration(video_path)
    if dur <= 0:
        return []
    
    frames = []
    interval = max(2, dur / (max_frames + 1))
    
    for i in range(1, max_frames + 1):
        t = min(i * interval, dur - 1)
        tmp = tempfile.mktemp(suffix='.jpg')
        try:
            subprocess.run([FFMPEG,'-y','-ss',str(t),'-i',video_path,
                           '-vframes','1','-q:v','5','-s','640x360',tmp],
                          capture_output=True, timeout=15)
            if os.path.exists(tmp):
                with open(tmp, 'rb') as f:
                    frames.append(base64.b64encode(f.read()).decode())
                os.unlink(tmp)
        except:
            if os.path.exists(tmp):
                os.unlink(tmp)
    
    return frames
