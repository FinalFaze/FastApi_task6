from sqlalchemy.orm import Session

from app.db.models import Post
from app.domain.entities import PostEntity
from app.repositories.base import BaseRepository
from app.repositories.mappers import to_post_entity


class PostRepository(BaseRepository[Post, PostEntity]):
    def __init__(self, db: Session):
        super().__init__(db, Post, to_post_entity)
