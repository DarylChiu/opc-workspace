#!/usr/bin/env python3
"""
Deepseek成本跟踪服务 - 集成到OpenClaw的长期运行服务
"""
import asyncio
import os
import sys
import signal
import logging
from pathlib import Path
from datetime import datetime, timedelta

# 添加当前目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from deepseek_cost_tracker import DeepseekCostTracker, DeepseekAPIInterceptor

class DeepseekTrackerService:
    """Deepseek成本跟踪服务"""
    
    def __init__(self):
        self.tracker = DeepseekCostTracker()
        self.interceptor = DeepseekAPIInterceptor(self.tracker)
        self.is_running = False
        self.check_interval = 60  # 检查间隔（秒）
        
        # 配置日志
        self.logger = logging.getLogger("DeepseekTrackerService")
        self.logger.setLevel(logging.INFO)
        
        # 处理信号
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
    
    def signal_handler(self, signum, frame):
        """信号处理函数"""
        self.logger.info(f"收到信号 {signum}，准备关闭...")
        self.is_running = False
    
    async def run(self):
        """运行服务"""
        self.logger.info("Deepseek成本跟踪服务启动")
        self.is_running = True
        
        # 启动时生成报告
        await self.generate_startup_report()
        
        # 主循环
        try:
            while self.is_running:
                # 检查警报
                alerts = self.tracker.check_alerts()
                if alerts:
                    await self.handle_alerts(alerts)
                
                # 每小时生成一次报告快照
                current_hour = datetime.now().hour
                if current_hour != getattr(self, '_last_report_hour', -1):
                    await self.generate_hourly_snapshot()
                    self._last_report_hour = current_hour
                
                # 等待
                await asyncio.sleep(self.check_interval)
        
        except Exception as e:
            self.logger.error(f"服务运行异常: {e}")
        
        finally:
            self.shutdown()
    
    async def generate_startup_report(self):
        """生成启动报告"""
        try:
            report = self.tracker.generate_markdown_report()
            report_file = f"deepseek_startup_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
            
            with open(report_file, 'w') as f:
                f.write(report)
            
            self.logger.info(f"启动报告已生成: {report_file}")
            
            # 输出简报到控制台
            daily_summary = self.tracker.get_daily_summary()
            self.logger.info(f"今日累计成本: ${daily_summary['total_cost_usd']:.6f}")
            
        except Exception as e:
            self.logger.error(f"生成启动报告失败: {e}")
    
    async def generate_hourly_snapshot(self):
        """生成每小时快照"""
        try:
            snapshot_time = datetime.now()
            report = f"## 📊 小时快照 {snapshot_time.strftime('%H:%M')}\n\n"
            
            daily_summary = self.tracker.get_daily_summary()
            report += f"- **当日累计成本**: ${daily_summary['total_cost_usd']:.6f}\n"
            report += f"- **API调用次数**: {daily_summary['record_count']}\n"
            
            # 保存快照
            snapshot_file = f"deepseek_hourly_{snapshot_time.strftime('%Y%m%d_%H')}.md"
            with open(snapshot_file, 'a') as f:
                f.write(report + "\n")
            
            self.logger.info(f"小时快照已保存: {snapshot_file}")
            
        except Exception as e:
            self.logger.error(f"生成小时快照失败: {e}")
    
    async def handle_alerts(self, alerts):
        """处理成本警报"""
        for alert in alerts:
            alert_type = alert['type']
            message = alert['message']
            
            self.logger.warning(f"成本警报: {message}")
    
    def shutdown(self):
        """关闭服务"""
        self.logger.info("关闭Deepseek成本跟踪服务")
        
        # 生成关闭报告
        try:
            report = self.tracker.generate_markdown_report()
            report_file = f"deepseek_shutdown_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
            
            with open(report_file, 'w') as f:
                f.write(report)
            
            self.logger.info(f"关闭报告已生成: {report_file}")
        
        except Exception as e:
            self.logger.error(f"生成关闭报告失败: {e}")
        
        finally:
            self.tracker.close()
            self.logger.info("服务已完全关闭")

async def main():
    """主函数"""
    service = DeepseekTrackerService()
    await service.run()

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('deepseek_tracker_service.log'),
            logging.StreamHandler()
        ]
    )
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n服务被用户中断")
    except Exception as e:
        print(f"服务异常: {e}")
        sys.exit(1)
