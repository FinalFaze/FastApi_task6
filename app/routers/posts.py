from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.domain.errors import DomainError
from app.domain.use_cases.blog import PostUseCase
from app.repositories.post import PostRepository
from app.routers.dependencies import get_current_user
from app.routers.utils import raise_http_error
from app.schemas.blog import PostCreate, PostOut, PostUpdate

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
