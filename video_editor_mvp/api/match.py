"""
Matcher API 模块
BGM 乐句槽位 → 视频素材匹配 + 时长适配 + 导出
"""
import json, os, subprocess, tempfile, time
from config import CONFIG

MATCH_AUTO = CONFIG['match_confidence_auto']
MATCH_REVIEW = CONFIG['match_confidence_review']

def match_phrases_to_clips(phrases, emotion_results):
    """自动匹配 BGM 乐句到视频素材片段，避免重复使用同一片段"""
    matches = []
    used_paths = set()  # 追踪已使用的片段路径+时间
    
    for phrase in phrases:
        bgm_emotion = (phrase.get('emotion', []) or [''])[0]
        bgm_dur = phrase.get('duration', phrase.get('end', 30) - phrase.get('start', 0))
        
        # 为每个素材片段打分（排除已使用的）
        scored = []
        for clip in emotion_results:
            clip_key = f"{clip.get('path','')}_{clip.get('start_sec',0)}"
            if clip_key in used_paths:
                continue
            
            clip_emotion = clip.get('L1', {}).get('primary_emotion', '')
            clip_conf = clip.get('L1', {}).get('confidence', 0)
            clip_dur = clip.get('duration', clip.get('end_sec', 0) - clip.get('start_sec', 0))
            
            emotion_score = (clip_conf * 40) if clip_emotion == bgm_emotion else (clip_conf * 15)
            dur_ratio = min(clip_dur / max(bgm_dur, 1), bgm_dur / max(clip_dur, 1))
            dur_score = dur_ratio * 30
            conf_score = clip_conf * 30
            total = emotion_score + dur_score + conf_score
            
            strategy = 'match'
            if dur_ratio > 0.85: strategy = '🟢 精准'
            elif clip_dur > bgm_dur: strategy = '🟡 截取'
            else: strategy = '🟡 拼接'
            if dur_ratio < 0.3: strategy = '🔴 差距大'
            
            scored.append({
                'path': clip.get('path', ''),
                'clip_id': clip.get('clip_id', ''),
                'start_sec': clip.get('start_sec', 0),
                'end_sec': clip.get('end_sec', 0),
                'duration': clip_dur,
                'L1': clip.get('L1', {}),
                'score': round(total, 1),
                'strategy': strategy,
                'confidence': round(clip_conf * 100),
            })
        
        scored.sort(key=lambda x: -x['score'])
        
        # 自动选择 top 1
        top = scored[0] if scored else None
        if top:
            clip_key = f"{top['path']}_{top['start_sec']}"
            used_paths.add(clip_key)
        auto_confidence = top['confidence'] if top else 0
        
        matches.append({
            'phrase': phrase,
            'top_candidates': scored[:4],
            'auto_pick': top,
            'auto_confidence': auto_confidence,
            'auto_status': '🟢 自动' if auto_confidence >= MATCH_AUTO * 100 else ('🟡 待确认' if auto_confidence >= MATCH_REVIEW * 100 else '🔴 需手动'),
            'strategy': '拼接' if top and top['duration'] < phrase.get('duration', 30) * 0.8 else ('截取' if top and top['duration'] > phrase.get('duration', 30) * 1.2 else '精准'),
        })
    
    return matches

def export_preview(matches, output_dir=None):
    """生成 360p 预览视频"""
    if not output_dir:
        output_dir = CONFIG.get('output_demo_dir', '/tmp')
    
    os.makedirs(output_dir, exist_ok=True)
    
    # 构建 ffmpeg concat 脚本
    # 简化版：逐段拼接
    concat_file = tempfile.mktemp(suffix='.txt')
    output_path = os.path.join(output_dir, 'preview_360p.mp4')
    
    with open(concat_file, 'w') as f:
        for m in matches:
            clip = m.get('auto_pick') or m.get('top_candidates', [{}])[0]
            vpath = clip.get('path', '')
            start = clip.get('start_sec', 0)
            dur = clip.get('duration', 5)
            
            # 截取片段
            seg = tempfile.mktemp(suffix='.mp4')
            subprocess.run(['ffmpeg','-y','-ss',str(start),'-i',vpath,
                           '-t',str(min(dur, 30)),'-c','copy',seg],
                          capture_output=True, timeout=15)
            
            if os.path.exists(seg):
                f.write(f"file '{seg}'\n")
    
    # 合并视频 + 叠加 BGM
    subprocess.run(['ffmpeg','-y','-f','concat','-safe','0','-i',concat_file,
                   '-vf','scale=640:360','-c:v','libx264','-crf','28',
                   '-preset','fast','-c:a','aac','-b:a','64k','-ar','22050',
                   '-shortest','-movflags','+faststart',output_path],
                  capture_output=True, timeout=60)
    
    # 清理
    if os.path.exists(concat_file): os.unlink(concat_file)
    
    return {
        'ok': os.path.exists(output_path),
        'path': output_path,
        'size_mb': round(os.path.getsize(output_path) / 1024 / 1024, 1) if os.path.exists(output_path) else 0,
    }

def export_final(matches, bgm_path, output_dir=None):
    """生成 1080p 最终视频 + BGM 音轨"""
    if not output_dir:
        output_dir = CONFIG.get('output_dir', '/Volumes/TOSHIBA EXT/Video/Masterpieces/Demo_video_auto_editor_output')
    
    os.makedirs(output_dir, exist_ok=True)
    
    concat_file = tempfile.mktemp(suffix='.txt')
    timestamp = time.strftime('%Y%m%d_%H%M%S')
    output_path = os.path.join(output_dir, f'demo_{timestamp}_1080p.mp4')
    
    seg_files = []
    for m in matches:
        clip = m.get('auto_pick') or m.get('top_candidates', [{}])[0]
        vpath = clip.get('path', '')
        start = clip.get('start_sec', 0)
        dur = clip.get('duration', min(30, m['phrase'].get('duration', 30)))
        
        seg = tempfile.mktemp(suffix='.mp4')
        subprocess.run(['ffmpeg','-y','-ss',str(start),'-i',vpath,
                       '-t',str(dur),'-c','copy',seg],
                      capture_output=True, timeout=15)
        if os.path.exists(seg):
            seg_files.append(seg)
            with open(concat_file, 'a') as f:
                f.write(f"file '{seg}'\n")
    
    if not seg_files:
        return {'ok': False, 'error': '无可渲染片段'}
    
    # 合并视频 + 叠加 BGM
    subprocess.run(['ffmpeg','-y','-f','concat','-safe','0','-i',concat_file,
                   '-i',bgm_path,
                   '-vf','scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2',
                   '-c:v','libx264','-crf','23','-preset','medium',
                   '-c:a','aac','-b:a','192k','-shortest',
                   '-movflags','+faststart',output_path],
                  capture_output=True, timeout=120)
    
    # 清理临时文件
    if os.path.exists(concat_file): os.unlink(concat_file)
    for s in seg_files:
        if os.path.exists(s): os.unlink(s)
    
    syncthing = os.path.exists(output_path)
    if syncthing:
        # 同时复制到 Syncthing 目录
        sync_dir = CONFIG.get('syncthing_output_dir', '')
        if sync_dir and os.path.exists(sync_dir):
            import shutil
            shutil.copy2(output_path, os.path.join(sync_dir, os.path.basename(output_path)))
    
    return {
        'ok': syncthing,
        'path': output_path,
        'filename': os.path.basename(output_path),
        'size_mb': round(os.path.getsize(output_path)/1024/1024, 1) if syncthing else 0,
        'syncthing': sync_dir if syncthing else '',
    }
