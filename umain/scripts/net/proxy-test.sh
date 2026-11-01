#!/bin/bash
# 验证代理链路
printf "%-24s %s\n" "本地7890端口" "$(nc -z 127.0.0.1 7890 && echo OPEN || echo CLOSED)"
for u in https://chatgpt.com https://api.openai.com/v1/models https://www.google.com; do
  printf "%-30s " "$u"
  curl -sS -o /dev/null -w "via-proxy=%{http_code} %{time_total}s\n" --max-time 15 -x http://127.0.0.1:7890 "$u" 2>&1 | tail -1
done
echo "--- 出口IP ---"
curl -sS --max-time 15 -x http://127.0.0.1:7890 "http://ip-api.com/json/?fields=country,isp,query" 2>&1
