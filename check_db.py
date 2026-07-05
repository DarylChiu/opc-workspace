#!/usr/bin/env python3
import sqlite3
from datetime import datetime

conn = sqlite3.connect('deepseek_cost.db')
cursor = conn.cursor()

print('📊 数据库内容检查')
print('=' * 50)

# 检查表结构
cursor.execute('SELECT name FROM sqlite_master WHERE type="table"')
tables = cursor.fetchall()
print(f'表数量: {len(tables)}')
for table in tables:
    print(f'  表名: {table[0]}')

# 检查cost_records表数据
print('\n📝 cost_records表数据:')
cursor.execute('SELECT COUNT(*) FROM cost_records')
count = cursor.fetchone()[0]
print(f'  记录总数: {count}')

if count > 0:
    cursor.execute('SELECT timestamp, project_tag, input_tokens, output_tokens, cost_usd FROM cost_records ORDER BY timestamp DESC LIMIT 5')
    records = cursor.fetchall()
    print(f'  最近的{len(records)}条记录:')
    for rec in records:
        print(f'    {rec[0]}: {rec[1]} - {rec[2]}输入/{rec[3]}输出 = ${rec[4]:.6f}')

# 查看今日记录
today = datetime.now().strftime('%Y-%m-%d')
cursor.execute('SELECT COUNT(*) FROM cost_records WHERE date(timestamp) = ?', (today,))
today_count = cursor.fetchone()[0]
print(f'\n🗓️  今日({today})记录数: {today_count}')

if today_count > 0:
    cursor.execute('''
        SELECT SUM(input_tokens), SUM(output_tokens), SUM(cost_usd) 
        FROM cost_records 
        WHERE date(timestamp) = ?
    ''', (today,))
    totals = cursor.fetchone()
    print(f'  今日总计: {totals[0] or 0}输入 + {totals[1] or 0}输出 = ${totals[2] or 0:.6f}')

conn.close()
print('\n✅ 数据库检查完成')