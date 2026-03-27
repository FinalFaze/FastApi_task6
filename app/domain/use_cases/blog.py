from datetime import datetime

from app.domain.entities import (
    CategoryEntity,
    CommentEntity,
    LocationEntity,
    PostEntity,
    UserEntity,
)
from app.domain.errors import (
    DomainConflictError,
    DomainDatabaseError,
    DomainNotFoundError,
    DomainValidationError,
)
from app.domain.ports import (
    CategoryRepositoryPort,
    CommentRepositoryPort,
    LocationRepositoryPort,
    PostRepositoryPort,
    UserRepositoryPort,
)
from app.errors import (
    InfrastructureConflictError,
    InfrastructureDatabaseError,
    InfrastructureError,
    InfrastructureIntegrityError,
    InfrastructureNotFoundError,
)
from app.security import hash_password


def _raise_domain_error(
    entity_name: str,
    exc: InfrastructureError,
    extra_details: dict | None = None,
) -> None:
    details = dict(exc.details)
    if extra_details:
        details.update(extra_details)

    if isinstance(exc, InfrastructureNotFoundError):
        raise DomainNotFoundError(
            message=f"{entity_name} not found",
            entity=entity_name,
            operation=exc.operation,
            details=details,
        ) from exc

    if isinstance(exc, InfrastructureConflictError):
        raise DomainConflictError(
            message=f"{entity_name} conflicts with existing data",
            entity=entity_name,
            operation=exc.operation,
            details=details,
        ) from exc

    if isinstance(exc, InfrastructureIntegrityError):
        raise DomainValidationError(
            message=f"{entity_name} contains invalid data",
            entity=entity_name,
            operation=exc.operation,
            details=details,
        ) from exc

    if isinstance(exc, InfrastructureDatabaseError):
        raise DomainDatabaseError(
            message=f"Database error while processing {entity_name.lower()}",
            entity=entity_name,
            operation=exc.operation,
            details=details,
        ) from exc

    raise DomainDatabaseError(
        message=f"Unexpected error while processing {entity_name.lower()}",
        entity=entity_name,
        operation=exc.operation,
        details=details,
    ) from exc


class UserUseCase:
    def __init__(self, repository: UserRepositoryPort):
        self.repository = repository

    def list(self) -> list[UserEntity]:
        try:
            return self.repository.list()
        except InfrastructureError as exc:
            _raise_domain_error("User", exc)

    def get(self, obj_id: int) -> UserEntity:
        try:
            return self.repository.get(obj_id)
        except InfrastructureError as exc:
            _raise_domain_error("User", exc, {"id": obj_id})

    def create(self, data: dict) -> UserEntity:
        payload = dict(data)
        payload["password"] = hash_password(payload["password"])
        payload["date_joined"] = datetime.utcnow()
        payload["last_login"] = None
        try:
            return self.repository.create(payload)
        except InfrastructureError as exc:
            _raise_domain_error("User", exc, {"payload": sorted(payload.keys())})

    def update(self, obj_id: int, data: dict) -> UserEntity:
        payload = dict(data)
        if "password" in payload:
            payload["password"] = hash_password(payload["password"])
        try:
            return self.repository.update(obj_id, payload)
        except InfrastructureError as exc:
            _raise_domain_error(
                "User",
                exc,
                {"id": obj_id, "payload": sorted(payload.keys())},
            )

    def delete(self, obj_id: int) -> None:
        try:
            self.repository.delete(obj_id)
        except InfrastructureError as exc:
            _raise_domain_error("User", exc, {"id": obj_id})


class CategoryUseCase:
    def __init__(self, repository: CategoryRepositoryPort):
        self.repository = repository

    def list(self) -> list[CategoryEntity]:
        try:
            return self.repository.list()
        except InfrastructureError as exc:
            _raise_domain_error("Category", exc)

    def get(self, obj_id: int) -> CategoryEntity:
        try:
            return self.repository.get(obj_id)
        except InfrastructureError as exc:
            _raise_domain_error("Category", exc, {"id": obj_id})

    def create(self, data: dict) -> CategoryEntity:
        payload = dict(data)
        try:
            return self.repository.create(payload)
        except InfrastructureError as exc:
            _raise_domain_error("Category", exc, {"payload": sorted(payload.keys())})

    def update(self, obj_id: int, data: dict) -> CategoryEntity:
        payload = dict(data)
        try:
            return self.repository.update(obj_id, payload)
        except InfrastructureError as exc:
            _raise_domain_error(
                "Category",
                exc,
                {"id": obj_id, "payload": sorted(payload.keys())},
            )

    def delete(self, obj_id: int) -> None:
        try:
            self.repository.delete(obj_id)
        except InfrastructureError as exc:
            _raise_domain_error("Category", exc, {"id": obj_id})


