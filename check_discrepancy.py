#!/usr/bin/env python3
"""
诊断Deepseek成本追踪器数据差异问题
"""

import sqlite3
import json
import os
from datetime import datetime, timedelta

def check_database_integrity():
    """检查数据库完整性和数据一致性"""
    print("🔍 检查Deepseek成本数据库完整性...")
    
    db_path = "deepseek_cost.db"
    if not os.path.exists(db_path):
        print(f"❌ 数据库文件不存在: {db_path}")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 1. 检查表结构
        print("\n📊 数据库表结构:")
        cursor.execute('SELECT name FROM sqlite_master WHERE type="table"')
        tables = cursor.fetchall()
        for table in tables:
            print(f"  - {table[0]}")
            cursor.execute(f'PRAGMA table_info({table[0]})')
            columns = cursor.fetchall()
            for col in columns:
                print(f"     {col[1]} ({col[2]})")
        
        # 2. 检查api_calls表记录
        print(f"\n📝 API调用记录统计:")
        cursor.execute('SELECT COUNT(*) FROM api_calls')
        total = cursor.fetchone()[0]
        print(f"  - 总记录数: {total}")
        
        # 按时间分布
        today = datetime.now().strftime('%Y-%m-%d')
        cursor.execute('SELECT COUNT(*) FROM api_calls WHERE date_str = ?', (today,))
        today_count = cursor.fetchone()[0]
        print(f"  - 今日记录: {today_count}")
        
        # 3. 检查项目分布
        print(f"\n🏷️ 项目分布:")
        cursor.execute('SELECT project_tag, COUNT(*), SUM(input_tokens), SUM(output_tokens), SUM(cost_usd) FROM api_calls GROUP BY project_tag')
        for row in cursor.fetchall():
            project, count, input_sum, output_sum, cost_sum = row
            print(f"  - {project}: {count}次调用, {input_sum}输入/{output_sum}输出 (${cost_sum:.6f})")
        
        # 4. 计算总成本
        cursor.execute('SELECT SUM(input_tokens), SUM(output_tokens), SUM(cost_usd) FROM api_calls')
        total_input, total_output, total_cost = cursor.fetchone()
        print(f"\n💰 数据库总成本: ${total_cost:.6f} ({total_input}输入/{total_output}输出)")
        
        # 5. 检查最近记录
        print(f"\n⏰ 最近5条调用记录:")
        cursor.execute('SELECT id, project_tag, input_tokens, output_tokens, cost_usd, timestamp FROM api_calls ORDER BY timestamp DESC LIMIT 5')
        for row in cursor.fetchall():
            id_, project, input_t, output_t, cost, timestamp = row
            print(f"  [{id_}] {project}: {input_t}→{output_t} (${cost:.6f}) @ {timestamp}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ 数据库检查失败: {e}")
        return False

def check_openclaw_config():
    """检查OpenClaw配置"""
    print("\n🔧 检查OpenClaw配置...")
    
    config_path = os.path.expanduser("~/.openclaw/config.json")
    if not os.path.exists(config_path):
        print("  - 未找到OpenClaw配置文件")
        return None
    
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        # 查找Deepseek配置
        deepseek_configs = []
        if 'providers' in config:
            for provider in config['providers']:
                if 'deepseek' in provider.get('name', '').lower():
                    deepseek_configs.append(provider)
        
        if deepseek_configs:
            print(f"  - 找到{len(deepseek_configs)}个Deepseek配置:")
            for idx, provider in enumerate(deepseek_configs, 1):
                print(f"    {idx}. {provider.get('name')}")
                print(f"       API Key: {provider.get('apiKey', '未设置')[:20]}...")
                print(f"       Base URL: {provider.get('baseUrl', '默认')}")
        else:
            print("  - 未找到Deepseek配置")
        
        return config
        
    except Exception as e:
        print(f"❌ 配置检查失败: {e}")
        return None

def check_gateway_active():
    """检查Gateway服务状态"""
    print("\n🔄 检查Gateway服务状态...")
    
    try:
        import subprocess
        result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
        gateway_count = len([line for line in result.stdout.split('\n') if 'openclaw-gateway' in line and 'grep' not in line])
        
        if gateway_count > 0:
            print(f"  - Gateway服务运行中 ({gateway_count}个进程)")
            # 获取最近日志
            log_cmd = "tail -5 ~/.openclaw/logs/gateway.log 2>/dev/null || echo '无日志文件'"
            log_result = subprocess.run(log_cmd, shell=True, capture_output=True, text=True)
            print(f"  - 最近日志: {log_result.stdout[:200]}...")
        else:
            print("  - Gateway服务未运行")
            
        return gateway_count > 0
        
    except Exception as e:
        print(f"❌ 服务检查失败: {e}")
        return False

def main():
    print("=" * 60)
    print("🔬 Deepseek成本数据差异诊断工具")
    print("=" * 60)
    
    # 切换到工作目录
    workspace = os.path.expanduser("~/.openclaw/xiaofeng_workspace")
    os.chdir(workspace)
    print(f"工作目录: {workspace}")
    
    # 执行检查
    db_ok = check_database_integrity()
    config = check_openclaw_config()
    gateway_ok = check_gateway_active()
    
    print("\n" + "=" * 60)
    print("📋 诊断总结")
    print("=" * 60)
    
    # 分析可能的差异原因
    print("\n🔍 可能的数据差异原因:")
    
    if not db_ok:
        print("1. ❌ 数据库损坏或不存在")
    else:
        print("1. ✅ 数据库正常")
    
    if not config:
        print("2. ❌ OpenClaw配置问题")
    else:
        print("2. ✅ OpenClaw配置正常")
    
    if not gateway_ok:
        print("3. ❌ Gateway服务未运行，API调用可能未被拦截")
    else:
        print("3. ✅ Gateway服务运行中")
    
    print("\n4. 📊 数据差异可能原因分析:")
    print("   a) API拦截器未正确捕获所有调用")
    print("   b) 其他系统直接调用Deepseek API（绕过拦截器）")
    print("   c) 时间统计窗口不一致（本地vs官方控制台）")
    print("   d) 数据库事务问题，部分记录未持久化")
    
    print("\n5. 🛠️ 建议解决方案:")
    print("   a) 验证拦截器是否在Gateway正确加载")
    print("   b) 检查是否有其他AI服务使用同一个API Key")
    print("   c) 对比完整时间段的成本数据")
    print("   d) 增加拦截器日志，验证每个API调用都被记录")

if __name__ == "__main__":
    main()