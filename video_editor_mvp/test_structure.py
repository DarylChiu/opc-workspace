#!/usr/bin/env python3
"""
Music Structure Segmentation POC — 不依赖 energy，用真正的 MIR 方法。

技术路线:
1. Chroma CQT → 和声/调性特征（区分 Verse/Chorus 的关键）
2. MFCC → 音色特征
3. 自相似矩阵 (SSM) → 检测重复段落（Chorus 会重复）
4. 拉普拉斯分割 / 谱聚类 → 找结构边界
5. 启发式标签：第一个短段落=Intro, 重复的高能量段=Chorus, 对比段=Bridge

Ref: Foote (2000), Paulus et al. (2010), McFee & Ellis (2014)
"""

import numpy as np
import librosa
import librosa.display
from sklearn.cluster import SpectralClustering, AgglomerativeClustering
from scipy.spatial.distance import pdist, squareform
from scipy.ndimage import gaussian_filter
import json

def load_and_extract_features(audio_path, sr=22050):
    """加载音频并提取多维度特征"""
    y, sr = librosa.load(audio_path, sr=sr)
    duration = len(y) / sr
    
    # 1. Chroma CQT — 和声特征（最关键, 和弦变化标志结构变化）
    chroma = librosa.feature.chroma_cqt(y=y, sr=sr, hop_length=512)
    
    # 2. MFCC — 音色特征
    mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13, hop_length=512)
    
    # 3. RMS Energy — 用于后期启发式标签，不用于边界检测
    rms = librosa.feature.rms(y=y, hop_length=512)[0]
    
    # 4. Spectral Contrast — 频谱对比度
    contrast = librosa.feature.spectral_contrast(y=y, sr=sr, hop_length=512)
    
    # 5. Tempogram — 节奏特征
    onset_env = librosa.onset.onset_strength(y=y, sr=sr, hop_length=512)
    tempogram = librosa.feature.tempogram(onset_envelope=onset_env, sr=sr, hop_length=512)
    
    # 拼接特征: chroma + mfcc + contrast (降采样 tempogram 对不齐，先不用)
    features = np.vstack([chroma, mfcc, contrast])
    
    # 降采样到 ~2Hz (每0.5s一个点) 减少计算量
    hop_length_feat = 512 * 4  # 每4个hop合并一个
    n_frames_down = features.shape[1] // 4
    features_down = features[:, :n_frames_down*4].reshape(features.shape[0], n_frames_down, 4).mean(axis=2)
    
    # RMS 也降采样
    rms_down = rms[:n_frames_down*4].reshape(n_frames_down, 4).mean(axis=1)
    rms_down = rms_down / rms_down.max()
    
    return y, sr, features_down, rms_down, duration, hop_length_feat

def compute_self_similarity(features):
    """计算自相似矩阵 — 发现重复结构（Chorus 的标志）"""
    # 归一化特征
    features_norm = features / (np.linalg.norm(features, axis=0, keepdims=True) + 1e-8)
    
    # 余弦距离矩阵 → 自相似矩阵
    dists = pdist(features_norm.T, metric='cosine')
    ssm = 1 - squareform(dists)  # 相似度矩阵 (值越大越相似)
    
    # 应用时间延迟惩罚 — 相邻帧天然相似，我们不希望边界太密
    n = ssm.shape[0]
    for i in range(n):
        for j in range(n):
            delay = abs(i - j)
            if delay > 0:
                ssm[i, j] *= np.exp(-delay / 50)  # 远距离相似性更有意义
    
    return ssm

def find_boundaries(ssm, min_segment_sec=8, frame_duration_sec=0.09):
    """从自相似矩阵找结构边界
    
    方法: 检查相邻帧的特征变化程度 (novelty detection)
    """
    n = ssm.shape[0]
    
    # 用 checkerboard kernel 做 novelty detection
    # 沿对角线检查自相似性的突变
    kernel_size = 16  # ~1.5s 窗口 (更细粒度检测)
    novelty = np.zeros(n)
    
    for i in range(kernel_size, n - kernel_size):
        # 检查对角线两侧的相似度差异
        left = np.mean(ssm[i-kernel_size:i, i-kernel_size:i])
        right = np.mean(ssm[i:i+kernel_size, i:i+kernel_size])
        cross = np.mean(ssm[i-kernel_size:i, i:i+kernel_size])
        novelty[i] = max(0, (left + right) / 2 - cross)
    
    # 高斯平滑后找峰值
    novelty = gaussian_filter(novelty, sigma=2)
    
    # 找峰值作为边界
    from scipy.signal import find_peaks
    # 最小段落 ~8秒
    min_distance = max(int(min_segment_sec / frame_duration_sec), 10)
    peaks, properties = find_peaks(novelty, 
                                    distance=min_distance,
                                    prominence=np.std(novelty) * 0.5,
                                    height=np.mean(novelty))
    
    # 转换为原始帧索引
    boundaries = (peaks + kernel_size).tolist()
    
    # 确保首尾
    if 0 not in boundaries:
        boundaries.insert(0, 0)
    if n not in boundaries:
        boundaries.append(n - 1)
    
    return sorted(set(boundaries)), novelty

