from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


def _strip_required(value: str) -> str:
    value = value.strip()
    if not value:
        raise ValueError("Field must not be empty")
    return value


def _strip_optional(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    value = value.strip()
    if not value:
        raise ValueError("Field must not be empty")
    return value


class ORMOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class StrictSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")


class CategoryCreate(StrictSchema):
    title: str = Field(min_length=1, max_length=256)
    description: str
    slug: str = Field(min_length=1, max_length=50)
    is_published: bool = True

    @field_validator("title", "description")
    @classmethod
    def validate_required_text_fields(cls, value: str) -> str:
        return _strip_required(value)

    @field_validator("slug")
    @classmethod
    def validate_slug(cls, value: str) -> str:
        value = _strip_required(value).lower()
        allowed = "abcdefghijklmnopqrstuvwxyz0123456789-"
        if value.startswith("-") or value.endswith("-") or "--" in value:
            raise ValueError("Slug format is invalid")
        if any(char not in allowed for char in value):
            raise ValueError("Slug may contain only lowercase letters, digits and hyphens")
        return value


class CategoryUpdate(StrictSchema):
    title: Optional[str] = Field(default=None, min_length=1, max_length=256)
    description: Optional[str] = None
    slug: Optional[str] = Field(default=None, min_length=1, max_length=50)
    is_published: Optional[bool] = None

    @field_validator("title", "description")
    @classmethod
    def validate_optional_text_fields(cls, value: Optional[str]) -> Optional[str]:
        return _strip_optional(value)

    @field_validator("slug")
    @classmethod
    def validate_optional_slug(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        value = _strip_required(value).lower()
        allowed = "abcdefghijklmnopqrstuvwxyz0123456789-"
        if value.startswith("-") or value.endswith("-") or "--" in value:
            raise ValueError("Slug format is invalid")
        if any(char not in allowed for char in value):
            raise ValueError("Slug may contain only lowercase letters, digits and hyphens")
        return value


class CategoryOut(ORMOut):
    id: int
    is_published: bool
    created_at: datetime
    title: str
    description: str
    slug: str


class LocationCreate(StrictSchema):
    name: str = Field(min_length=1, max_length=256)
    is_published: bool = True

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        return _strip_required(value)


class LocationUpdate(StrictSchema):
    name: Optional[str] = Field(default=None, min_length=1, max_length=256)
    is_published: Optional[bool] = None

    @field_validator("name")
    @classmethod
    def validate_optional_name(cls, value: Optional[str]) -> Optional[str]:
        return _strip_optional(value)


class LocationOut(ORMOut):
    id: int
    is_published: bool
    created_at: datetime
    name: str


class PostCreate(StrictSchema):
    title: str = Field(min_length=1, max_length=256)
    text: str
    pub_date: Optional[datetime] = None
    is_published: bool = True
    author_id: int = Field(ge=1)
    category_id: Optional[int] = Field(default=None, ge=1)
    location_id: Optional[int] = Field(default=None, ge=1)
    image: Optional[str] = Field(default=None, max_length=100)

    @field_validator("title", "text")
    @classmethod
    def validate_post_text_fields(cls, value: str) -> str:
        return _strip_required(value)

    @field_validator("image")
    @classmethod
    def validate_image(cls, value: Optional[str]) -> Optional[str]:
        value = _strip_optional(value)
        if value is None:
            return None
        lowered = value.lower()
        allowed_extensions = (".jpg", ".jpeg", ".png", ".gif", ".webp")
        if not lowered.endswith(allowed_extensions):
            raise ValueError("Image must end with a valid image extension")
        return value


class PostUpdate(StrictSchema):
    title: Optional[str] = Field(default=None, min_length=1, max_length=256)
    text: Optional[str] = None
    pub_date: Optional[datetime] = None
    is_published: Optional[bool] = None
    author_id: Optional[int] = Field(default=None, ge=1)
    category_id: Optional[int] = Field(default=None, ge=1)
    location_id: Optional[int] = Field(default=None, ge=1)
    image: Optional[str] = Field(default=None, max_length=100)

    @field_validator("title", "text")
    @classmethod
    def validate_optional_post_text_fields(
        cls,
        value: Optional[str],
    ) -> Optional[str]:
        return _strip_optional(value)

    @field_validator("image")
    @classmethod
    def validate_optional_image(cls, value: Optional[str]) -> Optional[str]:
        value = _strip_optional(value)
        if value is None:
            return None
        lowered = value.lower()
        allowed_extensions = (".jpg", ".jpeg", ".png", ".gif", ".webp")
        if not lowered.endswith(allowed_extensions):
            raise ValueError("Image must end with a valid image extension")
        return value


class PostOut(ORMOut):
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


class ImageUploadOut(BaseModel):
    file_name: str
    image: str


class CommentCreate(StrictSchema):
    text: str
    author_id: int = Field(ge=1)
    post_id: int = Field(ge=1)

    @field_validator("text")
    @classmethod
    def validate_comment_text(cls, value: str) -> str:
        return _strip_required(value)


class CommentUpdate(StrictSchema):
    text: Optional[str] = None
    author_id: Optional[int] = Field(default=None, ge=1)
    post_id: Optional[int] = Field(default=None, ge=1)

    @field_validator("text")
    @classmethod
    def validate_optional_comment_text(
        cls,
        value: Optional[str],
    ) -> Optional[str]:
        return _strip_optional(value)


class CommentOut(ORMOut):
    id: int
    text: str
    created_at: datetime
    author_id: int
    post_id: int


class UserCreate(StrictSchema):
    username: str = Field(min_length=1, max_length=150)
    password: str = Field(min_length=1, max_length=128)
    first_name: str = ""
    last_name: str = ""
    email: str = ""
    is_staff: bool = False
    is_active: bool = True
    is_superuser: bool = False

    @field_validator("username", "password")
    @classmethod
    def validate_user_required_fields(cls, value: str) -> str:
        value = _strip_required(value)
        if " " in value:
            raise ValueError("Field must not contain spaces")
        return value

    @field_validator("first_name", "last_name")
    @classmethod
    def validate_user_optional_names(cls, value: str) -> str:
        return value.strip()

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        value = value.strip()
        if not value:
            return ""
        if " " in value or "@" not in value:
            raise ValueError("Email format is invalid")
        return value.lower()


class UserUpdate(StrictSchema):
    username: Optional[str] = Field(default=None, min_length=1, max_length=150)
    password: Optional[str] = Field(default=None, min_length=1, max_length=128)
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    is_staff: Optional[bool] = None
    is_active: Optional[bool] = None
    is_superuser: Optional[bool] = None

    @field_validator("username", "password")
    @classmethod
    def validate_optional_user_required_fields(
        cls,
        value: Optional[str],
    ) -> Optional[str]:
        if value is None:
            return None
        value = _strip_required(value)
        if " " in value:
            raise ValueError("Field must not contain spaces")
        return value

    @field_validator("first_name", "last_name")
    @classmethod
    def validate_optional_user_names(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        return value.strip()

    @field_validator("email")
    @classmethod
    def validate_optional_email(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        value = value.strip()
        if not value:
            return ""
        if " " in value or "@" not in value:
            raise ValueError("Email format is invalid")
        return value.lower()


class UserOut(ORMOut):
    id: int
    username: str
    first_name: str
    last_name: str
    email: str
    is_staff: bool
    is_active: bool
    is_superuser: bool
    last_login: Optional[datetime]
    date_joined: datetime
