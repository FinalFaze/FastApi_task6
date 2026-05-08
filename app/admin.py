from fastapi import Request
from sqladmin import Admin, ModelView
from sqladmin.authentication import AuthenticationBackend

from app.core import settings
from app.db.database import SessionLocal, engine
from app.db.models import Category, Comment, Location, Post, User
from app.domain.errors import DomainError
from app.domain.use_cases.auth import AuthUseCase
from app.repositories.user import UserRepository
from app.web.auth import COOKIE_NAME


class AdminAuth(AuthenticationBackend):
    async def login(self, request: Request) -> bool:
        form = await request.form()
        username = str(form.get("username", "")).strip()
        password = str(form.get("password", ""))

        db = SessionLocal()
        try:
            token = AuthUseCase(UserRepository(db)).login(username, password)
            user = AuthUseCase(UserRepository(db)).get_current_user(token)

            if not user.is_staff and not user.is_superuser:
                return False

            request.session.update({"admin_token": token})
            return True
        except DomainError:
            return False
        finally:
            db.close()

    async def logout(self, request: Request) -> bool:
        request.session.clear()
        return True

    async def authenticate(self, request: Request) -> bool:
        token = request.session.get("admin_token") or request.cookies.get(COOKIE_NAME)

        if not token:
            return False

        db = SessionLocal()
        try:
            user = AuthUseCase(UserRepository(db)).get_current_user(token)
            return bool(user.is_staff or user.is_superuser)
        except DomainError:
            return False
        finally:
            db.close()


class UserAdmin(ModelView, model=User):
    name = "Пользователь"
    name_plural = "Пользователи"
    icon = "fa-solid fa-user"

    column_list = [
        User.id,
        User.username,
        User.email,
        User.is_staff,
        User.is_superuser,
        User.is_active,
        User.date_joined,
    ]
    column_searchable_list = [User.username, User.email]
    column_sortable_list = [User.id, User.username, User.date_joined]
    form_excluded_columns = ["posts", "comments"]


class CategoryAdmin(ModelView, model=Category):
    name = "Категория"
    name_plural = "Категории"
    icon = "fa-solid fa-folder"

    column_list = [
        Category.id,
        Category.title,
        Category.slug,
        Category.is_published,
        Category.created_at,
    ]
    column_searchable_list = [Category.title, Category.slug]
    column_sortable_list = [Category.id, Category.title, Category.created_at]
    form_excluded_columns = ["posts"]


class LocationAdmin(ModelView, model=Location):
    name = "Локация"
    name_plural = "Локации"
    icon = "fa-solid fa-location-dot"

    column_list = [
        Location.id,
        Location.name,
        Location.is_published,
        Location.created_at,
    ]
    column_searchable_list = [Location.name]
    column_sortable_list = [Location.id, Location.name, Location.created_at]
    form_excluded_columns = ["posts"]


class PostAdmin(ModelView, model=Post):
    name = "Публикация"
    name_plural = "Публикации"
    icon = "fa-solid fa-newspaper"

    column_list = [
        Post.id,
        Post.title,
        Post.author_id,
        Post.category_id,
        Post.location_id,
        Post.pub_date,
        Post.is_published,
        Post.created_at,
    ]
    column_searchable_list = [Post.title, Post.text]
    column_sortable_list = [Post.id, Post.title, Post.pub_date, Post.created_at]
    form_excluded_columns = ["comments"]


class CommentAdmin(ModelView, model=Comment):
    name = "Комментарий"
    name_plural = "Комментарии"
    icon = "fa-solid fa-comment"

    column_list = [
        Comment.id,
        Comment.post_id,
        Comment.author_id,
        Comment.text,
        Comment.created_at,
    ]
    column_searchable_list = [Comment.text]
    column_sortable_list = [Comment.id, Comment.created_at]


def setup_admin(app):
    authentication_backend = AdminAuth(secret_key=settings.jwt_secret_key)
    admin = Admin(
        app,
        engine,
        authentication_backend=authentication_backend,
        title="Blogicum Admin",
    )

    admin.add_view(UserAdmin)
    admin.add_view(CategoryAdmin)
    admin.add_view(LocationAdmin)
    admin.add_view(PostAdmin)
    admin.add_view(CommentAdmin)

    return admin
