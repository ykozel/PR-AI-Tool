"""File upload utilities for validation and storage"""
import os
import logging
import uuid
from pathlib import Path
from typing import Optional, Tuple

from app.core.config import settings

logger = logging.getLogger(__name__)


class FileUploadManager:
    """Manages file uploads, validation, and storage"""

    # Valid PDF MIME types
    VALID_MIME_TYPES = {"application/pdf"}
    
    # PDF file signature (magic bytes)
    PDF_SIGNATURE = b"%PDF"

    def __init__(self):
        """Initialize file upload manager"""
        self.upload_dir = Path(settings.temp_upload_dir)
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        self.max_file_size_bytes = settings.max_file_size * 1024 * 1024

    def validate_file(self, filename: str, content: bytes) -> Tuple[bool, str]:
        """
        Validate uploaded file
        
        Args:
            filename: Original filename
            content: File content in bytes
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check file extension
        if not filename.lower().endswith('.pdf'):
            return False, "File must be a PDF (.pdf extension)"
        
        # Check file size
        if len(content) == 0:
            return False, "File is empty"
        
        if len(content) > self.max_file_size_bytes:
            return False, f"File size exceeds maximum allowed size of {settings.max_file_size}MB"
        
        # Check PDF signature
        if not content.startswith(self.PDF_SIGNATURE):
            return False, "File is not a valid PDF file"
        
        return True, ""

    def generate_unique_filename(self, original_filename: str) -> str:
        """
        Generate a unique filename for storage
        
        Args:
            original_filename: Original filename from user
            
        Returns:
            Unique filename with UUID prefix
        """
        file_ext = os.path.splitext(original_filename)[1]
        unique_name = f"{uuid.uuid4().hex}_{original_filename}"
        return unique_name

    def save_uploaded_file(self, filename: str, content: bytes) -> Tuple[bool, str]:
        """
        Save uploaded file to disk
        
        Args:
            filename: Generated filename
            content: File content in bytes
            
        Returns:
            Tuple of (success, file_path_or_error)
        """
        try:
            file_path = self.upload_dir / filename
            
            # Write file to disk
            with open(file_path, 'wb') as f:
                f.write(content)
            
            logger.info(f"File saved successfully: {file_path}")
            return True, str(file_path)
            
        except Exception as e:
            error_msg = f"Error saving file: {str(e)}"
            logger.error(error_msg)
            return False, error_msg

    def get_file_path(self, filename: str) -> Optional[Path]:
        """
        Get path to uploaded file
        
        Args:
            filename: Filename to retrieve
            
        Returns:
            Path object if file exists, None otherwise
        """
        file_path = self.upload_dir / filename
        if file_path.exists():
            return file_path
        return None

    def delete_file(self, filename: str) -> Tuple[bool, str]:
        """
        Delete an uploaded file
        
        Args:
            filename: Filename to delete
            
        Returns:
            Tuple of (success, message)
        """
        try:
            file_path = self.upload_dir / filename
            if file_path.exists():
                file_path.unlink()
                logger.info(f"File deleted: {file_path}")
                return True, f"File {filename} deleted successfully"
            return False, f"File {filename} not found"
        except Exception as e:
            error_msg = f"Error deleting file {filename}: {str(e)}"
            logger.error(error_msg)
            return False, error_msg

    def get_file_size_mb(self, file_path: str) -> float:
        """Get file size in MB"""
        try:
            return os.path.getsize(file_path) / (1024 * 1024)
        except Exception as e:
            logger.error(f"Error getting file size: {str(e)}")
            return 0.0
