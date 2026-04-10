from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile

from app.core import BASE_DIR, settings
from app.domain.errors import DomainValidationError


ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}


def get_media_root_path() -> Path:
    media_root = Path(settings.media_root)
    if not media_root.is_absolute():
        media_root = BASE_DIR / media_root
    media_root.mkdir(parents=True, exist_ok=True)
    return media_root


def get_post_uploads_dir() -> Path:
    uploads_dir = get_media_root_path() / "posts"
    uploads_dir.mkdir(parents=True, exist_ok=True)
    return uploads_dir


def _validate_file_name(file_name: str | None) -> str:
    if not file_name:
        raise DomainValidationError(
            message="Image file name is missing",
            entity="Post",
            operation="save_image",
            details={},
        )
    return file_name


def _validate_extension(file_name: str) -> str:
    extension = Path(file_name).suffix.lower()
    if extension not in ALLOWED_IMAGE_EXTENSIONS:
        raise DomainValidationError(
            message="Unsupported image extension",
            entity="Post",
            operation="save_image",
            details={"file_name": file_name},
        )
    return extension


async def save_post_image(upload_file: UploadFile) -> str:
    file_name = _validate_file_name(upload_file.filename)
    extension = _validate_extension(file_name)
    content = await upload_file.read()

    if not content:
        raise DomainValidationError(
            message="Uploaded image is empty",
            entity="Post",
            operation="save_image",
            details={"file_name": file_name},
        )

    max_size_bytes = settings.max_upload_file_size_mb * 1024 * 1024
    if len(content) > max_size_bytes:
        raise DomainValidationError(
            message="Uploaded image is too large",
            entity="Post",
            operation="save_image",
            details={
                "file_name": file_name,
                "max_upload_file_size_mb": settings.max_upload_file_size_mb,
            },
        )

    stored_name = f"{uuid4().hex}{extension}"
    relative_path = Path("posts") / stored_name
    absolute_path = get_media_root_path() / relative_path
    absolute_path.write_bytes(content)
    return f"{settings.media_url.rstrip('/')}/{relative_path.as_posix()}"
