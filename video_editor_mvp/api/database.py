"""
视频编辑器 MVP · 数据库模型
song_lib: 歌曲库
phrase_lib: 乐句库（包含 8bar 子单元）
"""
import sqlite3
import json
import os

DB_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
DB_PATH = os.path.join(DB_DIR, 'bgm_library.db')

def get_db():
    os.makedirs(DB_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn

def init_db():
    """创建表结构（幂等）"""
    db = get_db()
    db.executescript("""
        CREATE TABLE IF NOT EXISTS song_lib (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            artist TEXT NOT NULL,
            file_path TEXT NOT NULL,
            duration_sec REAL,
            bpm REAL,
            key_signature TEXT,
            time_signature TEXT DEFAULT '4/4',
            total_bars INTEGER,
            source TEXT DEFAULT 'manual',
            tags TEXT DEFAULT '[]',
            thumbnail_waveform TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE TABLE IF NOT EXISTS phrase_lib (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            song_id TEXT NOT NULL REFERENCES song_lib(id),
            segment_order INTEGER NOT NULL,
            label TEXT NOT NULL,
            description TEXT,
            bar_start INTEGER NOT NULL,
            bar_end INTEGER NOT NULL,
            start_sec REAL NOT NULL,
            end_sec REAL NOT NULL,
            bpm REAL,
            key_signature TEXT,
            energy_level REAL,
            emotion_tags TEXT DEFAULT '[]',
            highlight_tags TEXT DEFAULT '[]',
            chord_progression TEXT DEFAULT '[]',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE TABLE IF NOT EXISTS phrase_8bar_units (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            phrase_id INTEGER NOT NULL REFERENCES phrase_lib(id),
            unit_order INTEGER NOT NULL,
            bar_offset INTEGER NOT NULL,
            start_sec REAL NOT NULL,
            end_sec REAL NOT NULL,
            bars INTEGER NOT NULL
        );
        
        CREATE INDEX IF NOT EXISTS idx_phrase_song ON phrase_lib(song_id);
        CREATE INDEX IF NOT EXISTS idx_8bar_phrase ON phrase_8bar_units(phrase_id);
    """)
    
    # 兼容旧数据库：添加 chord_progression 列（如果不存在）
    try:
        db.execute("ALTER TABLE phrase_lib ADD COLUMN chord_progression TEXT DEFAULT '[]'")
    except:
        pass
    
    db.commit()
    db.close()

def import_birds_of_a_feather():
    """导入 Birds of a Feather 的 Hooktheory 结构"""
    json_path = os.path.join(os.path.dirname(DB_DIR), 'data', 'bgm_structure_birds_of_a_feather.json')
    if not os.path.exists(json_path):
        json_path = os.path.join(os.path.dirname(DB_DIR), 'bgm_structure_birds_of_a_feather.json')
    if not os.path.exists(json_path):
        print("⚠️  Birds of a Feather 结构文件未找到")
        return False
    
    with open(json_path) as f:
        data = json.load(f)
    
    db = get_db()
    
    # 插入歌曲
    db.execute("""
        INSERT OR REPLACE INTO song_lib (id, title, artist, file_path, duration_sec, bpm, 
                                          key_signature, time_signature, total_bars, source, tags)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        'birds_of_a_feather',
        data['song'], data['artist'],
        os.path.join(os.path.dirname(os.path.dirname(__file__)), 'bgm_full.wav'),
        data['duration_sec'], data['bpm'],
        data['key'], data['time_signature'], data['total_bars'],
        'hooktheory',
        json.dumps(['Vlog', '治愈', '旅行'])
    ))
    
    # 删除旧乐句
    db.execute("DELETE FROM phrase_8bar_units WHERE phrase_id IN (SELECT id FROM phrase_lib WHERE song_id='birds_of_a_feather')")
    db.execute("DELETE FROM phrase_lib WHERE song_id='birds_of_a_feather'")
    
    # 插入乐句
    for i, sec in enumerate(data['sections']):
        # Calculate bar numbers from cumulative sections
        cumulative_bars = 0
        bar_start = 0
        for j in range(i):
            cumulative_bars += data['sections'][j].get('bars', 8)
        bar_start = cumulative_bars
        bar_end = bar_start + sec.get('bars', 8)
        
        cur = db.execute("""
            INSERT INTO phrase_lib (song_id, segment_order, label, description, 
                                     bar_start, bar_end, start_sec, end_sec,
                                     bpm, key_signature, energy_level, emotion_tags, highlight_tags, chord_progression)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            'birds_of_a_feather', i, sec['label'],
            '',
            bar_start, bar_end,
            sec['start_sec'], sec['end_sec'],
            data['bpm'], data['key'],
            sec.get('energy', 0.5),
            json.dumps([sec.get('emotion', '')]),
            json.dumps([]),
            json.dumps(sec.get('chord_progression', []))
        ))
        phrase_id = cur.lastrowid
        
        # 插入 8bar 子单元
        sub_units = [s for s in data['sub_8bars'] if s['section'] == sec['label']]
        for j, sub in enumerate(sub_units):
            db.execute("""
                INSERT INTO phrase_8bar_units (phrase_id, unit_order, bar_offset, start_sec, end_sec, bars)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (phrase_id, j, sub.get('bar_offset', j*8), sub['start_sec'], sub['end_sec'], sub['bars']))
    
    db.commit()
    db.close()
    print(f"✅ Birds of a Feather 导入完成: {len(data['sections'])} 乐句, {len(data['sub_8bars'])} 8bar单元")
    return True

if __name__ == '__main__':
    init_db()
    import_birds_of_a_feather()
