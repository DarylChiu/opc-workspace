#!/usr/bin/env python3
"""
Music Structure Segmentation POC v3
用 librosa.segment + recurrence matrix 做乐句结构识别
"""

import numpy as np
import librosa
import librosa.display
from sklearn.cluster import AgglomerativeClustering
import json

def analyze(audio_path):
    print(f"🎵 加载: {audio_path}")
    y, sr = librosa.load(audio_path, sr=22050)
    duration = len(y) / sr
    hop = 512
    print(f"   时长: {duration:.1f}s")
    
    # ===== 1. Beat-synchronous 特征 =====
    # 先做 beat tracking，然后用 beat 对齐的帧（更符合音乐结构）
    tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sr, hop_length=hop)
    tempo = float(tempo.item() if hasattr(tempo, 'item') else tempo)
    beat_times = librosa.frames_to_time(beat_frames, sr=sr, hop_length=hop)
    print(f"   BPM: {tempo:.0f}, Beats: {len(beat_times)}")
    
    # Beat-synchronous chroma
    chroma = librosa.feature.chroma_cqt(y=y, sr=sr, hop_length=hop)
    chroma_sync = librosa.util.sync(chroma, beat_frames, aggregate=np.median)
    
    # Beat-synchronous MFCC
    mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13, hop_length=hop)
    mfcc_sync = librosa.util.sync(mfcc, beat_frames, aggregate=np.median)
    
    # Beat-sync energy
    rms = librosa.feature.rms(y=y, hop_length=hop)[0]
    rms_sync = np.array([rms[bf:bf+4].mean() if bf+4 < len(rms) else rms[bf:].mean() 
                          for bf in beat_frames])
    rms_norm = rms_sync / rms_sync.max()
    
    # 拼接 beat-sync 特征
    features = np.vstack([chroma_sync, mfcc_sync])  # (25 dims, n_beats)
    n_beats = features.shape[1]
    print(f"   Beat frames: {n_beats}, 特征维度: {features.shape[0]}")
    
    # ===== 2. 用 librosa 的 recurrence matrix =====
    # 先用 time-lag 自相似矩阵找重复结构
    rec = librosa.segment.recurrence_matrix(features, mode='affinity', 
                                              metric='cosine', sym=True)
    
    # 增强对角线: time-lag 表示
    n = rec.shape[0]
    lag = np.zeros((n, n))
    for i in range(n):
        for j in range(n):
            lag[i, j] = rec[i, j] * (1 - 0.5 * abs(i-j)/n)  # 轻微时间惩罚
    
    # ===== 3. 结构边界: agglomerative clustering =====
    # 将 beat 同步帧聚类成结构段落
    # 使用时间约束: 相邻的帧更容易在同一段
    
    # 距离矩阵: 1 - 相似度, 加上时间位置惩罚
    dist = 1 - rec
    # 时间正则化: 相邻帧距离减半
    for i in range(n):
        for j in range(max(0,i-8), min(n,i+8)):
            if abs(i-j) <= 4:
                dist[i,j] *= 0.3  # 非常近 → 强烈吸引到同一段
            elif abs(i-j) <= 8:
                dist[i,j] *= 0.6
    
    # 确保对称
    dist = (dist + dist.T) / 2
    np.fill_diagonal(dist, 0)
    
    # Agglomerative clustering with connectivity constraint
    from sklearn.cluster import AgglomerativeClustering
    # 目标: 6-12 个段落 (典型流行歌曲)
    n_segments = min(12, max(6, n_beats // 16))
    
    # 时间连接约束: 只有相邻帧才能聚类
    connectivity = np.zeros((n, n))
    for i in range(n):
        for j in range(max(0,i-3), min(n,i+4)):
            if i != j:
                connectivity[i, j] = 1
    
    clustering = AgglomerativeClustering(
        n_clusters=n_segments,
        metric='precomputed',
        linkage='average',
        connectivity=connectivity
    )
    labels = clustering.fit_predict(dist)
    
    # ===== 4. 合并相邻的同标签帧 → 连续段落 =====
    segments_raw = []
    current_label = labels[0]
    seg_start = 0
    for i in range(1, n):
        if labels[i] != current_label:
            segments_raw.append((seg_start, i, current_label))
            seg_start = i
            current_label = labels[i]
    segments_raw.append((seg_start, n, current_label))
    
    # 过滤太短的段落 (< 6 beats)
    min_beats = 6
    segments_merged = []
    for start, end, lab in segments_raw:
        if end - start >= min_beats:
            segments_merged.append((start, end, lab))
        elif segments_merged:
            # 合并到上一个段落
            ps, pe, pl = segments_merged.pop()
            segments_merged.append((ps, end, pl))
    
    n_seg_final = len(segments_merged)
    print(f"   段落数: {len(segments_raw)} (raw) → {n_seg_final} (after merge)")
    
    # ===== 5. 提取每段特征 + 命名 =====
    segment_data = []
    for i, (start, end, lab) in enumerate(segments_merged):
        start_sec = beat_times[min(start, len(beat_times)-1)]
        end_sec = beat_times[min(end-1, len(beat_times)-1)]
        seg_energy = rms_norm[start:end].mean()
        seg_features = features[:, start:end].mean(axis=1)
        
        segment_data.append({
            'id': i,
            'start': round(float(start_sec), 1),
            'end': round(float(end_sec), 1),
            'duration': round(float(end_sec - start_sec), 1),
            'energy': round(float(seg_energy), 3),
            'beats': end - start,
            'features': seg_features,
        })
    
    # 找重复结构 (通过特征相似度)
    for i in range(n_seg_final):
        for j in range(i+1, n_seg_final):
            fi = segment_data[i]['features']
            fj = segment_data[j]['features']
            # 余弦相似度
            cos_sim = np.dot(fi, fj) / (np.linalg.norm(fi) * np.linalg.norm(fj) + 1e-8)
            if cos_sim > 0.92:  # 非常相似 → 可能是重复段落 (如 Chorus)
                segment_data[i].setdefault('similar_to', []).append(j)
                segment_data[j].setdefault('similar_to', []).append(i)
    
    # 启发式命名
    for seg in segment_data:
        dur = seg['duration']
        e = seg['energy']
        repeats = len(seg.get('similar_to', []))
        pos = seg['id']
        total = n_seg_final
        
        if pos == 0 and dur < 15 and e < 0.25:
            seg['label'] = 'Intro'
        elif pos == total - 1 and dur < 10 and e < 0.2:
            seg['label'] = 'Outro'
        elif repeats >= 2 and e > 0.4:
            seg['label'] = 'Chorus'
        elif repeats >= 1 and e > 0.35:
            seg['label'] = 'Pre-Chorus'
        elif repeats >= 1:
            seg['label'] = 'Verse'
        elif 0.2 < pos < total - 3 and e > 0.35 and repeats == 0:
            seg['label'] = 'Bridge'
        elif e > 0.5:
            seg['label'] = 'Chorus'
        elif e < 0.25:
            seg['label'] = 'Verse'
        else:
            seg['label'] = 'Verse'
    
    # 标记
    max_e = max(segment_data, key=lambda x: x['energy'])
    max_e['highlight'] = '⚡最激昂'
    
    best_narrative = segment_data[0]
    best_grad = 0
    for k in range(1, len(segment_data)):
        g = segment_data[k]['energy'] - segment_data[k-1]['energy']
        if g > best_grad:
            best_grad = g
            best_narrative = segment_data[k]
    if best_grad > 0.03:
        best_narrative['highlight'] = (best_narrative.get('highlight', '') + ' 📖最有叙事感').strip()
    
    # ===== 6. 输出 =====
    print(f"\n{'='*65}")
    print(f"📋 乐句结构分析结果")
    print(f"{'='*65}")
    print(f"{'标注':10s} {'起始':>6s} {'结束':>6s} {'时长':>6s} {'能量':>6s} {'重复':>4s} {'标记'}")
    print(f"{'-'*55}")
    for seg in segment_data:
        hl = seg.get('highlight', '')
        sim = f"×{len(seg.get('similar_to',[]))}" if seg.get('similar_to') else ''
        print(f"{seg['label']:10s} {seg['start']:5.1f}s {seg['end']:5.1f}s {seg['duration']:5.1f}s {seg['energy']:5.3f} {sim:>4s}  {hl}")
    
    return {
        'duration': round(duration, 1),
        'bpm': round(tempo, 0),
        'segments': [{k: v for k, v in seg.items() if k != 'features'} for seg in segment_data],
    }

if __name__ == '__main__':
    import sys
    path = sys.argv[1] if len(sys.argv) > 1 else '/Users/zhaoyuzhao/.openclaw/xiaofeng_workspace/video_editor_mvp/bgm_full.wav'
    result = analyze(path)
    print(f"\n✅ {len(result['segments'])} 个乐句段落, BPM: {result['bpm']:.0f}")
