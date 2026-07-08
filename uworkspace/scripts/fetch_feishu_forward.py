#!/usr/bin/env python3
"""Fetch ALL merged forward messages and their sub-messages from Feishu group chat"""
import json, requests, sys, io, os
from datetime import datetime

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

APP_ID = "cli_a9307c22ddb8dcd1"
APP_SECRET = "eWDmRnMYFRCHLRuvqDrIlhzTtdZ8Elad"
CHAT_ID = "oc_7d71d54d87cbd265d9c3811bc59840b2"
BASE = "https://open.feishu.cn/open-apis"
OUT_DIR = "/Users/zhaoyuzhao/.openclaw/workspace/feishu_forwards"

def get_token():
    r = requests.post(f"{BASE}/auth/v3/tenant_access_token/internal", 
                      json={"app_id": APP_ID, "app_secret": APP_SECRET}, timeout=10)
    r.raise_for_status()
    return r.json()["tenant_access_token"]

def list_messages(token, page_token=None):
    params = {
        "container_id_type": "chat",
        "container_id": CHAT_ID,
        "page_size": 50,
        "sort_type": "ByCreateTimeDesc"
    }
    if page_token:
        params["page_token"] = page_token
    r = requests.get(f"{BASE}/im/v1/messages", params=params,
                     headers={"Authorization": f"Bearer {token}"}, timeout=15)
    r.raise_for_status()
    return r.json()["data"]

def get_merged_detail(token, message_id):
    """Get a merge_forward message with all its sub-messages"""
    r = requests.get(f"{BASE}/im/v1/messages/{message_id}",
                     headers={"Authorization": f"Bearer {token}"}, timeout=15)
    r.raise_for_status()
    return r.json()["data"]

def extract_text(msg):
    """Extract readable text from any message"""
    body = msg.get("body", {}).get("content", "")
    msg_type = msg.get("msg_type", "")
    try:
        cj = json.loads(body)
        if msg_type == "text":
            return cj.get("text", "")
        elif msg_type == "post":
            parts = []
            title = cj.get("title", "")
            if title:
                parts.append(f"【{title}】\n")
            for block in cj.get("content", [[]]):
                for elem in block:
                    if isinstance(elem, dict):
                        tag = elem.get("tag", "")
                        if tag == "text":
                            parts.append(elem.get("text", ""))
                        elif tag == "at":
                            parts.append(f"@{elem.get('user_name', elem.get('user_id', ''))}")
                        elif tag == "a":
                            parts.append(elem.get("text", ""))
                parts.append("\n")
            return "".join(parts)
        elif msg_type == "interactive":
            # Try to get card title
            title = cj.get("title", "")
            elements = cj.get("elements", [])
            if elements:
                parts = [title] if title else []
                for row in elements:
                    for elem in row:
                        if isinstance(elem, dict):
                            if elem.get("tag") == "markdown":
                                parts.append(elem.get("content", ""))
                            elif elem.get("tag") == "text":
                                parts.append(elem.get("text", ""))
                return "\n".join(parts) if parts else "[Interactive card - content not fully extractable]"
            return "[Interactive card]"
        else:
            return f"[{msg_type} message]"
    except:
        return body

def get_sender_name(msg):
    sender = msg.get("sender", {})
    sid = sender.get("id", "unknown")
    # Map known IDs to names
    name_map = {
        "ou_3bf0d4dcf7a80d6ddf15be5bd2f7ad4f": "Daryl",
        "ou_1511f64890ba0d3016454e4419b49178": "忧郁小猫 (Kitty)",
        "ou_45e3689e9b823042f134d6bdc8f34887": "吹点小风 (Bryson)",
        "cli_a9307c22ddb8dcd1": "忧郁小猫 (Bot)",
        "cli_a94a032b6d385bd8": "吹点小风 (Bot)",
    }
    return name_map.get(sid, sid)

print("=== Step 1: Scan chat history for merge_forward messages ===")
token = get_token()
print("Token acquired\n")

