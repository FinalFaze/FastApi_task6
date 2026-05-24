from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


class PostImage(Base):
    __tablename__ = "blog_post_image"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    image: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    post_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("blog_post.id"), nullable=False)

    post: Mapped["Post"] = relationship(back_populates="images")
