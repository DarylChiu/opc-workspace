#!/usr/bin/env python3
"""
Music Structure Segmentation v4.1
改进：更敏感的 novelty + 位置先验 + spectral contrast 重复检测 + 能量趋势
"""

import numpy as np
import librosa
from scipy.ndimage import gaussian_filter1d
from scipy.signal import find_peaks
import json

MIN_SECTION_BARS = 8
SUBDIVISION_BARS = 8
BEATS_PER_BAR = 4


def analyze(audio_path, verbose=True):
    y, sr = librosa.load(audio_path, sr=22050)
    duration = len(y) / sr
    hop = 512
    
    if verbose:
        print(f"🎵 加载: {audio_path}")
        print(f"   时长: {duration:.1f}s")
    
    # ============================================================
    # Step 1: Beat & Bar
    # ============================================================
    tempo, beats = librosa.beat.beat_track(y=y, sr=sr, hop_length=hop)
    tempo = float(tempo.item() if hasattr(tempo, 'item') else tempo)
    beat_times = librosa.frames_to_time(beats, sr=sr, hop_length=hop)
    
    if verbose:
        print(f"   BPM: {tempo:.0f}, Raw beats: {len(beat_times)}")
    
    # ============================================================
    # Step 2: Beat-sync features
    # ============================================================
    chroma = librosa.feature.chroma_cqt(y=y, sr=sr, hop_length=hop)
    chroma_bs = librosa.util.sync(chroma, beats, aggregate=np.median)
    
    mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13, hop_length=hop)
    mfcc_bs = librosa.util.sync(mfcc, beats, aggregate=np.median)
    
    contrast = librosa.feature.spectral_contrast(y=y, sr=sr, hop_length=hop)
    contrast_bs = librosa.util.sync(contrast, beats, aggregate=np.median)
    
    rms = librosa.feature.rms(y=y, hop_length=hop)[0]
    rms_bs = np.array([rms[max(0,b):min(len(rms),b+4)].mean() for b in beats])
    rms_bs = rms_bs / (rms_bs.max() + 1e-8)
    
    onset = librosa.onset.onset_strength(y=y, sr=sr, hop_length=hop)
    onset_bs = np.array([onset[max(0,b):min(len(onset),b+4)].mean() for b in beats])
    onset_bs = onset_bs / (onset_bs.max() + 1e-8)
    
    # 对齐
    min_frames = min(chroma_bs.shape[1], mfcc_bs.shape[1], contrast_bs.shape[1],
                      len(rms_bs), len(onset_bs))
    chroma_bs = chroma_bs[:, :min_frames]
    mfcc_bs = mfcc_bs[:, :min_frames]
    contrast_bs = contrast_bs[:, :min_frames]
    rms_bs = rms_bs[:min_frames]
    onset_bs = onset_bs[:min_frames]
    beat_times = beat_times[:min_frames]
    
    n_beats_actual = min_frames
    n_bars_total = n_beats_actual // BEATS_PER_BAR
    bar_sec = 60 / tempo * BEATS_PER_BAR
    
    if verbose:
        print(f"   Beat帧: {n_beats_actual}, Bars: ~{n_bars_total}")
        print(f"   1 bar ≈ {bar_sec:.1f}s, 8 bars ≈ {bar_sec*8:.0f}s")
    
    # ============================================================
    # Step 3: Multi-feature SSM
    # ============================================================
    from sklearn.preprocessing import StandardScaler
    
    # 建两个 SSM：chroma（和声结构）和 timbre（MFCC+contrast，音色/配器）
    def make_ssm(feat_matrix, time_decay=0.3):
        f = StandardScaler().fit_transform(feat_matrix.T).T
        norms = np.linalg.norm(f, axis=0) + 1e-8
        s = np.dot(f.T, f) / np.outer(norms, norms)
        for i in range(s.shape[0]):
            for j in range(s.shape[0]):
                d = abs(i-j) / s.shape[0]
                s[i,j] *= np.exp(-time_decay * d)
        return s
    
    ssm_chroma = make_ssm(chroma_bs)
    ssm_timbre = make_ssm(np.vstack([mfcc_bs, contrast_bs]))
    
    # 融合 SSM：取两者最小值（两者都相似才是真相似）
    ssm = np.minimum(ssm_chroma, ssm_timbre)
    
    # ============================================================
    # Step 4: Novelty 函数（两轮：粗+细）
    # ============================================================
    def compute_novelty(s, Ls=[4, 8, 16]):
        """用多个 kernel 大小计算 novelty，然后取 max（多尺度）"""
        n = s.shape[0]
        nov = np.zeros(n)
        for L in Ls:
            for k in range(L, n - L):
                tl = s[k-L:k, k-L:k].mean()
                br = s[k:k+L, k:k+L].mean()
                cr = s[k-L:k, k:k+L].mean()
                nov[k] = max(nov[k], max(0, tl + br - 2*cr))
        return nov
    
    novelty_raw = compute_novelty(ssm)
    novelty_smooth = gaussian_filter1d(novelty_raw, sigma=2.0)
    
    # 多轮峰值检测：先用宽松阈值找候选，再过滤
    # 第1轮：较低阈值找所有候选
    thresh_low = np.percentile(novelty_smooth, 70)  # 前30%
    peaks_all, _ = find_peaks(novelty_smooth, height=thresh_low, distance=4)
    
    # 对齐到 bar
    all_candidates = sorted(set(
        round(p / BEATS_PER_BAR) * BEATS_PER_BAR for p in peaks_all
    ))
    all_candidates = [c for c in all_candidates if 0 < c < n_beats_actual - 4]
    
    # 按 novelty 值排序，从高到低取，但保持最小间距
    scored = [(c, novelty_smooth[c]) for c in all_candidates]
    scored.sort(key=lambda x: -x[1])
    
    min_gap = MIN_SECTION_BARS * BEATS_PER_BAR  # 32 beats min between sections
    selected = [0]
    for cand, score in scored:
        if all(abs(cand - s) >= min_gap for s in selected):
            selected.append(cand)
    
    selected.sort()
    if selected[-1] < n_beats_actual - 4:
        selected.append(n_beats_actual - 1)
    else:
        selected[-1] = n_beats_actual - 1
    
    # 确保首尾
    boundaries = [0]
    for b in selected[1:]:
        if b - boundaries[-1] >= min_gap:
            boundaries.append(b)
    if boundaries[-1] != n_beats_actual - 1:
        boundaries.append(n_beats_actual - 1)
    
    n_sections = len(boundaries) - 1
    
    if verbose:
        print(f"\n   Novelty peaks: {len(peaks_all)} candidates → {len(selected)} selected")
        print(f"   结构边界 (beats): {boundaries}")
        print(f"   段落数: {n_sections}")
    
    # ============================================================
    # Step 5: 段特征提取
    # ============================================================
    sections = []
    for i in range(n_sections):
        sb = boundaries[i]
        eb = boundaries[i+1]
        sec_beats = eb - sb
        sec_bars = sec_beats // BEATS_PER_BAR
        
        ts = beat_times[min(sb, len(beat_times)-1)]
        te = beat_times[min(eb-1, len(beat_times)-1)]
        
        seg_rms = rms_bs[sb:eb].mean()
        seg_onset = onset_bs[sb:eb].mean()
        
        # 能量趋势：线性回归斜率
        x = np.arange(sb, eb)
        y = rms_bs[sb:eb]
        if len(y) > 2:
            slope = np.polyfit(x, y, 1)[0] * 1000  # 每 beat 变化率 (放大)
        else:
            slope = 0
        
        # 段内 RMS 变化幅度
        rms_range = rms_bs[sb:eb].max() - rms_bs[sb:eb].min()
        
        # 段内 spectral contrast 均值（配器丰富度）
        seg_contrast = contrast_bs[:, sb:eb].mean()
        
        sections.append({
            'id': i,
            'beat_start': int(sb), 'beat_end': int(eb),
            'start': round(float(ts), 1), 'end': round(float(te), 1),
            'duration': round(float(te-ts), 1),
            'beats': int(sec_beats), 'bars': int(sec_bars),
            'energy': round(float(seg_rms), 3),
            'onset_density': round(float(seg_onset), 3),
            'energy_slope': round(float(slope), 2),
            'energy_range': round(float(rms_range), 3),
            'spectral_contrast': round(float(seg_contrast), 3),
            'chroma_vec': chroma_bs[:, sb:eb].mean(axis=1),
            'timbre_vec': np.hstack([mfcc_bs[:, sb:eb].mean(axis=1),
                                      contrast_bs[:, sb:eb].mean(axis=1)]),
        })
    
    # ============================================================
    # Step 6: 结构重复检测
    # ============================================================
    for a in range(n_sections):
        for b_idx in range(a + 1, n_sections):
            # Chroma 相似
            cs = np.dot(sections[a]['chroma_vec'], sections[b_idx]['chroma_vec']) / \
                 (np.linalg.norm(sections[a]['chroma_vec']) * np.linalg.norm(sections[b_idx]['chroma_vec']) + 1e-8)
            # Timbre 相似
            ts = np.dot(sections[a]['timbre_vec'], sections[b_idx]['timbre_vec']) / \
                 (np.linalg.norm(sections[a]['timbre_vec']) * np.linalg.norm(sections[b_idx]['timbre_vec']) + 1e-8)
            
            # 两者都相似 (>0.92) 才算重复段
            if cs > 0.92 and ts > 0.90:
                sections[a].setdefault('similar_to', []).append(b_idx)
                sections[b_idx].setdefault('similar_to', []).append(a)
    
    # ============================================================
    # Step 7: 智能分类
    # ============================================================
    for sec in sections:
        pos = sec['id']
        total = n_sections
        e = sec['energy']
        onset = sec['onset_density']
        slope = sec['energy_slope']
        repeats = len(sec.get('similar_to', []))
        bars = sec['bars']
        e_range = sec['energy_range']
        contrast = sec['spectral_contrast']
        
        label = None
        highlight = []
        
        # --- 位置先验 ---
        is_first = (pos == 0)
        is_last = (pos == total - 1)
        is_early = (pos <= total * 0.25)  # 前 25%
        is_late = (pos >= total * 0.75)   # 后 25%
        
        # --- 分类逻辑 ---
        
        # Intro: 第一段 + 能量偏低或正在上升
        if is_first:
            if e < 0.45:
                label = 'Intro'
                highlight.append('🌅开场')
            elif slope > 0.05:  # 能量在快速上升
                label = 'Intro / Build'
                highlight.append('🌅开场蓄力')
            else:
                label = 'Intro'
                highlight.append('🌅开场')
        
        # Outro: 最后一段 + 能量下降或偏低
        elif is_last:
            if slope < -0.05:
                label = 'Outro'
                highlight.append('🌇收束')
            elif e < 0.35:
                label = 'Outro'
                highlight.append('🌇尾声')
            else:
                label = 'Ending'
                highlight.append('🔚结束')
        
        # Bridge: 中间位置, 和其他段都不像, 能量偏低或变化大
        elif repeats == 0 and not is_first and not is_last:
            if contrast < 0.3:  # 配器简单
                label = 'Bridge'
                highlight.append('🌊间奏')
            elif e < 0.35:
                label = 'Bridge'
                highlight.append('🌊过渡')
            elif e_range > 0.15:  # 能量波动大
                label = 'Bridge'
                highlight.append('🌊转折')
            else:
                label = 'Verse'
        
        # Chorus: 重复出现 + 能量高 + onset 密
        elif repeats >= 1 and e > 0.35:
            label = 'Chorus'
            if e > 0.55:
                highlight.append('⚡高潮')
            if onset > 0.35:
                highlight.append('🥁密集')
        
        # Pre-Chorus / Build: 能量快速上升
        elif slope > 0.08 and e > 0.3:
            label = 'Build / Pre-Chorus'
            highlight.append('📈蓄力上升')
        
        # Verse: 中等能量, 没有明显特征
        elif 0.2 <= e <= 0.55:
            if repeats >= 1:
                label = 'Verse'
            else:
                label = 'Verse'
        
        # 兜底
        else:
            label = 'Verse' if e < 0.45 else 'Chorus'
        
        sec['label'] = label
        if highlight:
            sec['highlight'] = ' '.join(highlight)
    
    # ============================================================
    # Step 8: 8-bar 细分
    # ============================================================
    beats_per_8bar = SUBDIVISION_BARS * BEATS_PER_BAR
    
    for sec in sections:
        sub_chunks = []
        sb = sec['beat_start']
        eb = sec['beat_end']
        pos = sb
        while pos < eb:
            ce = min(pos + beats_per_8bar, eb)
            cb = ce - pos
            ts = beat_times[min(pos, len(beat_times)-1)]
            te = beat_times[min(ce-1, len(beat_times)-1)]
            sub_chunks.append({
                'bar_offset': (pos - sb) // BEATS_PER_BAR,
                'start': round(float(ts), 1),
                'end': round(float(te), 1),
                'duration': round(float(te-ts), 1),
                'bars': cb // BEATS_PER_BAR,
                'beats': int(cb),
            })
            pos = ce
        sec['sub_8bars'] = sub_chunks
    
    # 清理不可序列化的字段
    for sec in sections:
        del sec['chroma_vec']
        del sec['timbre_vec']
    
    # ============================================================
    # 输出
    # ============================================================
    if verbose:
        print(f"\n{'='*85}")
        print(f"📋 乐句结构分析 — 两层结果")
        print(f"{'='*85}")
        print(f"\n📍 第一层: 歌曲结构段 ({n_sections} 段)")
        print(f"{'标签':<22s} {'起始':>6s} {'结束':>6s} {'时长':>6s} {'bars':>5s} {'能量':>6s} {'斜率':>6s} {'重复':>4s} {'标记'}")
        print(f"{'-'*82}")
        for sec in sections:
            sim = f"×{len(sec.get('similar_to',[]))}" if sec.get('similar_to') else ''
            hl = sec.get('highlight', '')
            print(f"{sec['label']:<22s} {sec['start']:5.1f}s {sec['end']:5.1f}s "
                  f"{sec['duration']:5.1f}s {sec['bars']:4d}b {sec['energy']:5.3f} "
                  f"{sec['energy_slope']:5.2f} {sim:>4s}  {hl}")
        
        print(f"\n📍 第二层: 8-bar 最小单元切分")
        for sec in sections:
            print(f"  ┌─ {sec['label']} ({sec['start']:.0f}s–{sec['end']:.0f}s, {sec['bars']}bars)")
            for i, sub in enumerate(sec['sub_8bars']):
                bl = f"[bar {sub['bar_offset']}-{sub['bar_offset']+sub['bars']}]"
                print(f"  │  {i+1}. {bl:<14s} {sub['start']:6.1f}s – {sub['end']:6.1f}s "
                      f"({sub['bars']}bars, {sub['duration']:.1f}s)")
            print(f"  └─ {len(sec['sub_8bars'])} 个单元")
    
    return {
        'duration': round(duration, 1),
        'bpm': round(tempo, 0),
        'total_beats': n_beats_actual,
        'total_bars': n_bars_total,
        'bar_duration_sec': round(bar_sec, 2),
        'section_8bar_duration': round(bar_sec * SUBDIVISION_BARS, 1),
        'sections': sections,
    }


if __name__ == '__main__':
    import sys
    path = sys.argv[1] if len(sys.argv) > 1 else \
        '/Users/zhaoyuzhao/.openclaw/xiaofeng_workspace/video_editor_mvp/bgm_full.wav'
    result = analyze(path)
    
    total_8bar = sum(len(s['sub_8bars']) for s in result['sections'])
    print(f"\n✅ 歌曲结构: {len(result['sections'])} 段 → 合计 {total_8bar} 个 8-bar 单元, BPM: {result['bpm']:.0f}")
    
    out = path.replace('.wav', '_structure_v4.1.json')
    with open(out, 'w') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    print(f"💾 已保存: {out}")
