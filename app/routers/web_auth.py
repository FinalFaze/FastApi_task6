from urllib.parse import quote

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import User
from app.domain.errors import DomainError
from app.domain.use_cases.auth import AuthUseCase
from app.domain.use_cases.blog import UserUseCase
from app.repositories.user import UserRepository
from app.security import (
    create_password_reset_token,
    decode_password_reset_token,
    get_access_token_expire_seconds,
    get_password_reset_token_expire_minutes,
    verify_password,
)
from app.web.auth import COOKIE_NAME, get_current_web_user
from app.web.csrf import validate_csrf
from app.web.templates import templates


router = APIRouter(
    prefix="/auth",
    tags=["web-auth"],
    dependencies=[Depends(validate_csrf)],
)


def _redirect(url: str) -> RedirectResponse:
    return RedirectResponse(url=url, status_code=303)


def _login_redirect(request: Request) -> RedirectResponse:
    next_url = quote(request.url.path)
    return _redirect(f"/auth/login/?next={next_url}")


def _set_auth_cookie(response: RedirectResponse, token: str) -> RedirectResponse:
    response.set_cookie(
        key=COOKIE_NAME,
        value=token,
        max_age=get_access_token_expire_seconds(),
        httponly=True,
        samesite="lax",
    )
    return response


def _delete_auth_cookie(response):
    response.delete_cookie(COOKIE_NAME)
    return response


def _render_login(
    request: Request,
    user,
    error: str | None = None,
    username: str = "",
    next_url: str = "",
):
    return templates.TemplateResponse(
        request,
        "registration/login.html",
        {
            "user": user,
            "error": error,
            "values": {
                "username": username,
            },
            "next": next_url,
        },
    )


def _render_registration(
    request: Request,
    user,
    error: str | None = None,
    values: dict | None = None,
):
    return templates.TemplateResponse(
        request,
        "registration/registration_form.html",
        {
            "user": user,
            "error": error,
            "values": values or {},
        },
    )


def _find_user_for_reset(db: Session, username_or_email: str) -> User | None:
    value = username_or_email.strip()
    lowered = value.lower()

    if not value:
        return None

    return (
        db.query(User)
        .filter(
            User.is_active.is_(True),
            or_(
                User.username == value,
                User.email == lowered,
            ),
        )
        .first()
    )


def _render_password_reset_form(
    request: Request,
    user,
    error: str | None = None,
    username_or_email: str = "",
):
    return templates.TemplateResponse(
        request,
        "registration/password_reset_form.html",
        {
            "user": user,
            "error": error,
            "values": {
                "username_or_email": username_or_email,
            },
        },
    )


def _make_reset_links(request: Request, orm_user: User) -> tuple[str, str]:
    token = create_password_reset_token(orm_user.id, orm_user.username)
    reset_path = f"/auth/reset/{orm_user.id}/{token}/"
    reset_link = str(request.base_url).rstrip("/") + reset_path
    return reset_path, reset_link


@router.get("/login/")
def login_page(
    request: Request,
    next: str = "",
    db: Session = Depends(get_db),
):
    user = get_current_web_user(request, db)

    if user:
        return _redirect(next or "/")

    return _render_login(
        request=request,
        user=user,
        next_url=next,
    )


@router.post("/login/")
def login_action(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    next: str = Form(""),
    db: Session = Depends(get_db),
):
    username = username.strip()

    try:
        token = AuthUseCase(UserRepository(db)).login(username, password)
    except DomainError:
        return _render_login(
            request=request,
            user=None,
            error="Неверное имя пользователя или пароль.",
            username=username,
            next_url=next,
        )

    response = _redirect(next or "/")
    return _set_auth_cookie(response, token)


@router.get("/logout/")
def logout_page(request: Request):
    response = templates.TemplateResponse(
        request,
        "registration/logged_out.html",
        {
            "user": None,
        },
    )
    return _delete_auth_cookie(response)


@router.get("/registration/")
def registration_page(request: Request, db: Session = Depends(get_db)):
    user = get_current_web_user(request, db)

    if user:
        return _redirect("/")

    return _render_registration(
        request=request,
        user=user,
    )


