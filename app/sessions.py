import time

MAX_SESSIONS = 1000
MAX_HISTORY = 50
MODEL_CONTEXT_LIMIT = 20
SESSION_TTL = 24 * 60 * 60

sessions = {}


def _now():
    return time.time()


def _prune_sessions():
    expired = [sid for sid, s in sessions.items() if _now() - s["last_used"] > SESSION_TTL]
    for sid in expired:
        del sessions[sid]
    while len(sessions) > MAX_SESSIONS:
        oldest = min(sessions, key=lambda sid: sessions[sid]["last_used"])
        del sessions[oldest]


def get_session(session_id, system_prompt):
    s = sessions.get(session_id)
    if s is None:
        _prune_sessions()
        if len(sessions) >= MAX_SESSIONS:
            oldest = min(sessions, key=lambda sid: sessions[sid]["last_used"])
            del sessions[oldest]
        s = {"messages": [{"role": "system", "content": system_prompt}], "last_used": _now()}
        sessions[session_id] = s
    s["last_used"] = _now()
    return s


def add_message(session, role, content):
    session["messages"].append({"role": role, "content": content})
    if len(session["messages"]) > MAX_HISTORY:
        session["messages"] = [session["messages"][0]] + session["messages"][-(MAX_HISTORY - 1):]


def model_context(session):
    return session["messages"][1:][-MODEL_CONTEXT_LIMIT:]