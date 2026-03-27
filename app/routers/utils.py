from fastapi import HTTPException

from app.domain.errors import DomainError


def raise_http_error(exc: DomainError) -> None:
    headers = {"WWW-Authenticate": "Bearer"} if exc.status_code == 401 else None
    raise HTTPException(
        status_code=exc.status_code,
        detail=exc.to_dict(),
        headers=headers,
    )
