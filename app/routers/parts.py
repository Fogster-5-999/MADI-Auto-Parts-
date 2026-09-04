import logging
from typing import Optional

import httpx
from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse

from app import config

logger = logging.getLogger("madi")

router = APIRouter(prefix="/api/parts")

UMAPI_BASE = "https://api.umapi.ru/v2/autocatalog"

ALLOWED_ENDPOINTS = {
    "Manufacturers",
    "ModelSeries",
    "Passangers",
    "Categories",
    "Products",
    "Articles",
}


def _build_url(lang: str, region: str, endpoint: str, params: dict) -> str:
    path = f"{lang}-{region}/{endpoint}"
    url = f"{UMAPI_BASE}/{path}"
    if params:
        query = "&".join(f"{k}={v}" for k, v in params.items() if v is not None)
        url = f"{url}?{query}"
    return url


async def _proxy_get(url: str) -> dict:
    headers = {"X-App-Key": config.UMAPI_KEY}
    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.get(url, headers=headers)
        resp.raise_for_status()
        return resp.json()


def _error(msg: str, status: int = 400):
    return JSONResponse(status_code=status, content={"error": msg})


@router.get("/{lang}/{region}/{endpoint}")
async def proxy_parts(
    lang: str,
    region: str,
    endpoint: str,
    type: Optional[str] = Query(None),
    popular: Optional[str] = Query(None),
    fields: Optional[str] = Query(None),
    mfa_id: Optional[str] = Query(None),
    ms_id: Optional[str] = Query(None),
    id: Optional[str] = Query(None, alias="ID"),
    engines: Optional[str] = Query(None),
    category_id: Optional[str] = Query(None, alias="CATEGORY_ID"),
    pt_ids: Optional[str] = Query(None, alias="PT_IDS"),
    medias: Optional[str] = Query(None),
    limit: Optional[str] = Query(None),
):
    if endpoint not in ALLOWED_ENDPOINTS:
        return _error(f"unknown endpoint: {endpoint}", 404)

    if not config.UMAPI_KEY:
        return _error("UMAPI key not configured", 503)

    params = {
        "type": type,
        "popular": popular,
        "fields": fields,
        "MFA_ID": mfa_id,
        "MS_ID": ms_id,
        "ID": id,
        "Engines": engines,
        "CATEGORY_ID": category_id,
        "PT_IDS": pt_ids,
        "Medias": medias,
        "limit": limit,
    }

    url = _build_url(lang, region, endpoint, params)
    logger.info("proxy: %s", url)

    try:
        return await _proxy_get(url)
    except httpx.HTTPStatusError as e:
        logger.error("UMAPI %d: %s", e.response.status_code, url)
        return _error(f"upstream error: {e.response.status_code}", e.response.status_code)
    except Exception:
        logger.exception("proxy error: %s", url)
        return _error("proxy error", 502)
