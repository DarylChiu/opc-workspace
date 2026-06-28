"""
会话状态管理
"""
from datetime import datetime


class SessionManager:
    def __init__(self):
        self._sessions = {}

    def create(self, sid, mode="ielts_part1", pipeline="cascade"):
        self._sessions[sid] = {
            "mode": mode,
            "pipeline": pipeline,
            "status": "created",
            "transcripts": [],
            "created": datetime.now()
        }

    def get(self, sid):
        return self._sessions.get(sid)

    def update(self, sid, **kwargs):
        if sid in self._sessions:
            self._sessions[sid].update(kwargs)

    def remove(self, sid):
        self._sessions.pop(sid, None)

    def __len__(self):
        return len(self._sessions)
