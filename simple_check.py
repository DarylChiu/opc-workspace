import sqlite3
import datetime

conn = sqlite3.connect('/Users/zhaoyuzhao/.openclaw/xiaofeng_workspace/deepseek_cost.db')
cursor = conn.cursor()

print('📊 实际数据库内容检查')
print('=' * 50)

cursor.execute('SELECT COUNT(*) FROM cost_records')
total = cursor.fetchone()[0]
print(f'总记录数: {total}')

today = datetime.datetime.now().strftime('%Y-%m-%d')
cursor.execute('SELECT COUNT(*) FROM cost_records WHERE date(timestamp) = ?', (today,))
today_count = cursor.fetchone()[0]
print(f'今日记录: {today_count}')

print('\n🏷️ 项目成本分布:')
cursor.execute('SELECT project_tag, COUNT(*), SUM(input_tokens), SUM(output_tokens), SUM(cost_usd) FROM cost_records GROUP BY project_tag')
for row in cursor.fetchall():
    project, count, input_sum, output_sum, cost_sum = row
    if input_sum is None:
        input_sum = 0
    if output_sum is None:
        output_sum = 0
    if cost_sum is None:
        cost_sum = 0
    print(f'  - {project}: {count}次调用, {input_sum}输入/{output_sum}输出 (${cost_sum:.6f})')

cursor.execute('SELECT SUM(input_tokens), SUM(output_tokens), SUM(cost_usd) FROM cost_records')
row = cursor.fetchone()
total_input = row[0] if row[0] else 0
total_output = row[1] if row[1] else 0
total_cost = row[2] if row[2] else 0
print(f'\n💰 数据库总成本: ${total_cost:.6f} ({total_input}输入/{total_output}输出)')

print('\n⏰ 最近5条记录:')
cursor.execute('SELECT id, project_tag, input_tokens, output_tokens, cost_usd, timestamp FROM cost_records ORDER BY timestamp DESC LIMIT 5')
for row in cursor.fetchall():
    id_, project, input_t, output_t, cost, timestamp = row
    print(f'  [{id_}] {project}: {input_t}→{output_t} (${cost:.6f}) @ {timestamp}')

conn.close()