from app.domain.entities import UserEntity
from app.domain.errors import DomainDatabaseError, DomainUnauthorizedError
from app.domain.ports import UserRepositoryPort
from app.errors import InfrastructureDatabaseError, InfrastructureError, InfrastructureNotFoundError
from app.security import create_access_token, decode_access_token, verify_password


class AuthUseCase:
    def __init__(self, repository: UserRepositoryPort):
        self.repository = repository

    def login(self, username: str, password: str) -> str:
        try:
            user = self.repository.find_by_username(username)
        except InfrastructureDatabaseError as exc:
            raise DomainDatabaseError(
                message="Database error while authenticating user",
                entity="Auth",
                operation="login",
                details={"username": username, **exc.details},
            ) from exc

        if user is None or not user.is_active:
            raise DomainUnauthorizedError(
                message="Invalid username or password",
                entity="Auth",
                operation="login",
                details={"username": username},
            )

        if not verify_password(password, user.password):
            raise DomainUnauthorizedError(
                message="Invalid username or password",
                entity="Auth",
                operation="login",
                details={"username": username},
            )

        try:
            self.repository.touch_last_login(user.id)
        except InfrastructureDatabaseError as exc:
            raise DomainDatabaseError(
                message="Database error while updating user login time",
                entity="Auth",
                operation="login",
                details={"id": user.id, **exc.details},
            ) from exc

        return create_access_token(user.id, user.username)

    def get_current_user(self, token: str) -> UserEntity:
        payload = decode_access_token(token)
        subject = payload.get("sub")
        username = payload.get("username")

        try:
            user_id = int(subject)
        except (TypeError, ValueError) as exc:
            raise DomainUnauthorizedError(
                message="Invalid access token subject",
                entity="Auth",
                operation="get_current_user",
                details={},
            ) from exc

        try:
            user = self.repository.get(user_id)
        except InfrastructureNotFoundError as exc:
            raise DomainUnauthorizedError(
                message="User from token was not found",
                entity="Auth",
                operation="get_current_user",
                details={"id": user_id},
            ) from exc
        except InfrastructureError as exc:
            raise DomainDatabaseError(
                message="Database error while loading current user",
                entity="Auth",
                operation="get_current_user",
                details={"id": user_id, **exc.details},
            ) from exc

        if not user.is_active:
            raise DomainUnauthorizedError(
                message="Inactive user is not allowed",
                entity="Auth",
                operation="get_current_user",
                details={"id": user.id},
            )

        if username != user.username:
            raise DomainUnauthorizedError(
                message="Access token does not match the user",
                entity="Auth",
                operation="get_current_user",
                details={"id": user.id},
            )

        return user
