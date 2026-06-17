#!/bin/bash
# Record 42 guitar chord samples for chord-gesture
# Usage: bash record_chords.sh [mic_device_index]

FFMPEG="/Users/zhaoyuzhao/.workbuddy/binaries/ffmpeg"
SAMPLES="/Users/zhaoyuzhao/WorkBuddy/Claw/chord-gesture/samples"
mkdir -p "$SAMPLES"

MIC_DEVICE="${1:-0}"  # Default: GO 3S mic, or pass 1 for iPhone mic

ROOTS=(C D E F G A B)
TYPES=(maj m 7 maj7 sus4 dim)

echo "=========================================="
echo "  Chord Sampling — 42 chords total"
echo "  Mic device: $MIC_DEVICE"
echo "  Strum each chord once when prompted"
echo "=========================================="
echo ""
echo "Available mics:"
echo "  [0] GO 3S (default)"
echo "  [1] iPhone Microphone"
echo "  [2] iPhone Microphone"
echo ""

# Quick mic test
echo "Testing mic... (2s silence check)"
$FFMPEG -f avfoundation -i ":$MIC_DEVICE" -t 1 -ar 44100 -ac 1 -sample_fmt s16 \
  "$SAMPLES/_test.wav" -y -loglevel error 2>&1

if [ -f "$SAMPLES/_test.wav" ]; then
  rm "$SAMPLES/_test.wav"
  echo "✅ Mic working"
else
  echo "❌ Mic test failed. Check device index. Try: bash record_chords.sh 1"
  exit 1
fi

TOTAL=$(( ${#ROOTS[@]} * ${#TYPES[@]} ))
COUNT=0

for ROOT in "${ROOTS[@]}"; do
  for TYPE in "${TYPES[@]}"; do
    case "$TYPE" in
      maj)  NAME="${ROOT}" ;;
      m)    NAME="${ROOT}m" ;;
      7)    NAME="${ROOT}7" ;;
      maj7) NAME="${ROOT}maj7" ;;
      sus4) NAME="${ROOT}sus4" ;;
      dim)  NAME="${ROOT}dim" ;;
    esac

    COUNT=$((COUNT + 1))
    PERCENT=$(( COUNT * 100 / TOTAL ))

    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ [$PERCENT%]"
    echo "  🎸  $NAME"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    sleep 3

    echo "  ⏺  Recording... (2.5s)"
    $FFMPEG -f avfoundation -i ":$MIC_DEVICE" -t 2.5 -ar 44100 -ac 1 -sample_fmt s16 \
      "$SAMPLES/${NAME}.wav" -y -loglevel error 2>&1

    if [ -f "$SAMPLES/${NAME}.wav" ]; then
      SIZE=$(ls -lh "$SAMPLES/${NAME}.wav" | awk '{print $5}')
      echo "  ✅  saved ($SIZE)"
    else
      echo "  ❌  FAILED"
    fi
  done
done

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Done! $COUNT chord samples in samples/"
echo "  Refresh chord-gesture to play with real samples"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
ls -1 "$SAMPLES"/*.wav 2>/dev/null | wc -l | xargs echo "Files:"
