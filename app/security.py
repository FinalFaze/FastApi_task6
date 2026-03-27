from base64 import b64encode
from datetime import datetime, timedelta, timezone
from hashlib import pbkdf2_hmac
from hmac import compare_digest
from secrets import token_urlsafe

import jwt
from jwt import InvalidTokenError

from app.core import settings
from app.domain.errors import DomainUnauthorizedError


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


def create_access_token(user_id: int, username: str) -> str:
    expire_at = datetime.now(timezone.utc) + timedelta(
        minutes=settings.jwt_access_token_expire_minutes,
    )
    payload = {
        "sub": str(user_id),
        "username": username,
        "exp": expire_at,
    }
    return jwt.encode(
        payload,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )


def decode_access_token(token: str) -> dict:
    try:
        return jwt.decode(
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


def decode_access_token_silent(token: str) -> dict | None:
    try:
        return jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )
    except InvalidTokenError:
        return None
