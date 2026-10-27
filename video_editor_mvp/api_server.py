#!/usr/bin/env python3
"""Video Editor MVP · Phase 1 API Server
Serves frontend + REST API endpoints for all pipeline steps."""
import json, os, sys, subprocess, tempfile, glob, time, threading, base64, io
from pathlib import Path
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

ROOT = Path(__file__).parent
FRONTEND = ROOT / "frontend"
MATERIAL_DIR = "/Volumes/TOSHIBA EXT/Video/Raw Materials/Insta 360"
BGM_DIR = ROOT / "data" / "bgm"
OUTPUT_DIR = ROOT / "output"
THUMB_DIR = ROOT / "data" / "thumbs"
DATA_DIR = ROOT / "data"

for d in [BGM_DIR, OUTPUT_DIR, THUMB_DIR, DATA_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# Load env
API_KEYS = {}
env_file = ROOT / ".env"
if env_file.exists():
    for line in env_file.read_text().splitlines():
        if '=' in line and not line.startswith('#'):
            k, v = line.split('=', 1)
            API_KEYS[k.strip()] = v.strip()

# ─── Helpers ───
def run_ffprobe(path):
    """Get media file metadata"""
    try:
        cmd = ['ffprobe','-v','quiet','-print_format','json','-show_format','-show_streams',str(path)]
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        return json.loads(r.stdout)
    except:
        return None

def extract_thumbnail(video_path, time_sec, output_path, size=200):
    """Extract thumbnail from video at given time"""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run([
        'ffmpeg','-y','-ss',str(time_sec),'-i',str(video_path),
        '-vframes','1','-vf',f'scale={size}:-1','-q:v','3',str(output_path)
    ], capture_output=True, timeout=10)
    return str(output_path) if output_path.exists() else None

# ─── API Handlers ───
def api_scan(date_filter=None, max_files=50):
    """Scan material directory for media files grouped by date.
    Uses fast listing (no ffprobe) for initial scan."""
    groups = {}
    files = sorted(Path(MATERIAL_DIR).glob("VID_*.mp4"))
    
    if date_filter:
        files = [f for f in files if date_filter in f.stem]
    if max_files:
        files = files[:max_files]
    
    for f in files:
        name = f.stem
        parts = name.split('_')
        date_str = 'unknown'
        if len(parts) >= 2 and len(parts[1]) == 8:
            date_str = f"{parts[1][:4]}-{parts[1][4:6]}-{parts[1][6:8]}"
        
        # Quick duration from filesize estimate
        fsize_mb = f.stat().st_size / (1024*1024)
        est_duration = round(fsize_mb / 0.55, 1)  # ~5.5 MB per 10s for Insta360 5.7K
        # For 20260430 beach vlog, use ffprobe for accurate durations (11 files only)
        if date_str == '2026-04-30':
            try:
                probe = run_ffprobe(f)
                if probe: est_duration = round(float(probe['format']['duration']), 1)
            except: pass
        
        # Simple orientation guess from filename pattern
        # 120,122,124,126 etc are vertical based on project knowledge
        file_num = int(parts[-1]) if parts and parts[-1].isdigit() else 0
        orientation = '9:16' if file_num in [120,122,124,126] else '16:9'
        
        date_key = date_str if date_str != 'unknown' else 'unknown'
        if date_key not in groups:
            groups[date_key] = []
        groups[date_key].append({
            'id': f.stem.replace('VID_', ''),
            'path': str(f),
            'filename': f.name,
            'duration': est_duration,
            'orientation': orientation,
            'date': date_str,
            'size_mb': round(fsize_mb, 1)
        })
    
    return {'ok': True, 'groups': [
        {'name': f'{d} · 拍摄素材', 'date': d, 'count': len(fs), 'files': fs}
        for d, fs in sorted(groups.items())
    ]}

def api_bgm_analyze(data):
    """Analyze BGM structure using librosa"""
    bgm_path = data.get('path', '')
    if not bgm_path or not os.path.exists(bgm_path):
        # Use default BGM
        bgm_path = str(ROOT / "bgm_full.wav")
    if not os.path.exists(bgm_path):
        return {'ok': False, 'error': 'BGM file not found'}
    
    try:
        import librosa, numpy as np
        y, sr = librosa.load(bgm_path, sr=22050)
        duration = len(y) / sr
        
        # Beat tracking
        tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sr)
        import numpy as np
        tempo = float(tempo.item() if hasattr(tempo, 'item') else tempo)
        beat_times = librosa.frames_to_time(beat_frames, sr=sr).tolist()
        
        # Energy curve (RMS)
        hop_length = 512
        rms = librosa.feature.rms(y=y, hop_length=hop_length)[0]
        times_rms = librosa.frames_to_time(range(len(rms)), sr=sr, hop_length=hop_length)
        energy = (rms / rms.max()).tolist()
        
        # Simple structural segmentation based on energy
        # Split into 4-5 segments based on energy changes
        n_segments = 4
        seg_len = len(energy) // n_segments
        segments = []
        segment_types = ['intro','bridge','build','climax']
        
        for i in range(n_segments):
            s = i * seg_len
            e = min((i+1) * seg_len, len(energy))
            if s >= len(energy): break
            seg_energy = float(np.mean(energy[s:e]))
            seg_start = float(times_rms[s])
            seg_end = float(times_rms[e-1]) if e > 0 else float(duration)
            
            # Assign emotion based on segment type
            emotions = {'intro':'平和','bridge':'期待','build':'上升','climax':'释放'}
            
            segments.append({
                'type': segment_types[i] if i < len(segment_types) else 'ending',
                'start': round(seg_start, 1),
                'end': round(seg_end, 1),
                'bpm': round(tempo),
                'key': 'G',  # Would need music theory analysis
                'energy': round(seg_energy, 2),
                'emotion': emotions.get(segment_types[i] if i < len(segment_types) else 'ending', '未知')
            })
        
        # Fix the last segment end to match duration
        if segments:
            segments[-1]['end'] = round(duration, 1)
        
        return {
            'ok': True,
            'analysis': {
                'duration': round(duration, 1),
                'bpm': round(tempo),
                'key': 'G major',
                'beat_count': len(beat_times),
                'energy_curve': {
                    'times': [round(t,2) for t in times_rms.tolist()[::4]],
                    'values': [round(v,3) for v in energy[::4]]
                },
                'segments': segments
            }
        }
    except Exception as e:
        import traceback
        return {'ok': False, 'error': str(e), 'trace': traceback.format_exc()}

