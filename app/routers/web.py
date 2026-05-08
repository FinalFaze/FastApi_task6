from datetime import datetime
from urllib.parse import quote

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import RedirectResponse
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.core import settings
from app.db.database import get_db
from app.db.models import Category, Comment, Location, Post, User
from app.domain.errors import DomainError
from app.media import save_post_image
from app.security import create_access_token, get_access_token_expire_seconds
from app.web.auth import COOKIE_NAME, get_current_web_user
from app.web.pagination import paginate
from app.web.templates import templates
from app.web.csrf import validate_csrf

router = APIRouter(tags=["web"], dependencies=[Depends(validate_csrf)])
POSTS_PER_PAGE = 10


def _redirect(url: str) -> RedirectResponse:
    return RedirectResponse(url=url, status_code=303)


def _login_redirect(request: Request) -> RedirectResponse:
    next_url = quote(request.url.path)
    return _redirect(f"/auth/login/?next={next_url}")


def _set_auth_cookie(response: RedirectResponse, user_id: int, username: str):
    response.set_cookie(
        key=COOKIE_NAME,
        value=create_access_token(user_id, username),
        max_age=get_access_token_expire_seconds(),
        httponly=True,
        samesite="lax",
    )
    return response


def _get_user(db: Session, request: Request):
    return get_current_web_user(request, db)


def _not_found():
    raise HTTPException(status_code=404)


def _public_posts_query(db: Session):
    return (
        db.query(Post)
        .join(Category, Post.category_id == Category.id)
        .options(
            joinedload(Post.author),
            joinedload(Post.category),
            joinedload(Post.location),
        )
        .filter(
            Post.pub_date <= datetime.utcnow(),
            Post.is_published.is_(True),
            Category.is_published.is_(True),
        )
        .order_by(Post.pub_date.desc())
    )


def _attach_comment_counts(db: Session, posts: list[Post]) -> list[Post]:
    if not posts:
        return posts

    post_ids = [post.id for post in posts]
    rows = (
        db.query(Comment.post_id, func.count(Comment.id))
        .filter(Comment.post_id.in_(post_ids))
        .group_by(Comment.post_id)
        .all()
    )
    counts = {post_id: count for post_id, count in rows}

    for post in posts:
        post.comment_count = counts.get(post.id, 0)

    return posts


def _is_public(post: Post) -> bool:
    return (
        post.pub_date <= datetime.utcnow()
        and post.is_published
        and post.category is not None
        and post.category.is_published
    )


def _get_post_or_404(db: Session, post_id: int) -> Post:
    post = (
        db.query(Post)
        .options(
            joinedload(Post.author),
            joinedload(Post.category),
            joinedload(Post.location),
        )
        .filter(Post.id == post_id)
        .first()
    )

    if post is None:
        _not_found()

    return post


def _get_comment_or_404(db: Session, post_id: int, comment_id: int) -> Comment:
    comment = (
        db.query(Comment)
        .options(joinedload(Comment.author))
        .filter(
            Comment.id == comment_id,
            Comment.post_id == post_id,
        )
        .first()
    )

    if comment is None:
        _not_found()

    return comment


def _get_categories(db: Session) -> list[Category]:
    return db.query(Category).order_by(Category.title).all()


def _get_locations(db: Session) -> list[Location]:
    return db.query(Location).order_by(Location.name).all()


def _parse_optional_int(value: str | None) -> int | None:
    if value is None:
        return None

    value = str(value).strip()
    if not value:
        return None

    return int(value)


def _parse_pub_date(value: str | None) -> datetime:
    if value is None:
        return datetime.utcnow()

    value = value.strip()
    if not value:
        return datetime.utcnow()

    return datetime.fromisoformat(value)


def _format_pub_date_for_input(value: datetime | None) -> str:
    if value is None:
        return ""

    return value.strftime("%Y-%m-%dT%H:%M")


