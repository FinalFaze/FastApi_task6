from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.domain.errors import DomainError
from app.domain.use_cases.blog import LocationUseCase
from app.repositories.location import LocationRepository
from app.routers.dependencies import get_current_user
from app.routers.utils import raise_http_error
from app.schemas.blog import LocationCreate, LocationOut, LocationUpdate

router = APIRouter(
    prefix="/locations",
    tags=["locations"],
)


@router.get("", response_model=list[LocationOut])
def list_locations(db: Session = Depends(get_db)):
    try:
        return LocationUseCase(LocationRepository(db)).list()
    except DomainError as exc:
        raise_http_error(exc)


@router.post("", response_model=LocationOut, status_code=status.HTTP_201_CREATED)
def create_location(
    payload: LocationCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    try:
        return LocationUseCase(LocationRepository(db)).create(payload.model_dump())
    except DomainError as exc:
        raise_http_error(exc)


@router.get("/{location_id}", response_model=LocationOut)
def get_location(location_id: int, db: Session = Depends(get_db)):
    try:
        return LocationUseCase(LocationRepository(db)).get(location_id)
    except DomainError as exc:
        raise_http_error(exc)


@router.put("/{location_id}", response_model=LocationOut)
def update_location(
    location_id: int,
    payload: LocationUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    try:
        return LocationUseCase(LocationRepository(db)).update(
            location_id,
            payload.model_dump(exclude_unset=True),
        )
    except DomainError as exc:
        raise_http_error(exc)


@router.delete("/{location_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_location(
    location_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    try:
        LocationUseCase(LocationRepository(db)).delete(location_id)
    except DomainError as exc:
        raise_http_error(exc)
