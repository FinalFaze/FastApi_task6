import logging

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.domain.errors import DomainError
from app.domain.use_cases.auth import AuthUseCase
from app.repositories.user import UserRepository
from app.routers.dependencies import get_current_user
from app.routers.utils import raise_http_error
from app.schemas.auth import LoginRequest, TokenOut
from app.schemas.blog import UserOut

router = APIRouter(prefix="/auth", tags=["auth"])
logger = logging.getLogger("app.audit")


@router.post("/login", response_model=TokenOut)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    try:
        token = AuthUseCase(UserRepository(db)).login(
            payload.username,
            payload.password,
        )
        logger.info("login_success username=%s", payload.username)
        return TokenOut(access_token=token)
    except DomainError as exc:
        logger.warning(
            "login_failed username=%s status=%s",
            payload.username,
            exc.status_code,
        )
        raise_http_error(exc)


@router.get("/me", response_model=UserOut)
def me(current_user=Depends(get_current_user)):
    return current_user
