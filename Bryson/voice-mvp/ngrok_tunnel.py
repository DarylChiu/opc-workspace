#!/usr/bin/env python3
"""
Bryson语音MVP - ngrok隧道管理
用于创建外部可访问链接
"""

import os
import sys
import time
import logging
import webbrowser
from datetime import datetime
from pyngrok import ngrok, conf

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class NgrokManager:
    def __init__(self, port=8000, auth_token=None):
        """
        初始化ngrok管理器
        
        参数:
            port: 本地端口号
            auth_token: ngrok认证令牌（可选）
        """
        self.port = port
        self.auth_token = auth_token
        self.tunnel = None
        self.public_url = None
        
        # 检查ngrok是否安装
        self.check_ngrok_installed()
        
    def check_ngrok_installed(self):
        """检查ngrok是否已安装"""
        try:
            # 尝试获取ngrok版本
            ngrok_version = ngrok.get_version()
            logger.info(f"✅ ngrok已安装: 版本 {ngrok_version}")
            
            # 检查认证令牌
            if self.auth_token:
                ngrok.set_auth_token(self.auth_token)
                logger.info("✅ ngrok认证令牌已设置")
            else:
                logger.warning("⚠️  未提供ngrok认证令牌，使用基本功能")
                
        except Exception as e:
            logger.error(f"❌ ngrok检查失败: {e}")
            logger.info("尝试自动安装ngrok...")
            self.install_ngrok()
    
    def install_ngrok(self):
        """自动安装ngrok"""
        try:
            logger.info("正在安装ngrok...")
            ngrok.install_ngrok()
            logger.info("✅ ngrok安装完成")
        except Exception as e:
            logger.error(f"❌ ngrok安装失败: {e}")
            logger.info("请手动安装ngrok: https://ngrok.com/download")
            logger.info("或使用其他隧道方案")
            return False
        return True
    
    def start_tunnel(self):
        """启动ngrok隧道"""
        try:
            logger.info(f"🚀 启动ngrok隧道到本地端口 {self.port}")
            
            # 启动隧道
            self.tunnel = ngrok.connect(self.port, proto="http", options={
                "region": "ap",  # 亚太地区
                "bind_tls": True,  # 启用TLS
            })
            
            self.public_url = self.tunnel.public_url
            logger.info(f"✅ 隧道已建立!")
            logger.info(f"   公开网址: {self.public_url}")
            logger.info(f"   本地地址: http://localhost:{self.port}")
            
            # 显示隧道信息
            self.print_tunnel_info()
            
            return self.public_url
            
        except Exception as e:
            logger.error(f"❌ 启动隧道失败: {e}")
            
            # 检查常见错误
            if "authtoken" in str(e).lower():
                logger.error("需要ngrok认证令牌!")
                logger.info("获取方式:")
                logger.info("1. 访问 https://dashboard.ngrok.com/get-started/your-authtoken")
                logger.info("2. 注册免费账户获取authtoken")
                logger.info("3. 运行: ngrok config add-authtoken YOUR_TOKEN")
                
            elif "404" in str(e):
                logger.error("ngrok服务暂时不可用")
                logger.info("请检查网络连接或稍后重试")
                
            else:
                logger.error(f"未知错误: {e}")
                
            return None
    
    def stop_tunnel(self):
        """停止ngrok隧道"""
        try:
            if self.tunnel:
                ngrok.disconnect(self.tunnel.public_url)
                logger.info("🛑 ngrok隧道已停止")
                self.tunnel = None
                self.public_url = None
        except Exception as e:
            logger.error(f"停止隧道时出错: {e}")
    
    def print_tunnel_info(self):
        """打印隧道信息"""
        print("\n" + "="*60)
        print("🌐 Bryson语音MVP - 外部访问链接已创建!")
        print("="*60)
        print(f"   公开访问地址: {self.public_url}")
        print(f"   本地访问地址: http://localhost:{self.port}")
        print(f"   创建时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("\n📱 移动设备访问:")
        print("   1. 手机/平板浏览器打开以上链接")
        print("   2. 点击链接后会重定向到语音界面")
        print("   3. 首次访问可能需要授权麦克风权限")
        print("\n🛡️ 安全提示:")
        print("   • 该链接为临时隧道，8小时后自动失效")
        print("   • 仅分享给测试人员")
        print("   • 请勿用于生产环境")
        print("="*60 + "\n")
        
        # 保存链接到文件
        self.save_url_to_file()
    
    def save_url_to_file(self):
        """保存链接到文件"""
        if not self.public_url:
            return
            
        url_file = "external_url.txt"
        try:
            with open(url_file, 'w', encoding='utf-8') as f:
                f.write(f"# Bryson语音MVP外部访问链接\n")
                f.write(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"有效期: 8小时后自动失效\n\n")
                f.write(f"🔥 主访问链接:\n")
                f.write(f"{self.public_url}\n\n")
                f.write(f"📱 手机访问说明:\n")
                f.write(f"1. 使用手机/平板浏览器打开以上链接\n")
                f.write(f"2. 点击'连接'按钮建立WebRTC连接\n")
                f.write(f"3. 确保蓝牙耳机已连接并授权麦克风\n")
            
            logger.info(f"✅ 链接已保存到: {url_file}")
            
        except Exception as e:
            logger.error(f"保存链接文件失败: {e}")
    
    def open_in_browser(self):
        """在浏览器中打开链接"""
        if self.public_url:
            try:
                webbrowser.open(self.public_url)
                logger.info("🌐 已在浏览器中打开链接")
            except Exception as e:
                logger.error(f"无法打开浏览器: {e}")
    
    def run_keep_alive(self):
        """保持隧道运行并监控"""
        if not self.public_url:
            logger.error("隧道未启动，无法保持运行")
            return
        
        print("\n🔄 保持隧道运行中...")
        print("按 Ctrl+C 停止隧道和服务器")
        print("-" * 40)
        
        try:
            while True:
                # 检查隧道状态
                tunnels = ngrok.get_tunnels()
                active = any(t.public_url == self.public_url for t in tunnels)
                
                if active:
                    print(f"🟢 隧道状态正常 [{datetime.now().strftime('%H:%M:%S')}]", end='\r')
                else:
                    logger.warning("⚠️  隧道可能已断开，正在尝试重连...")
                    self.stop_tunnel()
                    time.sleep(1)
                    self.start_tunnel()
                
                time.sleep(10)  # 每10秒检查一次
                
        except KeyboardInterrupt:
            print("\n\n🔴 用户中断，正在清理...")
            self.stop_tunnel()
            logger.info("✅ 清理完成")
        except Exception as e:
            logger.error(f"监控过程中出错: {e}")

def main():
    """主函数"""
    print("\n" + "="*60)
    print("🚀 Bryson语音MVP - 外部访问隧道管理器")
    print("="*60)
    
    # 配置参数
    PORT = 8000  # 修改为应用程序实际端口
    
    # 检查ngrok认证令牌
    auth_token = os.environ.get("NGROK_AUTHTOKEN")
    if not auth_token:
        print("⚠️  未设置NGROK_AUTHTOKEN环境变量")
        print("   如需稳定隧道，请设置:")
        print("   export NGROK_AUTHTOKEN='您的令牌'")
        print("   或直接修改脚本配置")
        print("\n🔗 获取令牌: https://dashboard.ngrok.com/get-started/your-authtoken")
        print("💡 没有令牌也可使用基本隧道（部分限制）\n")
    
    # 创建管理器
    manager = NgrokManager(port=PORT, auth_token=auth_token)
    
    # 启动隧道
    url = manager.start_tunnel()
    
    if url:
        # 等待几秒让服务器准备
        print("⏳ 等待服务器启动...")
        time.sleep(3)
        
        # 在浏览器中打开
        open_browser = input("是否在浏览器中打开链接? [y/N]: ").lower().strip()
        if open_browser in ['y', 'yes', '是的']:
            manager.open_in_browser()
        
        # 保持运行
        manager.run_keep_alive()
    else:
        print("❌ 隧道启动失败，请检查网络和配置")
        return 1
    
    return 0

# 备用方案：不使用ngrok的选项
def get_alternative_solutions():
    """获取备用隧道方案"""
    solutions = [
        {
            "name": "Cloudflare Tunnel",
            "desc": "免费、稳定，需要Cloudflare账户",
            "setup": "cloudflared tunnel --url http://localhost:8000",
            "link": "https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/"
        },
        {
            "name": "localhost.run",
            "desc": "SSH隧道，无需安装额外软件",
            "setup": "ssh -R 80:localhost:8000 ssh.localhost.run",
            "link": "https://localhost.run/"
        },
        {
            "name": "Serveo",
            "desc": "另一个SSH隧道服务",
            "setup": "ssh -R 80:localhost:8000 serveo.net",
            "link": "https://serveo.net/"
        },
        {
            "name": "Manual Port Forwarding",
            "desc": "手动配置路由器端口转发",
            "setup": "在路由器中转发端口8000到本机IP",
            "link": "路由器管理界面"
        }
    ]
    
    return solutions

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n👋 操作已取消")
        sys.exit(0)
    except Exception as e:
        print(f"❌ 程序异常: {e}")
        sys.exit(1)