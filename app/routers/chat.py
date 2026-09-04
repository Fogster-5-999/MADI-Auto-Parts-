import logging
import uuid

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from app import config
from app.sessions import add_message, get_session, model_context
from app.services import ai
from app.text import clean_ai_response

logger = logging.getLogger("madi")

router = APIRouter()


@router.post("/chat")
async def chat(request: Request):
    if not config.AI_ENABLED or ai.client is None:
        return JSONResponse(status_code=503, content={"error": "AI is not configured on the server"})

    try:
        data = await request.json()
        message = data.get("message", "").strip()
        session_id = data.get("session_id") or str(uuid.uuid4())

        if not message:
            return JSONResponse(status_code=400, content={"error": "empty message"})

        if len(message) > 4000:
            return JSONResponse(status_code=400, content={"error": "message too long"})

        session = get_session(session_id, ai.SYSTEM_PROMPT)
        add_message(session, "user", message)

        response = ai.client.chat.completions.create(
            model=config.MODEL,
            temperature=0.6,
            max_tokens=2500,
            messages=model_context(session),
        )

        reply = response.choices[0].message.content.strip()
        cleaned_reply = clean_ai_response(reply)
        add_message(session, "assistant", cleaned_reply)

        return {"reply": cleaned_reply, "session_id": session_id}

    except Exception:
        logger.exception("Chat error")
        return JSONResponse(status_code=500, content={"error": "internal server error"})