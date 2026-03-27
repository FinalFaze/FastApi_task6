from typing import Callable, Generic, Type, TypeVar

from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.errors import (
    InfrastructureConflictError,
    InfrastructureDatabaseError,
    InfrastructureIntegrityError,
    InfrastructureNotFoundError,
)

TModel = TypeVar("TModel")
TEntity = TypeVar("TEntity")


class BaseRepository(Generic[TModel, TEntity]):
    def __init__(
        self,
        db: Session,
        model: Type[TModel],
        mapper: Callable[[TModel], TEntity],
    ):
        self.db = db
        self.model = model
        self.mapper = mapper

    def list(self) -> list[TEntity]:
        try:
            items = self.db.query(self.model).order_by(self.model.id).all()
            return [self.mapper(item) for item in items]
        except SQLAlchemyError as exc:
            raise InfrastructureDatabaseError(
                message=f"Failed to list {self.model.__name__}",
                entity=self.model.__name__,
                operation="list",
                details={"db_error": str(exc)},
            ) from exc

    def get(self, obj_id: int) -> TEntity:
        try:
            obj = self.db.get(self.model, obj_id)
        except SQLAlchemyError as exc:
            raise InfrastructureDatabaseError(
                message=f"Failed to get {self.model.__name__}",
                entity=self.model.__name__,
                operation="get",
                details={"id": obj_id, "db_error": str(exc)},
            ) from exc
        if not obj:
            raise InfrastructureNotFoundError(
                message=f"{self.model.__name__} not found",
                entity=self.model.__name__,
                operation="get",
                details={"id": obj_id},
            )
        return self.mapper(obj)

    def create(self, data: dict) -> TEntity:
        obj = self.model(**data)
        self.db.add(obj)
        try:
            self.db.commit()
            self.db.refresh(obj)
        except IntegrityError as exc:
            self.db.rollback()
            raise self._map_integrity_error(exc, "create", data) from exc
        except SQLAlchemyError as exc:
            self.db.rollback()
            raise InfrastructureDatabaseError(
                message=f"Failed to create {self.model.__name__}",
                entity=self.model.__name__,
                operation="create",
                details={"payload": sorted(data.keys()), "db_error": str(exc)},
            ) from exc
        return self.mapper(obj)

    def update(self, obj_id: int, data: dict) -> TEntity:
        try:
            obj = self.db.get(self.model, obj_id)
        except SQLAlchemyError as exc:
            raise InfrastructureDatabaseError(
                message=f"Failed to get {self.model.__name__}",
                entity=self.model.__name__,
                operation="update",
                details={"id": obj_id, "db_error": str(exc)},
            ) from exc

        if not obj:
            raise InfrastructureNotFoundError(
                message=f"{self.model.__name__} not found",
                entity=self.model.__name__,
                operation="update",
                details={"id": obj_id},
            )

        for key, value in data.items():
            setattr(obj, key, value)

        try:
            self.db.commit()
            self.db.refresh(obj)
        except IntegrityError as exc:
            self.db.rollback()
            raise self._map_integrity_error(
                exc,
                "update",
                {"id": obj_id, "payload": sorted(data.keys())},
            ) from exc
        except SQLAlchemyError as exc:
            self.db.rollback()
            raise InfrastructureDatabaseError(
                message=f"Failed to update {self.model.__name__}",
                entity=self.model.__name__,
                operation="update",
                details={
                    "id": obj_id,
                    "payload": sorted(data.keys()),
                    "db_error": str(exc),
                },
            ) from exc
        return self.mapper(obj)

    def delete(self, obj_id: int) -> None:
        try:
            obj = self.db.get(self.model, obj_id)
        except SQLAlchemyError as exc:
            raise InfrastructureDatabaseError(
                message=f"Failed to get {self.model.__name__}",
                entity=self.model.__name__,
                operation="delete",
                details={"id": obj_id, "db_error": str(exc)},
            ) from exc

        if not obj:
            raise InfrastructureNotFoundError(
                message=f"{self.model.__name__} not found",
                entity=self.model.__name__,
                operation="delete",
                details={"id": obj_id},
            )

        self.db.delete(obj)
        try:
            self.db.commit()
        except IntegrityError as exc:
            self.db.rollback()
            raise self._map_integrity_error(exc, "delete", {"id": obj_id}) from exc
        except SQLAlchemyError as exc:
            self.db.rollback()
            raise InfrastructureDatabaseError(
                message=f"Failed to delete {self.model.__name__}",
                entity=self.model.__name__,
                operation="delete",
                details={"id": obj_id, "db_error": str(exc)},
            ) from exc

    def _map_integrity_error(
        self,
        exc: IntegrityError,
        operation: str,
        details: dict,
    ) -> InfrastructureIntegrityError:
        original_error = str(exc.orig).lower()

        if (
            "unique constraint failed" in original_error
            or "duplicate key value violates unique constraint" in original_error
        ):
            return InfrastructureConflictError(
                message=f"{self.model.__name__} conflicts with existing data",
                entity=self.model.__name__,
                operation=operation,
                details={**details, "db_error": str(exc.orig)},
            )

        if (
            "foreign key constraint failed" in original_error
            or "violates foreign key constraint" in original_error
        ):
            return InfrastructureIntegrityError(
                message=f"{self.model.__name__} contains invalid related object references",
                entity=self.model.__name__,
                operation=operation,
                details={**details, "db_error": str(exc.orig)},
            )

        return InfrastructureIntegrityError(
            message=f"{self.model.__name__} contains invalid data",
            entity=self.model.__name__,
            operation=operation,
            details={**details, "db_error": str(exc.orig)},
        )
