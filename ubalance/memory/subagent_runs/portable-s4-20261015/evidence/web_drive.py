#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""S3 证据脚本 · 完全模拟页面的 HTTP 交互（不用任何命令行 workflow 调用）。

① upload_one() —— 与 index.html 的 fetch('/api/upload') 同款：
     POST /api/upload，头 X-Filename(urlenc)，体 = 文件原始字节
② /api/run → 轮询 /api/job → 打印状态与产物

用法: python3 web_drive.py <workflow> <file1> [file2 ...] --params '<json>'
"""
import json
import os
import sys
import time
import urllib.parse
import urllib.request

BASE = 'http://127.0.0.1:8000'


def _post(path, data=b'', headers=None, ctype=None):
    req = urllib.request.Request(BASE + path, data=data, method='POST')
    for k, v in (headers or {}).items():
        req.add_header(k, v)
    if ctype:
        req.add_header('Content-Type', ctype)
    with urllib.request.urlopen(req, timeout=300) as r:
        return json.loads(r.read().decode('utf-8'))


def upload(path):
    name = os.path.basename(path)
    hdr = {'X-Filename': urllib.parse.quote(name)}
    if upload.token:
        hdr['X-Token'] = upload.token
    with open(path, 'rb') as fh:
        body = fh.read()
    res = _post('/api/upload', body, hdr)
    if not res.get('ok'):
        raise SystemExit('❌ 上传失败: %s' % res)
    upload.token = res['token']
    print(f'  ⬆ 上传 {name} ({len(body)} B) → token={res["token"]}')
    return res


upload.token = None


def main():
    args = sys.argv[1:]
    params = {}
    if '--params' in args:
        i = args.index('--params')
        params = json.loads(args[i + 1])
        args = args[:i] + args[i + 2:]
    flow, files = args[0], args[1:]
    print(f'=== Web 驱动 · 流程={flow} · 参数={params} ===')
    for f in files:
        upload(f)
    res = _post('/api/run', json.dumps({'workflow': flow, 'token': upload.token,
                                        'params': params}).encode('utf-8'),
                ctype='application/json')
    if not res.get('ok'):
        raise SystemExit('❌ 提交失败: %s' % res)
    jid = res['job_id']
    print(f'=== job_id = {jid} ===')
    t0 = time.time()
    while True:
        with urllib.request.urlopen(f'{BASE}/api/job?id={jid}', timeout=60) as r:
            j = json.loads(r.read().decode('utf-8'))['job']
        el = round(time.time() - t0, 1)
        print(f'  [{el:>7.1f}s] status={j["status"]} elapsed={j["elapsed_sec"]}')
        if j['status'] in ('done', 'failed'):
            print('--- stdout tail ---')
            print(j.get('stdout_tail', ''))
            if j.get('stderr_tail'):
                print('--- stderr tail ---')
                print(j['stderr_tail'])
            print('--- artifacts ---')
            for a in j.get('artifacts', []):
                print(f'  {a["name"]}  {a["size"]} B')
            print('JOB_ID=%s STATUS=%s' % (jid, j['status']))
            return 0 if j['status'] == 'done' else 1
        if el > 3600:
            print('TIMEOUT'); return 2
        time.sleep(5)


if __name__ == '__main__':
    sys.exit(main())
