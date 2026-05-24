import logging

from dishka.integrations.fastapi import DishkaSyncRoute, FromDishka
from fastapi import APIRouter, Depends

from app.domain.errors import DomainError
from app.domain.use_cases.auth import AuthUseCase
from app.routers.dependencies import get_current_user
from app.routers.utils import raise_http_error
from app.schemas.auth import AccessTokenOut, LoginRequest, RefreshTokenRequest, TokenOut
from app.schemas.blog import UserOut
from app.security import get_access_token_expire_seconds

router = APIRouter(prefix="/auth", tags=["auth"], route_class=DishkaSyncRoute)
logger = logging.getLogger("app.audit")


@router.post("/login", response_model=TokenOut)
def login(payload: LoginRequest, auth_use_case: FromDishka[AuthUseCase]):
    try:
        token_pair = auth_use_case.login(
            payload.username,
            payload.password,
        )
        logger.info(
            "login_success username=%s expires_in_seconds=%s refresh_expires_in_seconds=%s",
            payload.username,
            token_pair.expires_in,
            token_pair.refresh_expires_in,
        )
        return TokenOut(
            access_token=token_pair.access_token,
            refresh_token=token_pair.refresh_token,
            expires_in=token_pair.expires_in,
            refresh_expires_in=token_pair.refresh_expires_in,
        )
    except DomainError as exc:
        logger.warning(
            "login_failed username=%s status=%s",
            payload.username,
            exc.status_code,
        )
        raise_http_error(exc)


@router.post("/refresh", response_model=AccessTokenOut)
def refresh_access_token(
    payload: RefreshTokenRequest,
    auth_use_case: FromDishka[AuthUseCase],
):
    try:
        access_token = auth_use_case.refresh_access_token(payload.refresh_token)
        logger.info("refresh_token_success expires_in_seconds=%s", get_access_token_expire_seconds())
        return AccessTokenOut(
            access_token=access_token,
            expires_in=get_access_token_expire_seconds(),
        )
    except DomainError as exc:
        logger.warning("refresh_token_failed status=%s", exc.status_code)
        raise_http_error(exc)


@router.get("/me", response_model=UserOut)
def me(current_user=Depends(get_current_user)):
    return current_user
