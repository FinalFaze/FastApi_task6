from base64 import b64encode
from datetime import datetime, timedelta, timezone
from hashlib import pbkdf2_hmac
from hmac import compare_digest
from secrets import token_urlsafe

import jwt
from jwt import InvalidTokenError

from app.core import settings
from app.domain.errors import DomainUnauthorizedError


PASSWORD_RESET_TOKEN_EXPIRE_MINUTES = 30


def _encode_django_pbkdf2(password: str, salt: str, iterations: int) -> str:
    digest = pbkdf2_hmac(
        "sha256",
        password.encode(),
        salt.encode(),
        iterations,
    )
    return b64encode(digest).decode().strip()


def hash_password(password: str) -> str:
    salt = token_urlsafe(12)
    iterations = 1200000
    encoded = _encode_django_pbkdf2(password, salt, iterations)
    return f"pbkdf2_sha256${iterations}${salt}${encoded}"


def verify_password(password: str, stored_password: str) -> bool:
    if stored_password.startswith("pbkdf2_sha256$"):
        try:
            _, iterations, salt, encoded_hash = stored_password.split("$", 3)
            calculated_hash = _encode_django_pbkdf2(password, salt, int(iterations))
            return compare_digest(calculated_hash, encoded_hash)
        except ValueError:
            return False

    return compare_digest(password, stored_password)


def get_access_token_expire_seconds() -> int:
    return settings.jwt_access_token_expire_minutes * 60


def get_refresh_token_expire_seconds() -> int:
    return settings.jwt_refresh_token_expire_days * 24 * 60 * 60


def _create_jwt_token(user_id: int, username: str, purpose: str, expires_delta: timedelta) -> str:
    now = datetime.now(timezone.utc)
    expire_at = now + expires_delta
    payload = {
        "sub": str(user_id),
        "username": username,
        "purpose": purpose,
        "iat": now,
        "exp": expire_at,
    }
    return jwt.encode(
        payload,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )


def create_access_token(user_id: int, username: str) -> str:
    return _create_jwt_token(
        user_id=user_id,
        username=username,
        purpose="access",
        expires_delta=timedelta(minutes=settings.jwt_access_token_expire_minutes),
    )


def create_refresh_token(user_id: int, username: str) -> str:
    return _create_jwt_token(
        user_id=user_id,
        username=username,
        purpose="refresh",
        expires_delta=timedelta(days=settings.jwt_refresh_token_expire_days),
    )


def _decode_token(token: str, purpose: str, operation: str) -> dict:
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )
    except InvalidTokenError as exc:
        raise DomainUnauthorizedError(
            message=f"Invalid or expired {purpose} token",
            entity="Auth",
            operation=operation,
            details={},
        ) from exc

    if payload.get("purpose") != purpose:
        raise DomainUnauthorizedError(
            message=f"Invalid {purpose} token purpose",
            entity="Auth",
            operation=operation,
            details={},
        )

    return payload


def decode_access_token(token: str) -> dict:
    return _decode_token(token, "access", "decode_access_token")


def decode_refresh_token(token: str) -> dict:
    return _decode_token(token, "refresh", "decode_refresh_token")


def decode_access_token_silent(token: str) -> dict | None:
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )
    except InvalidTokenError:
        return None

    if payload.get("purpose") != "access":
        return None

    return payload


def get_password_reset_token_expire_minutes() -> int:
    return PASSWORD_RESET_TOKEN_EXPIRE_MINUTES


def create_password_reset_token(user_id: int, username: str) -> str:
    return _create_jwt_token(
        user_id=user_id,
        username=username,
        purpose="password_reset",
        expires_delta=timedelta(minutes=PASSWORD_RESET_TOKEN_EXPIRE_MINUTES),
    )


def decode_password_reset_token(token: str) -> dict:
    return _decode_token(token, "password_reset", "decode_password_reset_token")
