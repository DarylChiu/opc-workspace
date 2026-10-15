#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""S4 trace 写入器：保证 ts 单调递增（严格 > 上一条）。"""
import datetime
import json
import os
import sys

P = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'execution_trace.jsonl')
TZ = datetime.timezone(datetime.timedelta(hours=7))

step, action, result = sys.argv[1], sys.argv[2], sys.argv[3]
last = None
if os.path.exists(P):
    with open(P, encoding='utf-8') as fh:
        for line in fh:
            line = line.strip()
            if line:
                try:
                    last = json.loads(line)
                except Exception:
                    pass
ts = datetime.datetime.now(TZ).isoformat(timespec='seconds')
if last and ts <= last['ts']:
    ts = (datetime.datetime.fromisoformat(last['ts'])
          + datetime.timedelta(seconds=1)).isoformat(timespec='seconds')
rec = {'ts': ts, 'step': str(step), 'action': action, 'result': result}
with open(P, 'a', encoding='utf-8') as fh:
    fh.write(json.dumps(rec, ensure_ascii=False) + '\n')
print(ts, step, action)
