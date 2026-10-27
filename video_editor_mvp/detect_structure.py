#!/usr/bin/env python3
"""
Birds of a Feather - 和弦检测 + 结构映射
已知: Hooktheory给出了两个不同的和弦进行
  Verse型: D7 Bm(add9) Em7 A7sus4 
  Chorus型: D Bm7 Em7 A
用librosa检测每拍的根音，匹配进行模式来找段落边界
"""

import numpy as np
import librosa
import json

AUDIO = '/Users/zhaoyuzhao/.openclaw/xiaofeng_workspace/video_editor_mvp/bgm_full.wav'

y, sr = librosa.load(AUDIO, sr=22050)
hop = 512
duration = len(y) / sr

# Beat tracking
tempo, beats = librosa.beat.beat_track(y=y, sr=sr, hop_length=hop)
tempo = float(tempo.item() if hasattr(tempo, 'item') else tempo)
beat_times = librosa.frames_to_time(beats, sr=sr, hop_length=hop)
print(f"BPM: {tempo:.0f}, beats: {len(beat_times)}, duration: {duration:.0f}s")

# Chroma at beat positions
chroma = librosa.feature.chroma_cqt(y=y, sr=sr, hop_length=hop)
chroma_beat = librosa.util.sync(chroma, beats, aggregate=np.mean)

# Map chroma peak to note name for each beat
NOTES = ['C','C#','D','D#','E','F','F#','G','G#','A','A#','B']
beat_roots = []
for i in range(chroma_beat.shape[1]):
    peak = np.argmax(chroma_beat[:, i])
    beat_roots.append(NOTES[peak])

# Group by 4-beat bars and find dominant root per bar
bars_roots = []
for i in range(0, len(beat_roots), 4):
    chunk = beat_roots[i:i+4]
    if len(chunk) >= 3:
        # Most common root in this bar
        from collections import Counter
        dominant = Counter(chunk).most_common(1)[0][0]
        bars_roots.append(dominant)

bar_times = beat_times[::4][:len(bars_roots)]
n_bars = len(bars_roots)

print(f"Bars: {n_bars}, each ≈ {60/tempo*4:.1f}s")

# The known progression is D - Bm - Em - A (roots: D, B, E, A)
# Look for this 4-bar pattern in the bar sequence
target_pattern = ['D', 'B', 'E', 'A']

# Find matches: compare each 4-bar window against target
pattern_scores = []
for i in range(n_bars - 3):
    window = bars_roots[i:i+4]
    matches = sum(1 for a, b in zip(window, target_pattern) if a == b)
    pattern_scores.append((i, matches, window))

# Find regions where the 4-bar pattern repeats consistently
# A section = 2 repetitions of the 4-bar pattern = 8 bars
print("\n=== 4-bar pattern matches (D-B-E-A) ===")
for i, score, window in pattern_scores:
    if score >= 3:  # At least 3 out of 4 roots match
        t = bar_times[i] if i < len(bar_times) else 0
        print(f"  bar {i:3d}  t={t:6.1f}s  [{', '.join(window)}]  match={score}/4")

# Now find consecutive matches (sections)
print("\n=== 连续匹配块 (>=6 bars, 至少一个4-bar pattern) ===")
in_block = False
block_start = 0
blocks = []
for i, score, window in pattern_scores:
    if score >= 3 and not in_block:
        block_start = i
        in_block = True
    elif score < 3 and in_block:
        block_end = i + 3  # end of last matched 4-bar window
        if block_end - block_start >= 6:
            t0 = bar_times[block_start] if block_start < len(bar_times) else 0
            t1 = bar_times[min(block_end, len(bar_times)-1)]
            blocks.append((block_start, block_end, t0, t1))
        in_block = False

if in_block:
    block_end = n_bars - 1
    t0 = bar_times[block_start]
    t1 = bar_times[min(block_end, len(bar_times)-1)]
    blocks.append((block_start, block_end, t0, t1))

for start, end, t0, t1 in blocks:
    bars_count = end - start
    print(f"  bars {start:3d}-{end:3d}  {t0:5.1f}s – {t1:5.1f}s  ({bars_count} bars, {t1-t0:.0f}s)")

