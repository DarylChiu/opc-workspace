"""
SCAN API 模块
素材扫描 + 缩略图
"""
import os, json, subprocess, time, base64, tempfile, shutil
from pathlib import Path
from config import CONFIG

# 绝对路径解析：即使 PATH 缺失也能找到 ffmpeg/ffprobe（launchd 环境兼容）
FFPROBE = shutil.which('ffprobe') or '/opt/homebrew/bin/ffprobe'
FFMPEG = shutil.which('ffmpeg') or '/opt/homebrew/bin/ffmpeg'

MATERIAL_DIR = CONFIG['material_dir']

_material_cache = None
_material_cache_time = 0

def scan_groups(date_str=None):
    """扫描素材目录，返回按日期分组的文件列表（带缓存）"""
    global _material_cache, _material_cache_time
    
    if _material_cache and time.time() - _material_cache_time < 300:
        if date_str:
            filtered = [g for g in _material_cache if date_str in g.get('name','')]
            return {'ok': True, 'groups': filtered or _material_cache, 'material_dir': MATERIAL_DIR, 'cached': True}
        return {'ok': True, 'groups': _material_cache, 'material_dir': MATERIAL_DIR, 'cached': True}
    
    if not os.path.isdir(MATERIAL_DIR):
        return {'ok': False, 'error': f'素材目录不存在: {MATERIAL_DIR}'}
    
    pattern = f"VID_{date_str}_*.mp4" if date_str else "VID_*.mp4"
    files = sorted(Path(MATERIAL_DIR).glob(pattern))
    groups = {}
    
    for f in files:
        name = f.stem
        parts = name.split('_')
        d = 'unknown'
        if len(parts) >= 2 and len(parts[1]) == 8 and parts[1].isdigit():
            d = parts[1]
        
        if d not in groups:
            groups[d] = {'name': f'{d[:4]}-{d[4:6]}-{d[6:8]}', 'files': [], 'excluded': []}
        
        dur = get_duration(str(f))
        orientation = get_orientation(str(f))
        file_id = name.replace(f'VID_{d}_', '')
        
        info = {'id': file_id, 'path': str(f), 'filename': f.name,
                'duration': dur, 'orientation': orientation}
        
        if orientation == '9:16':
            groups[d]['excluded'].append(info)
        else:
            groups[d]['files'].append(info)
    
    result = list(groups.values())
    _material_cache = result
    _material_cache_time = time.time()
    
    return {'ok': True, 'groups': result, 'material_dir': MATERIAL_DIR}

def get_duration(path):
    """获取视频时长（秒）。
    优先 format.duration；缺失/为 0 时回退到视频流 duration；
    再不行用 nb_frames / avg_frame_rate 估算（兼容 moov 在文件尾部等无 format 时长的情况）。
    """
    try:
        r = subprocess.run([FFPROBE,'-v','quiet','-print_format','json',
                           '-show_format','-show_streams', path],
                          capture_output=True, text=True, timeout=15)
        data = json.loads(r.stdout or '{}')
        dur = 0.0
        # 1) format.duration
        try:
            dur = float(data.get('format', {}).get('duration', 0) or 0)
        except Exception:
            dur = 0.0
        # 2) 视频流 duration
        if dur <= 0:
            for s in data.get('streams', []):
                try:
                    d = float(s.get('duration', 0) or 0)
                except Exception:
                    d = 0.0
                if d > 0:
                    dur = d
                    break
        # 3) nb_frames / avg_frame_rate
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
    except Exception:
        return 0

def get_orientation(path):
    try:
        r = subprocess.run([FFPROBE,'-v','quiet','-select_streams','v:0',
                           '-show_entries','stream=width,height','-of','csv=p=0', path],
                          capture_output=True, text=True, timeout=15)
        w, h = map(int, r.stdout.strip().split(','))
        return '16:9' if w > h else '9:16'
    except:
        return '16:9'

def get_thumbnail(video_path, time_sec=1.0):
    tmp = tempfile.mktemp(suffix='.jpg')
    try:
        subprocess.run([FFMPEG,'-y','-ss',str(time_sec),'-i',video_path,
                       '-vframes','1','-q:v','3','-s','320x180', tmp],
                      capture_output=True, timeout=15)
        if os.path.exists(tmp):
            with open(tmp, 'rb') as f:
                return base64.b64encode(f.read()).decode()
    except:
        pass
    finally:
        if os.path.exists(tmp): os.unlink(tmp)
    return ''
