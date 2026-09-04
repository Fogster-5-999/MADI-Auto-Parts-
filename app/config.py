import os

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
UMAPI_KEY = os.getenv("UMAPI_KEY")
MODEL = os.getenv("MODEL", "qwen/qwen3-235b:free")

AI_ENABLED = bool(OPENROUTER_API_KEY)

CORS_ORIGINS = [
    o.strip() for o in os.getenv("CORS_ORIGINS", "").split(",") if o.strip()
] or ["http://localhost:8000", "https://madi-parts.onrender.com"]