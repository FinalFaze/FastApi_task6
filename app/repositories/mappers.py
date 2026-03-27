from app.db.models import Category, Comment, Location, Post, User
from app.domain.entities import (
    CategoryEntity,
    CommentEntity,
    LocationEntity,
    PostEntity,
    UserEntity,
)


def to_user_entity(model: User) -> UserEntity:
    return UserEntity(
        id=model.id,
        password=model.password,
        last_login=model.last_login,
        is_superuser=model.is_superuser,
        username=model.username,
        first_name=model.first_name,
        last_name=model.last_name,
        email=model.email,
        is_staff=model.is_staff,
        is_active=model.is_active,
        date_joined=model.date_joined,
    )


def to_category_entity(model: Category) -> CategoryEntity:
    return CategoryEntity(
        id=model.id,
        is_published=model.is_published,
        created_at=model.created_at,
        title=model.title,
        description=model.description,
        slug=model.slug,
    )


def to_location_entity(model: Location) -> LocationEntity:
    return LocationEntity(
        id=model.id,
        is_published=model.is_published,
        created_at=model.created_at,
        name=model.name,
    )


def to_post_entity(model: Post) -> PostEntity:
    return PostEntity(
        id=model.id,
        is_published=model.is_published,
        created_at=model.created_at,
        title=model.title,
        text=model.text,
        pub_date=model.pub_date,
        author_id=model.author_id,
        category_id=model.category_id,
        location_id=model.location_id,
        image=model.image,
    )


def to_comment_entity(model: Comment) -> CommentEntity:
    return CommentEntity(
        id=model.id,
        text=model.text,
        created_at=model.created_at,
        author_id=model.author_id,
        post_id=model.post_id,
    )
