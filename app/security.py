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


def create_access_token(user_id: int, username: str) -> str:
    now = datetime.now(timezone.utc)
    expire_at = now + timedelta(minutes=settings.jwt_access_token_expire_minutes)

    payload = {
        "sub": str(user_id),
        "username": username,
        "purpose": "access",
        "iat": now,
        "exp": expire_at,
    }

    return jwt.encode(
        payload,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )


def decode_access_token(token: str) -> dict:
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )
    except InvalidTokenError as exc:
        raise DomainUnauthorizedError(
            message="Invalid or expired access token",
            entity="Auth",
            operation="decode_token",
            details={},
        ) from exc

    purpose = payload.get("purpose", "access")
    if purpose != "access":
        raise DomainUnauthorizedError(
            message="Invalid access token purpose",
            entity="Auth",
            operation="decode_token",
            details={},
        )

    return payload


def decode_access_token_silent(token: str) -> dict | None:
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )
    except InvalidTokenError:
        return None

    purpose = payload.get("purpose", "access")
    if purpose != "access":
        return None

    return payload


def get_password_reset_token_expire_minutes() -> int:
    return PASSWORD_RESET_TOKEN_EXPIRE_MINUTES


def create_password_reset_token(user_id: int, username: str) -> str:
    now = datetime.now(timezone.utc)
    expire_at = now + timedelta(minutes=PASSWORD_RESET_TOKEN_EXPIRE_MINUTES)

    payload = {
        "sub": str(user_id),
        "username": username,
        "purpose": "password_reset",
        "iat": now,
        "exp": expire_at,
    }

    return jwt.encode(
        payload,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )


def decode_password_reset_token(token: str) -> dict:
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )
    except InvalidTokenError as exc:
        raise DomainUnauthorizedError(
            message="Invalid or expired password reset token",
            entity="Auth",
            operation="decode_password_reset_token",
            details={},
        ) from exc

    if payload.get("purpose") != "password_reset":
        raise DomainUnauthorizedError(
            message="Invalid password reset token purpose",
            entity="Auth",
            operation="decode_password_reset_token",
            details={},
        )

    return payload
