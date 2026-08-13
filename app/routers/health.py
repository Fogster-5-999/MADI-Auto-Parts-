from fastapi import APIRouter

from app import config

router = APIRouter()


@router.get("/health")
async def health_check():
    return {"status": "healthy", "model": config.MODEL, "ai_enabled": config.AI_ENABLED}