#!/usr/bin/env python3
"""Local server to receive chord samples from sampler and save as WAV."""

import http.server
import os
import sys
import subprocess
import tempfile

SAMPLES_DIR = "/Users/zhaoyuzhao/WorkBuddy/Claw/chord-gesture/samples"
FFMPEG = "/Users/zhaoyuzhao/.workbuddy/binaries/ffmpeg"
PORT = 9876

os.makedirs(SAMPLES_DIR, exist_ok=True)


class SampleHandler(http.server.BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, X-Chord-Name")
        self.end_headers()

    def do_POST(self):
        chord_name = self.headers.get("X-Chord-Name", "unknown")
        content_length = int(self.headers.get("Content-Length", 0))
        data = self.rfile.read(content_length)

        if not data:
            self.send_error(400, "No data")
            return

        # Save webm to temp file, convert to WAV
        webm_path = os.path.join(SAMPLES_DIR, f"{chord_name}.webm")
        wav_path = os.path.join(SAMPLES_DIR, f"{chord_name}.wav")

        with open(webm_path, "wb") as f:
            f.write(data)

        # Convert to WAV
        result = subprocess.run(
            [FFMPEG, "-i", webm_path, "-ar", "44100", "-ac", "1",
             "-sample_fmt", "s16", wav_path, "-y", "-loglevel", "error"],
            capture_output=True, text=True
        )

        if os.path.exists(wav_path) and os.path.getsize(wav_path) > 100:
            os.remove(webm_path)
            size_kb = os.path.getsize(wav_path) // 1024
            self.send_response(200)
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(f'{{"ok":true,"chord":"{chord_name}","size_kb":{size_kb}}}'.encode())
            print(f"  ✅ {chord_name}.wav ({size_kb} KB)")
        else:
            self.send_response(500)
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(b'{"ok":false}')
            print(f"  ❌ {chord_name} conversion failed")
            if result.stderr:
                print(f"     {result.stderr[:200]}")

    def log_message(self, format, *args):
        pass  # Suppress default logging


if __name__ == "__main__":
    print(f"Chord sample receiver running on http://localhost:{PORT}")
    print(f"Saving to: {SAMPLES_DIR}")
    print("Waiting for sampler to send recordings...")
    print()
    server = http.server.HTTPServer(("127.0.0.1", PORT), SampleHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped")