def _render_post_form(
    request: Request,
    user,
    db: Session,
    post: Post | None = None,
    error: str | None = None,
    values: dict | None = None,
):
    return templates.TemplateResponse(
        request,
        "blog/create.html",
        {
            "user": user,
            "post": post,
            "categories": _get_categories(db),
            "locations": _get_locations(db),
            "error": error,
            "values": values or {},
            "pub_date_value": (
                values.get("pub_date")
                if values and values.get("pub_date") is not None
                else _format_pub_date_for_input(post.pub_date if post else None)
            ),
        },
    )


def _render_comment_form(
    request: Request,
    user,
    post: Post,
    comment: Comment,
    error: str | None = None,
    values: dict | None = None,
):
    return templates.TemplateResponse(
        request,
        "blog/comment.html",
        {
            "user": user,
            "post": post,
            "comment": comment,
            "error": error,
            "values": values or {},
        },
    )


def _post_form_values(
    title: str,
    text: str,
    pub_date: str,
    category_id: str,
    location_id: str,
):
    return {
        "title": title,
        "text": text,
        "pub_date": pub_date,
        "category_id": category_id,
        "location_id": location_id,
    }


def _validate_author(user, post: Post) -> bool:
    return user is not None and user.id == post.author_id


@router.get("/")
def index(request: Request, page: int = 1, db: Session = Depends(get_db)):
    user = _get_user(db, request)
    posts = _attach_comment_counts(db, _public_posts_query(db).all())
    page_obj = paginate(posts, page, POSTS_PER_PAGE)

    return templates.TemplateResponse(
        request,
        "blog/index.html",
        {
            "user": user,
            "page_obj": page_obj,
        },
    )


@router.get("/category/{category_slug}/")
def category_posts(
    category_slug: str,
    request: Request,
    page: int = 1,
    db: Session = Depends(get_db),
):
    user = _get_user(db, request)
    category = (
        db.query(Category)
        .filter(
            Category.slug == category_slug,
            Category.is_published.is_(True),
        )
        .first()
    )

    if category is None:
        _not_found()

    posts = _attach_comment_counts(
        db,
        _public_posts_query(db).filter(Post.category_id == category.id).all(),
    )
    page_obj = paginate(posts, page, POSTS_PER_PAGE)

    return templates.TemplateResponse(
        request,
        "blog/category.html",
        {
            "user": user,
            "category": category,
            "page_obj": page_obj,
        },
    )


@router.get("/profile/edit/")
def profile_edit_page(request: Request, db: Session = Depends(get_db)):
    user = _get_user(db, request)

    if user is None:
        return _login_redirect(request)

    return templates.TemplateResponse(
        request,
        "blog/user.html",
        {
            "user": user,
        },
    )


@router.post("/profile/edit/")
def profile_edit_action(
    request: Request,
    username: str = Form(...),
    first_name: str = Form(""),
    last_name: str = Form(""),
    email: str = Form(""),
    db: Session = Depends(get_db),
):
    user = _get_user(db, request)

    if user is None:
        return _login_redirect(request)

    username = username.strip()
    first_name = first_name.strip()
    last_name = last_name.strip()
    email = email.strip().lower()

    values = {
        "username": username,
        "first_name": first_name,
        "last_name": last_name,
        "email": email,
    }

    if not username:
        return templates.TemplateResponse(
            request,
            "blog/user.html",
            {
                "user": user,
                "error": "Имя пользователя не может быть пустым.",
                "values": values,
            },
        )

    if " " in username:
        return templates.TemplateResponse(
            request,
            "blog/user.html",
            {
                "user": user,
                "error": "Имя пользователя не должно содержать пробелы.",
                "values": values,
            },
        )

    if email and (" " in email or "@" not in email):
        return templates.TemplateResponse(
            request,
            "blog/user.html",
            {
                "user": user,
                "error": "Email указан неверно.",
                "values": values,
            },
        )

    exists = (
        db.query(User)
        .filter(
            User.username == username,
            User.id != user.id,
        )
        .first()
    )

    if exists is not None:
        return templates.TemplateResponse(
            request,
            "blog/user.html",
            {
                "user": user,
                "error": "Пользователь с таким именем уже существует.",
                "values": values,
            },
        )

    orm_user = db.get(User, user.id)

    if orm_user is None:
        _not_found()

    orm_user.username = username
    orm_user.first_name = first_name
    orm_user.last_name = last_name
    orm_user.email = email

    db.add(orm_user)
    db.commit()

    response = _redirect(f"/profile/{username}/")
    return _set_auth_cookie(response, orm_user.id, orm_user.username)


