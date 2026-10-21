#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
classify_task.py — M2 任务识别状态机（三层信号 + 状态机判定）

Daryl 设计确认 (2026-08-04):
  不是"一次是/否判断"，而是带状态的分类状态机:
    第一层: 消息信号提取（确定性关键词表，零LLM）
    第二层: 任务状态机（session级 task_state.json）
    第三层: LLM仲裁（仅信号冲突时兜底，~100 tokens）

判定结果 4 种:
  A. 🆕 新任务   → 全量三层检索注入 top-5
  B. 🔁 同任务   → 不重复注入（教训已在上下文）
  C. 📤 产出升级 → 轻量注入（只注入交付物类模式 top-3）
  D. 💬 闲聊     → 零注入

用法:
  python3 classify_task.py --msg "<用户消息>" [--project <项目>] [--agent <id>] [--session <id>]
  python3 classify_task.py --reset --session <id>    # 重置任务状态
  python3 classify_task.py --debug --msg "..."

输出: JSON { decision, task_id, subject, type, injected, reason }
"""
import json
import os
import re
import sys
import hashlib
import datetime
import argparse

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
WORKSPACE = os.environ.get("WORKSPACE") or os.path.abspath(os.path.join(_SCRIPT_DIR, "..", ".."))
STATE_DIR = os.path.join(WORKSPACE, "memory/evolution/state")
STATE_FILE = os.path.join(STATE_DIR, "task_state.json")

# ============================================================
# 第一层 · 信号关键词表（确定性）
# ============================================================

# 任务型标记: 有 → 候选任务
TASK_MARKERS = [
    "开发", "写", "编写", "实现", "修复", "修改", "更新", "升级", "重构",
    "调研", "研究", "分析", "评估", "对比", "方案", "设计", "规划",
    "计算", "统计", "整理", "汇总", "生成", "创建", "搭建", "部署",
    "翻译", "审核", "检查", "排查", "优化", "调试", "测试", "集成",
    "制作", "编写", "梳理", "盘点", "提取", "抓取", "爬取", "监控",
    "改", "改一下", "调整", "前端", "UI",
    "界面", "样式", "页面", "接口", "配置", "接入", "对接", "迁移",
    "清理", "删除", "移除", "新增", "添加", "扩展", "封装", "调用",
    # Balance 财务域补充 (2026-08-05 Balance试点部署)
    "做", "核算", "入账", "申报", "登记", "核对", "处理", "台账",
    "扫描", "对账", "结算", "凭证", "发票", "归集", "计提", "摊销",
    "折旧", "材料包", "报表", "底稿", "拨备", "核销", "暂估",
]

# 交付物标记: 有 → 产出升级信号（C）
DELIVERABLE_MARKERS = [
    "报告", "md文件", "文档", "表格", "PPT", "演示", "汇报", "交付",
    "输出文件", "生成文件", "导出", "总结", "纪要", "清单", "列表",
    "物料", "产物", "输出", "邮件", "消息稿", "发布",
    # Balance 财务域交付物补充
    "材料包", "申报表", "报表", "台账", "底稿", "测算表", "案例卡片",
]

# 延续标记: 有 → 大概率同任务（B）
CONTINUATION_MARKERS = [
    "继续", "接着", "然后", "下一步", "改成", "优化一下", "补充",
    "再", "还有", "另外", "顺便", "按这个", "按此", "同样", "如上",
    "继续做", "接着做", "调整", "加点", "去掉", "换成",
]

# 闲聊标记: 有 → 大概率不注入（D）
CHAT_MARKERS = [
    "天气", "你好", "在吗", "谢谢", "晚安", "早安", "中午好", "下午好",
    "几点", "吃饭", "累", "休息", "哈哈", "开玩笑", "再见", "拜拜",
    "辛苦了", "好的", "收到", "嗯", "哦", "OK", "ok",
]

# 任务类型映射（用于 subject 归类）
TYPE_KEYWORDS = {
    "前端": ["前端", "UI", "界面", "样式", "交互", "看板", "页面"],
    "后端": ["后端", "API", "服务", "数据库", "接口", "server"],
    "开发": ["开发", "写代码", "实现", "修复", "调试", "重构", "脚本"],
    "调研": ["调研", "研究", "搜索", "查", "对比", "评估", "对标"],
    "分析": ["分析", "统计", "计算", "评估", "核算"],
    "文档": ["文档", "报告", "md", "方案", "SOP", "清单", "总结"],
    "财务": ["账", "成本", "费用", "报销", "预算", "采购", "发票"],
    "内容": ["翻译", "写作", "编辑", "内容", "文案"],
}

# 交付物专属类别（C 轻量注入时只注入这些）
DELIVERABLE_CATEGORIES = ["data_provenance", "traceability", "documentation", "reporting"]


# ============================================================
# 第二层 · 任务状态机
# ============================================================

def load_state():
    if not os.path.exists(STATE_FILE):
        return {"sessions": {}}
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"sessions": {}}


def save_state(state):
    os.makedirs(STATE_DIR, exist_ok=True)
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def get_session_state(state, session_id):
    return state["sessions"].get(session_id, {
        "task_id": None,
        "subject": None,
        "type": None,
        "injected_patterns": [],
        "started_at": None,
        "msg_count": 0,
    })


def set_session_state(state, session_id, sess):
    state["sessions"][session_id] = sess
    # 清理 48h 前的旧 session
    cutoff = (datetime.datetime.now() - datetime.timedelta(hours=48)).isoformat()
    for sid in list(state["sessions"].keys()):
        if state["sessions"][sid].get("started_at") and state["sessions"][sid]["started_at"] < cutoff:
            del state["sessions"][sid]


# ============================================================
# 第一层 · 信号提取
# ============================================================

def extract_signals(msg):
    """返回 {has_task, has_deliverable, has_continuation, has_chat, task_type}"""
    msg_l = msg.lower()
    has_task = any(m in msg for m in TASK_MARKERS)
    has_deliverable = any(m in msg for m in DELIVERABLE_MARKERS)
    has_continuation = any(m in msg for m in CONTINUATION_MARKERS)
    has_chat = any(m in msg_l for m in CHAT_MARKERS)

    # 任务类型
    task_type = None
    for t, kws in TYPE_KEYWORDS.items():
        if any(k in msg for k in kws):
            task_type = t
            break

    return {
        "has_task": has_task,
        "has_deliverable": has_deliverable,
        "has_continuation": has_continuation,
        "has_chat": has_chat,
        "task_type": task_type,
    }


def subject_hash(msg):
    """任务主题哈希：取消息中任务相关关键词的稳定指纹"""
    # 提取中文2-gram + 英文词 作为主题指纹
    grams = []
    cjk = [c for c in msg if '\u4e00' <= c <= '\u9fff']
    for i in range(len(cjk) - 1):
        grams.append(cjk[i] + cjk[i+1])
    words = [w for w in re.findall(r'[a-zA-Z0-9]+', msg.lower()) if len(w) > 1]
    sig = "".join(sorted(set(grams + words)))
    return hashlib.md5(sig.encode()).hexdigest()[:12] if sig else "chat"


# ============================================================
# 第三层 · LLM 仲裁（信号冲突时兜底）
# ============================================================

def llm_arbitrate(msg, signals):
    """信号冲突时用 LLM 判定。返回 decision 之一: new_task|continuation|deliverable_upgrade|chat"""
    api_key = os.environ.get("DEEPSEEK_API_KEY", "")
    if not api_key:
        return None  # 无API → 返回 None，调用方用保守规则
    import urllib.request
    payload = {
        "model": "deepseek-v4-pro",
        "messages": [
            {"role": "system", "content": "你是任务分类器。判断用户消息属于哪类：new_task(新任务开始)/continuation(延续当前任务)/deliverable_upgrade(要求产出交付物)/chat(闲聊)。只输出JSON: {\"decision\": \"...\", \"reason\": \"...\"}"},
            {"role": "user", "content": f"消息: {msg}\n信号: {json.dumps(signals, ensure_ascii=False)}"},
        ],
        "temperature": 0.1,
        "max_tokens": 100,
    }
    req = urllib.request.Request(
        "https://api.deepseek.com/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"},
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            content = data["choices"][0]["message"]["content"]
            start, end = content.find("{"), content.rfind("}") + 1
            result = json.loads(content[start:end])
            return result.get("decision")
    except Exception:
        return None


# ============================================================
# 主判定逻辑（状态机）
# ============================================================

def classify(msg, session_id="default", project=None, debug=False):
    state = load_state()
    sess = get_session_state(state, session_id)
    signals = extract_signals(msg)

    # 消息计数
    sess["msg_count"] = sess.get("msg_count", 0) + 1

    decision = None
    reason = ""
    new_task = None

    # ---- 状态机判定 ----
    if sess.get("task_id") is None:
        # 无活动任务
        if signals["has_task"] or signals["has_deliverable"]:
            decision = "new_task"
            reason = "无活动任务 + 任务/交付物标记"
        else:
            decision = "chat"
            reason = "无活动任务 + 无任务标记"
    else:
        # 有活动任务
        cur_hash = subject_hash(msg)
        same_subject = (cur_hash == sess.get("subject_hash")) or signals["has_continuation"]

        if signals["has_chat"] and not signals["has_task"] and not signals["has_deliverable"]:
            decision = "chat"
            reason = "闲聊标记"
        elif signals["has_deliverable"] and not signals["has_task"]:
            # 产出升级：有交付物标记但无新任务标记 → C
            decision = "deliverable_upgrade"
            reason = f"交付物标记 + 同任务延续 (主题hash: {cur_hash})"
        elif signals["has_task"] and not same_subject:
            # 新任务标记 + 主题变化 → A
            decision = "new_task"
            reason = f"新任务标记 + 主题变化 (hash {sess.get('subject_hash')}→{cur_hash})"
        elif signals["has_task"] and same_subject:
            decision = "continuation"
            reason = "任务标记 + 同主题/延续标记"
        elif signals["has_continuation"]:
            decision = "continuation"
            reason = "延续标记"
        else:
            # 信号弱 → LLM 仲裁
            arb = llm_arbitrate(msg, signals)
            if arb in ("new_task", "continuation", "deliverable_upgrade", "chat"):
                decision = arb
                reason = f"LLM仲裁: {arb}"
            else:
                # 保守默认：同任务延续（不重复注入，省token）
                decision = "continuation"
                reason = "信号弱 + 默认延续(保守)"

    # ---- 执行状态更新 ----
    if decision == "new_task":
        new_task = {
            "task_id": f"task-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}",
            "subject": msg[:50],
            "subject_hash": subject_hash(msg),
            "type": signals["task_type"],
            "project": project,
            "injected_patterns": [],
            "started_at": datetime.datetime.now().isoformat(timespec="seconds"),
        }
        sess.update(new_task)
        sess["msg_count"] = 1

    set_session_state(state, session_id, sess)
    save_state(state)

    result = {
        "decision": decision,
        "reason": reason,
        "signals": signals,
        "task_id": sess.get("task_id"),
        "subject": sess.get("subject"),
        "type": sess.get("type"),
        "msg_count": sess.get("msg_count"),
        "new_task": new_task is not None,
    }

    if debug:
        print(f"📨 消息: {msg[:60]}")
        print(f"🔍 信号: task={signals['has_task']} deliverable={signals['has_deliverable']} "
              f"cont={signals['has_continuation']} chat={signals['has_chat']} type={signals['task_type']}")
        print(f"📋 判定: {decision} — {reason}")
        print(f"   session={session_id} task_id={sess.get('task_id')} count={sess.get('msg_count')}")

    return result


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--msg", default=None)
    ap.add_argument("--session", default="default")
    ap.add_argument("--project", default=None)
    ap.add_argument("--debug", action="store_true")
    ap.add_argument("--reset", action="store_true")
    args = ap.parse_args()

    if args.reset:
        state = load_state()
        state["sessions"].pop(args.session, None)
        save_state(state)
        print(f"✅ 已重置 session {args.session}")
        sys.exit(0)

    if not args.msg:
        print("❌ 需要 --msg 或 --reset")
        sys.exit(2)

    result = classify(args.msg, args.session, args.project, args.debug)
    if not args.debug:
        print(json.dumps(result, ensure_ascii=False, indent=2))
