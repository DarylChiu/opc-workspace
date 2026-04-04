#!/usr/bin/env python3
"""
测试外部网络访问性
"""

import socket
import subprocess
import requests
from datetime import datetime
import os

def get_local_ip():
    """获取本地IP地址"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except Exception as e:
        return f"获取失败: {e}"

def get_public_ip():
    """获取公网IP"""
    try:
        response = requests.get('https://api.ipify.org', timeout=5)
        return response.text
    except:
        try:
            response = requests.get('https://icanhazip.com', timeout=5)
            return response.text.strip()
        except Exception as e:
            return f"获取失败: {e}"

def check_port_open(host, port, timeout=2):
    """检查端口是否开放"""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(timeout)
            result = sock.connect_ex((host, port))
            return result == 0
    except Exception as e:
        return f"检查失败: {e}"

def check_router_upnp():
    """检查UPnP端口转发可能性"""
    try:
        import upnpclient
        # 尝试获取路由器信息
        devices = upnpclient.discover()
        if devices:
            return {
                "available": True,
                "device_count": len(devices),
                "device_names": [d.friendly_name for d in devices[:3]]
            }
        return {"available": False, "reason": "未发现UPnP设备"}
    except ImportError:
        return {"available": False, "reason": "未安装upnpclient模块"}
    except Exception as e:
        return {"available": False, "reason": f"检查异常: {e}"}

def check_firewall_status():
    """检查防火墙状态"""
    try:
        # macOS防火墙检查
        result = subprocess.run(
            ["/usr/libexec/ApplicationFirewall/socketfilterfw", "--getglobalstate"],
            capture_output=True, text=True, timeout=5
        )
        return result.stdout.strip()
    except Exception:
        try:
            # Linux防火墙检查
            result = subprocess.run(
                ["sudo", "ufw", "status"],
                capture_output=True, text=True, timeout=5
            )
            return result.stdout.strip()
        except Exception as e:
            return f"检查失败: {e}"

def main():
    print("=" * 60)
    print("🌐 外部网络访问性检查")
    print("=" * 60)
    
    # 基本网络信息
    print("\n📡 网络信息:")
    local_ip = get_local_ip()
    print(f"  局域网IP: {local_ip}")
    
    public_ip = get_public_ip()
    print(f"  公网IP: {public_ip}")
    
    # 检查WebRTC服务器端口
    print("\n🔌 端口检查 (8000 - WebRTC服务器):")
    ports_to_check = [8000, 8001, 8080, 9000]
    
    for port in ports_to_check:
        local_status = check_port_open("127.0.0.1", port)
        lan_status = check_port_open(local_ip, port) if isinstance(local_ip, str) and local_ip != "获取失败" else "N/A"
        
        print(f"  端口 {port}:")
        print(f"    🏠 本地访问: {'✅ 开放' if local_status == True else '❌ 关闭' if local_status == False else f'⚠️ {local_status}'}")
        print(f"    📡 局域网访问: {'✅ 开放' if lan_status == True else '❌ 关闭' if lan_status == False else f'⚠️ {lan_status}'}")
    
    # 防火墙状态
    print("\n🛡️ 防火墙状态:")
    firewall = check_firewall_status()
    print(f"  {firewall[:100]}...")
    
    # UPnP检查
    print("\n🔗 UPnP端口转发检查:")
    upnp_status = check_router_upnp()
    if upnp_status["available"]:
        print(f"  ✅ UPnP可用")
        print(f"    发现设备: {', '.join(upnp_status['device_names'])}")
    else:
        print(f"  ⚠️ UPnP不可用: {upnp_status['reason']}")
    
    # 建议
    print("\n💡 外部访问建议:")
    print("  1. 如果端口8000无法外网访问，建议方案:")
    print("     a) 使用ngrok隧道路由 (首选)")
    print("     b) 配置路由器端口转发")
    print("     c) 临时使用云服务器部署")
    
    print("  2. 手机/平板测试要求外网访问，当前公网IP:")
    print(f"     http://{public_ip}:8000")
    
    return {
        "local_ip": local_ip,
        "public_ip": public_ip,
        "ports": ports_to_check
    }

if __name__ == "__main__":
    main()