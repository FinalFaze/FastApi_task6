from fastapi import Request
from sqlalchemy.orm import Session

from app.domain.errors import DomainError
from app.domain.use_cases.auth import AuthUseCase
from app.repositories.user import UserRepository


COOKIE_NAME = "access_token"


def get_current_web_user(request: Request, db: Session):
    token = request.cookies.get(COOKIE_NAME)
    if not token:
        return None

    try:
        return AuthUseCase(UserRepository(db)).get_current_user(token)
    except DomainError:
        return None