# Collect all messages to find merge_forward types
merge_forward_ids = []
page_token = None
pages = 0

while pages < 20:
    data = list_messages(token, page_token)
    items = data.get("items", [])
    pages += 1
    
    for m in items:
        if m.get("msg_type") == "merge_forward":
            ts = datetime.fromtimestamp(int(m["create_time"]) / 1000).strftime("%Y-%m-%d %H:%M:%S")
            mid = m["message_id"]
            if mid not in merge_forward_ids:
                merge_forward_ids.append(mid)
                print(f"  Found: {mid} | {ts}")
    
    if not data.get("has_more"):
        break
    page_token = data.get("page_token")
    if not page_token:
        break

print(f"\nScanned {pages} pages, found {len(merge_forward_ids)} merge_forward messages\n")

if not merge_forward_ids:
    print("No merge_forward messages found. Checking message types available...")
    data = list_messages(token)
    types = set()
    for m in data.get("items", []):
        types.add(m.get("msg_type"))
    print(f"Message types in chat: {types}")
    sys.exit(1)

os.makedirs(OUT_DIR, exist_ok=True)

print("=== Step 2: Extract sub-messages from each merge_forward ===")

for mid in merge_forward_ids:
    print(f"\nProcessing: {mid}")
    detail = get_merged_detail(token, mid)
    items = detail.get("items", [])
    
    # Separate: items[0] is the merge_forward itself, items[1:] are sub-messages
    merge_msg = items[0] if items else None
    sub_msgs = [m for m in items if m.get("upper_message_id") == mid]
    
    if not merge_msg:
        print("  No merge message found in response")
        continue
    
    ts = datetime.fromtimestamp(int(merge_msg["create_time"]) / 1000).strftime("%Y%m%d_%H%M")
    ts_readable = datetime.fromtimestamp(int(merge_msg["create_time"]) / 1000).strftime("%Y-%m-%d %H:%M:%S")
    
    print(f"  Created: {ts_readable}")
    print(f"  Sub-messages: {len(sub_msgs)}")
    
    # Sort sub-messages by time
    sub_msgs.sort(key=lambda m: int(m.get("create_time", "0")))
    
    # Build output
    lines = [
        f"# OPC看板交互系统 — 合并转发聊天记录",
        f"",
        f"> 转发时间: {ts_readable}",
        f"> 转发者: {get_sender_name(merge_msg)}",
        f"> 消息数: {len(sub_msgs)}",
        f"> 原始转发ID: {mid}",
        f"",
        f"---",
        f"",
    ]
    
    for i, sm in enumerate(sub_msgs):
        sm_ts = datetime.fromtimestamp(int(sm["create_time"]) / 1000).strftime("%Y-%m-%d %H:%M:%S")
        sender = get_sender_name(sm)
        content = extract_text(sm)
        msg_type = sm.get("msg_type", "")
        
        lines.append(f"## [{i+1}] {sender} ({sm_ts})")
        lines.append(f"")
        
        if msg_type == "interactive":
            lines.append(f"> _[交互卡片/按钮消息，内容可能不完整]_")
            if content and content not in ("[Interactive card]", "[Interactive card - content not fully extractable]"):
                lines.append(f"")
                lines.append(content)
        else:
            lines.append(content)
        
        lines.append(f"")
        lines.append(f"---")
        lines.append(f"")
    
    filename = f"{OUT_DIR}/forward_{ts}.md"
    with open(filename, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    
    # Print preview
    print(f"\n  Preview of first sub-messages:")
    for i, sm in enumerate(sub_msgs[:3]):
        content = extract_text(sm)[:120]
        sender = get_sender_name(sm)
        print(f"  [{i+1}] {sender}: {content}...")
    
    print(f"\n  ✅ Saved: {filename}")

print(f"\n=== DONE ===")
print(f"Files saved in: {OUT_DIR}")
for f in sorted(os.listdir(OUT_DIR)):
    if f.endswith('.md'):
        print(f"  - {f}")