@router.get("/profile/{username}/")
def profile(
    username: str,
    request: Request,
    page: int = 1,
    db: Session = Depends(get_db),
):
    user = _get_user(db, request)
    profile_user = db.query(User).filter(User.username == username).first()

    if profile_user is None:
        _not_found()

    if user is not None and user.id == profile_user.id:
        posts = (
            db.query(Post)
            .options(
                joinedload(Post.author),
                joinedload(Post.category),
                joinedload(Post.location),
            )
            .filter(Post.author_id == profile_user.id)
            .order_by(Post.pub_date.desc())
            .all()
        )
    else:
        posts = _public_posts_query(db).filter(Post.author_id == profile_user.id).all()

    posts = _attach_comment_counts(db, posts)
    page_obj = paginate(posts, page, POSTS_PER_PAGE)

    return templates.TemplateResponse(
        request,
        "blog/profile.html",
        {
            "user": user,
            "profile": profile_user,
            "page_obj": page_obj,
        },
    )


@router.get("/posts/create/")
def post_create_page(request: Request, db: Session = Depends(get_db)):
    user = _get_user(db, request)

    if user is None:
        return _login_redirect(request)

    return _render_post_form(
        request=request,
        user=user,
        db=db,
    )


@router.post("/posts/create/")
async def post_create_action(
    request: Request,
    title: str = Form(...),
    text: str = Form(...),
    pub_date: str = Form(""),
    category_id: str = Form(""),
    location_id: str = Form(""),
    is_published: bool = Form(False),
    image_file: UploadFile | None = File(None),
    db: Session = Depends(get_db),
):
    user = _get_user(db, request)

    if user is None:
        return _login_redirect(request)

    values = _post_form_values(
        title=title,
        text=text,
        pub_date=pub_date,
        category_id=category_id,
        location_id=location_id,
    )

    title = title.strip()
    text = text.strip()

    if not title:
        return _render_post_form(
            request=request,
            user=user,
            db=db,
            error="Заголовок не может быть пустым.",
            values=values,
        )

    if not text:
        return _render_post_form(
            request=request,
            user=user,
            db=db,
            error="Текст публикации не может быть пустым.",
            values=values,
        )

    try:
        image = None
        if image_file is not None and image_file.filename:
            image = await save_post_image(image_file)

        post = Post(
            title=title,
            text=text,
            pub_date=_parse_pub_date(pub_date),
            is_published=is_published,
            author_id=user.id,
            category_id=_parse_optional_int(category_id),
            location_id=_parse_optional_int(location_id),
            image=image,
        )
        db.add(post)
        db.commit()
        db.refresh(post)
    except (ValueError, DomainError):
        db.rollback()
        return _render_post_form(
            request=request,
            user=user,
            db=db,
            error="Проверьте данные формы. Возможно, дата или изображение указаны неверно.",
            values=values,
        )

    return _redirect(f"/posts/{post.id}/")


@router.get("/posts/{post_id}/edit/")
def post_edit_page(
    post_id: int,
    request: Request,
    db: Session = Depends(get_db),
):
    user = _get_user(db, request)

    if user is None:
        return _login_redirect(request)

    post = _get_post_or_404(db, post_id)

    if not _validate_author(user, post):
        return _redirect(f"/posts/{post.id}/")

    return _render_post_form(
        request=request,
        user=user,
        db=db,
        post=post,
    )


