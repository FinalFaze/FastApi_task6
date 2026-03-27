from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


class Comment(Base):
    __tablename__ = "blog_comment"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    author_id: Mapped[int] = mapped_column(Integer, ForeignKey("auth_user.id"), nullable=False)
    post_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("blog_post.id"), nullable=False)

    post: Mapped["Post"] = relationship(back_populates="comments")
