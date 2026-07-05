#!/usr/bin/env python3
"""
Deepseek成本跟踪系统 - Bryson专属
基于Deepseek原生API的精确成本追踪
"""

import os
import json
import time
import sqlite3
import asyncio
import aiohttp
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import logging
from dataclasses import dataclass
from pathlib import Path

# 配置
DEEPSEEK_API_KEY = "REDACTED_API_KEY"
DEEPSEEK_BASE_URL = "https://api.deepseek.com"
DEEPSEEK_MODEL = "deepseek-chat"

# 费率配置（Deepseek官方费率）
RATE_INPUT = 0.14  # $0.14 per 1M tokens
RATE_OUTPUT = 0.28  # $0.28 per 1M tokens

# 项目分段配置
PROJECT_PREFIXES = ["project_", "feature_", "teaching_", "task_", "debug_", "test_"]

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('deepseek_cost_tracker.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class CostRecord:
    """成本记录数据类"""
    timestamp: datetime
    project_tag: str
    input_tokens: int
    output_tokens: int
    cost_usd: float
    session_id: Optional[str] = None
    metadata: Optional[Dict] = None
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            "timestamp": self.timestamp.isoformat(),
            "project_tag": self.project_tag,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "cost_usd": self.cost_usd,
            "session_id": self.session_id,
            "metadata": self.metadata or {}
        }

