"""
Cloudinary Upload Service — Centralized media upload handler.

Supports: images, PDFs, raw files (CSV, JSON, etc.)
All uploads go to Cloudinary and return a secure URL.

Usage:
    from apps.cloudinary_service.upload import CloudinaryUploadService

    # Upload a file from request (Django UploadedFile)
    result = CloudinaryUploadService.upload_file(request_file)

    # Upload raw bytes (e.g., generated PDF)
    result = CloudinaryUploadService.upload_bytes(pdf_bytes, filename="report.pdf")

    # Delete a file from Cloudinary
    CloudinaryUploadService.delete_file(public_id)
"""

import logging
import mimetypes
from io import BytesIO

import cloudinary.uploader

logger = logging.getLogger(__name__)

# ── Mapping of MIME prefixes / extensions → Cloudinary resource_type ──
IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg', '.bmp', '.tiff', '.ico'}
VIDEO_EXTENSIONS = {'.mp4', '.mov', '.avi', '.mkv', '.webm', '.flv'}
RAW_EXTENSIONS = {'.pdf', '.csv', '.json', '.xlsx', '.xls', '.doc', '.docx', '.txt', '.zip'}


def _detect_resource_type(filename: str) -> str:
    """Detect Cloudinary resource_type from filename extension."""
    ext = '.' + filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
    if ext in IMAGE_EXTENSIONS:
        return 'image'
    if ext in VIDEO_EXTENSIONS:
        return 'video'
    # PDFs, CSVs, raw documents, etc.
    return 'raw'


class CloudinaryUploadService:
    """
    Centralised Cloudinary upload/delete service.
    Every public method returns a dict:
        {
            "success": bool,
            "url": str | None,
            "public_id": str | None,
            "resource_type": str | None,
            "error": str | None,
        }
    """

    # ── Base folder on Cloudinary ──
    ROOT_FOLDER = "twinengine"

    # ── Public API ───────────────────────────────────────────────

    @classmethod
    def upload_file(cls, uploaded_file, folder: str = "uploads", public_id: str | None = None):
        """
        Upload a Django InMemoryUploadedFile / TemporaryUploadedFile.

        Args:
            uploaded_file: Django request.FILES['file'] object
            folder: Sub-folder inside twinengine/ on Cloudinary
            public_id: Optional custom public_id (auto-generated if None)

        Returns:
            dict with success, url, public_id, resource_type, error
        """
        filename = uploaded_file.name
        resource_type = _detect_resource_type(filename)
        full_folder = f"{cls.ROOT_FOLDER}/{folder}"

        upload_kwargs = {
            "folder": full_folder,
            "resource_type": resource_type,
            "use_filename": True,
            "unique_filename": True,
            "overwrite": False,
        }
        if public_id:
            upload_kwargs["public_id"] = public_id

        try:
            result = cloudinary.uploader.upload(uploaded_file, **upload_kwargs)
            logger.info(
                "Cloudinary upload OK | %s | %s",
                result.get("public_id"),
                result.get("secure_url"),
            )
            return {
                "success": True,
                "url": result["secure_url"],
                "public_id": result["public_id"],
                "resource_type": resource_type,
                "original_filename": result.get("original_filename", filename),
                "format": result.get("format"),
                "bytes": result.get("bytes"),
                "error": None,
            }
        except Exception as exc:
            logger.error("Cloudinary upload FAILED | %s | %s", filename, exc)
            return {
                "success": False,
                "url": None,
                "public_id": None,
                "resource_type": resource_type,
                "error": str(exc),
            }

    @classmethod
    def upload_bytes(
        cls,
        data: bytes,
        filename: str,
        folder: str = "generated",
        public_id: str | None = None,
    ):
        """
        Upload raw bytes (e.g., a generated PDF or exported CSV).

        Args:
            data: Raw bytes of the file
            filename: Desired filename (used for extension detection)
            folder: Sub-folder inside twinengine/ on Cloudinary
            public_id: Optional custom public_id

        Returns:
            dict with success, url, public_id, resource_type, error
        """
        resource_type = _detect_resource_type(filename)
        full_folder = f"{cls.ROOT_FOLDER}/{folder}"

        upload_kwargs = {
            "folder": full_folder,
            "resource_type": resource_type,
            "use_filename": True,
            "unique_filename": True,
            "overwrite": False,
        }
        if public_id:
            upload_kwargs["public_id"] = public_id

        # Cloudinary accepts a file-like object
        file_io = BytesIO(data)
        file_io.name = filename  # Cloudinary reads .name to infer format

        try:
            result = cloudinary.uploader.upload(file_io, **upload_kwargs)
            logger.info(
                "Cloudinary bytes upload OK | %s | %s",
                result.get("public_id"),
                result.get("secure_url"),
            )
            return {
                "success": True,
                "url": result["secure_url"],
                "public_id": result["public_id"],
                "resource_type": resource_type,
                "original_filename": filename,
                "format": result.get("format"),
                "bytes": result.get("bytes"),
                "error": None,
            }
        except Exception as exc:
            logger.error("Cloudinary bytes upload FAILED | %s | %s", filename, exc)
            return {
                "success": False,
                "url": None,
                "public_id": None,
                "resource_type": resource_type,
                "error": str(exc),
            }

    @classmethod
    def delete_file(cls, public_id: str, resource_type: str = "image"):
        """
        Delete a file from Cloudinary by its public_id.

        Args:
            public_id: The Cloudinary public_id of the asset
            resource_type: 'image', 'raw', or 'video'

        Returns:
            dict with success, error
        """
        try:
            result = cloudinary.uploader.destroy(public_id, resource_type=resource_type)
            ok = result.get("result") == "ok"
            if ok:
                logger.info("Cloudinary delete OK | %s", public_id)
            else:
                logger.warning("Cloudinary delete returned | %s | %s", public_id, result)
            return {"success": ok, "error": None if ok else f"Cloudinary returned: {result}"}
        except Exception as exc:
            logger.error("Cloudinary delete FAILED | %s | %s", public_id, exc)
            return {"success": False, "error": str(exc)}
