from sqlalchemy.orm import Session

from app.db.models import Comment
from app.domain.entities import CommentEntity
from app.repositories.base import BaseRepository
from app.repositories.mappers import to_comment_entity


class CommentRepository(BaseRepository[Comment, CommentEntity]):
    def __init__(self, db: Session):
        super().__init__(db, Comment, to_comment_entity)