def label_segments(boundaries, features, rms, n_frames, duration, frame_duration):
    """给检测到的段落打标签
    
    启发式规则:
    - 第一个短段落 (<8s): Intro
    - 重复出现 + 能量相对高: Chorus  
    - 中间 + 特征差异大: Bridge
    - 默认: Verse
    - 最后短段落: Outro
    """
    n = len(boundaries) - 1
    segments = []
    
    for i in range(n):
        start_frame = boundaries[i]
        end_frame = boundaries[i+1]
        start_sec = start_frame * frame_duration
        end_sec = end_frame * frame_duration
        seg_frames = end_frame - start_frame
        seg_duration = end_sec - start_sec
        
        # 该段的特征均值
        seg_features = features[:, start_frame:end_frame].mean(axis=1)
        seg_energy = rms[start_frame:end_frame].mean()
        
        segments.append({
            'id': i,
            'start': round(start_sec, 1),
            'end': round(end_sec, 1),
            'duration': round(seg_duration, 1),
            'energy': round(float(seg_energy), 3),
            'n_frames': seg_frames,
            'features_mean': seg_features.tolist(),
        })
    
    # 1. 找重复段落（通过特征相似度）
    for i in range(n):
        for j in range(i+1, n):
            fi = np.array(segments[i]['features_mean'])
            fj = np.array(segments[j]['features_mean'])
            sim = 1 - np.dot(fi, fj) / (np.linalg.norm(fi) * np.linalg.norm(fj) + 1e-8)
            if sim < 0.15:  # 余弦距离 < 0.15 = 非常相似
                segments[i].setdefault('similar_to', []).append(j)
                segments[j].setdefault('similar_to', []).append(i)
    
    # 2. 打标签
    for seg in segments:
        dur = seg['duration']
        is_short = dur < 8
        has_repeats = len(seg.get('similar_to', [])) > 0
        is_high_energy = seg['energy'] > 0.5
        is_low_energy = seg['energy'] < 0.2
        
        if seg['id'] == 0 and is_short and is_low_energy:
            seg['label'] = 'Intro'
        elif seg['id'] == n - 1 and is_short and seg['energy'] < 0.3:
            seg['label'] = 'Outro'
        elif has_repeats and is_high_energy:
            seg['label'] = 'Chorus'
        elif seg['id'] == n - 2 and not has_repeats:
            # 倒数第二段，特征差异大的 → Bridge
            seg['label'] = 'Bridge'
        elif is_high_energy:
            seg['label'] = 'Pre-Chorus'
        else:
            seg['label'] = 'Verse'
    
    # 3. 特殊标记
    # 找最激昂的段落
    max_energy_seg = max(segments, key=lambda s: s['energy'])
    max_energy_seg['highlight'] = '最激昂 ⚡'
    
    # 找最有叙事感的段落（能量爬升最大的）
    best_narrative = segments[0]
    best_gradient = 0
    for i in range(1, len(segments)):
        grad = segments[i]['energy'] - segments[i-1]['energy']
        if grad > best_gradient:
            best_gradient = grad
            best_narrative = segments[i]
    if best_gradient > 0.1:
        best_narrative['highlight'] = '最有叙事感 📖'
    
    return segments

def analyze_structure(audio_path):
    """主入口: 完整乐句结构分析"""
    print(f"🎵 分析: {audio_path}")
    
    # Step 1: 加载 + 特征提取
    y, sr, features, rms, duration, frame_duration = load_and_extract_features(audio_path)
    frame_duration_sec = frame_duration / sr
    n_frames = features.shape[1]
    print(f"   时长: {duration:.1f}s, 帧数: {n_frames}, 帧间隔: {frame_duration_sec:.2f}s")
    
    # Step 2: 自相似矩阵
    ssm = compute_self_similarity(features)
    print(f"   自相似矩阵: {ssm.shape}")
    
    # Step 3: 边界检测
    boundaries, novelty = find_boundaries(ssm, min_segment_sec=8, frame_duration_sec=frame_duration_sec)
    print(f"   检测到 {len(boundaries)-1} 个段落, 边界: {[round(b*frame_duration_sec,1) for b in boundaries]}")
    
    # Step 4: 标签
    segments = label_segments(boundaries, features, rms, n_frames, duration, frame_duration_sec)
    
    # Step 5: 输出
    print(f"\n📋 乐句结构分析结果:")
    print(f"{'标签':10s} {'起始':>6s} {'结束':>6s} {'时长':>6s} {'能量':>6s} {'标记'}")
    print("-" * 60)
    for seg in segments:
        highlight = seg.get('highlight', '')
        similar = f" ≈段{seg['similar_to']}" if seg.get('similar_to') else ''
        print(f"{seg['label']:10s} {seg['start']:5.1f}s {seg['end']:5.1f}s {seg['duration']:5.1f}s {seg['energy']:5.3f}  {highlight}{similar}")
    
    return {
        'duration': round(duration, 1),
        'frame_interval_sec': round(frame_duration_sec, 2),
        'n_boundaries': len(boundaries),
        'segments': segments,
    }

if __name__ == "__main__":
    import sys
    path = sys.argv[1] if len(sys.argv) > 1 else "/Users/zhaoyuzhao/.openclaw/xiaofeng_workspace/video_editor_mvp/bgm_full.wav"
    result = analyze_structure(path)
