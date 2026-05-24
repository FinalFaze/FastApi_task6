from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


class CommentImage(Base):
    __tablename__ = "blog_comment_image"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    image: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    comment_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("blog_comment.id"), nullable=False)

    comment: Mapped["Comment"] = relationship(back_populates="images")
