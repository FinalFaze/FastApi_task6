from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.domain.errors import DomainError
from app.domain.use_cases.blog import CommentUseCase
from app.repositories.comment import CommentRepository
from app.routers.dependencies import get_current_user
from app.routers.utils import raise_http_error
from app.schemas.blog import CommentCreate, CommentOut, CommentUpdate

router = APIRouter(
    prefix="/comments",
    tags=["comments"],
)


@router.get("", response_model=list[CommentOut])
def list_comments(db: Session = Depends(get_db)):
    try:
        return CommentUseCase(CommentRepository(db)).list()
    except DomainError as exc:
        raise_http_error(exc)


@router.post("", response_model=CommentOut, status_code=status.HTTP_201_CREATED)
def create_comment(
    payload: CommentCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    try:
        return CommentUseCase(CommentRepository(db)).create(payload.model_dump())
    except DomainError as exc:
        raise_http_error(exc)


@router.get("/{comment_id}", response_model=CommentOut)
def get_comment(comment_id: int, db: Session = Depends(get_db)):
    try:
        return CommentUseCase(CommentRepository(db)).get(comment_id)
    except DomainError as exc:
        raise_http_error(exc)


@router.put("/{comment_id}", response_model=CommentOut)
def update_comment(
    comment_id: int,
    payload: CommentUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
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
    try:
        CommentUseCase(CommentRepository(db)).delete(comment_id)
    except DomainError as exc:
        raise_http_error(exc)
