from datetime import datetime
from typing import Optional

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


class Post(Base):
    __tablename__ = "blog_post"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    is_published: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    title: Mapped[str] = mapped_column(String(256), nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    pub_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    author_id: Mapped[int] = mapped_column(Integer, ForeignKey("auth_user.id"), nullable=False)

    category_id: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("blog_category.id"), nullable=True)
    location_id: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("blog_location.id"), nullable=True)

    image: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    category: Mapped[Optional["Category"]] = relationship(back_populates="posts")
    location: Mapped[Optional["Location"]] = relationship(back_populates="posts")
    comments: Mapped[list["Comment"]] = relationship(back_populates="post")
