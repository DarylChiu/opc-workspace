#!/usr/bin/env python3
"""
Music Structure Segmentation POC v2
用自相似矩阵 + 谱聚类做真正的乐句结构识别
"""

import numpy as np
import librosa
from sklearn.cluster import AgglomerativeClustering
from scipy.ndimage import gaussian_filter
from scipy.signal import find_peaks
from scipy.spatial.distance import pdist, squareform
import json

def analyze(audio_path):
    print(f"🎵 加载: {audio_path}")
    y, sr = librosa.load(audio_path, sr=22050)
    duration = len(y) / sr
    print(f"   时长: {duration:.1f}s, 采样率: {sr}")
    
    # ===== 1. 提取多维度特征 =====
    hop = 2048  # ~0.09s per frame
    chroma = librosa.feature.chroma_cqt(y=y, sr=sr, hop_length=hop)
    mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13, hop_length=hop)
    contrast = librosa.feature.spectral_contrast(y=y, sr=sr, hop_length=hop, n_bands=6)
    rms = librosa.feature.rms(y=y, hop_length=hop)[0]
    
    # 拼接 → 每帧一个特征向量
    features = np.vstack([chroma, mfcc, contrast])  # (12+13+7=32 dims, n_frames)
    n_frames = features.shape[1]
    frame_sec = hop / sr
    print(f"   帧数: {n_frames}, 帧间隔: {frame_sec:.3f}s, 特征维度: {features.shape[0]}")
    
    # ===== 2. 自相似矩阵 =====
    # L2归一化
    feat_norm = features / (np.linalg.norm(features, axis=0, keepdims=True) + 1e-8)
    # 余弦相似度
    ssm = feat_norm.T @ feat_norm  # (n_frames, n_frames), 值范围 [0,1]
    
    # 时间距离惩罚: 太近的帧天然相似，我们更关注远距离的重复
    times = np.arange(n_frames) * frame_sec
    td = np.abs(times[:, None] - times[None, :])
    ssm = ssm * (1 - np.exp(-td / 30))  # 30秒内天然衰减
    
    # 高斯模糊 → 去噪
    ssm_smooth = gaussian_filter(ssm, sigma=1.5)
    
    print(f"   自相似矩阵: {ssm_smooth.shape}, 均值: {ssm_smooth.mean():.3f}")
    
    # ===== 3. 边界检测 =====
    # 用 checkerboard kernel 做 novelty detection
    ks = 24  # ~2.2s 窗口
    novelty = np.zeros(n_frames)
    for i in range(ks, n_frames - ks):
        left = ssm_smooth[i-ks:i, i-ks:i].mean()
        right = ssm_smooth[i:i+ks, i:i+ks].mean()
        cross = ssm_smooth[i-ks:i, i:i+ks].mean()
        novelty[i] = max(0, left + right - 2 * cross)
    
    novelty = gaussian_filter(novelty, sigma=4)
    
    # 找峰值
    min_dist = int(6 / frame_sec)  # 最小6秒间距
    peaks, props = find_peaks(novelty, distance=min_dist,
                               prominence=np.std(novelty) * 0.3)
    
    boundaries = [0] + peaks.tolist() + [n_frames - 1]
    boundaries = sorted(set(boundaries))
    
    # 过滤太短的段落 (<3s)
    min_frames = int(3 / frame_sec)
    filtered = [boundaries[0]]
    for i in range(1, len(boundaries)):
        if boundaries[i] - filtered[-1] >= min_frames:
            filtered.append(boundaries[i])
    boundaries = filtered
    n_seg = len(boundaries) - 1
    
    print(f"   检测到 {n_seg} 个段落:")
    for i in range(n_seg):
        s = boundaries[i] * frame_sec
        e = boundaries[i+1] * frame_sec
        seg_feat = features[:, boundaries[i]:boundaries[i+1]].mean(axis=1)
        seg_energy = rms[boundaries[i]:boundaries[i+1]].mean() / rms.max()
        print(f"      段{i}: {s:5.1f}s - {e:5.1f}s  ({e-s:5.1f}s)  能量:{seg_energy:.3f}")
    
    # ===== 4. 聚类相似段落 (找 Verse/Chorus 重复) =====
    segment_features = []
    segment_energies = []
    for i in range(n_seg):
        sf = features[:, boundaries[i]:boundaries[i+1]].mean(axis=1)
        segment_features.append(sf)
        segment_energies.append(rms[boundaries[i]:boundaries[i+1]].mean())
    
    segment_features = np.array(segment_features)
    segment_energies = np.array(segment_energies)
    segment_energies = segment_energies / segment_energies.max()
    
    # 谱聚类: 把段落分成2-3组 (Verse组/Chorus组/Bridge组)
    n_clusters = min(3, n_seg)
    if n_seg >= 3:
        clustering = AgglomerativeClustering(n_clusters=n_clusters, metric='cosine', linkage='average')
        labels = clustering.fit_predict(segment_features)
    else:
        labels = np.zeros(n_seg, dtype=int)
    
    # 给每组一个名字: 能量最高的组=Chorus, 最低的=Verse, 中间的=Bridge
    cluster_energy = {}
    for i, lab in enumerate(labels):
        cluster_energy.setdefault(lab, []).append(segment_energies[i])
    cluster_mean_energy = {k: np.mean(v) for k, v in cluster_energy.items()}
    sorted_clusters = sorted(cluster_mean_energy, key=cluster_mean_energy.get)
    
    cluster_names = {}
    if len(sorted_clusters) >= 3:
        cluster_names[sorted_clusters[0]] = 'Verse'
        cluster_names[sorted_clusters[1]] = 'Bridge'
        cluster_names[sorted_clusters[2]] = 'Chorus'
    else:
        cluster_names[sorted_clusters[0]] = 'Chorus' if cluster_mean_energy[sorted_clusters[0]] > 0.5 else 'Verse'
        if len(sorted_clusters) > 1:
            cluster_names[sorted_clusters[1]] = 'Chorus'
    
    # ===== 5. 生成最终结果 =====
    segments = []
    for i in range(n_seg):
        s = round(boundaries[i] * frame_sec, 1)
        e = round(boundaries[i+1] * frame_sec, 1)
        label = cluster_names.get(labels[i], f'Seg{i}')
        seg_energy = round(float(segment_energies[i]), 3)
        
        # 第一段短+低能量 → Intro
        if i == 0 and (e - s) < 12 and seg_energy < 0.3:
            label = 'Intro'
        # 最后一段短+低能量 → Outro
        if i == n_seg - 1 and (e - s) < 8 and seg_energy < 0.2:
            label = 'Outro'
        
        seg = {
            'id': i, 'start': s, 'end': e,
            'duration': round(e - s, 1),
            'label': label,
            'energy': seg_energy,
            'cluster': int(labels[i]),
        }
        segments.append(seg)
    
    # 标记: 最激昂 + 最有叙事感
    max_e = max(segments, key=lambda x: x['energy'])
    max_e['highlight'] = '最激昂'
    
    best_narrative = segments[0]
    best_grad = 0
    for i in range(1, len(segments)):
        g = segments[i]['energy'] - segments[i-1]['energy']
        if g > best_grad:
            best_grad = g
            best_narrative = segments[i]
    if best_grad > 0.05:
        best_narrative['highlight'] = '最有叙事感'
    
    # ===== 6. 输出 =====
    print(f"\n{'='*70}")
    print(f"📋 乐句结构: {audio_path.split('/')[-1]}")
    print(f"{'='*70}")
    print(f"{'标注':8s} {'起始':>6s} {'结束':>6s} {'时长':>6s} {'能量':>6s} {'标记'}")
    print(f"{'-'*55}")
    for seg in segments:
        hl = seg.get('highlight', '')
        print(f"{seg['label']:8s} {seg['start']:5.1f}s {seg['end']:5.1f}s {seg['duration']:5.1f}s {seg['energy']:5.3f}  {hl}")
    
    return {
        'duration': round(duration, 1),
        'segments': segments,
        'frame_interval': round(frame_sec, 3),
    }

if __name__ == '__main__':
    import sys
    path = sys.argv[1] if len(sys.argv) > 1 else '/Users/zhaoyuzhao/.openclaw/xiaofeng_workspace/video_editor_mvp/bgm_full.wav'
    result = analyze(path)
    print(f"\n✅ 分析完成: {len(result['segments'])} 个乐句段落")
