#!/usr/bin/env python3
"""
视频自动化剪辑MVP · API Server v3.0
模块化重构: api/ (database, bgm, scan, asr, emotion, match) + config/
"""
import json
import os
import sys
import uuid
import time
import threading
import traceback
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

# ── PATH 引导 ──────────────────────────────────────────────
# launchd 环境 PATH 极简（/usr/bin:/bin:/usr/sbin:/sbin），找不到 Homebrew 的
# ffmpeg/ffprobe，会导致 scan/ASR/emotion/match 所有 subprocess 调用静默失败
# （时长=0、缩略图为空等）。这里在导入 api 模块前把 Homebrew bin 补进 PATH。
for _hb in ('/opt/homebrew/bin', '/usr/local/bin'):
    if os.path.isdir(_hb) and _hb not in os.environ.get('PATH', '').split(os.pathsep):
        os.environ['PATH'] = _hb + os.pathsep + os.environ.get('PATH', '')

# 添加项目根目录
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import CONFIG, get_path
from api.database import init_db, import_birds_of_a_feather, get_db
from api import bgm as bgm_api
from api import scan as scan_api
from api import asr as asr_api
from api import emotion as emotion_api
from api import match as match_api

# 服务端口
PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8768

# Task 管理（异步任务）
tasks = {}
tasks_lock = threading.Lock()

def create_task():
    tid = str(uuid.uuid4())[:8]
    with tasks_lock:
        tasks[tid] = {'status': 'pending', 'created': time.time(), 'result': None}
    return tid

def update_task(tid, status, result=None):
    with tasks_lock:
        if tid in tasks:
            tasks[tid]['status'] = status
            tasks[tid]['result'] = result

# ═══════════════════════════════════════════════════════════
# HTTP Handler
# ═══════════════════════════════════════════════════════════

