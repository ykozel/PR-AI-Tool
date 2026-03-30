"""Core package for configuration, constants, and infrastructure"""
from .config import settings
from .constants import (
    UploadType,
    FeedbackType,
    UploadStatus,
    FILE_TYPE_TO_FEEDBACK_TYPE,
    MAX_FILE_SIZE_MB,
    MAX_FILE_SIZE_BYTES,
    ALLOWED_FILE_EXTENSIONS,
)
from .error_handler import (
    APIException,
    FileValidationError,
    FileNotFoundError,
    TextExtractionError,
    DocumentProcessingError,
    AIAnalysisError,
    ErrorHandler,
)
from .repositories import (
    RepositoryFactory,
    UploadedFileRepository,
    FeedbackRepository,
    ProjectActivityRepository,
    FunctionActivityRepository,
)

__all__ = [
    "settings",
    # Constants
    "UploadType",
    "FeedbackType",
    "UploadStatus",
    "FILE_TYPE_TO_FEEDBACK_TYPE",
    "MAX_FILE_SIZE_MB",
    "MAX_FILE_SIZE_BYTES",
    "ALLOWED_FILE_EXTENSIONS",
    # Error handling
    "APIException",
    "FileValidationError",
    "FileNotFoundError",
    "TextExtractionError",
    "DocumentProcessingError",
    "AIAnalysisError",
    "ErrorHandler",
    # Repositories
    "RepositoryFactory",
    "UploadedFileRepository",
    "FeedbackRepository",
    "ProjectActivityRepository",
    "FunctionActivityRepository",
]
