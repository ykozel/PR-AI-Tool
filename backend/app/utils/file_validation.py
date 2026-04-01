"""Utilities for file handling, validation, and common operations (DRY principle)"""
import os
import re
import logging
from typing import Tuple, Optional
from pathlib import Path

from app.core.constants import (
    MAX_FILE_SIZE_BYTES, 
    ALLOWED_FILE_EXTENSIONS,
    ERROR_EMPTY_FILE,
    ERROR_FILE_TOO_LARGE,
    ERROR_INVALID_FILE_TYPE,
)

logger = logging.getLogger(__name__)


class FileValidator:
    """Centralized file validation logic"""
    
    @staticmethod
    def validate_doc_upload(filename: str, content: bytes) -> Tuple[bool, Optional[str]]:
        """
        Validate uploaded .doc/.docx file comprehensively.
        
        Returns:
            (is_valid, error_message)
        """
        if not content:
            return False, ERROR_EMPTY_FILE
        
        if len(content) > MAX_FILE_SIZE_BYTES:
            return False, ERROR_FILE_TOO_LARGE
        
        # Check file extension
        file_ext = Path(filename).suffix.lower()
        if file_ext not in ALLOWED_FILE_EXTENSIONS:
            return False, ERROR_INVALID_FILE_TYPE
        
        # Check .docx magic bytes (PK ZIP header: 50 4B 03 04)
        # .docx is a ZIP-based format; legacy .doc starts with D0 CF 11 E0
        if file_ext == ".docx" and not content.startswith(b'PK\x03\x04'):
            return False, "File does not appear to be a valid .docx document"
        if file_ext == ".doc" and not content.startswith(b'\xd0\xcf\x11\xe0'):
            return False, "File does not appear to be a valid .doc document"
        
        return True, None
    
    @staticmethod
    def secure_filename(filename: str) -> str:
        """
        Sanitize filename to prevent path traversal and invalid characters.
        Keeps only alphanumeric, dash, underscore, and dot.
        
        Returns:
            Cleaned filename
        """
        # Remove path separators and null characters
        filename = filename.replace("\\", "").replace("/", "").replace("\0", "")
        # Keep only alphanumeric, dash, underscore, and dot
        filename = re.sub(r"[^\w\-\.]", "_", filename)
        # Remove leading dots and underscores
        filename = filename.lstrip("._")
        # Limit length
        return filename[:200] if filename else "file"


class FileOperations:
    """Centralized file I/O operations"""
    
    @staticmethod
    def get_file_size_mb(file_path: str) -> float:
        """Get file size in MB"""
        if not os.path.exists(file_path):
            return 0.0
        return os.path.getsize(file_path) / (1024 * 1024)
    
    @staticmethod
    def get_file_size_bytes(file_path: str) -> int:
        """Get file size in bytes"""
        if not os.path.exists(file_path):
            return 0
        return os.path.getsize(file_path)
    
    @staticmethod
    def ensure_directory(directory: str) -> None:
        """Create directory if it doesn't exist"""
        os.makedirs(directory, exist_ok=True)
    
    @staticmethod
    def save_file(file_path: str, content: bytes) -> Tuple[bool, str]:
        """
        Save file to disk safely.
        
        Returns:
            (success, message_or_path)
        """
        try:
            # Ensure parent directory exists
            os.makedirs(os.path.dirname(file_path) or ".", exist_ok=True)
            with open(file_path, "wb") as f:
                f.write(content)
            return True, file_path
        except IOError as e:
            error_msg = f"Failed to save file: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
    
    @staticmethod
    def file_exists(file_path: str) -> bool:
        """Check if file exists"""
        return os.path.exists(file_path)
    
    @staticmethod
    def delete_file(file_path: str) -> bool:
        """Delete file safely"""
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
            return True
        except IOError as e:
            logger.error(f"Failed to delete file {file_path}: {str(e)}")
            return False