# Identify gaps (sections where the pattern doesn't match - likely Intro/Outro/Verse variations)
print("\n=== 段落间隙 (可能是 Verse 变体 / Intro / Outro) ===")
gaps = []
prev_end = 0
for start, end, t0, t1 in blocks:
    if start > prev_end + 4:  # Gap of more than 4 bars
        gap_bars = bars_roots[prev_end:start]
        gt0 = bar_times[prev_end] if prev_end < len(bar_times) else 0
        gt1 = bar_times[min(start, len(bar_times)-1)]
        gaps.append((prev_end, start, gt0, gt1, gap_bars))
    prev_end = end

# Check for gap after last block
if prev_end < n_bars - 4:
    gap_bars = bars_roots[prev_end:]
    gt0 = bar_times[prev_end]
    gt1 = bar_times[-1]
    gaps.append((prev_end, n_bars, gt0, gt1, gap_bars))

for start, end, t0, t1, roots in gaps:
    r = ' '.join(roots[:20])
    if len(roots) > 20:
        r += '...'
    print(f"  bars {start:3d}-{end:3d}  {t0:5.1f}s – {t1:5.1f}s  ({end-start} bars) [{r}]")

# Build the full structure
print(f"\n{'='*70}")
print(f"📋 Birds of a Feather — 歌曲结构推断")
print(f"{'='*70}")
print(f"BPM: {tempo:.0f} | {n_bars} bars | {duration:.0f}s | 1 bar = {60/tempo*4:.1f}s")
print()

# Create combined timeline
all_sections = []
pos = 0
for start, end, t0, t1 in blocks:
    if pos < start:
        # This is a gap (non-matching section)
        gt0 = bar_times[pos]
        gt1 = bar_times[min(start, len(bar_times)-1)]
        all_sections.append(('gap', pos, start, gt0, gt1))
    all_sections.append(('pattern', start, end, t0, t1))
    pos = end
if pos < n_bars:
    gt0 = bar_times[pos] if pos < len(bar_times) else 0
    gt1 = bar_times[-1]
    all_sections.append(('gap', pos, n_bars, gt0, gt1))

# Label sections based on position and length
section_id = 0
for stype, start, end, t0, t1 in all_sections:
    n = end - start
    pos_ratio = start / n_bars
    
    if stype == 'gap':
        if start == 0:
            label = 'Intro (instrumental)'
        elif t1 > duration * 0.85:
            label = 'Outro / Ending'
        elif n < 12:
            label = 'Verse'
        else:
            label = 'Verse'
    else:  # pattern match
        if n <= 10:
            label = 'Pre-Chorus'
        else:
            # Could be Chorus or part of Verse with matching pattern
            label = 'Chorus'
    
    all_sections[section_id] = (*all_sections[section_id], label)
    section_id += 1

for stype, start, end, t0, t1, label in all_sections:
    n = end - start
    n8 = n // 8
    rem = n % 8
    print(f"  {label:<22s} bars {start:3d}-{end:3d}  {t0:5.1f}s – {t1:5.1f}s  "
          f"({n} bars / {n8}×8bar + {rem}bar)")

print(f"\n💡 说明:")
print(f"  'pattern' = 和弦根音匹配 D-B-E-A 进行 (Pre-Chorus/Chorus)")
print(f"  'gap'     = 和弦变化/变体 (Verse, Intro, Outro)")

# Save
out = {
    'song': 'Birds of a Feather - Billie Eilish',
    'bpm': round(tempo, 0),
    'bars_total': n_bars,
    'duration_sec': round(duration, 1),
    'bar_sec': round(60/tempo*4, 2),
    'sections': [{'type': label, 'bars': end-start, 'bar_start': start, 'bar_end': end,
                   'time_start': round(t0,1), 'time_end': round(t1,1)} 
                 for _, start, end, t0, t1, label in all_sections]
}
with open('/Users/zhaoyuzhao/.openclaw/xiaofeng_workspace/video_editor_mvp/bgm_structure_chords.json', 'w') as f:
    json.dump(out, f, indent=2, ensure_ascii=False)
print(f"\n💾 已保存: bgm_structure_chords.json")
