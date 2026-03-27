from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.domain.errors import DomainError
from app.domain.use_cases.blog import UserUseCase
from app.repositories.user import UserRepository
from app.routers.dependencies import get_current_user
from app.routers.utils import raise_http_error
from app.schemas.blog import UserCreate, UserOut, UserUpdate

router = APIRouter(prefix="/users", tags=["users"])


@router.get("", response_model=list[UserOut])
def list_users(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    try:
        return UserUseCase(UserRepository(db)).list()
    except DomainError as exc:
        raise_http_error(exc)


@router.post("", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def create_user(payload: UserCreate, db: Session = Depends(get_db)):
    try:
        return UserUseCase(UserRepository(db)).create(payload.model_dump())
    except DomainError as exc:
        raise_http_error(exc)


@router.get("/{user_id}", response_model=UserOut)
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    try:
        return UserUseCase(UserRepository(db)).get(user_id)
    except DomainError as exc:
        raise_http_error(exc)


@router.put("/{user_id}", response_model=UserOut)
def update_user(
    user_id: int,
    payload: UserUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    try:
        return UserUseCase(UserRepository(db)).update(
            user_id,
            payload.model_dump(exclude_unset=True),
        )
    except DomainError as exc:
        raise_http_error(exc)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    try:
        UserUseCase(UserRepository(db)).delete(user_id)
    except DomainError as exc:
        raise_http_error(exc)