def api_asr(data):
    """Run Whisper ASR on video files"""
    video_path = data.get('path', '')
    if not video_path or not os.path.exists(video_path):
        # Try to find a video
        files = sorted(Path(MATERIAL_DIR).glob("VID_20260430_*.mp4"))
        if files:
            video_path = str(files[0])
        else:
            return {'ok': False, 'error': 'No video file found'}
    
    try:
        import whisper
        model = whisper.load_model("base")
        
        # Extract audio to temp file
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp:
            audio_path = tmp.name
        
        subprocess.run([
            'ffmpeg','-y','-i',video_path,'-vn','-acodec','pcm_s16le',
            '-ar','16000','-ac','1', audio_path
        ], capture_output=True, timeout=60)
        
        result = model.transcribe(audio_path, language='en', verbose=False)
        os.unlink(audio_path)
        
        # Format segments
        segments = []
        for seg in result.get('segments', []):
            segments.append({
                'start': round(seg['start'], 1),
                'end': round(seg['end'], 1),
                'text': seg['text'].strip()
            })
        
        # Simple scene detection based on text gaps
        scenes = []
        if segments:
            scenes.append({'start': segments[0]['start'], 'end': segments[0]['end'], 'label': '🎬 开场'})
            for i in range(1, len(segments)):
                gap = segments[i]['start'] - segments[i-1]['end']
                if gap > 2.0:  # Gap > 2s = new scene
                    scenes[-1]['end'] = segments[i-1]['end']
                    scenes.append({'start': segments[i]['start'], 'end': segments[i]['end'], 'label': f'🎬 场景{len(scenes)+1}'})
            if scenes:
                scenes[-1]['end'] = segments[-1]['end']
        
        return {
            'ok': True,
            'file': Path(video_path).name,
            'transcript': segments,
            'scenes': scenes,
            'language': result.get('language', 'en')
        }
    except Exception as e:
        import traceback
        return {'ok': False, 'error': str(e), 'trace': traceback.format_exc()}

