#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""pkg_drive.py — S4「包自包含性实测」HTTP 驱动（完全模拟页面交互，不走任何 CLI workflow）。

子命令：
  state                                   → GET /api/state（读页面顶部状态）
  save-root <path>                        → POST /api/save-source-root（页面 ⓪ 保存数据文件夹）
  run <payment|loan> <file...> --params '<json>'   → /api/upload (逐个) → /api/run → 轮询 /api/job
  download <job_id> <name> <out>          → GET /api/download（取产出）
环境变量：HUATEX_BASE（默认 http://127.0.0.1:8000）
"""
import json
import os
import sys
import time
import urllib.parse
import urllib.request

BASE = os.environ.get('HUATEX_BASE', 'http://127.0.0.1:8000')


def _req(path, data=None, headers=None, ctype=None, raw=False):
    req = urllib.request.Request(BASE + path, data=data, method='POST' if data is not None else 'GET')
    for k, v in (headers or {}).items():
        req.add_header(k, v)
    if ctype:
        req.add_header('Content-Type', ctype)
    with urllib.request.urlopen(req, timeout=600) as r:
        body = r.read()
    return body if raw else json.loads(body.decode('utf-8'))


def cmd_state():
    print(json.dumps(_req('/api/state'), ensure_ascii=False, indent=2))


def cmd_save_root(path):
    print(json.dumps(_req('/api/save-source-root', json.dumps({'path': path}).encode('utf-8'),
                          ctype='application/json'), ensure_ascii=False))


def cmd_download(jid, name, out):
    body = _req('/api/download?id=%s&name=%s' % (jid, urllib.parse.quote(name)), raw=True)
    with open(out, 'wb') as fh:
        fh.write(body)
    print('DOWNLOADED %s (%d bytes) → %s' % (name, len(body), out))


def cmd_run(flow, files, params):
    token = None
    for f in files:
        hdr = {'X-Filename': urllib.parse.quote(os.path.basename(f))}
        if token:
            hdr['X-Token'] = token
        with open(f, 'rb') as fh:
            body = fh.read()
        res = _req('/api/upload', body, hdr)
        token = res['token']
        print('UPLOAD %s (%d B) token=%s' % (os.path.basename(f), len(body), token))
    res = _req('/api/run', json.dumps({'workflow': flow, 'token': token,
                                       'params': params}).encode('utf-8'),
               ctype='application/json')
    jid = res['job_id']
    print('JOB %s' % jid)
    t0 = time.time()
    while True:
        j = _req('/api/job?id=%s' % jid)['job']
        el = time.time() - t0
        print('  [%6.1fs] %s' % (el, j['status']))
        if j['status'] in ('done', 'failed'):
            print('--- stdout tail ---')
            print(j.get('stdout_tail', ''))
            if j.get('stderr_tail'):
                print('--- stderr tail ---')
                print(j['stderr_tail'])
            print('--- artifacts ---')
            for a in j.get('artifacts', []):
                print('  %s  %d B' % (a['name'], a['size']))
            print('RESULT job=%s status=%s elapsed=%s' % (jid, j['status'], j.get('elapsed_sec')))
            return 0 if j['status'] == 'done' else 1
        if el > 2400:
            print('TIMEOUT')
            return 2
        time.sleep(5)


def main():
    a = sys.argv[1:]
    if not a:
        raise SystemExit(__doc__)
    c = a[0]
    if c == 'state':
        return cmd_state()
    if c == 'save-root':
        return cmd_save_root(a[1])
    if c == 'download':
        return cmd_download(a[1], a[2], a[3])
    params = {}
    if '--params' in a:
        i = a.index('--params')
        params = json.loads(a[i + 1])
        a = a[:i]
    return cmd_run(a[1], a[2:], params)


if __name__ == '__main__':
    sys.exit(main() or 0)
