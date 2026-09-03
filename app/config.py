import os

FOLDER_ID = os.getenv("FOLDER_ID")
API_KEY = os.getenv("API_KEY")
UMAPI_KEY = os.getenv("UMAPI_KEY")
MODEL = os.getenv("MODEL", "qwen3-235b-a22b-fp8/latest")

AI_ENABLED = bool(FOLDER_ID and API_KEY)

CORS_ORIGINS = [
    o.strip() for o in os.getenv("CORS_ORIGINS", "").split(",") if o.strip()
] or ["http://localhost:8000", "https://madi-parts.onrender.com"]