class DeepseekCostTracker:
    """Deepseek成本追踪器"""
    
    def __init__(self, db_path: str = "deepseek_cost.db"):
        self.api_key = DEEPSEEK_API_KEY
        self.db_path = db_path
        self.current_project = "default"
        self.session_start_time = datetime.now()
        self.session_id = f"session_{self.session_start_time.strftime('%Y%m%d_%H%M%S')}"
        
        # 初始化数据库
        self._init_database()
        
        # 初始化会话统计
        self.session_stats = {
            "input_tokens": 0,
            "output_tokens": 0,
            "cost_usd": 0.0,
            "api_calls": 0
        }
        
        logger.info(f"Deepseek成本追踪器初始化完成，会话ID: {self.session_id}")
    
    def _init_database(self):
        """初始化SQLite数据库"""
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()
        
        # 创建成本记录表
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS cost_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME NOT NULL,
                project_tag TEXT NOT NULL,
                input_tokens INTEGER NOT NULL,
                output_tokens INTEGER NOT NULL,
                cost_usd REAL NOT NULL,
                session_id TEXT,
                metadata TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 创建每日汇总表
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS daily_summary (
                date DATE PRIMARY KEY,
                total_input_tokens INTEGER DEFAULT 0,
                total_output_tokens INTEGER DEFAULT 0,
                total_cost_usd REAL DEFAULT 0.0,
                project_counts TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 创建项目统计表
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS project_stats (
                project_tag TEXT PRIMARY KEY,
                total_input_tokens INTEGER DEFAULT 0,
                total_output_tokens INTEGER DEFAULT 0,
                total_cost_usd REAL DEFAULT 0.0,
                last_used DATETIME,
                call_count INTEGER DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        self.conn.commit()
        logger.info(f"数据库初始化完成: {self.db_path}")
    
    def set_current_project(self, project_name: str):
        """设置当前项目标签"""
        # 自动添加前缀
        if not any(project_name.startswith(prefix) for prefix in PROJECT_PREFIXES):
            # 尝试推断项目类型
            if "ielts" in project_name.lower() or "teaching" in project_name.lower():
                project_name = f"teaching_{project_name}"
            elif "feature" in project_name.lower():
                project_name = f"feature_{project_name}"
            else:
                project_name = f"project_{project_name}"
        
        self.current_project = project_name
        logger.info(f"当前项目设置为: {project_name}")
    
    def calculate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """计算成本（美元）"""
        input_cost = (input_tokens / 1_000_000) * RATE_INPUT
        output_cost = (output_tokens / 1_000_000) * RATE_OUTPUT
        total_cost = input_cost + output_cost
        return round(total_cost, 6)
    
    def record_usage(self, input_tokens: int, output_tokens: int, 
                    project_tag: str = None, metadata: Dict = None) -> CostRecord:
        """记录API使用量"""
        project_tag = project_tag or self.current_project
        cost_usd = self.calculate_cost(input_tokens, output_tokens)
        
        record = CostRecord(
            timestamp=datetime.now(),
            project_tag=project_tag,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_usd=cost_usd,
            session_id=self.session_id,
            metadata=metadata
        )
        
        # 保存到数据库
        self._save_record(record)
        
        # 更新会话统计
        self.session_stats["input_tokens"] += input_tokens
        self.session_stats["output_tokens"] += output_tokens
        self.session_stats["cost_usd"] += cost_usd
        self.session_stats["api_calls"] += 1
        
        logger.info(f"记录使用量: {input_tokens}输入 + {output_tokens}输出 = ${cost_usd:.6f} ({project_tag})")
        return record
    
    def _save_record(self, record: CostRecord):
        """保存记录到数据库"""
        try:
            self.cursor.execute('''
                INSERT INTO cost_records 
                (timestamp, project_tag, input_tokens, output_tokens, cost_usd, session_id, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                record.timestamp,
                record.project_tag,
                record.input_tokens,
                record.output_tokens,
                record.cost_usd,
                record.session_id,
                json.dumps(record.metadata) if record.metadata else None
            ))
            
            # 更新项目统计
            self.cursor.execute('''
                INSERT INTO project_stats 
                (project_tag, total_input_tokens, total_output_tokens, total_cost_usd, last_used, call_count)
                VALUES (?, ?, ?, ?, ?, 1)
                ON CONFLICT(project_tag) DO UPDATE SET
                    total_input_tokens = total_input_tokens + ?,
                    total_output_tokens = total_output_tokens + ?,
                    total_cost_usd = total_cost_usd + ?,
                    last_used = ?,
                    call_count = call_count + 1,
                    updated_at = CURRENT_TIMESTAMP
            ''', (
                record.project_tag,
                record.input_tokens,
                record.output_tokens,
                record.cost_usd,
                record.timestamp,
                record.input_tokens,
                record.output_tokens,
                record.cost_usd,
                record.timestamp
            ))
            
            self.conn.commit()
            
        except Exception as e:
            logger.error(f"保存记录失败: {e}")
            self.conn.rollback()
    
    def get_session_summary(self) -> Dict:
        """获取当前会话摘要"""
        return {
            "session_id": self.session_id,
            "start_time": self.session_start_time.isoformat(),
            "duration_seconds": (datetime.now() - self.session_start_time).total_seconds(),
            "stats": self.session_stats,
            "current_project": self.current_project
        }
    
    def get_daily_summary(self, date: str = None) -> Dict:
        """获取每日摘要"""
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")
        
        self.cursor.execute('''
            SELECT 
                SUM(input_tokens) as total_input,
                SUM(output_tokens) as total_output,
                SUM(cost_usd) as total_cost,
                COUNT(*) as record_count
            FROM cost_records 
            WHERE DATE(timestamp) = ?
        ''', (date,))
        
        result = self.cursor.fetchone()
        
        # 获取项目分布
        self.cursor.execute('''
            SELECT 
                project_tag,
                SUM(input_tokens) as input_tokens,
                SUM(output_tokens) as output_tokens,
                SUM(cost_usd) as cost_usd,
                COUNT(*) as call_count
            FROM cost_records 
            WHERE DATE(timestamp) = ?
            GROUP BY project_tag
            ORDER BY cost_usd DESC
        ''', (date,))
        
        projects = []
        for row in self.cursor.fetchall():
            projects.append({
                "project": row[0],
                "input_tokens": row[1],
                "output_tokens": row[2],
                "cost_usd": row[3],
                "call_count": row[4],
                "percentage": (row[3] / result[2] * 100) if result[2] else 0
            })
        
        return {
            "date": date,
            "total_input_tokens": result[0] or 0,
            "total_output_tokens": result[1] or 0,
            "total_cost_usd": result[2] or 0.0,
            "record_count": result[3] or 0,
            "projects": projects,
            "average_cost_per_call": result[2] / result[3] if result[2] and result[3] else 0
        }
    
    def get_project_summary(self, project_tag: str) -> Dict:
        """获取项目摘要"""
        self.cursor.execute('''
            SELECT 
                SUM(input_tokens) as total_input,
                SUM(output_tokens) as total_output,
                SUM(cost_usd) as total_cost,
                COUNT(*) as call_count,
                MIN(timestamp) as first_used,
                MAX(timestamp) as last_used
            FROM cost_records 
            WHERE project_tag = ?
        ''', (project_tag,))
        
        result = self.cursor.fetchone()
        
        if not result or not result[0]:
            return {"project": project_tag, "error": "无数据"}
        
        return {
            "project": project_tag,
            "total_input_tokens": result[0] or 0,
            "total_output_tokens": result[1] or 0,
            "total_cost_usd": result[2] or 0.0,
            "call_count": result[3] or 0,
            "first_used": result[4],
            "last_used": result[5],
            "average_cost_per_call": result[2] / result[3] if result[2] and result[3] else 0
        }
    
    def generate_markdown_report(self, date: str = None) -> str:
        """生成Markdown格式报告"""
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")
        
        daily_summary = self.get_daily_summary(date)
        
        report = f"""# 📊 Deepseek成本报告 - Bryson专属

## 📈 今日总览 ({date})
- **总成本**: ${daily_summary['total_cost_usd']:.6f} USD
- **输入tokens**: {daily_summary['total_input_tokens']:,} ({daily_summary['total_input_tokens']/(daily_summary['total_input_tokens']+daily_summary['total_output_tokens'])*100:.1f}%)
- **输出tokens**: {daily_summary['total_output_tokens']:,} ({daily_summary['total_output_tokens']/(daily_summary['total_input_tokens']+daily_summary['total_output_tokens'])*100:.1f}%)
- **API调用次数**: {daily_summary['record_count']}次
- **平均每次成本**: ${daily_summary['average_cost_per_call']:.6f}

## 🛠️ 项目分解
"""
        
        for project in daily_summary['projects']:
            report += f"- **{project['project']}**: ${project['cost_usd']:.6f} ({project['percentage']:.1f}%)\n"
        
        if not daily_summary['projects']:
            report += "- 暂无项目数据\n"
        
        # 获取月度统计
        monthly_cost = self.get_monthly_cost()
        
        report += f"""
## 📅 月度统计
- **本月总成本**: ${monthly_cost:.6f} USD
- **预算进度**: {monthly_cost/20*100:.1f}% ($20预算)
- **日均成本**: ${monthly_cost/datetime.now().day:.6f}

## ⚠️ 成本警报状态
"""
        
        if daily_summary['total_cost_usd'] > 1.0:
            report += "🔴 **日成本超出$1.0阈值**\n"
        elif daily_summary['total_cost_usd'] > 0.8:
            report += "🟡 **日成本接近$1.0阈值**\n"
        else:
            report += "🟢 **日成本正常**\n"
        
        if monthly_cost > 15.0:
            report += "🔴 **月成本超出$15.0阈值**\n"
        elif monthly_cost > 12.0:
            report += "🟡 **月成本接近$15.0阈值**\n"
        else:
            report += "🟢 **月成本正常**\n"
        
        report += f"""
## 🔧 当前会话状态
- **会话ID**: {self.session_id}
- **会话开始**: {self.session_start_time.strftime('%H:%M:%S')}
- **会话时长**: {(datetime.now() - self.session_start_time).total_seconds()/3600:.1f}小时
- **会话成本**: ${self.session_stats['cost_usd']:.6f}
- **当前项目**: {self.current_project}

---

*报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
*Deepseek费率: ${RATE_INPUT}/1M输入tokens, ${RATE_OUTPUT}/1M输出tokens*
"""
        
        return report
    
    def get_monthly_cost(self) -> float:
        """获取本月总成本"""
        current_month = datetime.now().strftime("%Y-%m")
        self.cursor.execute('''
            SELECT SUM(cost_usd) 
            FROM cost_records 
            WHERE strftime('%Y-%m', timestamp) = ?
        ''', (current_month,))
        
        result = self.cursor.fetchone()
        return result[0] or 0.0
    
    def check_alerts(self) -> List[Dict]:
        """检查成本警报"""
        alerts = []
        
        # 日成本警报
        daily_summary = self.get_daily_summary()
        if daily_summary['total_cost_usd'] > 1.0:
            alerts.append({
                "type": "daily_cost_exceeded",
                "threshold": 1.0,
                "actual": daily_summary['total_cost_usd'],
                "message": f"日成本超出阈值: ${daily_summary['total_cost_usd']:.6f} > $1.0"
            })
        elif daily_summary['total_cost_usd'] > 0.8:
            alerts.append({
                "type": "daily_cost_warning",
                "threshold": 1.0,
                "actual": daily_summary['total_cost_usd'],
                "message": f"日成本接近阈值: ${daily_summary['total_cost_usd']:.6f} > $0.8"
            })
        
        # 月成本警报
        monthly_cost = self.get_monthly_cost()
        if monthly_cost > 15.0:
            alerts.append({
                "type": "monthly_cost_exceeded",
                "threshold": 15.0,
                "actual": monthly_cost,
                "message": f"月成本超出阈值: ${monthly_cost:.6f} > $15.0"
            })
        elif monthly_cost > 12.0:
            alerts.append({
                "type": "monthly_cost_warning",
                "threshold": 15.0,
                "actual": monthly_cost,
                "message": f"月成本接近阈值: ${monthly_cost:.6f} > $12.0"
            })
        
        return alerts
    
    def close(self):
        """关闭数据库连接"""
        self.conn.close()
        logger.info("数据库连接已关闭")

class DeepseekAPIInterceptor:
    """Deepseek API拦截器（模拟）"""
    
    def __init__(self, tracker: DeepseekCostTracker):
        self.tracker = tracker
        self.session = None
        
    async def intercept_request(self, request_data: Dict) -> Dict:
        """拦截API请求并记录使用量"""
        # 这里模拟API调用，实际应该集成到OpenClaw的API调用链中
        # 实际集成时，需要修改OpenClaw的API调用代码
        
        # 模拟API响应
        response_data = {
            "id": f"chatcmpl-{int(time.time())}",
            "object": "chat.completion",
            "created": int(time.time()),
            "model": DEEPSEEK_MODEL,
            "choices": [{
                "index": 0,
                "message": {"role": "assistant", "content": "模拟响应"},
                "finish_reason": "stop"
            }],
            "usage": {
                "prompt_tokens": 100,  # 模拟输入tokens
                "completion_tokens": 50,  # 模拟输出tokens
                "total_tokens": 150,
                "prompt_tokens_details": {"cached_tokens": 0},
                "prompt_cache_hit_tokens": 0,
                "prompt_cache_miss_tokens": 100
            }
        }
        
        # 记录使用量
        usage = response_data.get("usage", {})
        input_tokens = usage.get("prompt_tokens", 0)
        output_tokens = usage.get("completion_tokens", 0)
        
        # 从请求中推断项目标签
        project_tag = self._infer_project_from_request(request_data)
        
        # 记录成本
        self.tracker.record_usage(
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            project_tag=project_tag,
            metadata={
                "model": request_data.get("model", DEEPSEEK_MODEL),
                "timestamp": datetime.now().isoformat()
            }
        )
        
        return response_data
    
    def _infer_project_from_request(self, request_data: Dict) -> str:
        """从请求数据推断项目标签"""
        # 这里可以根据请求内容推断项目
        # 例如：根据消息内容、模型类型等
        
        messages = request_data.get("messages", [])
        if messages:
            # 检查消息内容中的关键词
            content = " ".join([msg.get("content", "") for msg in messages])
            
            if "ielts" in content.lower() or "speaking" in content.lower():
                return "teaching_ielts"
            elif "cost" in content.lower() or "tracking" in content.lower():
                return "feature_cost_tracking"
            elif "voice" in content.lower() or "tts" in content.lower():
                return "project_voice_mvp"
            elif "debug" in content.lower() or "test" in content.lower():
                return "debug_system"
        
        # 默认返回当前项目
        return self.tracker.current_project

def main():
    """主函数：演示成本追踪器"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Deepseek成本追踪系统")
    parser.add_argument("--action", choices=["report", "summary", "project", "alerts", "test"], 
                       default="report", help="执行动作")
    parser.add_argument("--date", help="日期 (YYYY-MM-DD)")
    parser.add_argument("--project", help="项目标签")
    parser.add_argument("--set-project", help="设置当前项目")
    
    args = parser.parse_args()
    
    # 初始化追踪器
    tracker = DeepseekCostTracker()
    
    try:
        if args.set_project:
            tracker.set_current_project(args.set_project)
            print(f"✅ 当前项目设置为: {tracker.current_project}")
        
        if args.action == "report":
            # 生成报告
            report = tracker.generate_markdown_report(args.date)
            print(report)
            
            # 保存报告到文件
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_file = f"deepseek_cost_report_{timestamp}.md"
            with open(report_file, 'w') as f:
                f.write(report)
            print(f"\n📄 报告已保存至: {report_file}")
            
        elif args.action == "summary":
            # 显示摘要
            summary = tracker.get_daily_summary(args.date)
            print(f"📊 {summary['date']} 成本摘要:")
            print(f"   总成本: ${summary['total_cost_usd']:.6f}")
            print(f"   输入tokens: {summary['total_input_tokens']:,}")
            print(f"   输出tokens: {summary['total_output_tokens']:,}")
            print(f"   API调用次数: {summary['record_count']}")
            
            if summary['projects']:
                print(f"\n🛠️ 项目分布:")
                for project in summary['projects']:
                    print(f"   - {project['project']}: ${project['cost_usd']:.6f} ({project['percentage']:.1f}%)")
        
        elif args.action == "project":
            if not args.project:
                print("❌ 需要指定项目标签 (--project)")
                return
            
            project_summary = tracker.get_project_summary(args.project)
            if "error" in project_summary:
                print(f"❌ {project_summary['error']}")
            else:
                print(f"📋 项目: {project_summary['project']}")
                print(f"   总成本: ${project_summary['total_cost_usd']:.6f}")
                print(f"   总输入tokens: {project_summary['total_input_tokens']:,}")
                print(f"   总输出tokens: {project_summary['total_output_tokens']:,}")
                print(f"   调用次数: {project_summary['call_count']}")
                print(f"   首次使用: {project_summary['first_used']}")
                print(f"   最后使用: {project_summary['last_used']}")
        
        elif args.action == "alerts":
            alerts = tracker.check_alerts()
            if alerts:
                print("⚠️ 成本警报:")
                for alert in alerts:
                    print(f"   [{alert['type']}] {alert['message']}")
            else:
                print("✅ 无成本警报")
        
        elif args.action == "test":
            # 测试模式：模拟一些API调用
            print("🧪 测试模式：模拟API调用...")
            
            # 设置不同项目
            projects = ["project_voice_mvp", "teaching_ielts", "feature_cost_tracking", "debug_system"]
            
            for i, project in enumerate(projects):
                tracker.set_current_project(project)
                
                # 模拟API调用
                for j in range(3):
                    input_tokens = 100 + i * 50 + j * 20
                    output_tokens = 50 + i * 30 + j * 10
                    
                    record = tracker.record_usage(
                        input_tokens=input_tokens,
                        output_tokens=output_tokens,
                        metadata={"test": True, "iteration": j}
                    )
                    
                    print(f"   {project}: {input_tokens}输入 + {output_tokens}输出 = ${record.cost_usd:.6f}")
            
            # 生成测试报告
            report = tracker.generate_markdown_report()
            print("\n" + "="*50)
            print(report)
            
            # 检查警报
            alerts = tracker.check_alerts()
            if alerts:
                print("\n⚠️ 测试警报:")
                for alert in alerts:
                    print(f"   {alert['message']}")
    
    finally:
        tracker.close()

if __name__ == "__main__":
    main()