@router.post("/registration/")
def registration_action(
    request: Request,
    username: str = Form(...),
    first_name: str = Form(""),
    last_name: str = Form(""),
    email: str = Form(""),
    password1: str = Form(...),
    password2: str = Form(...),
    db: Session = Depends(get_db),
):
    username = username.strip()
    first_name = first_name.strip()
    last_name = last_name.strip()
    email = email.strip().lower()

    values = {
        "username": username,
        "first_name": first_name,
        "last_name": last_name,
        "email": email,
    }

    if not username:
        return _render_registration(
            request=request,
            user=None,
            error="Имя пользователя не может быть пустым.",
            values=values,
        )

    if " " in username:
        return _render_registration(
            request=request,
            user=None,
            error="Имя пользователя не должно содержать пробелы.",
            values=values,
        )

    if password1 != password2:
        return _render_registration(
            request=request,
            user=None,
            error="Пароли не совпадают.",
            values=values,
        )

    if len(password1) < 8:
        return _render_registration(
            request=request,
            user=None,
            error="Пароль должен быть не короче 8 символов.",
            values=values,
        )

    payload = {
        "username": username,
        "password": password1,
        "first_name": first_name,
        "last_name": last_name,
        "email": email,
        "is_staff": False,
        "is_active": True,
        "is_superuser": False,
    }

    try:
        UserUseCase(UserRepository(db)).create(payload)
        token = AuthUseCase(UserRepository(db)).login(username, password1)
    except DomainError:
        return _render_registration(
            request=request,
            user=None,
            error="Пользователь с таким именем уже существует или данные заполнены неверно.",
            values=values,
        )

    response = _redirect(f"/profile/{username}/")
    return _set_auth_cookie(response, token)


@router.get("/password_change/")
def password_change_page(request: Request, db: Session = Depends(get_db)):
    user = get_current_web_user(request, db)

    if user is None:
        return _login_redirect(request)

    return templates.TemplateResponse(
        request,
        "registration/password_change_form.html",
        {
            "user": user,
        },
    )


@router.post("/password_change/")
def password_change_action(
    request: Request,
    old_password: str = Form(...),
    new_password1: str = Form(...),
    new_password2: str = Form(...),
    db: Session = Depends(get_db),
):
    user = get_current_web_user(request, db)

    if user is None:
        return _login_redirect(request)

    if not verify_password(old_password, user.password):
        return templates.TemplateResponse(
            request,
            "registration/password_change_form.html",
            {
                "user": user,
                "error": "Старый пароль указан неверно.",
            },
        )

    if new_password1 != new_password2:
        return templates.TemplateResponse(
            request,
            "registration/password_change_form.html",
            {
                "user": user,
                "error": "Новые пароли не совпадают.",
            },
        )

    if len(new_password1) < 8:
        return templates.TemplateResponse(
            request,
            "registration/password_change_form.html",
            {
                "user": user,
                "error": "Новый пароль должен быть не короче 8 символов.",
            },
        )

    try:
        UserUseCase(UserRepository(db)).update(
            user.id,
            {
                "password": new_password1,
            },
        )
    except DomainError:
        return templates.TemplateResponse(
            request,
            "registration/password_change_form.html",
            {
                "user": user,
                "error": "Не удалось изменить пароль.",
            },
        )

    return _redirect("/auth/password_change/done/")


@router.get("/password_change/done/")
def password_change_done(request: Request, db: Session = Depends(get_db)):
    user = get_current_web_user(request, db)

    if user is None:
        return _login_redirect(request)

    return templates.TemplateResponse(
        request,
        "registration/password_change_done.html",
        {
            "user": user,
        },
    )


@router.get("/password_reset/")
def password_reset_page(request: Request, db: Session = Depends(get_db)):
    user = get_current_web_user(request, db)

    return _render_password_reset_form(
        request=request,
        user=user,
    )


@router.post("/password_reset/")
def password_reset_action(
    request: Request,
    username_or_email: str = Form(...),
    db: Session = Depends(get_db),
):
    user = get_current_web_user(request, db)
    username_or_email = username_or_email.strip()
    orm_user = _find_user_for_reset(db, username_or_email)

    if orm_user is None:
        return _render_password_reset_form(
            request=request,
            user=user,
            error="Пользователь с таким username или email не найден.",
            username_or_email=username_or_email,
        )

    reset_path, reset_link = _make_reset_links(request, orm_user)

    return templates.TemplateResponse(
        request,
        "registration/password_reset_done.html",
        {
            "user": user,
            "reset_path": reset_path,
            "reset_link": reset_link,
            "reset_username": orm_user.username,
            "expire_minutes": get_password_reset_token_expire_minutes(),
        },
    )


