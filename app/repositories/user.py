from datetime import datetime

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.db.models import User
from app.domain.entities import UserEntity
from app.errors import InfrastructureDatabaseError, InfrastructureNotFoundError
from app.repositories.base import BaseRepository
from app.repositories.mappers import to_user_entity


class UserRepository(BaseRepository[User, UserEntity]):
    def __init__(self, db: Session):
        super().__init__(db, User, to_user_entity)

    def find_by_username(self, username: str) -> UserEntity | None:
        try:
            user = self.db.query(User).filter(User.username == username).first()
        except SQLAlchemyError as exc:
            raise InfrastructureDatabaseError(
                message="Failed to get user by username",
                entity="User",
                operation="find_by_username",
                details={"username": username, "db_error": str(exc)},
            ) from exc
        if user is None:
            return None
        return self.mapper(user)

    def touch_last_login(self, obj_id: int) -> UserEntity:
        try:
            user = self.db.get(User, obj_id)
        except SQLAlchemyError as exc:
            raise InfrastructureDatabaseError(
                message="Failed to get User",
                entity="User",
                operation="touch_last_login",
                details={"id": obj_id, "db_error": str(exc)},
            ) from exc

        if user is None:
            raise InfrastructureNotFoundError(
                message="User not found",
                entity="User",
                operation="touch_last_login",
                details={"id": obj_id},
            )

        user.last_login = datetime.utcnow()

        try:
            self.db.commit()
            self.db.refresh(user)
        except SQLAlchemyError as exc:
            self.db.rollback()
            raise InfrastructureDatabaseError(
                message="Failed to update user last login",
                entity="User",
                operation="touch_last_login",
                details={"id": obj_id, "db_error": str(exc)},
            ) from exc

        return self.mapper(user)
