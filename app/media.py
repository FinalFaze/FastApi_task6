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


def get_uploads_dir(folder: str) -> Path:
    uploads_dir = get_media_root_path() / folder
    uploads_dir.mkdir(parents=True, exist_ok=True)
    return uploads_dir


def get_post_uploads_dir() -> Path:
    return get_uploads_dir("posts")


def get_comment_uploads_dir() -> Path:
    return get_uploads_dir("comments")


def _validate_file_name(file_name: str | None, entity: str, operation: str) -> str:
    if not file_name:
        raise DomainValidationError(
            message="Image file name is missing",
            entity=entity,
            operation=operation,
            details={},
        )
    return file_name


def _validate_extension(file_name: str, entity: str, operation: str) -> str:
    extension = Path(file_name).suffix.lower()
    if extension not in ALLOWED_IMAGE_EXTENSIONS:
        raise DomainValidationError(
            message="Unsupported image extension",
            entity=entity,
            operation=operation,
            details={"file_name": file_name},
        )
    return extension


def _validate_content_type(upload_file: UploadFile, entity: str, operation: str) -> None:
    content_type = upload_file.content_type or ""
    if content_type and not content_type.startswith("image/"):
        raise DomainValidationError(
            message="Uploaded file must be an image",
            entity=entity,
            operation=operation,
            details={"file_name": upload_file.filename, "content_type": content_type},
        )


def _validate_uploads_count(upload_files: list[UploadFile], entity: str, operation: str) -> None:
    if not upload_files:
        raise DomainValidationError(
            message="At least one image must be provided",
            entity=entity,
            operation=operation,
            details={},
        )
    if len(upload_files) > settings.max_upload_files_per_request:
        raise DomainValidationError(
            message="Too many images in one request",
            entity=entity,
            operation=operation,
            details={"max_upload_files_per_request": settings.max_upload_files_per_request},
        )


def delete_saved_media_paths(paths: list[str]) -> None:
    media_url = settings.media_url.rstrip("/") + "/"
    media_root = get_media_root_path()
    for path in paths:
        if not path.startswith(media_url):
            continue
        relative_path = path[len(media_url):]
        absolute_path = (media_root / relative_path).resolve()
        try:
            absolute_path.relative_to(media_root.resolve())
        except ValueError:
            continue
        if absolute_path.exists() and absolute_path.is_file():
            absolute_path.unlink()


async def save_image(upload_file: UploadFile, folder: str, entity: str, operation: str) -> str:
    file_name = _validate_file_name(upload_file.filename, entity, operation)
    extension = _validate_extension(file_name, entity, operation)
    _validate_content_type(upload_file, entity, operation)
    content = await upload_file.read()

    if not content:
        raise DomainValidationError(
            message="Uploaded image is empty",
            entity=entity,
            operation=operation,
            details={"file_name": file_name},
        )

    max_size_bytes = settings.max_upload_file_size_mb * 1024 * 1024
    if len(content) > max_size_bytes:
        raise DomainValidationError(
            message="Uploaded image is too large",
            entity=entity,
            operation=operation,
            details={
                "file_name": file_name,
                "max_upload_file_size_mb": settings.max_upload_file_size_mb,
            },
        )

    stored_name = f"{uuid4().hex}{extension}"
    relative_path = Path(folder) / stored_name
    absolute_path = get_media_root_path() / relative_path
    absolute_path.parent.mkdir(parents=True, exist_ok=True)
    absolute_path.write_bytes(content)
    return f"{settings.media_url.rstrip('/')}/{relative_path.as_posix()}"


async def save_images(upload_files: list[UploadFile], folder: str, entity: str, operation: str) -> list[str]:
    _validate_uploads_count(upload_files, entity, operation)
    saved_paths = []
    try:
        for upload_file in upload_files:
            saved_paths.append(await save_image(upload_file, folder, entity, operation))
    except Exception:
        delete_saved_media_paths(saved_paths)
        raise
    return saved_paths


async def save_post_image(upload_file: UploadFile) -> str:
    return await save_image(upload_file, "posts", "Post", "save_image")


async def save_post_images(upload_files: list[UploadFile]) -> list[str]:
    return await save_images(upload_files, "posts", "PostImage", "save_images")


async def save_comment_images(upload_files: list[UploadFile]) -> list[str]:
    return await save_images(upload_files, "comments", "CommentImage", "save_images")
