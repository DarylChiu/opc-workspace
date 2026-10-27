"""
BGM API 模块
端点: /api/bgm/library, /api/bgm/phrases, /api/bgm/analyze
"""
import json
import os
import sqlite3
from .database import get_db

def get_library():
    """获取歌曲库列表"""
    db = get_db()
    rows = db.execute("""
        SELECT id, title, artist, duration_sec, bpm, key_signature, 
               time_signature, total_bars, source, tags
        FROM song_lib ORDER BY artist, title
    """).fetchall()
    db.close()
    
    return {
        'ok': True,
        'songs': [{
            'id': r['id'],
            'title': r['title'],
            'artist': r['artist'],
            'duration': r['duration_sec'],
            'bpm': r['bpm'],
            'key': r['key_signature'],
            'time_signature': r['time_signature'],
            'total_bars': r['total_bars'],
            'source': r['source'],
            'tags': json.loads(r['tags']) if r['tags'] else [],
        } for r in rows]
    }

def get_phrases(song_id):
    """获取歌曲的乐句结构（含 8bar 单元 + 预标记）"""
    db = get_db()
    
    song = db.execute("SELECT * FROM song_lib WHERE id=?", (song_id,)).fetchone()
    if not song:
        db.close()
        return {'ok': False, 'error': '歌曲未找到'}
    
    phrases = db.execute("""
        SELECT * FROM phrase_lib WHERE song_id=? ORDER BY segment_order
    """, (song_id,)).fetchall()
    
    result_phrases = []
    for p in phrases:
        # 获取 8bar 子单元
        units = db.execute("""
            SELECT * FROM phrase_8bar_units WHERE phrase_id=? ORDER BY unit_order
        """, (p['id'],)).fetchall()
        
        sub_units = [{
            'order': u['unit_order'],
            'bar_offset': u['bar_offset'],
            'start': u['start_sec'],
            'end': u['end_sec'],
            'bars': u['bars'],
        } for u in units]
        
        result_phrases.append({
            'id': p['id'],
            'label': p['label'],
            'description': p['description'] or '',
            'start': p['start_sec'],
            'end': p['end_sec'],
            'duration': round(p['end_sec'] - p['start_sec'], 1),
            'bars': p['bar_end'] - p['bar_start'] if p['bar_end'] > p['bar_start'] else 0,
            'bpm': p['bpm'],
            'key': p['key_signature'],
            'energy': p['energy_level'],
            'emotion': json.loads(p['emotion_tags']) if p['emotion_tags'] else [],
            'highlight': json.loads(p['highlight_tags']) if p['highlight_tags'] else [],
            'chord_progression': json.loads(p['chord_progression']) if p['chord_progression'] else [],
            'sub_8bars': sub_units,
        })
    
    # 预标记逻辑
    _apply_highlights(result_phrases)
    
    db.close()
    
    return {
        'ok': True,
        'song': {
            'id': song['id'],
            'title': song['title'],
            'artist': song['artist'],
            'duration': song['duration_sec'],
            'bpm': song['bpm'],
            'key': song['key_signature'],
            'total_bars': song['total_bars'],
            'source': song['source'],
        },
        'phrases': result_phrases,
    }

def _apply_highlights(phrases):
    """应用预标记: ⚡最激昂 + 📖最有叙事感"""
    if not phrases:
        return
    
    # ⚡最激昂: 能量最高的段落
    max_energy = max(p['energy'] for p in phrases)
    for p in phrases:
        if p['energy'] >= max_energy - 0.05:  # 允许浮动
            if '⚡最激昂' not in p['highlight']:
                p['highlight'].append('⚡最激昂')
    
    # 📖最有叙事感: 能量爬升最快的段落（相邻段能量差最大）
    best_narrative = None
    best_gradient = 0
    for i in range(1, len(phrases)):
        gradient = phrases[i]['energy'] - phrases[i-1]['energy']
        if gradient > best_gradient:
            best_gradient = gradient
            best_narrative = phrases[i]
    
    if best_narrative and best_gradient > 0.03:
        if '📖最有叙事感' not in best_narrative['highlight']:
            best_narrative['highlight'].append('📖最有叙事感')