@router.post("/posts/{post_id}/edit/")
async def post_edit_action(
    post_id: int,
    request: Request,
    title: str = Form(...),
    text: str = Form(...),
    pub_date: str = Form(""),
    category_id: str = Form(""),
    location_id: str = Form(""),
    is_published: bool = Form(False),
    image_file: UploadFile | None = File(None),
    db: Session = Depends(get_db),
):
    user = _get_user(db, request)

    if user is None:
        return _login_redirect(request)

    post = _get_post_or_404(db, post_id)

    if not _validate_author(user, post):
        return _redirect(f"/posts/{post.id}/")

    values = _post_form_values(
        title=title,
        text=text,
        pub_date=pub_date,
        category_id=category_id,
        location_id=location_id,
    )

    title = title.strip()
    text = text.strip()

    if not title:
        return _render_post_form(
            request=request,
            user=user,
            db=db,
            post=post,
            error="Заголовок не может быть пустым.",
            values=values,
        )

    if not text:
        return _render_post_form(
            request=request,
            user=user,
            db=db,
            post=post,
            error="Текст публикации не может быть пустым.",
            values=values,
        )

    try:
        if image_file is not None and image_file.filename:
            post.image = await save_post_image(image_file)

        post.title = title
        post.text = text
        post.pub_date = _parse_pub_date(pub_date)
        post.is_published = is_published
        post.category_id = _parse_optional_int(category_id)
        post.location_id = _parse_optional_int(location_id)

        db.add(post)
        db.commit()
    except (ValueError, DomainError):
        db.rollback()
        return _render_post_form(
            request=request,
            user=user,
            db=db,
            post=post,
            error="Проверьте данные формы. Возможно, дата или изображение указаны неверно.",
            values=values,
        )

    return _redirect(f"/posts/{post.id}/")


@router.get("/posts/{post_id}/delete/")
def post_delete_page(
    post_id: int,
    request: Request,
    db: Session = Depends(get_db),
):
    user = _get_user(db, request)

    if user is None:
        return _login_redirect(request)

    post = _get_post_or_404(db, post_id)

    if not _validate_author(user, post):
        return _redirect(f"/posts/{post.id}/")

    return _render_post_form(
        request=request,
        user=user,
        db=db,
        post=post,
    )


@router.post("/posts/{post_id}/delete/")
def post_delete_action(
    post_id: int,
    request: Request,
    db: Session = Depends(get_db),
):
    user = _get_user(db, request)

    if user is None:
        return _login_redirect(request)

    post = _get_post_or_404(db, post_id)

    if not _validate_author(user, post):
        return _redirect(f"/posts/{post.id}/")

    username = user.username

    db.delete(post)
    db.commit()

    return _redirect(f"/profile/{username}/")


@router.post("/posts/{post_id}/comment/")
def comment_create_action(
    post_id: int,
    request: Request,
    text: str = Form(...),
    db: Session = Depends(get_db),
):
    user = _get_user(db, request)

    if user is None:
        return _login_redirect(request)

    post = _get_post_or_404(db, post_id)
    is_author = user.id == post.author_id

    if not is_author and not _is_public(post):
        _not_found()

    text = text.strip()

    if not text:
        comments = (
            db.query(Comment)
            .options(joinedload(Comment.author))
            .filter(Comment.post_id == post.id)
            .order_by(Comment.created_at)
            .all()
        )

        return templates.TemplateResponse(
            request,
            "blog/detail.html",
            {
                "user": user,
                "post": post,
                "comments": comments,
                "error": "Комментарий не может быть пустым.",
                "values": {"text": text},
            },
        )

    comment = Comment(
        text=text,
        author_id=user.id,
        post_id=post.id,
    )

    db.add(comment)
    db.commit()
    db.refresh(comment)

    return _redirect(f"/posts/{post.id}/#comment_{comment.id}")


