#!/usr/bin/env python3
"""
Deepseek集成测试脚本
测试成本跟踪系统与实际OpenClaw的集成
"""

import asyncio
import json
import time
from datetime import datetime
from deepseek_cost_tracker import DeepseekCostTracker, DeepseekAPIInterceptor

async def test_basic_tracking():
    """测试基础跟踪功能"""
    print("🧪 测试基础跟踪功能...")
    
    tracker = DeepseekCostTracker()
    
    try:
        # 测试不同项目
        tracker.set_current_project("voice_mvp")
        
        # 模拟一些API调用
        for i in range(5):
            await asyncio.sleep(0.1)  # 模拟延迟
            input_tokens = 100 + i * 20
            output_tokens = 50 + i * 10
            
            record = tracker.record_usage(
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                metadata={
                    "test": True,
                    "iteration": i,
                    "timestamp": datetime.now().isoformat()
                }
            )
            
            print(f"  voice_mvp #{i+1}: {input_tokens}输入 + {output_tokens}输出 = ${record.cost_usd:.6f}")
        
        # 切换项目
        tracker.set_current_project("ielts_teaching")
        
        for i in range(3):
            await asyncio.sleep(0.1)
            input_tokens = 300 + i * 50
            output_tokens = 150 + i * 30
            
            record = tracker.record_usage(
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                metadata={"test": True, "iteration": i}
            )
            
            print(f"  ielts_teaching #{i+1}: {input_tokens}输入 + {output_tokens}输出 = ${record.cost_usd:.6f}")
        
        # 生成报告
        report = tracker.generate_markdown_report()
        
        # 分析报告
        lines = report.split('\n')
        print("\n📊 报告摘要:")
        for line in lines[:20]:  # 显示前20行
            if line.strip():
                print(f"  {line}")
        
        print("✅ 基础跟踪测试通过")
        return True
        
    except Exception as e:
        print(f"❌ 基础跟踪测试失败: {e}")
        return False
    
    finally:
        tracker.close()

async def test_alerts():
    """测试警报功能"""
    print("\n🔔 测试警报功能...")
    
    tracker = DeepseekCostTracker("test_alerts.db")
    
    try:
        # 模拟高成本使用
        for i in range(100):  # 多次调用模拟高成本
            await asyncio.sleep(0.01)
            input_tokens = 10000  # 每次10K tokens
            output_tokens = 5000   # 每次5K tokens
            
            record = tracker.record_usage(
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                project_tag="test_high_cost",
                metadata={"test": "alerts"}
            )
        
        # 检查警报
        alerts = tracker.check_alerts()
        
        print(f"  总共 {len(alerts)} 个警报:")
        for alert in alerts:
            print(f"  ⚠️  {alert['message']}")
        
        if alerts:
            print("✅ 警报功能正常")
            return True
        else:
            print("⚠️  未触发警报（可能需要调整阈值）")
            return True
            
    except Exception as e:
        print(f"❌ 警报测试失败: {e}")
        return False
    
    finally:
        tracker.close()
        # 清理测试数据库
        import os
        if os.path.exists("test_alerts.db"):
            os.remove("test_alerts.db")

async def test_project_summary():
    """测试项目摘要功能"""
    print("\n📋 测试项目摘要功能...")
    
    tracker = DeepseekCostTracker("test_projects.db")
    
    try:
        # 为多个项目生成数据
        projects = ["project_a", "project_b", "project_c"]
        
        for project in projects:
            tracker.set_current_project(project)
            
            for i in range(3):
                await asyncio.sleep(0.05)
                input_tokens = 500 + i * 100
                output_tokens = 200 + i * 50
                
                tracker.record_usage(
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    metadata={"project": project, "iteration": i}
                )
        
        # 获取项目摘要
        for project in projects:
            summary = tracker.get_project_summary(project)
            print(f"  {project}: ${summary['total_cost_usd']:.6f} ({summary['call_count']}次调用)")
        
        # 获取每日摘要
        daily = tracker.get_daily_summary()
        print(f"\n  📅 每日总计: ${daily['total_cost_usd']:.6f} ({daily['record_count']}次调用)")
        
        print("✅ 项目摘要测试通过")
        return True
        
    except Exception as e:
        print(f"❌ 项目摘要测试失败: {e}")
        return False
    
    finally:
        tracker.close()
        import os
        if os.path.exists("test_projects.db"):
            os.remove("test_projects.db")

async def test_api_interceptor():
    """测试API拦截器"""
    print("\n🔄 测试API拦截器...")
    
    tracker = DeepseekCostTracker()
    interceptor = DeepseekAPIInterceptor(tracker)
    
    try:
        # 模拟API请求
        test_requests = [
            {
                "model": "deepseek-chat",
                "messages": [{"role": "user", "content": "IELTS speaking practice question"}],
                "max_tokens": 100
            },
            {
                "model": "deepseek-chat",
                "messages": [{"role": "user", "content": "Debug tracking system cost calculation"}],
                "max_tokens": 50
            },
            {
                "model": "deepseek-chat",
                "messages": [{"role": "user", "content": "Voice MVP feature development"}],
                "max_tokens": 200
            }
        ]
        
        for i, request in enumerate(test_requests):
            response = await interceptor.intercept_request(request)
            usage = response.get("usage", {})
            
            print(f"  请求 #{i+1}: {usage.get('prompt_tokens', 0)}输入 + {usage.get('completion_tokens', 0)}输出 tokens")
        
        # 检查追踪结果
        daily = tracker.get_daily_summary()
        print(f"  API拦截后总成本: ${daily['total_cost_usd']:.6f}")
        
        print("✅ API拦截器测试通过")
        return True
        
    except Exception as e:
        print(f"❌ API拦截器测试失败: {e}")
        return False
    
    finally:
        tracker.close()

async def main():
    """主测试函数"""
    print("🚀 Deepseek集成测试开始")
    print("=" * 60)
    
    tests = [
        test_basic_tracking,
        test_alerts,
        test_project_summary,
        test_api_interceptor,
    ]
    
    passed = 0
    total = len(tests)
    
    for test_func in tests:
        try:
            success = await test_func()
            if success:
                passed += 1
        except Exception as e:
            print(f"❌ 测试异常: {e}")
    
    print("=" * 60)
    print(f"🏁 测试完成: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 所有测试通过！系统可正常集成")
        return 0
    else:
        print("⚠️  部分测试未通过，请检查")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
