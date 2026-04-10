from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, UploadFile, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.domain.errors import DomainError
from app.domain.use_cases.blog import PostUseCase
from app.media import save_post_image
from app.repositories.post import PostRepository
from app.routers.dependencies import get_current_user
from app.routers.utils import raise_http_error
from app.schemas.blog import ImageUploadOut, PostCreate, PostOut, PostUpdate

router = APIRouter(
    prefix="/posts",
    tags=["posts"],
)


@router.get("", response_model=list[PostOut])
def list_posts(db: Session = Depends(get_db)):
    try:
        return PostUseCase(PostRepository(db)).list()
    except DomainError as exc:
        raise_http_error(exc)


@router.get("/{post_id}", response_model=PostOut)
def get_post(post_id: int, db: Session = Depends(get_db)):
    try:
        return PostUseCase(PostRepository(db)).get(post_id)
    except DomainError as exc:
        raise_http_error(exc)


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


@router.post("/form", response_model=PostOut, status_code=status.HTTP_201_CREATED)
async def create_post_with_optional_image(
    title: str = Form(...),
    text: str = Form(...),
    author_id: int = Form(...),
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

        payload = PostCreate(
            title=title,
            text=text,
            pub_date=pub_date,
            is_published=is_published,
            author_id=author_id,
            category_id=category_id,
            location_id=location_id,
            image=image_path,
        )
        data = payload.model_dump()
        if data.get("pub_date") is None:
            data.pop("pub_date")
        return PostUseCase(PostRepository(db)).create(data)
    except DomainError as exc:
        raise_http_error(exc)


@router.post("", response_model=PostOut, status_code=status.HTTP_201_CREATED)
def create_post(
    payload: PostCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    data = payload.model_dump()
    if data.get("pub_date") is None:
        data.pop("pub_date")
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
    try:
        PostUseCase(PostRepository(db)).delete(post_id)
    except DomainError as exc:
        raise_http_error(exc)
