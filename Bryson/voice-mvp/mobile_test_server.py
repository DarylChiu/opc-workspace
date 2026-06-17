
import http.server
import socketserver
import webbrowser
import threading
import time
import sys

PORT = 8081

class TestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory="./frontend", **kwargs)
    
    def log_message(self, format, *args):
        pass  # 静默日志

def start_test_server():
    with socketserver.TCPServer(("0.0.0.0", PORT), TestHandler) as httpd:
        print(f"✅ 测试服务器运行在: http://0.0.0.0:{PORT}")
        print(f"📱 手机可以访问: http://<your-ip>:{PORT}")
        print(f"💡 在手机上输入电脑的IP地址")
        httpd.serve_forever()

if __name__ == "__main__":
    thread = threading.Thread(target=start_test_server, daemon=True)
    thread.start()
    print("按Ctrl+C停止服务器")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("
停止服务器...")
