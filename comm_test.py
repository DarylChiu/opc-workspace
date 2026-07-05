import socket
import sys

def test_port(port):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(2)
            result = s.connect_ex(('127.0.0.1', port))
            return result == 0
    except Exception as e:
        return f"Error: {str(e)}"

# 测试端口
ports = [50051, 50052]
results = {}

for port in ports:
    if test_port(port):
        results[port] = "🟢 OPEN"
    else:
        results[port] = "🔴 CLOSED"

# 输出结果
print("端口状态测试报告:")
for port, status in results.items():
    print(f"Port {port}: {status}")