import logging
from pathlib import Path
from time import perf_counter

import app.db.models
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles

from app.core import BASE_DIR, settings
from app.logging_config import setup_logging
from app.routers.auth import router as auth_router
from app.routers.users import router as users_router
from app.routers.categories import router as categories_router
from app.routers.locations import router as locations_router
from app.routers.posts import router as posts_router
from app.routers.comments import router as comments_router
from app.security import decode_access_token_silent

setup_logging()
audit_logger = logging.getLogger("app.audit")

app = FastAPI(title="Blogicum API", version="0.6.0")

media_root = Path(settings.media_root)
if not media_root.is_absolute():
    media_root = BASE_DIR / media_root
media_root.mkdir(parents=True, exist_ok=True)
app.mount(settings.media_url, StaticFiles(directory=media_root), name="media")

app.include_router(auth_router, prefix="/api/v1")
app.include_router(users_router, prefix="/api/v1")
app.include_router(categories_router, prefix="/api/v1")
app.include_router(locations_router, prefix="/api/v1")
app.include_router(posts_router, prefix="/api/v1")
app.include_router(comments_router, prefix="/api/v1")


@app.middleware("http")
async def log_user_actions(request: Request, call_next):
    started_at = perf_counter()
    status_code = 500
    username = "anonymous"
    user_id = "-"

    authorization = request.headers.get("Authorization", "")
    if authorization.startswith("Bearer "):
        token = authorization.split(" ", 1)[1]
        payload = decode_access_token_silent(token)
        if payload:
            username = str(payload.get("username", "anonymous"))
            user_id = str(payload.get("sub", "-"))

    try:
        response = await call_next(request)
        status_code = response.status_code
        return response
    finally:
        duration_ms = (perf_counter() - started_at) * 1000
        client_ip = request.client.host if request.client else "-"
        audit_logger.info(
            "user_action method=%s path=%s status=%s user_id=%s username=%s client_ip=%s duration_ms=%.2f",
            request.method,
            request.url.path,
            status_code,
            user_id,
            username,
            client_ip,
            duration_ms,
        )


@app.get("/api/v1/health", tags=["health"])
def health():
    return {"status": "ok"}
