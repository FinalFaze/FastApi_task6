from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session, joinedload, selectinload

from app.db.database import get_db
from app.db.models import Category, Comment, Post
from app.domain.errors import DomainError
from app.domain.use_cases.blog import CommentImageUseCase, CommentUseCase
from app.media import delete_saved_media_paths, save_comment_images
from app.repositories.comment import CommentRepository
from app.repositories.images import CommentImageRepository
from app.routers.dependencies import get_current_user, get_optional_current_user
from app.routers.utils import raise_http_error
from app.schemas.blog import CommentCreate, CommentOut, CommentUpdate, ImageUploadOut

router = APIRouter(
    prefix="/comments",
    tags=["comments"],
)


def _is_public_post(post: Post) -> bool:
    return (
        post.pub_date <= datetime.utcnow()
        and post.is_published
        and post.category is not None
        and post.category.is_published
    )


def _get_post_or_404(db: Session, post_id: int) -> Post:
    post = (
        db.query(Post)
        .options(joinedload(Post.category))
        .filter(Post.id == post_id)
        .first()
    )

    if post is None:
        raise HTTPException(status_code=404, detail="Post not found")

    return post


def _get_comment_or_404(db: Session, comment_id: int) -> Comment:
    comment = (
        db.query(Comment)
        .options(
            joinedload(Comment.post).joinedload(Post.category),
            selectinload(Comment.images),
        )
        .filter(Comment.id == comment_id)
        .first()
    )

    if comment is None:
        raise HTTPException(status_code=404, detail="Comment not found")

    return comment


def _check_comment_visible(comment: Comment, current_user) -> None:
    post = comment.post
    is_comment_author = current_user is not None and current_user.id == comment.author_id
    is_post_author = current_user is not None and current_user.id == post.author_id

    if not is_comment_author and not is_post_author and not _is_public_post(post):
        raise HTTPException(status_code=404, detail="Comment not found")


def _check_comment_author(comment: Comment, current_user) -> None:
    if current_user.id != comment.author_id:
        raise HTTPException(status_code=403, detail="You cannot modify this comment")


def _image_upload_out(record) -> ImageUploadOut:
    return ImageUploadOut(
        id=record.id,
        file_name=Path(record.image).name,
        image=record.image,
        created_at=record.created_at,
    )


@router.get("", response_model=list[CommentOut])
def list_comments(db: Session = Depends(get_db)):
    return (
        db.query(Comment)
        .join(Post, Comment.post_id == Post.id)
        .join(Category, Post.category_id == Category.id)
        .options(selectinload(Comment.images))
        .filter(
            Post.pub_date <= datetime.utcnow(),
            Post.is_published.is_(True),
            Category.is_published.is_(True),
        )
        .order_by(Comment.created_at)
        .all()
    )


@router.post("", response_model=CommentOut, status_code=status.HTTP_201_CREATED)
def create_comment(
    payload: CommentCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    post = _get_post_or_404(db, payload.post_id)

    if not _is_public_post(post) and post.author_id != current_user.id:
        raise HTTPException(status_code=404, detail="Post not found")

    data = payload.model_dump()
    data["author_id"] = current_user.id

    try:
        return CommentUseCase(CommentRepository(db)).create(data)
    except DomainError as exc:
        raise_http_error(exc)


@router.post("/{comment_id}/images", response_model=list[ImageUploadOut], status_code=status.HTTP_201_CREATED)
async def add_comment_images(
    comment_id: int,
    image_files: list[UploadFile] = File(...),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    comment = _get_comment_or_404(db, comment_id)
    _check_comment_author(comment, current_user)
    saved_paths = []

    try:
        saved_paths = await save_comment_images(image_files)
        records = CommentImageUseCase(CommentImageRepository(db)).add_images(comment_id, saved_paths)
        return [_image_upload_out(record) for record in records]
    except DomainError as exc:
        delete_saved_media_paths(saved_paths)
        raise_http_error(exc)


@router.get("/images/{image_id}", response_model=ImageUploadOut)
def get_comment_image(
    image_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_optional_current_user),
):
    try:
        record = CommentImageUseCase(CommentImageRepository(db)).get(image_id)
    except DomainError as exc:
        raise_http_error(exc)

    comment = _get_comment_or_404(db, record.comment_id)
    _check_comment_visible(comment, current_user)
    return _image_upload_out(record)


@router.get("/{comment_id}", response_model=CommentOut)
def get_comment(
    comment_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_optional_current_user),
):
    comment = _get_comment_or_404(db, comment_id)
    _check_comment_visible(comment, current_user)
    return comment


@router.put("/{comment_id}", response_model=CommentOut)
def update_comment(
    comment_id: int,
    payload: CommentUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    comment = _get_comment_or_404(db, comment_id)
    _check_comment_author(comment, current_user)

    try:
        return CommentUseCase(CommentRepository(db)).update(
            comment_id,
            payload.model_dump(exclude_unset=True),
        )
    except DomainError as exc:
        raise_http_error(exc)


@router.delete("/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_comment(
    comment_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    comment = _get_comment_or_404(db, comment_id)
    _check_comment_author(comment, current_user)

    try:
        CommentUseCase(CommentRepository(db)).delete(comment_id)
    except DomainError as exc:
        raise_http_error(exc)
