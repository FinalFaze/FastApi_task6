from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.domain.errors import DomainError
from app.domain.use_cases.blog import CategoryUseCase
from app.repositories.category import CategoryRepository
from app.routers.dependencies import get_current_user
from app.routers.utils import raise_http_error
from app.schemas.blog import CategoryCreate, CategoryOut, CategoryUpdate

router = APIRouter(
    prefix="/categories",
    tags=["categories"],
)


@router.get("", response_model=list[CategoryOut])
def list_categories(db: Session = Depends(get_db)):
    try:
        return CategoryUseCase(CategoryRepository(db)).list()
    except DomainError as exc:
        raise_http_error(exc)


@router.post("", response_model=CategoryOut, status_code=status.HTTP_201_CREATED)
def create_category(
    payload: CategoryCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    try:
        return CategoryUseCase(CategoryRepository(db)).create(payload.model_dump())
    except DomainError as exc:
        raise_http_error(exc)


@router.get("/{category_id}", response_model=CategoryOut)
def get_category(category_id: int, db: Session = Depends(get_db)):
    try:
        return CategoryUseCase(CategoryRepository(db)).get(category_id)
    except DomainError as exc:
        raise_http_error(exc)


@router.put("/{category_id}", response_model=CategoryOut)
def update_category(
    category_id: int,
    payload: CategoryUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    try:
        return CategoryUseCase(CategoryRepository(db)).update(
            category_id,
            payload.model_dump(exclude_unset=True),
        )
    except DomainError as exc:
        raise_http_error(exc)


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category(
    category_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    try:
        CategoryUseCase(CategoryRepository(db)).delete(category_id)
    except DomainError as exc:
        raise_http_error(exc)