def api_emotion(data):
    """Run emotion analysis on defined clips"""
    clips = data.get('clips', [])
    if not clips:
        return {'ok': False, 'error': 'No clips provided'}
    
    results = []
    for clip in clips:
        video_path = clip.get('path', '')
        start = clip.get('start', 0)
        end = clip.get('end', 3)
        
        # Extract frame for visual analysis
        thumb_path = THUMB_DIR / f"clip_{clip.get('id','unknown')}.jpg"
        extract_thumbnail(video_path, (start+end)/2, thumb_path)
        
        # L1: Basic color/brightness analysis (simulate with real computation)
        try:
            from PIL import Image
            import numpy as np
            if thumb_path.exists():
                img = Image.open(thumb_path).convert('RGB')
                arr = np.array(img, dtype=np.float32)
                brightness = float(arr.mean() / 255.0)
                # Color variance as proxy for "interestingness"
                std = float(arr.std(axis=(0,1)).mean() / 255.0)
            else:
                brightness, std = 0.5, 0.3
        except:
            brightness, std = 0.5, 0.3
        
        # L2 visual signals (from brightness + duration)
        duration = end - start
        
        # L3: Gemini native video analysis (real API call)
        l3_label = "待分析"
        l3_detail = ""
        l3_confidence = 0
        emotion_scores = {"平静":0,"愉悦":0,"震撼":0,"漫步":0,"自由":0,"好奇":0,"生机":0}
        
        try:
            l3_result = gemini_analyze_clip(video_path, start, end)
            if l3_result:
                l3_label = l3_result.get('emotion', '未知')
                l3_detail = l3_result.get('detail', '')
                l3_confidence = l3_result.get('confidence', 70)
                if l3_result.get('scores'):
                    emotion_scores.update(l3_result['scores'])
        except Exception as e:
            l3_detail = f"Gemini analysis unavailable: {e}"
        
        # Override if no Gemini result with heuristic
        if l3_confidence == 0:
            if brightness > 0.7:
                l3_label, l3_confidence = '愉悦' if std > 0.3 else '温暖', 65
            elif brightness < 0.3:
                l3_label, l3_confidence = '深沉', 60
            elif std > 0.4:
                l3_label, l3_confidence = '震撼', 70
            else:
                l3_label, l3_confidence = '平静', 60
            l3_detail = f"视觉分析: 亮度{brightness:.2f}, 色彩变化{std:.2f}"
        
        # Emotion scoring
        for emo in emotion_scores:
            if emo == l3_label:
                emotion_scores[emo] = max(emotion_scores.get(emo, 0), l3_confidence)
        
        results.append({
            'id': clip.get('id', ''),
            'emotion': l3_label,
            'confidence': l3_confidence,
            'l3_detail': l3_detail,
            'l1_brightness': round(brightness, 3),
            'l1_color_std': round(std, 3),
            'layers': 'L1+L2+L3',
            'scores': emotion_scores,
            'thumbnail': str(thumb_path) if thumb_path.exists() else None
        })
    
    return {'ok': True, 'clips': results}

