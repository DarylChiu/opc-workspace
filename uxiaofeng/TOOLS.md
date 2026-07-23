# TOOLS.md - Local Notes

## L4 · 交付前质量自检 ⭐ 强制

任何给 Daryl 验收的交付物，回复前必须确认：
1. 本地完整流程走通至少一次，无阻断 Bug
2. JS 无语法错误 / API 全部可达 / async/await 正确
3. Mock/API 数据与实际素材一致，无越界/格式不匹配
4. 公网 URL 已验证可访问（如需要）
5. 功能实现与设计文档描述一致

→ 详见 `scripts/quality/checklist.md`
→ 自检通过后回复标注「✅ L4 交付自检通过」
→ 任一项不通过，先修再提测

---

Skills define _how_ tools work. This file is for _your_ specifics — the stuff that's unique to your setup.

## What Goes Here

Things like:

### Communication Rules
- **Language**: Use Chinese for questions and task reports
- **Group Reply**: Reply as normal messages in group chats (no "topic" style)

- Camera names and locations
- SSH hosts and aliases
- Preferred voices for TTS
- Speaker/room names
- Device nicknames
- Anything environment-specific

## Examples

```markdown
### Cameras

- living-room → Main area, 180° wide angle
- front-door → Entrance, motion-triggered

### SSH

- home-server → 192.168.1.100, user: admin

### TTS

- Preferred voice: "Nova" (warm, slightly British)
- Default speaker: Kitchen HomePod
```

## Why Separate?

Skills are shared. Your setup is yours. Keeping them apart means you can update skills without losing your notes, and share skills without leaking your infrastructure.

---

Add whatever helps you do your job. This is your cheat sheet.
