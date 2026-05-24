from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session, joinedload, selectinload

from app.db.database import get_db
from app.db.models import Category, Post
from app.domain.errors import DomainError
from app.domain.use_cases.blog import PostImageUseCase, PostUseCase
from app.media import delete_saved_media_paths, save_post_image, save_post_images
from app.repositories.images import PostImageRepository
from app.repositories.post import PostRepository
from app.routers.dependencies import get_current_user, get_optional_current_user
from app.routers.utils import raise_http_error
from app.schemas.blog import ImageUploadOut, PostCreate, PostOut, PostUpdate

router = APIRouter(
    prefix="/posts",
    tags=["posts"],
)


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
        .options(joinedload(Post.category), selectinload(Post.images))
        .filter(Post.id == post_id)
        .first()
    )

    if post is None:
        raise HTTPException(status_code=404, detail="Post not found")

    return post


def _check_post_visible(post: Post, current_user) -> None:
    is_author = current_user is not None and current_user.id == post.author_id
    if not is_author and not _is_public(post):
        raise HTTPException(status_code=404, detail="Post not found")


def _check_post_author(post: Post, current_user) -> None:
    if current_user.id != post.author_id:
        raise HTTPException(status_code=403, detail="You cannot modify this post")


def _image_upload_out(record) -> ImageUploadOut:
    return ImageUploadOut(
        id=record.id,
        file_name=Path(record.image).name,
        image=record.image,
        created_at=record.created_at,
    )


@router.get("", response_model=list[PostOut])
def list_posts(db: Session = Depends(get_db)):
    return (
        db.query(Post)
        .join(Category, Post.category_id == Category.id)
        .options(joinedload(Post.category), selectinload(Post.images))
        .filter(
            Post.pub_date <= datetime.utcnow(),
            Post.is_published.is_(True),
            Category.is_published.is_(True),
        )
        .order_by(Post.pub_date.desc())
        .all()
    )


@router.post("/upload-image", response_model=ImageUploadOut, status_code=status.HTTP_201_CREATED)
async def upload_post_image(
    image_file: UploadFile = File(...),
    current_user=Depends(get_current_user),
):
    try:
        image_path = await save_post_image(image_file)
        return ImageUploadOut(
            file_name=Path(image_path).name,
            image=image_path,
        )
    except DomainError as exc:
        raise_http_error(exc)


@router.post("/{post_id}/images", response_model=list[ImageUploadOut], status_code=status.HTTP_201_CREATED)
async def add_post_images(
    post_id: int,
    image_files: list[UploadFile] = File(...),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    post = _get_post_or_404(db, post_id)
    _check_post_author(post, current_user)
    saved_paths = []

    try:
        saved_paths = await save_post_images(image_files)
        records = PostImageUseCase(PostImageRepository(db)).add_images(post_id, saved_paths)
        return [_image_upload_out(record) for record in records]
    except DomainError as exc:
        delete_saved_media_paths(saved_paths)
        raise_http_error(exc)


@router.get("/images/{image_id}", response_model=ImageUploadOut)
def get_post_image(
    image_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_optional_current_user),
):
    try:
        record = PostImageUseCase(PostImageRepository(db)).get(image_id)
    except DomainError as exc:
        raise_http_error(exc)

    post = _get_post_or_404(db, record.post_id)
    _check_post_visible(post, current_user)
    return _image_upload_out(record)


@router.get("/{post_id}", response_model=PostOut)
def get_post(
    post_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_optional_current_user),
):
    post = _get_post_or_404(db, post_id)
    _check_post_visible(post, current_user)
    return post


@router.post("/form", response_model=PostOut, status_code=status.HTTP_201_CREATED)
async def create_post_with_optional_image(
    title: str = Form(...),
    text: str = Form(...),
    pub_date: datetime | None = Form(default=None),
    is_published: bool = Form(default=True),
    category_id: int | None = Form(default=None),
    location_id: int | None = Form(default=None),
    image_file: UploadFile | None = File(default=None),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    image_path = None

    try:
        if image_file is not None and image_file.filename:
            image_path = await save_post_image(image_file)

        payload = {
            "title": title,
            "text": text,
            "pub_date": pub_date or datetime.utcnow(),
            "is_published": is_published,
            "author_id": current_user.id,
            "category_id": category_id,
            "location_id": location_id,
            "image": image_path,
        }

        return PostUseCase(PostRepository(db)).create(payload)
    except DomainError as exc:
        if image_path:
            delete_saved_media_paths([image_path])
        raise_http_error(exc)


@router.post("", response_model=PostOut, status_code=status.HTTP_201_CREATED)
def create_post(
    payload: PostCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    data = payload.model_dump()
    if data.get("pub_date") is None:
        data["pub_date"] = datetime.utcnow()
    data["author_id"] = current_user.id

    try:
        return PostUseCase(PostRepository(db)).create(data)
    except DomainError as exc:
        raise_http_error(exc)


@router.put("/{post_id}", response_model=PostOut)
def update_post(
    post_id: int,
    payload: PostUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    post = _get_post_or_404(db, post_id)
    _check_post_author(post, current_user)

    data = payload.model_dump(exclude_unset=True)
    if "pub_date" in data and data["pub_date"] is None:
        data.pop("pub_date")

    try:
        return PostUseCase(PostRepository(db)).update(post_id, data)
    except DomainError as exc:
        raise_http_error(exc)


@router.delete("/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_post(
    post_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    post = _get_post_or_404(db, post_id)
    _check_post_author(post, current_user)

    try:
        PostUseCase(PostRepository(db)).delete(post_id)
    except DomainError as exc:
        raise_http_error(exc)
