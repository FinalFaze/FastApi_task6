from secrets import compare_digest, token_urlsafe

from fastapi import HTTPException, Request
from markupsafe import Markup


CSRF_COOKIE_NAME = "csrftoken"
CSRF_FIELD_NAME = "csrf_token"
SAFE_METHODS = {"GET", "HEAD", "OPTIONS", "TRACE"}


def generate_csrf_token() -> str:
    return token_urlsafe(32)


def get_csrf_token(request: Request) -> str:
    token = request.cookies.get(CSRF_COOKIE_NAME)

    if not token:
        token = getattr(request.state, "csrf_token", None)

    if not token:
        token = generate_csrf_token()

    request.state.csrf_token = token
    return token


def csrf_input(request: Request) -> Markup:
    token = get_csrf_token(request)
    return Markup(
        f'<input type="hidden" name="{CSRF_FIELD_NAME}" value="{token}">'
    )


async def validate_csrf(request: Request) -> None:
    if request.method in SAFE_METHODS:
        return

    form = await request.form()
    cookie_token = request.cookies.get(CSRF_COOKIE_NAME)
    form_token = form.get(CSRF_FIELD_NAME)

    if not cookie_token or not form_token:
        raise HTTPException(status_code=403, detail="CSRF token missing")

    if not compare_digest(str(cookie_token), str(form_token)):
        raise HTTPException(status_code=403, detail="CSRF token invalid")


async def csrf_cookie_middleware(request: Request, call_next):
    response = await call_next(request)
    token = getattr(request.state, "csrf_token", None)

    if token and request.cookies.get(CSRF_COOKIE_NAME) != token:
        response.set_cookie(
            key=CSRF_COOKIE_NAME,
            value=token,
            httponly=True,
            samesite="lax",
        )

    return response