def gemini_analyze_clip(video_path, start_sec, end_sec, max_frames=5):
    """Analyze a video clip using Gemini Vision API"""
    api_key = API_KEYS.get('GEMINI_API_KEY') or API_KEYS.get('OPENROUTER_API_KEY') or os.environ.get('GEMINI_API_KEY','')
    if not api_key:
        return None
    
    import urllib.request, base64
    
    # Extract frames
    frames = []
    duration = end_sec - start_sec
    n_frames = min(max_frames, max(3, int(duration)))
    interval = duration / (n_frames + 1)
    
    for i in range(1, n_frames + 1):
        t = start_sec + i * interval
        try:
            with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp:
                fname = tmp.name
            subprocess.run([
                'ffmpeg','-y','-ss',str(t),'-i',str(video_path),
                '-vframes','1','-q:v','3','-vf','scale=512:-1',fname
            ], capture_output=True, timeout=5)
            if os.path.exists(fname) and os.path.getsize(fname) > 100:
                with open(fname, 'rb') as f:
                    frames.append(base64.b64encode(f.read()).decode())
            os.unlink(fname)
        except:
            continue
    
    if not frames:
        return None
    
    # Build Gemini request (OpenRouter OpenAI-compatible format)
    content = []
    for i, b64 in enumerate(frames):
        content.append({"type": "text", "text": f"Frame {i+1} at {start_sec + (i+1)*interval:.1f}s:"})
        content.append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}})
    
    content.append({"type": "text", "text": """Analyze these frames from a video clip. Return ONLY a JSON object:
{
  "emotion": "one of: 平静/愉悦/震撼/漫步/自由/好奇/生机/温暖/深沉",
  "detail": "brief scene description in Chinese (what, mood, composition)",
  "confidence": <number 0-100>,
  "scores": {"平静": <0-100>, "愉悦": <0-100>, "震撼": <0-100>, "漫步": <0-100>, "自由": <0-100>}
}
Be concise. Maximum 100 words total."""})
    
    body = {
        "model": "google/gemini-2.5-flash",
        "messages": [{"role": "user", "content": content}],
        "max_tokens": 300,
        "temperature": 0.3
    }
    
    try:
        req = urllib.request.Request(
            "https://openrouter.ai/api/v1/chat/completions",
            data=json.dumps(body).encode(),
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
        )
        resp = urllib.request.urlopen(req, timeout=30)
        data = json.loads(resp.read())
        content = data['choices'][0]['message']['content']
        
        # Extract JSON from response
        if '```json' in content:
            content = content.split('```json')[1].split('```')[0]
        elif '```' in content:
            content = content.split('```')[1].split('```')[0]
        
        result = json.loads(content.strip())
        result['confidence'] = int(result.get('confidence', 70))
        return result
    except Exception as e:
        print(f"Gemini API error: {e}")
        return None

def api_match(data):
    """Match BGM segments to video clips"""
    bgm_segments = data.get('bgm_segments', [])
    clips = data.get('clips', [])
    
    if not bgm_segments or not clips:
        return {'ok': False, 'error': 'Need both bgm_segments and clips'}
    
    # Simple emotion-based matching algorithm
    # Map BGM segment emotions to clip emotions
    emotion_map = {
        '平和': ['平静','温暖','宁静'],
        '期待': ['愉悦','好奇','自由'],
        '上升': ['震撼','自由','生机'],
        '释放': ['震撼','漫步','自由'],
        'intro': ['平静','温暖'],
        'bridge': ['愉悦','好奇'],
        'build': ['震撼','自由','生机'],
        'climax': ['震撼','漫步']
    }
    
    timeline = []
    used_clips = set()
    
    for seg in bgm_segments:
        seg_type = seg.get('type', 'intro')
        seg_emotion = seg.get('emotion', 'intro')
        
        # Find compatible clips
        preferred = emotion_map.get(seg_type, []) + emotion_map.get(seg_emotion, [])
        
        best_clip = None
        best_score = 0
        
        for clip in clips:
            if clip.get('id') in used_clips:
                continue
            clip_emotion = clip.get('emotion', '')
            clip_conf = clip.get('confidence', 50)
            
            # Score: emotion match + confidence
            score = clip_conf
            if clip_emotion in preferred:
                score += 20
            
            if score > best_score:
                best_score = score
                best_clip = clip
        
        if best_clip:
            used_clips.add(best_clip['id'])
        
        timeline.append({
            'phrase_type': seg_type,
            'start': seg.get('start', 0),
            'end': seg.get('end', 0),
            'label': f"{'🌅' if seg_type=='intro' else '🌊' if seg_type=='bridge' else '📈' if seg_type=='build' else '🔥'} {seg_type.upper()}",
            'clip': best_clip,
            'match_score': round(best_score) if best_clip else 0,
            'candidates': []  # Will be populated by frontend
        })
    
    # Add candidate info for each slot
    for slot in timeline:
        slot['candidates'] = [
            {'id': c.get('id'), 'emotion': c.get('emotion'), 'confidence': c.get('confidence', 0)}
            for c in sorted(clips, key=lambda x: -x.get('confidence', 0))
        ]
    
    return {
        'ok': True,
        'timeline': timeline,
        'total_duration': timeline[-1]['end'] if timeline else 0
    }

