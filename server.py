from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from pathlib import Path
import openai
import uvicorn
import uuid
import os
import re
import time
import logging

logger = logging.getLogger("madi")

app = FastAPI()

CORS_ORIGINS = [
    o.strip() for o in os.getenv("CORS_ORIGINS", "").split(",") if o.strip()
] or ["http://localhost:8000", "https://madi-parts.onrender.com"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# === ПЕРЕМЕННЫЕ ОКРУЖЕНИЯ ===
FOLDER_ID = os.getenv("FOLDER_ID")
API_KEY = os.getenv("API_KEY") 
MODEL = os.getenv("MODEL", "qwen3-235b-a22b-fp8/latest")

AI_ENABLED = bool(FOLDER_ID and API_KEY)

client = None
if AI_ENABLED:
    client = openai.OpenAI(
        api_key=API_KEY,
        base_url="https://rest-assistant.api.cloud.yandex.net/v1",
        project=FOLDER_ID,
    )

# === ХРАНИЛИЩЕ СЕССИЙ (in-memory, с лимитами) ===
sessions = {}
MAX_SESSIONS = 1000
MAX_HISTORY = 50
MODEL_CONTEXT_LIMIT = 20
SESSION_TTL = 24 * 60 * 60

SYSTEM_PROMPT = """
тебе будут поступать запросы по автозапчастям и в целом проблемам с автомобилями, твоя задача давать реальные заменители запчастей и в целом на любые вопросы отвечать как лучший эксперт в автомобильной сфере(используй все свои знания).  
также твоей задача - давать советы по удешевлению ремонта, и, если возможно решить проблему с применением работы своими руками, тоже давай информацию по этому поводу. используй свои знания по максимуму. 
ВАЖНО: НЕ ДАВАЙ КЛИКАБЕЛЬНЫЕ ССЫЛКИ В СВОЕМ ОТВЕТЕ, ДАВАЙ ТОЛЬКО ТЕКСТ, НЕ ВЫДУМЫВАЙ САМИ ИНТЕРНЕТ ССЫЛКИ. также постарайся если это возможно дать совет как решить проблему своими руками
ВАЖНО: Используй обычный текст без Markdown форматирования. Не используй **жирный**, *курсив*, ### заголовки, > цитаты, маркированные списки с -, *, •.
"""

def _now():
    return time.time()

def _prune_sessions():
    expired = [sid for sid, s in sessions.items() if _now() - s["last_used"] > SESSION_TTL]
    for sid in expired:
        del sessions[sid]
    while len(sessions) > MAX_SESSIONS:
        oldest = min(sessions, key=lambda sid: sessions[sid]["last_used"])
        del sessions[oldest]

def _get_session(session_id):
    s = sessions.get(session_id)
    if s is None:
        _prune_sessions()
        if len(sessions) >= MAX_SESSIONS:
            oldest = min(sessions, key=lambda sid: sessions[sid]["last_used"])
            del sessions[oldest]
        s = {"messages": [{"role": "system", "content": SYSTEM_PROMPT}], "last_used": _now()}
        sessions[session_id] = s
    s["last_used"] = _now()
    return s

def _add_message(session, role, content):
    session["messages"].append({"role": role, "content": content})
    if len(session["messages"]) > MAX_HISTORY:
        session["messages"] = [session["messages"][0]] + session["messages"][-(MAX_HISTORY - 1):]

def _model_context(session):
    return session["messages"][1:][-MODEL_CONTEXT_LIMIT:]

def clean_ai_response(text):
    """
    Очищает текст от форматирования Markdown, но сохраняет эмодзи
    """
    if not text:
        return ""
    
    # Удаляем маркеры форматирования Markdown
    text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)  # **жирный**
    text = re.sub(r'\*(.*?)\*', r'\1', text)      # *курсив*
    text = re.sub(r'_(.*?)_', r'\1', text)        # _курсив_
    text = re.sub(r'`(.*?)`', r'\1', text)        # `код`
    text = re.sub(r'~~(.*?)~~', r'\1', text)      # ~~зачеркнутый~~
    
    # Удаляем заголовки Markdown
    text = re.sub(r'^#+\s+', '', text, flags=re.MULTILINE)
    
    # Удаляем блоки цитат
    text = re.sub(r'^>\s+', '', text, flags=re.MULTILINE)
    
    # Заменяем маркированные списки на обычные строки
    text = re.sub(r'^[\s]*[-*•]\s+', '', text, flags=re.MULTILINE)
    text = re.sub(r'^[\s]*\d+\.\s+', '', text, flags=re.MULTILINE)
    
    # Удаляем лишние разделители (но оставляем обычные пунктуационные символы)
    text = re.sub(r'─{3,}', '', text)
    text = re.sub(r'═{3,}', '', text)
    text = re.sub(r'─{2,}', '', text)
    
    # Убираем лишние пробелы и переносы (но сохраняем структуру абзацев)
    text = re.sub(r'\n\s*\n\s*\n', '\n\n', text)
    text = re.sub(r'[ \t]+', ' ', text)
    
    # Обрезаем пробелы в начале и конце
    text = text.strip()
    
    return text

# Serve frontend
current_dir = Path(__file__).parent

@app.get("/")
async def serve_frontend():
    return FileResponse(current_dir / "MADIPARTS.html")

# Health check
@app.get("/health")
async def health_check():
    return {"status": "healthy", "model": MODEL, "ai_enabled": AI_ENABLED}

# Chat endpoint
@app.post("/chat")
async def chat(request: Request):
    if not AI_ENABLED:
        return JSONResponse(status_code=503, content={"error": "AI is not configured on the server"})

    try:
        data = await request.json()
        message = data.get("message", "").strip()
        session_id = data.get("session_id") or str(uuid.uuid4())

        if not message:
            return JSONResponse(status_code=400, content={"error": "empty message"})

        if len(message) > 4000:
            return JSONResponse(status_code=400, content={"error": "message too long"})

        session = _get_session(session_id)
        _add_message(session, "user", message)

        response = client.responses.create(
            model=f"gpt://{FOLDER_ID}/{MODEL}",
            temperature=0.6,
            max_output_tokens=2500,
            instructions=SYSTEM_PROMPT,
            input=_model_context(session)
        )

        reply = response.output_text.strip()
        cleaned_reply = clean_ai_response(reply)
        _add_message(session, "assistant", cleaned_reply)

        return {"reply": cleaned_reply, "session_id": session_id}

    except Exception:
        logger.exception("Chat error")
        return JSONResponse(status_code=500, content={"error": "internal server error"})

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")

