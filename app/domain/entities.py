from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass(slots=True)
class UserEntity:
    id: int
    password: str
    last_login: Optional[datetime]
    is_superuser: bool
    username: str
    first_name: str
    last_name: str
    email: str
    is_staff: bool
    is_active: bool
    date_joined: datetime


@dataclass(slots=True)
class TokenPairEntity:
    access_token: str
    refresh_token: str
    expires_in: int
    refresh_expires_in: int


@dataclass(slots=True)
class CategoryEntity:
    id: int
    is_published: bool
    created_at: datetime
    title: str
    description: str
    slug: str


@dataclass(slots=True)
class LocationEntity:
    id: int
    is_published: bool
    created_at: datetime
    name: str


@dataclass(slots=True)
class PostEntity:
    id: int
    is_published: bool
    created_at: datetime
    title: str
    text: str
    pub_date: datetime
    author_id: int
    category_id: Optional[int]
    location_id: Optional[int]
    image: Optional[str]


@dataclass(slots=True)
class CommentEntity:
    id: int
    text: str
    created_at: datetime
    author_id: int
    post_id: int


@dataclass(slots=True)
class PostImageEntity:
    id: int
    image: str
    created_at: datetime
    post_id: int


@dataclass(slots=True)
class CommentImageEntity:
    id: int
    image: str
    created_at: datetime
    comment_id: int