def api_bgm_library():
    """Return BGM library"""
    return {
        'ok': True,
        'songs': [
            {
                'id': 'bgm1',
                'title': 'Birds of a Feather',
                'artist': 'Billie Eilish',
                'path': str(ROOT / 'bgm_full.wav'),
                'duration': 55,
                'bpm': 92,
                'key': 'G major',
                'tags': ['Vlog','治愈','旅行']
            }
        ]
    }

# ─── HTTP Server ───
class APIHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(FRONTEND), **kwargs)
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET,POST,OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        qs = parse_qs(parsed.query)
        
        if path == '/api/health':
            self._json({'ok': True, 'version': '1.0.0', 'phase': 1})
        elif path == '/api/scan/groups':
            date_filter = qs.get('date', [None])[0]
            self._json(api_scan(date_filter=date_filter))
        elif path.startswith('/api/task/'):
            task_id = path.split('/api/task/')[1]
            task_file = DATA_DIR / f"task_{task_id}.json"
            if task_file.exists():
                self._json(json.loads(task_file.read_text()))
            else:
                self._json({'ok': False, 'status': 'pending', 'error': 'Task not found or still running'}, 202)
        elif path == '/api/bgm/library':
            self._json(api_bgm_library())
        elif path.startswith('/api/thumb/'):
            # Serve thumbnail
            thumb_path = THUMB_DIR / path.replace('/api/thumb/', '')
            if thumb_path.exists():
                self.send_response(200)
                self.send_header('Content-Type', 'image/jpeg')
                self.end_headers()
                self.wfile.write(thumb_path.read_bytes())
            else:
                self.send_error(404)
        else:
            super().do_GET()
    
    def do_POST(self):
        path = urlparse(self.path).path
        content_len = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_len) if content_len > 0 else b'{}'
        
        try:
            data = json.loads(body) if body else {}
        except:
            data = {}
        
        if path == '/api/scan':
            self._json(api_scan())
        elif path == '/api/bgm/analyze':
            self._bg_task('bgm_analyze', lambda: api_bgm_analyze(data))
        elif path == '/api/bgm/shift':
            # Pitch/tempo shift — TODO: implement ffmpeg rubberband
            self._json({'ok': True, 'message': 'Shift requested (not yet implemented)', 'output': None})
        elif path == '/api/video/asr':
            self._bg_task('asr', lambda: api_asr(data))
        elif path == '/api/video/emotion':
            self._bg_task('emotion', lambda: api_emotion(data))
        elif path == '/api/edit/create':
            self._json(api_match(data))
        elif path == '/api/render/preview':
            self._json({'ok': True, 'message': 'Preview render requested', 'status': 'started'})
        else:
            self._json({'ok': False, 'error': f'Unknown endpoint: {path}'}, 404)
    
    def _json(self, data, code=200):
        self.send_response(code)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False, indent=2).encode())
    
    def _bg_task(self, name, fn):
        """Run task in background, return immediately with task ID"""
        task_id = f"{name}_{int(time.time()*1000)}"
        self._json({'ok': True, 'task_id': task_id, 'status': 'started'})
        
        def run():
            try:
                result = fn()
                # Store result for later retrieval
                task_file = DATA_DIR / f"task_{task_id}.json"
                task_file.write_text(json.dumps(result, ensure_ascii=False))
            except Exception as e:
                task_file = DATA_DIR / f"task_{task_id}.json"
                task_file.write_text(json.dumps({'ok': False, 'error': str(e)}, ensure_ascii=False))
        
        threading.Thread(target=run, daemon=True).start()
    
    def log_message(self, format, *args):
        # Quieter logging
        msg = str(args[0]) if args else ''
        if '/api/' in msg or msg.startswith('POST'):
            print(f"[API] {msg}")
        # else: suppress static file & error logs

def start(port=8766):
    server = HTTPServer(('0.0.0.0', port), APIHandler)
    print(f"""
╔══════════════════════════════════════════════╗
║  🎬 Video Editor MVP · Phase 1 API Server  ║
║  Frontend → http://localhost:{port}            ║
║  API Docs → http://localhost:{port}/api/health ║
╚══════════════════════════════════════════════╝
""")
    server.serve_forever()

if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument('--port', type=int, default=8766)
    args = p.parse_args()
    start(args.port)
