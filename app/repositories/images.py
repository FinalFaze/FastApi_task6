from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.db.models import CommentImage, PostImage
from app.domain.entities import CommentImageEntity, PostImageEntity
from app.errors import InfrastructureDatabaseError
from app.repositories.base import BaseRepository
from app.repositories.mappers import to_comment_image_entity, to_post_image_entity


class PostImageRepository(BaseRepository[PostImage, PostImageEntity]):
    def __init__(self, db: Session):
        super().__init__(db, PostImage, to_post_image_entity)

    def create_many(self, post_id: int, image_paths: list[str]) -> list[PostImageEntity]:
        records = [PostImage(post_id=post_id, image=image_path) for image_path in image_paths]
        self.db.add_all(records)
        try:
            self.db.commit()
            for record in records:
                self.db.refresh(record)
        except IntegrityError as exc:
            self.db.rollback()
            raise self._map_integrity_error(
                exc,
                "create_many",
                {"post_id": post_id, "images_count": len(image_paths)},
            ) from exc
        except SQLAlchemyError as exc:
            self.db.rollback()
            raise InfrastructureDatabaseError(
                message="Failed to create PostImage records",
                entity="PostImage",
                operation="create_many",
                details={"post_id": post_id, "images_count": len(image_paths), "db_error": str(exc)},
            ) from exc
        return [to_post_image_entity(record) for record in records]


class CommentImageRepository(BaseRepository[CommentImage, CommentImageEntity]):
    def __init__(self, db: Session):
        super().__init__(db, CommentImage, to_comment_image_entity)

    def create_many(self, comment_id: int, image_paths: list[str]) -> list[CommentImageEntity]:
        records = [CommentImage(comment_id=comment_id, image=image_path) for image_path in image_paths]
        self.db.add_all(records)
        try:
            self.db.commit()
            for record in records:
                self.db.refresh(record)
        except IntegrityError as exc:
            self.db.rollback()
            raise self._map_integrity_error(
                exc,
                "create_many",
                {"comment_id": comment_id, "images_count": len(image_paths)},
            ) from exc
        except SQLAlchemyError as exc:
            self.db.rollback()
            raise InfrastructureDatabaseError(
                message="Failed to create CommentImage records",
                entity="CommentImage",
                operation="create_many",
                details={"comment_id": comment_id, "images_count": len(image_paths), "db_error": str(exc)},
            ) from exc
        return [to_comment_image_entity(record) for record in records]