@router.get("/posts/{post_id}/edit_comment/{comment_id}/")
def comment_edit_page(
    post_id: int,
    comment_id: int,
    request: Request,
    db: Session = Depends(get_db),
):
    user = _get_user(db, request)

    if user is None:
        return _login_redirect(request)

    post = _get_post_or_404(db, post_id)
    comment = _get_comment_or_404(db, post_id, comment_id)

    if comment.author_id != user.id:
        return _redirect(f"/posts/{post.id}/#comment_{comment.id}")

    return _render_comment_form(
        request=request,
        user=user,
        post=post,
        comment=comment,
    )


@router.post("/posts/{post_id}/edit_comment/{comment_id}/")
def comment_edit_action(
    post_id: int,
    comment_id: int,
    request: Request,
    text: str = Form(...),
    db: Session = Depends(get_db),
):
    user = _get_user(db, request)

    if user is None:
        return _login_redirect(request)

    post = _get_post_or_404(db, post_id)
    comment = _get_comment_or_404(db, post_id, comment_id)

    if comment.author_id != user.id:
        return _redirect(f"/posts/{post.id}/#comment_{comment.id}")

    text = text.strip()

    if not text:
        return _render_comment_form(
            request=request,
            user=user,
            post=post,
            comment=comment,
            error="Комментарий не может быть пустым.",
            values={"text": text},
        )

    comment.text = text
    db.add(comment)
    db.commit()

    return _redirect(f"/posts/{post.id}/#comment_{comment.id}")


@router.get("/posts/{post_id}/delete_comment/{comment_id}/")
def comment_delete_page(
    post_id: int,
    comment_id: int,
    request: Request,
    db: Session = Depends(get_db),
):
    user = _get_user(db, request)

    if user is None:
        return _login_redirect(request)

    post = _get_post_or_404(db, post_id)
    comment = _get_comment_or_404(db, post_id, comment_id)

    if comment.author_id != user.id:
        return _redirect(f"/posts/{post.id}/#comment_{comment.id}")

    return _render_comment_form(
        request=request,
        user=user,
        post=post,
        comment=comment,
    )


@router.post("/posts/{post_id}/delete_comment/{comment_id}/")
def comment_delete_action(
    post_id: int,
    comment_id: int,
    request: Request,
    db: Session = Depends(get_db),
):
    user = _get_user(db, request)

    if user is None:
        return _login_redirect(request)

    post = _get_post_or_404(db, post_id)
    comment = _get_comment_or_404(db, post_id, comment_id)

    if comment.author_id != user.id:
        return _redirect(f"/posts/{post.id}/#comment_{comment.id}")

    db.delete(comment)
    db.commit()

    return _redirect(f"/posts/{post.id}/")


@router.get("/posts/{post_id}/")
def post_detail(
    post_id: int,
    request: Request,
    db: Session = Depends(get_db),
):
    user = _get_user(db, request)
    post = _get_post_or_404(db, post_id)
    is_author = user is not None and user.id == post.author_id

    if not is_author and not _is_public(post):
        _not_found()

    comments = (
        db.query(Comment)
        .options(joinedload(Comment.author))
        .filter(Comment.post_id == post.id)
        .order_by(Comment.created_at)
        .all()
    )

    return templates.TemplateResponse(
        request,
        "blog/detail.html",
        {
            "user": user,
            "post": post,
            "comments": comments,
        },
    )


@router.get("/about/")
def about(request: Request, db: Session = Depends(get_db)):
    user = _get_user(db, request)

    return templates.TemplateResponse(
        request,
        "pages/about.html",
        {
            "user": user,
        },
    )


@router.get("/rules/")
def rules(request: Request, db: Session = Depends(get_db)):
    user = _get_user(db, request)

    return templates.TemplateResponse(
        request,
        "pages/rules.html",
        {
            "user": user,
        },
    )
