from collections.abc import Iterator

from dishka import Provider, Scope, make_container, provide
from dishka.integrations.fastapi import FastapiProvider
from sqlalchemy.orm import Session

from app.db.database import SessionLocal
from app.domain.use_cases.auth import AuthUseCase
from app.domain.use_cases.blog import (
    CategoryUseCase,
    CommentImageUseCase,
    CommentUseCase,
    LocationUseCase,
    PostImageUseCase,
    PostUseCase,
    UserUseCase,
)
from app.repositories.category import CategoryRepository
from app.repositories.comment import CommentRepository
from app.repositories.images import CommentImageRepository, PostImageRepository
from app.repositories.location import LocationRepository
from app.repositories.post import PostRepository
from app.repositories.user import UserRepository


class AppProvider(Provider):
    @provide(scope=Scope.REQUEST)
    def get_db_session(self) -> Iterator[Session]:
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()

    @provide(scope=Scope.REQUEST)
    def get_user_repository(self, db: Session) -> UserRepository:
        return UserRepository(db)

    @provide(scope=Scope.REQUEST)
    def get_post_repository(self, db: Session) -> PostRepository:
        return PostRepository(db)

    @provide(scope=Scope.REQUEST)
    def get_comment_repository(self, db: Session) -> CommentRepository:
        return CommentRepository(db)

    @provide(scope=Scope.REQUEST)
    def get_category_repository(self, db: Session) -> CategoryRepository:
        return CategoryRepository(db)

    @provide(scope=Scope.REQUEST)
    def get_location_repository(self, db: Session) -> LocationRepository:
        return LocationRepository(db)

    @provide(scope=Scope.REQUEST)
    def get_post_image_repository(self, db: Session) -> PostImageRepository:
        return PostImageRepository(db)

    @provide(scope=Scope.REQUEST)
    def get_comment_image_repository(self, db: Session) -> CommentImageRepository:
        return CommentImageRepository(db)

    @provide(scope=Scope.REQUEST)
    def get_auth_use_case(self, repository: UserRepository) -> AuthUseCase:
        return AuthUseCase(repository)

    @provide(scope=Scope.REQUEST)
    def get_user_use_case(self, repository: UserRepository) -> UserUseCase:
        return UserUseCase(repository)

    @provide(scope=Scope.REQUEST)
    def get_post_use_case(self, repository: PostRepository) -> PostUseCase:
        return PostUseCase(repository)

    @provide(scope=Scope.REQUEST)
    def get_comment_use_case(self, repository: CommentRepository) -> CommentUseCase:
        return CommentUseCase(repository)

    @provide(scope=Scope.REQUEST)
    def get_category_use_case(self, repository: CategoryRepository) -> CategoryUseCase:
        return CategoryUseCase(repository)

    @provide(scope=Scope.REQUEST)
    def get_location_use_case(self, repository: LocationRepository) -> LocationUseCase:
        return LocationUseCase(repository)

    @provide(scope=Scope.REQUEST)
    def get_post_image_use_case(self, repository: PostImageRepository) -> PostImageUseCase:
        return PostImageUseCase(repository)

    @provide(scope=Scope.REQUEST)
    def get_comment_image_use_case(self, repository: CommentImageRepository) -> CommentImageUseCase:
        return CommentImageUseCase(repository)


def create_container():
    return make_container(AppProvider(), FastapiProvider())
