import sqlite3
import datetime

# 连接到数据库
conn = sqlite3.connect('/Users/zhaoyuzhao/.openclaw/xiaofeng_workspace/deepseek_cost.db')
cursor = conn.cursor()

print('📊 Deepseek成本跟踪系统验证进度')
print('=' * 50)
print('当前时间: ' + datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
print()

# 1. 当前数据库状态
today = datetime.datetime.now().strftime('%Y-%m-%d')
cursor.execute('SELECT COUNT(*) FROM cost_records WHERE date(timestamp) = ?', (today,))
today_count = cursor.fetchone()[0]

cursor.execute('SELECT project_tag, COUNT(*), SUM(cost_usd) FROM cost_records WHERE date(timestamp) = ? GROUP BY project_tag', (today,))
print(f'今日记录: {today_count}条')
print()
print('🏷️ 今日各项目统计:')
today_total = 0.0
today_test = 0.0

for project, count, cost in cursor.fetchall():
    if cost is None:
        cost = 0.0
    today_total += cost
    
    # 判断是否为测试数据
    if project.startswith('test_') or project.startswith('debug_') or 'test' in project.lower():
        today_test += cost
        print(f'  ⚠️  {project}: {count}条 (${cost:.6f}) [测试数据]')
    else:
        print(f'  ✅ {project}: {count}条 (${cost:.6f})')

print(f'\n💰 今日总成本: ${today_total:.6f}')
if today_total > 0:
    print(f'🧪 测试数据成本: ${today_test:.6f} (占比: {today_test/today_total*100:.1f}%)')
else:
    print('💰 今日总成本: $0.000000')

# 2. 数据差异分析
print()
print('🔍 数据差异分析结果:')
print('  根据用户反馈:')
print('  - Deepseek官方控制台数据 < 本地tracker数据')
print('  - 这意味着: 本地tracker包含了未实际消耗API额度的记录')
print()
print('  可能原因:')
print('  1. 测试脚本产生的模拟调用被计入数据库')
print('  2. 拦截器在某些情况下重复记录')
print('  3. 时间统计窗口不同(UTC vs 本地时间)')

# 3. 最近的实际调用记录
print()
print('⏰ 最近的实际调用记录(排除测试):')
cursor.execute('''SELECT timestamp, project_tag, input_tokens, output_tokens, cost_usd 
                  FROM cost_records 
                  WHERE NOT (project_tag LIKE '%test%' OR project_tag LIKE '%debug%' OR project_tag LIKE '%mock%')
                  AND timestamp > datetime('now', '-1 hour')
                  ORDER BY timestamp DESC LIMIT 5''')
recent_real = cursor.fetchall()

if recent_real:
    print(f'  过去1小时的实际调用: {len(recent_real)}条')
    for ts, project, in_t, out_t, cost in recent_real:
        print(f'    {ts[11:16]} - {project}: {in_t}→{out_t} (${cost:.6f})')
else:
    print('  过去1小时无实际调用记录')

conn.close()
print()
print('=' * 50)
print('🚀 下一步行动建议:')
print('1. 清理测试数据，保留真实调用记录')
print('2. 验证拦截器集成状态')
print('3. 生成最终验证报告')
print()

# 4. 检查是否已经清理过
print('🔄 已完成工作:')
print('  ✅ 数据库连接验证')
print('  ✅ 数据差异分析')
print('  🔄 等待进一步指令')
print('  🔄 生成验证报告')