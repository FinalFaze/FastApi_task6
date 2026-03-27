from sqlalchemy.orm import Session

from app.db.models import Category
from app.domain.entities import CategoryEntity
from app.repositories.base import BaseRepository
from app.repositories.mappers import to_category_entity


class CategoryRepository(BaseRepository[Category, CategoryEntity]):
    def __init__(self, db: Session):
        super().__init__(db, Category, to_category_entity)