class APIHandler(BaseHTTPRequestHandler):
    
    def log_message(self, format, *args):
        pass  # 静默日志
    
    def _send(self, code, data, content_type='application/json'):
        body = json.dumps(data, ensure_ascii=False).encode()
        self.send_response(code)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', len(body))
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(body)
    
    def _static(self, path, mime='text/html'):
        try:
            full = os.path.join(os.path.dirname(__file__), path)
            with open(full, 'rb') as f:
                data = f.read()
            self.send_response(200)
            self.send_header('Content-Type', mime)
            self.send_header('Content-Length', len(data))
            self.end_headers()
            self.wfile.write(data)
        except FileNotFoundError:
            self._send(404, {'error': 'not found'})
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET,POST,OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def do_GET(self):
        url = urlparse(self.path)
        path = url.path
        qs = parse_qs(url.query)
        
        try:
            # 根路径 → 前端
            if path == '/' or path == '':
                return self._static('frontend/index.html')
            
            # 前端静态资源
            if path.startswith('/frontend/'):
                return self._static(path.lstrip('/'))
            
            # 输出文件 (预览/导出视频) — 支持 Range 请求
            if path.startswith('/output/'):
                try:
                    full = os.path.join(os.path.dirname(__file__), path.lstrip('/'))
                    fsize = os.path.getsize(full)
                    ext = path.rsplit('.',1)[-1]
                    mime = {'mp4':'video/mp4','webm':'video/webm','jpg':'image/jpeg','png':'image/png'}.get(ext,'application/octet-stream')
                    
                    range_header = self.headers.get('Range', '')
                    if range_header and range_header.startswith('bytes='):
                        byte_range = range_header.replace('bytes=','').split('-')
                        start = int(byte_range[0]) if byte_range[0] else 0
                        end = int(byte_range[1]) if len(byte_range) > 1 and byte_range[1] else fsize - 1
                        end = min(end, fsize - 1)
                        length = end - start + 1
                        with open(full, 'rb') as f:
                            f.seek(start)
                            data = f.read(length)
                        self.send_response(206)
                        self.send_header('Content-Type', mime)
                        self.send_header('Content-Length', length)
                        self.send_header('Content-Range', f'bytes {start}-{end}/{fsize}')
                        self.send_header('Accept-Ranges', 'bytes')
                        self.end_headers()
                        self.wfile.write(data)
                    else:
                        with open(full, 'rb') as f:
                            data = f.read()
                        self.send_response(200)
                        self.send_header('Content-Type', mime)
                        self.send_header('Content-Length', fsize)
                        self.send_header('Accept-Ranges', 'bytes')
                        self.end_headers()
                        self.wfile.write(data)
                    return
                except FileNotFoundError:
                    return self._send(404, {'error': 'file not found'})
            
            # API
            if path == '/api/health':
                return self._send(200, {'ok': True, 'version': '3.0.0'})
            
            if path == '/api/bgm/library':
                return self._send(200, bgm_api.get_library())
            
            if path == '/api/scan/groups':
                date = qs.get('date', [None])[0]
                return self._send(200, scan_api.scan_groups(date))
            
            if path == '/api/thumb':
                vpath = qs.get('path', [None])[0]
                if not vpath:
                    return self._send(400, {'error': 'missing path'})
                import base64
                b64 = scan_api.get_thumbnail(vpath)
                return self._send(200, {'data': f'data:image/jpeg;base64,{b64}'} if b64 else {'error': 'failed'})
            
            if path == '/api/bgm/phrases':
                sid = qs.get('song_id', [None])[0]
                if not sid:
                    return self._send(400, {'error': 'missing song_id'})
                return self._send(200, bgm_api.get_phrases(sid))
            
            if path == '/api/bgm/audio':
                fpath = qs.get('path', [None])[0]
                if not fpath:
                    return self._send(400, {'error': 'missing path'})
                return self._serve_audio(fpath)
            
            if path == '/api/task':
                tid = qs.get('id', [None])[0]
                with tasks_lock:
                    t = tasks.get(tid, {'status': 'not_found'})
                return self._send(200, t)
            
            if path == '/api/scene/detect':
                vpath = qs.get('path', [None])[0]
                if not vpath:
                    return self._send(400, {'error': 'missing path'})
                return self._send(200, asr_api.detect_scenes(vpath))
            
            if path == '/api/emotion/analyze':
                return self._send(400, {'error': 'use POST'})
            
            return self._send(404, {'error': f'unknown: {path}'})
            
        except Exception as e:
            traceback.print_exc()
            self._send(500, {'error': str(e)})
    
    def do_POST(self):
        url = urlparse(self.path)
        path = url.path
        
        # 读取 body
        length = int(self.headers.get('Content-Length', 0))
        body = json.loads(self.rfile.read(length)) if length > 0 else {}
        
        try:
            if path == '/api/match/run':
                tid = create_task()
                threading.Thread(target=self._run_match, args=(tid, body), daemon=True).start()
                return self._send(202, {'task_id': tid, 'status': 'pending'})
            
            if path == '/api/emotion/analyze':
                tid = create_task()
                threading.Thread(target=self._analyze_emotion, args=(tid, body), daemon=True).start()
                return self._send(202, {'task_id': tid, 'status': 'pending'})
            
            if path == '/api/bgm/analyze':
                # 异步分析
                tid = create_task()
                threading.Thread(target=self._analyze_bgm, args=(tid, body), daemon=True).start()
                return self._send(202, {'task_id': tid, 'status': 'pending'})
            
            if path == '/api/bgm/concat':
                phrase_ids = body.get('phrase_ids', [])
                song_id = body.get('song_id', '')
                if not phrase_ids:
                    return self._send(400, {'error': 'missing phrase_ids'})
                result = self._concat_phrases(phrase_ids, song_id)
                return self._send(200, result)
            
            return self._send(404, {'error': f'unknown: {path}'})
            
        except Exception as e:
            traceback.print_exc()
            self._send(500, {'error': str(e)})
    
    def _serve_audio(self, fpath):
        """音频流式传输，支持 Range 请求"""
        try:
            full = os.path.join(os.path.dirname(__file__), fpath)
            fsize = os.path.getsize(full)
            ext = fpath.rsplit('.',1)[-1].lower()
            mime = {'mp3':'audio/mpeg', 'wav':'audio/wav', 'ogg':'audio/ogg', 'm4a':'audio/mp4', 'aac':'audio/aac'}.get(ext, 'audio/wav')
            
            range_header = self.headers.get('Range', '')
            if range_header and range_header.startswith('bytes='):
                byte_range = range_header.replace('bytes=','').split('-')
                start = int(byte_range[0]) if byte_range[0] else 0
                end = int(byte_range[1]) if len(byte_range) > 1 and byte_range[1] else fsize - 1
                end = min(end, fsize - 1)
                length = end - start + 1
                with open(full, 'rb') as f:
                    f.seek(start)
                    data = f.read(length)
                self.send_response(206)
                self.send_header('Content-Type', mime)
                self.send_header('Content-Length', length)
                self.send_header('Content-Range', f'bytes {start}-{end}/{fsize}')
                self.send_header('Accept-Ranges', 'bytes')
                self.end_headers()
                self.wfile.write(data)
            else:
                with open(full, 'rb') as f:
                    data = f.read()
                self.send_response(200)
                self.send_header('Content-Type', mime)
                self.send_header('Content-Length', fsize)
                self.send_header('Accept-Ranges', 'bytes')
                self.end_headers()
                self.wfile.write(data)
        except FileNotFoundError:
            self._send(404, {'error': 'audio file not found'})
    
    def _concat_phrases(self, phrase_ids, song_id):
        """用 ffmpeg 连接乐句片段"""
        import subprocess, tempfile
        try:
            db = get_db()
            phrases = db.execute("""
                SELECT label, start_sec, end_sec FROM phrase_lib 
                WHERE id IN ({}) ORDER BY segment_order
            """.format(','.join('?' for _ in phrase_ids)), phrase_ids).fetchall()
            
            # 查找音频文件路径
            song = db.execute("SELECT file_path FROM song_lib WHERE id=?", (song_id,)).fetchone() if song_id else None
            db.close()
            
            audio_path = song['file_path'] if song else os.path.join(os.path.dirname(os.path.dirname(__file__)), 'bgm_full.wav')
            if not os.path.exists(audio_path):
                return {'ok': False, 'error': '音频文件不存在'}
            
            out_dir = os.path.join(os.path.dirname(__file__), 'output')
            os.makedirs(out_dir, exist_ok=True)
            out_name = f"bgm_concat_{'_'.join(str(i) for i in phrase_ids)}.wav"
            out_path = os.path.join(out_dir, out_name)
            
            # 如果只有一段，直接截取
            if len(phrases) == 1:
                p = phrases[0]
                cmd = ['ffmpeg', '-y', '-ss', str(p['start_sec']), '-t', str(p['end_sec'] - p['start_sec']),
                       '-i', audio_path, '-c', 'copy', out_path]
            else:
                # 多段拼接：生成 concat 文件列表
                concat_file = os.path.join(out_dir, 'concat_list.txt')
                with open(concat_file, 'w') as f:
                    for p in phrases:
                        seg_path = os.path.join(out_dir, f'_seg_{p["label"]}.wav')
                        extract_cmd = ['ffmpeg', '-y', '-ss', str(p['start_sec']), '-t', str(p['end_sec'] - p['start_sec']),
                                       '-i', audio_path, '-c', 'copy', seg_path]
                        subprocess.run(extract_cmd, capture_output=True, timeout=30)
                        f.write(f"file '{seg_path}'\n")
                
                cmd = ['ffmpeg', '-y', '-f', 'concat', '-safe', '0', '-i', concat_file, '-c', 'copy', out_path]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            if result.returncode != 0:
                return {'ok': False, 'error': result.stderr[-200:]}
            
            # 清理临时文件
            for f in os.listdir(out_dir):
                if f.startswith('_seg_') or f == 'concat_list.txt':
                    try: os.remove(os.path.join(out_dir, f))
                    except: pass
            
            return {
                'ok': True,
                'output_path': out_path,
                'output_name': out_name,
                'phrases': [{'label': p['label'], 'start': p['start_sec'], 'end': p['end_sec']} for p in phrases],
            }
        except Exception as e:
            import traceback
            traceback.print_exc()
            return {'ok': False, 'error': str(e)}
    
    def _analyze_emotion(self, tid, body):
        """三层情感漏斗分析（异步）"""
        try:
            clips = body.get('clips', [])  # [{path, start_sec, end_sec, dialogue_text}]
            if not clips:
                update_task(tid, 'error', {'error': 'no clips provided'})
                return
            
            total = len(clips)
            results = []
            l2_l3_candidates = []
            
            for i, clip in enumerate(clips):
                progress = int((i / total) * 90)
                update_task(tid, 'running', {
                    'progress': progress,
                    'status': f'L1 分析中 ({i+1}/{total})'
                })
                
                video_path = clip['path']
                start = clip['start_sec']
                end = clip['end_sec']
                
                # L1: Gemini 视频分析
                l1 = emotion_api.analyze_clip(video_path, start, end)
                
                # L2: 对白情绪
                l2 = emotion_api.analyze_l2_dialogue(clip.get('dialogue_text', ''))
                
                # L3: 视觉信号
                l3 = emotion_api.analyze_l3_visual(video_path, start, end)
                
                results.append({
                    'path': video_path,
                    'start_sec': start,
                    'end_sec': end,
                    'duration': round(end - start, 1),
                    'L1': l1,
                    'L2': l2,
                    'L3': l3,
                })
                
                # 补漏检查: L2+L3 发现的可能有效素材
                if not l1.get('ok') and (l2.get('confidence', 0) > 0.3 or l3.get('motion_estimate') == 'high'):
                    l2_l3_candidates.append(clip)
            
            update_task(tid, 'running', {
                'progress': 95,
                'status': f'完成 {total}/{total}，待补漏 {len(l2_l3_candidates)}' if l2_l3_candidates else f'完成 {total}/{total}'
            })
            
            update_task(tid, 'done', {
                'ok': True,
                'results': results,
                'total': total,
                'l1_success': sum(1 for r in results if r['L1'].get('ok')),
                'l2_l3_candidates': len(l2_l3_candidates),
                'progress': 100,
            })
        except Exception as e:
            update_task(tid, 'error', {'ok': False, 'error': str(e)})
    
    def _run_match(self, tid, body):
        """执行匹配编排 + 导出（异步）"""
        try:
            phrases = body.get('phrases', [])
            clips = body.get('clips', [])
            export_type = body.get('export', 'match')  # match | preview | final
            
            update_task(tid, 'running', {'progress': 0, 'status': '匹配中...'})
            
            # 匹配
            matches = match_api.match_phrases_to_clips(phrases, clips)
            update_task(tid, 'running', {'progress': 50, 'status': '匹配完成'})
            
            result = {'matches': matches}
            
            if export_type == 'preview':
                update_task(tid, 'running', {'progress': 60, 'status': '生成360p预览...'})
                preview = match_api.export_preview(matches)
                result['preview'] = preview
                update_task(tid, 'running', {'progress': 90, 'status': '预览完成'})
            
            if export_type == 'final':
                update_task(tid, 'running', {'progress': 60, 'status': '渲染1080p...'})
                bgm_path = body.get('bgm_path', '')
                final = match_api.export_final(matches, bgm_path)
                result['final'] = final
                update_task(tid, 'running', {'progress': 95, 'status': '渲染完成'})
            
            update_task(tid, 'done', {'ok': True, **result, 'progress': 100})
        except Exception as e:
            import traceback
            traceback.print_exc()
            update_task(tid, 'error', {'ok': False, 'error': str(e)})
    
    def _analyze_bgm(self, tid, body):
        """BGM 分析任务（异步）"""
        try:
            update_task(tid, 'running', {'progress': 0})
            
            # 当前只支持 Birds of a Feather
            song_id = body.get('song_id', 'birds_of_a_feather')
            result = bgm_api.get_phrases(song_id)
            
            update_task(tid, 'done', {
                'ok': True,
                'analysis': result,
                'progress': 100,
            })
        except Exception as e:
            update_task(tid, 'error', {'ok': False, 'error': str(e)})


# ═══════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════

if __name__ == '__main__':
    # 初始化数据库
    init_db()
    if get_db().execute("SELECT COUNT(*) FROM song_lib").fetchone()[0] == 0:
        import_birds_of_a_feather()
    
    server = HTTPServer(('0.0.0.0', PORT), APIHandler)
    print(f"🎬 Video Editor MVP v3.0 · http://localhost:{PORT}")
    print(f"   BGM DB: {len(bgm_api.get_library()['songs'])} songs loaded")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n👋 服务已停止")