class LocationUseCase:
    def __init__(self, repository: LocationRepositoryPort):
        self.repository = repository

    def list(self) -> list[LocationEntity]:
        try:
            return self.repository.list()
        except InfrastructureError as exc:
            _raise_domain_error("Location", exc)

    def get(self, obj_id: int) -> LocationEntity:
        try:
            return self.repository.get(obj_id)
        except InfrastructureError as exc:
            _raise_domain_error("Location", exc, {"id": obj_id})

    def create(self, data: dict) -> LocationEntity:
        payload = dict(data)
        try:
            return self.repository.create(payload)
        except InfrastructureError as exc:
            _raise_domain_error("Location", exc, {"payload": sorted(payload.keys())})

    def update(self, obj_id: int, data: dict) -> LocationEntity:
        payload = dict(data)
        try:
            return self.repository.update(obj_id, payload)
        except InfrastructureError as exc:
            _raise_domain_error(
                "Location",
                exc,
                {"id": obj_id, "payload": sorted(payload.keys())},
            )

    def delete(self, obj_id: int) -> None:
        try:
            self.repository.delete(obj_id)
        except InfrastructureError as exc:
            _raise_domain_error("Location", exc, {"id": obj_id})


class PostUseCase:
    def __init__(self, repository: PostRepositoryPort):
        self.repository = repository

    def list(self) -> list[PostEntity]:
        try:
            return self.repository.list()
        except InfrastructureError as exc:
            _raise_domain_error("Post", exc)

    def get(self, obj_id: int) -> PostEntity:
        try:
            return self.repository.get(obj_id)
        except InfrastructureError as exc:
            _raise_domain_error("Post", exc, {"id": obj_id})

    def create(self, data: dict) -> PostEntity:
        payload = dict(data)
        try:
            return self.repository.create(payload)
        except InfrastructureError as exc:
            _raise_domain_error("Post", exc, {"payload": sorted(payload.keys())})

    def update(self, obj_id: int, data: dict) -> PostEntity:
        payload = dict(data)
        try:
            return self.repository.update(obj_id, payload)
        except InfrastructureError as exc:
            _raise_domain_error(
                "Post",
                exc,
                {"id": obj_id, "payload": sorted(payload.keys())},
            )

    def delete(self, obj_id: int) -> None:
        try:
            self.repository.delete(obj_id)
        except InfrastructureError as exc:
            _raise_domain_error("Post", exc, {"id": obj_id})


class CommentUseCase:
    def __init__(self, repository: CommentRepositoryPort):
        self.repository = repository

    def list(self) -> list[CommentEntity]:
        try:
            return self.repository.list()
        except InfrastructureError as exc:
            _raise_domain_error("Comment", exc)

    def get(self, obj_id: int) -> CommentEntity:
        try:
            return self.repository.get(obj_id)
        except InfrastructureError as exc:
            _raise_domain_error("Comment", exc, {"id": obj_id})

    def create(self, data: dict) -> CommentEntity:
        payload = dict(data)
        try:
            return self.repository.create(payload)
        except InfrastructureError as exc:
            _raise_domain_error("Comment", exc, {"payload": sorted(payload.keys())})

    def update(self, obj_id: int, data: dict) -> CommentEntity:
        payload = dict(data)
        try:
            return self.repository.update(obj_id, payload)
        except InfrastructureError as exc:
            _raise_domain_error(
                "Comment",
                exc,
                {"id": obj_id, "payload": sorted(payload.keys())},
            )

    def delete(self, obj_id: int) -> None:
        try:
            self.repository.delete(obj_id)
        except InfrastructureError as exc:
            _raise_domain_error("Comment", exc, {"id": obj_id})
