import logging
from contextlib import asynccontextmanager
from pathlib import Path
from time import perf_counter
from uuid import uuid4

import app.db.models
from dishka.integrations.fastapi import setup_dishka
from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.admin import setup_admin
from app.container import create_container
from app.core import BASE_DIR, settings
from app.db.database import SessionLocal
from app.logging_config import setup_logging
from app.routers.auth import router as auth_router
from app.routers.categories import router as categories_router
from app.routers.comments import router as comments_router
from app.routers.locations import router as locations_router
from app.routers.posts import router as posts_router
from app.routers.users import router as users_router
from app.routers.web import router as web_router
from app.routers.web_auth import router as web_auth_router
from app.security import decode_access_token_silent
from app.web.auth import get_current_web_user
from app.web.csrf import csrf_cookie_middleware
from app.web.templates import templates


setup_logging()
app_logger = logging.getLogger("app")
audit_logger = logging.getLogger("app.audit")


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    app.state.dishka_container.close()


app = FastAPI(
    title="Blogicum API",
    version="0.8.0",
    lifespan=lifespan,
)

app.middleware("http")(csrf_cookie_middleware)

static_root = BASE_DIR / "app" / "static"
if static_root.exists():
    app.mount("/static", StaticFiles(directory=static_root), name="static")

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
app.include_router(web_auth_router)
app.include_router(web_router)

setup_admin(app)
setup_dishka(container=create_container(), app=app)


@app.middleware("http")
async def log_user_actions(request: Request, call_next):
    started_at = perf_counter()
    status_code = 500
    username = "anonymous"
    user_id = "-"
    request_id = request.headers.get("X-Request-ID") or uuid4().hex
    request.state.request_id = request_id

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
        response.headers["X-Request-ID"] = request_id
        return response
    except Exception:
        app_logger.exception(
            "unhandled_request_error request_id=%s method=%s path=%s user_id=%s username=%s",
            request_id,
            request.method,
            request.url.path,
            user_id,
            username,
        )
        raise
    finally:
        duration_ms = (perf_counter() - started_at) * 1000
        client_ip = request.client.host if request.client else "-"
        audit_logger.info(
            "user_action request_id=%s method=%s path=%s status=%s user_id=%s username=%s client_ip=%s duration_ms=%.2f",
            request_id,
            request.method,
            request.url.path,
            status_code,
            user_id,
            username,
            client_ip,
            duration_ms,
        )


def _is_api_request(request: Request) -> bool:
    return request.url.path.startswith("/api/")


def _request_id(request: Request) -> str:
    return getattr(request.state, "request_id", "-")


@app.get("/api/v1/health", tags=["health"])
def health():
    return {"status": "ok"}


@app.exception_handler(RequestValidationError)
async def validation_error(request: Request, exc: RequestValidationError):
    app_logger.warning(
        "request_validation_error request_id=%s path=%s errors=%s",
        _request_id(request),
        request.url.path,
        exc.errors(),
    )
    return JSONResponse(
        status_code=422,
        content={
            "detail": exc.errors(),
            "request_id": _request_id(request),
        },
    )


@app.exception_handler(HTTPException)
async def http_error(request: Request, exc: HTTPException):
    if _is_api_request(request):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "detail": exc.detail,
                "request_id": _request_id(request),
            },
            headers=getattr(exc, "headers", None),
        )

    if exc.status_code == 404:
        template_name = "pages/404.html"
    elif exc.status_code == 403:
        template_name = "pages/403csrf.html"
    else:
        template_name = "pages/500.html"

    db = SessionLocal()
    try:
        user = get_current_web_user(request, db)
        return templates.TemplateResponse(
            request,
            template_name,
            {"user": user},
            status_code=exc.status_code,
        )
    finally:
        db.close()


@app.exception_handler(Exception)
async def server_error(request: Request, exc: Exception):
    app_logger.exception(
        "internal_server_error request_id=%s path=%s",
        _request_id(request),
        request.url.path,
    )

    if _is_api_request(request):
        return JSONResponse(
            status_code=500,
            content={
                "detail": "Internal server error",
                "request_id": _request_id(request),
            },
        )

    db = SessionLocal()
    try:
        user = get_current_web_user(request, db)
        return templates.TemplateResponse(
            request,
            "pages/500.html",
            {"user": user},
            status_code=500,
        )
    finally:
        db.close()
