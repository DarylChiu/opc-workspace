#!/usr/bin/env python3
"""
生成Bryson语音MVP测试链接的二维码
"""

import qrcode
import qrcode.image.svg
import os
import sys

def create_qr_code(url: str, output_path: str = None):
    """创建QR二维码"""
    # If no output path specified, create in frontend directory
    frontend_dir = os.path.join(os.path.dirname(__file__), "frontend")
    if output_path is None:
        output_path = os.path.join(frontend_dir, "test_qr.png")
    
    # Create directory if needed
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Generate QR code
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(url)
    qr.make(fit=True)
    
    # Create and save image
    img = qr.make_image(fill_color="black", back_color="white")
    img.save(output_path)
    
    print(f"✅ QR code generated: {output_path}")
    print(f"📱 Test URL: {url}")
    print(f"📏 Size: {img.size[0]}x{img.size[1]} pixels")
    
    return output_path

def create_simple_qr_page():
    """创建简单的HTML测试页面"""
    url = "https://tasty-islands-like.loca.lt"
    
    # QR code file
    qr_file = "test_qr.png"
    qr_path = os.path.join(os.path.dirname(__file__), "frontend", qr_file)
    create_qr_code(url, qr_path)
    
    # Create HTML page
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Bryson Voice MVP Test</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            text-align: center;
        }}
        .container {{
            background: #f5f5f5;
            border-radius: 10px;
            padding: 30px;
            margin: 20px 0;
        }}
        .status {{
            margin: 20px 0;
        }}
        .success {{
            color: #28a745;
            font-weight: bold;
        }}
        .warning {{
            color: #ffc107;
        }}
        .qr-container {{
            margin: 30px 0;
        }}
        .qr-code {{
            max-width: 300px;
            margin: 0 auto;
        }}
        a {{
            display: inline-block;
            margin: 15px;
            padding: 12px 24px;
            background: #007bff;
            color: white;
            text-decoration: none;
            border-radius: 5px;
        }}
    </style>
</head>
<body>
    <h1>🌬️ Bryson Voice MVP Test</h1>
    
    <div class="container">
        <div class="status">
            <p><strong>Service URL:</strong> <a href="{url}" target="_blank">{url}</a></p>
            <p class="success">✅ Backend server running</p>
            <p class="success">✅ WebSocket endpoint ready</p>
            <p class="warning">⚠️ Mobile browser testing recommended</p>
        </div>
        
        <div class="qr-container">
            <h3>Scan QR Code on Mobile:</h3>
            <div class="qr-code">
                <img src="{qr_file}" alt="Test QR Code" width="300">
            </div>
        </div>
        
        <div>
            <h3>Test Links:</h3>
            <a href="{url}" target="_blank">Open in Browser</a>
            <a href="{url}#webrtc" target="_blank">Test WebRTC</a>
            <a href="{url}/api/status" target="_blank">Check Status</a>
        </div>
    </div>
    
    <footer>
        <p>📊 Server status: <a href="{url}/api/status" target="_blank">API Status</a></p>
    </footer>
</body>
</html>
"""
    
    html_path = os.path.join(os.path.dirname(__file__), "frontend", "test_page.html")
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_content)
    
    print(f"✅ HTML test page created: {html_path}")
    return html_path

if __name__ == "__main__":
    # First check if server is reachable
    try:
        import urllib.request
        import json
        url = "https://tasty-islands-like.loca.lt/api/status"
        response = urllib.request.urlopen(url, timeout=5)
        data = json.loads(response.read().decode())
        print(f"✅ Server reachable: {data['message']}")
    except Exception as e:
        print(f"⚠️ Server unreachable: {e}")
        print("Continuing with QR generation...")
    
    # Generate QR code and test page
    html_page = create_simple_qr_page()
    print(f"\n🎯 Test page ready at:")
    print(f"    Local: http://localhost:8080/test_page.html")
    print(f"    External: https://tasty-islands-like.loca.lt/test_page.html")
    print(f"\n📱 Scan the QR code on your mobile device or click the links to test!")