#!/bin/bash
# Convert recorded webm chord samples to WAV
# Usage: place all *.webm files in chord-gesture/samples/ then run this

FFMPEG="/Users/zhaoyuzhao/.workbuddy/binaries/ffmpeg"
SAMPLES_DIR="/Users/zhaoyuzhao/WorkBuddy/Claw/chord-gesture/samples"

cd "$SAMPLES_DIR" 2>/dev/null || { echo "samples/ dir not found"; exit 1; }

COUNT=0
for f in *.webm; do
  [ -f "$f" ] || continue
  name="${f%.webm}"
  $FFMPEG -i "$f" -ar 44100 -ac 1 -sample_fmt s16 "$name.wav" -y -loglevel error 2>&1
  if [ -f "$name.wav" ]; then
    echo "✅ $name.wav"
    COUNT=$((COUNT + 1))
  fi
done

echo ""
echo "Converted $COUNT files to WAV"
echo "Now refresh chord-gesture to use real samples"
