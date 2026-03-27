from sqlalchemy.orm import Session

from app.db.models import Location
from app.domain.entities import LocationEntity
from app.repositories.base import BaseRepository
from app.repositories.mappers import to_location_entity


class LocationRepository(BaseRepository[Location, LocationEntity]):
    def __init__(self, db: Session):
        super().__init__(db, Location, to_location_entity)