@router.get("/password_reset/done/")
def password_reset_done(request: Request, db: Session = Depends(get_db)):
    user = get_current_web_user(request, db)

    return templates.TemplateResponse(
        request,
        "registration/password_reset_done.html",
        {
            "user": user,
            "reset_path": None,
            "reset_link": None,
            "reset_username": None,
            "expire_minutes": get_password_reset_token_expire_minutes(),
        },
    )


@router.get("/reset/{uid}/{token}/")
def password_reset_confirm_page(
    uid: int,
    token: str,
    request: Request,
    db: Session = Depends(get_db),
):
    user = get_current_web_user(request, db)

    try:
        payload = decode_password_reset_token(token)
        token_user_id = int(payload.get("sub"))
        token_username = payload.get("username")
    except (DomainError, TypeError, ValueError):
        return templates.TemplateResponse(
            request,
            "registration/password_reset_confirm.html",
            {
                "user": user,
                "validlink": False,
                "error": "Ссылка восстановления недействительна или устарела.",
            },
            status_code=400,
        )

    orm_user = db.get(User, uid)

    if orm_user is None or orm_user.id != token_user_id or orm_user.username != token_username:
        return templates.TemplateResponse(
            request,
            "registration/password_reset_confirm.html",
            {
                "user": user,
                "validlink": False,
                "error": "Ссылка восстановления недействительна или устарела.",
            },
            status_code=400,
        )

    return templates.TemplateResponse(
        request,
        "registration/password_reset_confirm.html",
        {
            "user": user,
            "validlink": True,
            "reset_username": orm_user.username,
        },
    )


@router.post("/reset/{uid}/{token}/")
def password_reset_confirm_action(
    uid: int,
    token: str,
    request: Request,
    new_password1: str = Form(...),
    new_password2: str = Form(...),
    db: Session = Depends(get_db),
):
    current_user = get_current_web_user(request, db)

    try:
        payload = decode_password_reset_token(token)
        token_user_id = int(payload.get("sub"))
        token_username = payload.get("username")
    except (DomainError, TypeError, ValueError):
        return templates.TemplateResponse(
            request,
            "registration/password_reset_confirm.html",
            {
                "user": current_user,
                "validlink": False,
                "error": "Ссылка восстановления недействительна или устарела.",
            },
            status_code=400,
        )

    orm_user = db.get(User, uid)

    if orm_user is None or orm_user.id != token_user_id or orm_user.username != token_username:
        return templates.TemplateResponse(
            request,
            "registration/password_reset_confirm.html",
            {
                "user": current_user,
                "validlink": False,
                "error": "Ссылка восстановления недействительна или устарела.",
            },
            status_code=400,
        )

    if new_password1 != new_password2:
        return templates.TemplateResponse(
            request,
            "registration/password_reset_confirm.html",
            {
                "user": current_user,
                "validlink": True,
                "reset_username": orm_user.username,
                "error": "Пароли не совпадают.",
            },
        )

    if len(new_password1) < 8:
        return templates.TemplateResponse(
            request,
            "registration/password_reset_confirm.html",
            {
                "user": current_user,
                "validlink": True,
                "reset_username": orm_user.username,
                "error": "Пароль должен быть не короче 8 символов.",
            },
        )

    try:
        UserUseCase(UserRepository(db)).update(
            orm_user.id,
            {
                "password": new_password1,
            },
        )
    except DomainError:
        return templates.TemplateResponse(
            request,
            "registration/password_reset_confirm.html",
            {
                "user": current_user,
                "validlink": True,
                "reset_username": orm_user.username,
                "error": "Не удалось изменить пароль.",
            },
        )

    response = _redirect("/auth/reset/done/")
    return _delete_auth_cookie(response)


@router.get("/reset/done/")
def password_reset_complete(request: Request, db: Session = Depends(get_db)):
    user = get_current_web_user(request, db)

    return templates.TemplateResponse(
        request,
        "registration/password_reset_complete.html",
        {
            "user": user,
        },
    )
