import logging
import uuid
import httpx
from typing import Optional
from fastapi import UploadFile

from app.core.config import settings
from app.utils.errors import AppException

logger = logging.getLogger(__name__)

ALLOWED_IMAGE_MIME_TYPES = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}
MAX_IMAGE_SIZE_BYTES = 5 * 1024 * 1024  # 5 MB


class StorageService:
    """Service handling secure image uploads to Supabase Storage."""

    @staticmethod
    def validate_image_file(file: UploadFile, content: bytes) -> str:
        """Validate uploaded image MIME type and file size.
        
        Returns:
            Extension (e.g. '.jpg', '.png', '.webp')
        """
        # 1. Size check
        if len(content) > MAX_IMAGE_SIZE_BYTES:
            raise AppException(
                status_code=400,
                code="FILE_TOO_LARGE",
                message="Image file size exceeds the 5 MB limit.",
            )

        # 2. Content-type check
        content_type = file.content_type or ""
        if content_type.lower() not in ALLOWED_IMAGE_MIME_TYPES:
            raise AppException(
                status_code=400,
                code="INVALID_FILE_TYPE",
                message="Unsupported image format. Allowed formats: JPEG, PNG, WebP.",
            )

        return ALLOWED_IMAGE_MIME_TYPES[content_type.lower()]

    @classmethod
    async def upload_snack_image(cls, file: UploadFile) -> str:
        """Upload image to Supabase Storage bucket and return the public URL.
        
        If Supabase Storage credentials are not configured (e.g. local dev / test),
        generates a mock public image reference.
        """
        content = await file.read()
        extension = cls.validate_image_file(file, content)

        unique_filename = f"snack_{uuid.uuid4().hex}{extension}"

        # If Supabase Storage is configured in backend settings:
        if settings.SUPABASE_URL and settings.SUPABASE_SERVICE_ROLE_KEY:
            bucket = settings.SUPABASE_STORAGE_BUCKET
            supabase_url = settings.SUPABASE_URL.rstrip("/")
            upload_url = f"{supabase_url}/storage/v1/object/{bucket}/{unique_filename}"

            headers = {
                "Authorization": f"Bearer {settings.SUPABASE_SERVICE_ROLE_KEY}",
                "apikey": settings.SUPABASE_SERVICE_ROLE_KEY,
                "Content-Type": file.content_type or "application/octet-stream",
            }

            try:
                async with httpx.AsyncClient(timeout=15.0) as client:
                    resp = await client.post(upload_url, content=content, headers=headers)
                    if resp.status_code not in (200, 201):
                        logger.error(f"Supabase Storage error: {resp.status_code} - {resp.text}")
                        raise AppException(
                            status_code=502,
                            code="STORAGE_UPLOAD_FAILED",
                            message="Failed to upload image to storage service.",
                        )
                # Return standard public URL for public bucket
                return f"{supabase_url}/storage/v1/object/public/{bucket}/{unique_filename}"
            except AppException:
                raise
            except Exception as exc:
                logger.error(f"Storage connection error: {exc}")
                raise AppException(
                    status_code=502,
                    code="STORAGE_UNAVAILABLE",
                    message="Storage provider is currently unreachable.",
                )

        # Fallback / local / testing URL
        return f"/uploads/snacks/{unique_filename}"


storage_service = StorageService()
