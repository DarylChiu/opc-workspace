#!/usr/bin/env python3
"""Fix repeat questions + assessment issues in server.py"""
path = '/Users/zhaoyuzhao/.openclaw/xiaofeng_workspace/ielts_tutor/backend/server.py'
with open(path) as f:
    content = f.read()

# ═══ Fix 1: IELTS Part 1 prompt — add topic tracking to prevent repeats ═══
old_part1 = '''"ielts_part1": """You are Alex, a friendly IELTS Speaking examiner doing Part 1.

CRITICAL RULES:
- Ask ONE question at a time about familiar topics (work, home, hobbies, daily life, travel, food, etc.)
- Vary your responses naturally — don't use the same phrases every time. Mix it up.
- Keep responses SHORT: 1-3 sentences max, then ask your next question.
- React naturally to what the candidate says before moving on. Show you're listening.
- Occasionally use different transitions: 'Interesting...', 'I see...', 'Let's talk about...', 'How about...', 'Moving on...'
- NEVER give scores, NEVER say 'good' or 'excellent' repeatedly
- Match the candidate's level — don't use overly complex vocabulary
- Be warm and conversational, like chatting with a friend""",'''

new_part1 = '''"ielts_part1": """You are Alex, a friendly IELTS Speaking examiner doing Part 1.

CRITICAL RULES:
- Ask ONE question at a time about familiar topics.
- TOPIC LIST: work/study, hometown, home/accommodation, hobbies/free time, reading, music, travel, food, sports, weather, daily routine, friends/family. You must cover at least 5 different topics.
- DO NOT repeat a question you already asked. Before asking, check: did I already ask about this topic? If yes, move to a completely new topic.
- Keep responses SHORT: 1-3 sentences max, then ask your next question.
- React naturally to what the candidate says before moving on. Show you're listening.
- Use varied transitions: 'Interesting...', 'I see...', 'Let's talk about...', 'How about...', 'Moving on...', 'That reminds me...'
- NEVER give scores, NEVER say 'good' or 'excellent' repeatedly
- Match the candidate's level — don't use overly complex vocabulary
- After 6-8 exchanges, wrap up naturally with a closing remark
- Be warm and conversational, like chatting with a friend""",'''

content = content.replace(old_part1, new_part1)

# ═══ Fix 2: Expand context window — 13→17 (8 exchanges) ═══
content = content.replace(
    'if len(history) > 13: history[:] = [history[0]] + history[-10:]',
    'if len(history) > 17: history[:] = [history[0]] + history[-14:]'
)

# ═══ Fix 3: Evaluate — add explicit logging + ensure it runs ═══
old_eval = '''            elif t == "evaluate_final":
                if not user_texts: continue
                all_text = "\n---\n".join(user_texts[-10:])
                sys_prompt = """You are an IELTS examiner. Evaluate the conversation and return ONLY JSON:'''

new_eval = '''            elif t == "evaluate_final":
                logger.info(f"EVALUATE_FINAL received: {len(user_texts)} user texts, {len(history)} history")
                if not user_texts: 
                    logger.warning("EVALUATE: no user texts, skipping")
                    await ws.send_json({"type": "score", "scores": {"overall": 0, "summary": "No speech detected for evaluation"}})
                    continue
                all_text = "\n---\n".join(user_texts[-10:])
                logger.info(f"EVALUATE: sending to DeepSeek ({len(all_text)} chars)")
                sys_prompt = """You are an IELTS examiner. Evaluate the conversation and return ONLY JSON:'''

content = content.replace(old_eval, new_eval)

# ═══ Fix 4: Score response — add logging ═══
old_score_log = '''                    sc = json.loads(r)'''
new_score_log = '''                    logger.info(f"EVALUATE: DS response {len(r)} chars")
                    sc = json.loads(r)
                    logger.info(f"EVALUATE: score={sc.get('overall')}")'''

content = content.replace(old_score_log, new_score_log)

# Add logging for score send
old_score_send = '''                    await ws.send_json({"type": "score", "scores": sc})'''
new_score_send = '''                    logger.info(f"EVALUATE: sending score to frontend, overall={sc.get('overall')}")
                    await ws.send_json({"type": "score", "scores": sc})'''
content = content.replace(old_score_send, new_score_send)

# Add logging for parse fail
old_parse_fail = '''                    logger.debug(f"Score fail: {r[:80]}")'''
new_parse_fail = '''                    logger.error(f"EVALUATE: JSON parse failed: {r[:200]}")'''
content = content.replace(old_parse_fail, new_parse_fail)

# ═══ Fix 5: Evaluate in finally block — run evaluation even on disconnect ═══
# Replace the finally block for cascade pipeline to run eval if there are user_texts
old_finally = '''    finally:
        if tracker:
            debug_manager.remove_tracker(sid)
        await event_bus.emit("session_end", sid=sid, pipeline="cascade")
        sessions.end_session(sid)'''

new_finally = '''    finally:
        # Run evaluation if session had user speech but no score sent yet
        if user_texts and not globals().get(f'_scored_{sid}', False):
            try:
                logger.info(f"FINALLY: auto-evaluating session {sid} ({len(user_texts)} texts)")
                globals()[f'_scored_{sid}'] = True
                all_text = "\n---\n".join(user_texts[-10:])
                sys_prompt = """You are an IELTS examiner. Evaluate and return ONLY JSON:
{"fluency":X.X,"vocabulary":X.X,"grammar":X.X,"pronunciation":X.X,"overall":X.X,
"summary":"2-3 sentence overall assessment",
"improvements":["You said ~~wrong~~ → **correct** — why",...],
"highlights":["Good use of ``expression`` → **better** — why",...]}"""
                r = await ds_chat([{"role":"system","content":sys_prompt},
                                   {"role":"user","content":f"Evaluate:\n{all_text}"}],
                                  max_tokens=400, temp=0.3)
                try:
                    sc = json.loads(r)
                    await ws.send_json({"type": "score", "scores": sc})
                    sessions.save_evaluation(sid, sc)
                    logger.info(f"FINALLY: auto-score sent, overall={sc.get('overall')}")
                except Exception as e:
                    logger.error(f"FINALLY: eval failed: {e}")
            except Exception as e:
                logger.error(f"FINALLY: auto-eval error: {e}")
        
        if tracker:
            debug_manager.remove_tracker(sid)
        await event_bus.emit("session_end", sid=sid, pipeline="cascade")
        sessions.end_session(sid)'''

content = content.replace(old_finally, new_finally)

with open(path, 'w') as f:
    f.write(content)

# Verify syntax
import py_compile
py_compile.compile(path, doraise=True)

print("✅ Fixes applied:")
print("   1. System prompt: topic tracking + no-repeat rule")
print("   2. Context window: 13→17 messages (8 exchanges)")
print("   3. Evaluate: explicit logging at each step")
print("   4. Auto-eval in finally: runs even if WS disconnects early")
