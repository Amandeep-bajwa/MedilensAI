import os
import re
from typing import Tuple, Optional
from fastapi import status
from app.core.config import settings
from app.core.errors import AppException

ALLOWED_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg"}

# Known Magic Byte signatures for strict MIME validation
MAGIC_SIGNATURES = {
    "pdf": b"%PDF",
    "png": b"\x89PNG\r\n\x1a\n",
    "jpeg": b"\xff\xd8\xff",
}

def sanitize_filename(filename: str) -> str:
    """
    Strips directory traversal sequences, unsafe symbols, and normalizes file name.
    """
    clean_name = os.path.basename(filename)
    clean_name = re.sub(r'[^a-zA-Z0-9_.-]', '_', clean_name)
    clean_name = re.sub(r'_+', '_', clean_name)
    if len(clean_name) > 100:
        name_part, ext = os.path.splitext(clean_name)
        clean_name = name_part[:90] + ext
    return clean_name or "document"

def validate_file_security(file_bytes: bytes, filename: str) -> str:
    """
    Enforces security guarantees on uploaded files:
    1. Rejects zero-byte empty uploads.
    2. Enforces maximum size limits (MAX_FILE_SIZE_MB).
    3. Validates file extension against allowed clinical formats.
    4. Performs cryptographic magic-byte inspection to prevent spoofed/executable files.
    """
    file_size = len(file_bytes)
    max_bytes = settings.MAX_FILE_SIZE_MB * 1024 * 1024

    if file_size == 0:
        raise AppException(
            status_code=status.HTTP_400_BAD_REQUEST,
            code="EMPTY_FILE",
            message="Uploaded file is empty."
        )

    if file_size > max_bytes:
        raise AppException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            code="FILE_TOO_LARGE",
            message=f"File size exceeds maximum permitted threshold of {settings.MAX_FILE_SIZE_MB}MB."
        )

    _, ext = os.path.splitext(filename.lower())
    if ext not in ALLOWED_EXTENSIONS:
        raise AppException(
            status_code=status.HTTP_400_BAD_REQUEST,
            code="UNSUPPORTED_FILE_TYPE",
            message=f"File extension '{ext}' is not permitted. Allowed extensions: {', '.join(sorted(ALLOWED_EXTENSIONS))}."
        )

    # Magic byte verification
    detected_type = None
    if ext == ".pdf":
        if file_bytes.startswith(MAGIC_SIGNATURES["pdf"]):
            detected_type = "pdf"
    elif ext == ".png":
        if file_bytes.startswith(MAGIC_SIGNATURES["png"]):
            detected_type = "png"
    elif ext in [".jpg", ".jpeg"]:
        if file_bytes.startswith(MAGIC_SIGNATURES["jpeg"]):
            detected_type = "jpeg"

    if not detected_type:
        raise AppException(
            status_code=status.HTTP_400_BAD_REQUEST,
            code="CORRUPTED_OR_SPOOFED_FILE",
            message="File binary header does not match its claimed file extension."
        )

    return detected_type

def save_upload_file(
    user_id: str,
    report_id: str,
    original_filename: str,
    file_bytes: bytes
) -> Tuple[str, str]:
    """
    Stores an authoritative medical document on disk in a secure multi-tenant path:
    uploads/<user_id>/<report_id>_<safe_filename>
    """
    safe_name = sanitize_filename(original_filename)
    user_dir = os.path.abspath(os.path.join(settings.UPLOAD_DIR, user_id))
    os.makedirs(user_dir, exist_ok=True)

    target_filename = f"{report_id}_{safe_name}"
    target_path = os.path.join(user_dir, target_filename)

    with open(target_path, "wb") as f:
        f.write(file_bytes)

    return safe_name, target_path

def delete_upload_file(file_path: str) -> bool:
    """
    Safely purges physical document file from disk.
    """
    if file_path and os.path.isfile(file_path):
        try:
            os.remove(file_path)
            return True
        except OSError:
            return False
    return False

def get_file_size(file_path: str) -> Optional[int]:
    """
    Returns the file size in bytes if present on disk.
    """
    if file_path and os.path.isfile(file_path):
        try:
            return os.path.getsize(file_path)
        except OSError:
            return None
    return None
