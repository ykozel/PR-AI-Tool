"""Centralized error handling and custom exceptions (Single Responsibility)"""
import logging
from typing import Optional, Tuple
from fastapi import HTTPException
from enum import Enum

logger = logging.getLogger(__name__)


class ErrorCode(str, Enum):
    """Standardized error codes for API responses"""
    INVALID_FILE = "INVALID_FILE"
    FILE_NOT_FOUND = "FILE_NOT_FOUND"
    PROCESSING_ERROR = "PROCESSING_ERROR"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    DATABASE_ERROR = "DATABASE_ERROR"
    EXTRACTION_ERROR = "EXTRACTION_ERROR"
    ANALYSIS_ERROR = "ANALYSIS_ERROR"
    INTERNAL_ERROR = "INTERNAL_ERROR"


class APIException(Exception):
    """Base exception for API errors"""
    
    def __init__(
        self,
        message: str,
        status_code: int = 400,
        error_code: ErrorCode = ErrorCode.INTERNAL_ERROR,
        detail: Optional[str] = None,
    ):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        self.detail = detail or message
        super().__init__(self.message)
    
    def to_http_exception(self) -> HTTPException:
        """Convert to FastAPI HTTPException"""
        return HTTPException(
            status_code=self.status_code,
            detail=self.detail
        )


class FileValidationError(APIException):
    """File validation failure"""
    def __init__(self, message: str):
        super().__init__(
            message=message,
            status_code=400,
            error_code=ErrorCode.INVALID_FILE,
        )


class FileNotFoundError(APIException):
    """File not found in database"""
    def __init__(self, file_id: int):
        super().__init__(
            message=f"File with ID {file_id} not found",
            status_code=404,
            error_code=ErrorCode.FILE_NOT_FOUND,
        )


class TextExtractionError(APIException):
    """Text extraction from PDF failed"""
    def __init__(self, reason: str = "Unable to extract text from PDF"):
        super().__init__(
            message=reason,
            status_code=422,
            error_code=ErrorCode.EXTRACTION_ERROR,
        )


class DocumentProcessingError(APIException):
    """Document processing failed"""
    def __init__(self, reason: str = "Error processing document"):
        super().__init__(
            message=reason,
            status_code=422,
            error_code=ErrorCode.PROCESSING_ERROR,
        )


class AIAnalysisError(APIException):
    """AI analysis failed"""
    def __init__(self, reason: str = "Error during AI analysis"):
        super().__init__(
            message=reason,
            status_code=422,
            error_code=ErrorCode.ANALYSIS_ERROR,
        )


class DatabaseError(APIException):
    """Database operation failed"""
    def __init__(self, reason: str = "Database operation failed"):
        super().__init__(
            message=reason,
            status_code=500,
            error_code=ErrorCode.DATABASE_ERROR,
        )


class ErrorHandler:
    """Centralized exception handling logic"""
    
    @staticmethod
    def handle_exception(
        exception: Exception,
        context: str = "operation",
        log_traceback: bool = True,
    ) -> Tuple[int, str]:
        """
        Handle any exception and return HTTP status code and error message.
        
        Args:
            exception: The exception to handle
            context: Context descriptor for logging
            log_traceback: Whether to log full traceback
            
        Returns:
            (status_code, error_message)
        """
        if isinstance(exception, APIException):
            logger.warning(f"{context}: {exception.message} (code: {exception.error_code})")
            return exception.status_code, exception.detail
        
        elif isinstance(exception, HTTPException):
            logger.warning(f"{context}: HTTP error {exception.status_code}")
            return exception.status_code, exception.detail or "Request failed"
        
        else:
            # Generic exception - log with traceback
            if log_traceback:
                logger.error(f"{context}: {str(exception)}", exc_info=True)
            else:
                logger.error(f"{context}: {str(exception)}")
            
            # Don't expose internal error details to clients
            return 500, "Internal server error"
    
    @staticmethod
    def safe_call(
        func,
        *args,
        fallback_return=None,
        error_message: str = "Operation failed",
        context: str = "operation",
        **kwargs
    ):
        """
        Execute function with error handling, returning fallback on error.
        
        Used for non-critical operations that shouldn't crash processing.
        """
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.error(f"{context}: {error_message} - {str(e)}")
            return fallback_return
