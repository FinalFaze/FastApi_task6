from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


class Location(Base):
    __tablename__ = "blog_location"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    is_published: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    name: Mapped[str] = mapped_column(String(256), nullable=False)

    posts: Mapped[list["Post"]] = relationship(back_populates="location")
