from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.domain.errors import DomainError, DomainUnauthorizedError
from app.domain.use_cases.auth import AuthUseCase
from app.repositories.user import UserRepository
from app.routers.utils import raise_http_error

bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
):
    if credentials is None:
        raise_http_error(
            DomainUnauthorizedError(
                message="Authentication credentials were not provided",
                entity="Auth",
                operation="get_current_user",
                details={},
            )
        )

    if credentials.scheme.lower() != "bearer":
        raise_http_error(
            DomainUnauthorizedError(
                message="Invalid authentication scheme",
                entity="Auth",
                operation="get_current_user",
                details={},
            )
        )

    try:
        return AuthUseCase(UserRepository(db)).get_current_user(credentials.credentials)
    except DomainError as exc:
        raise_http_error(exc)
