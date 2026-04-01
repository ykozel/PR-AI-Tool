"""Application-wide constants and enums to reduce duplication (DRY principle)"""
from enum import Enum
from typing import Dict


class UploadType(str, Enum):
    """Document upload types"""
    COMPANY_FUNCTION = "company_function"
    AUTO_FEEDBACK = "auto_feedback"
    PROJECT_FEEDBACK = "project_feedback"
    CLIENT_FEEDBACK = "client_feedback"
    ADDITIONAL_FEEDBACK = "additional_feedback"
    PDP = "pdp"
    TRAININGS = "trainings"
    PROJECT_ACTIVITY = "project_activity"


class FeedbackType(str, Enum):
    """Normalized feedback types for internal processing"""
    FUNCTION = "function"
    AUTO = "auto"
    PROJECT = "project"
    CLIENT = "client"
    ADDITIONAL = "additional"
    PDP = "pdp"
    TRAININGS = "trainings"
    PROJECT_ACTIVITY = "project_activity"
    UNKNOWN = "unknown"


class UploadStatus(str, Enum):
    """Upload processing status"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class ProcessingPhase(str, Enum):
    """Processing pipeline phases"""
    UPLOAD_VALIDATE = "upload_validate"
    TEXT_EXTRACTION = "text_extraction"
    DOCUMENT_PROCESSING = "document_processing"
    AI_ANALYSIS = "ai_analysis"


# Map file upload types to internal feedback types
FILE_TYPE_TO_FEEDBACK_TYPE: Dict[str, FeedbackType] = {
    UploadType.COMPANY_FUNCTION: FeedbackType.FUNCTION,
    UploadType.AUTO_FEEDBACK: FeedbackType.AUTO,
    UploadType.PROJECT_FEEDBACK: FeedbackType.PROJECT,
    UploadType.CLIENT_FEEDBACK: FeedbackType.CLIENT,
    UploadType.ADDITIONAL_FEEDBACK: FeedbackType.ADDITIONAL,
    UploadType.PDP: FeedbackType.PDP,
    UploadType.TRAININGS: FeedbackType.TRAININGS,
    UploadType.PROJECT_ACTIVITY: FeedbackType.PROJECT_ACTIVITY,
}

# File upload constraints
MAX_FILE_SIZE_MB = 100
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024
ALLOWED_FILE_EXTENSIONS = {".doc", ".docx"}

# Processing quality thresholds
MIN_PARSING_QUALITY = 0.5
GOOD_PARSING_QUALITY = 0.8

# Error messages
ERROR_FILE_NOT_FOUND = "File not found"
ERROR_EMPTY_FILE = "Uploaded file is empty"
ERROR_FILE_TOO_LARGE = f"File size exceeds {MAX_FILE_SIZE_MB}MB limit"
ERROR_INVALID_FILE_TYPE = "Only .doc and .docx files are allowed"
ERROR_TEXT_EXTRACTION_FAILED = "Could not extract text from document"
ERROR_DOCUMENT_PROCESSING_FAILED = "Error processing document"
ERROR_AI_ANALYSIS_FAILED = "Error analyzing document"
ERROR_INVALID_FILE_TYPE_ENUM = "Invalid upload type specified"

# Success messages
SUCCESS_FILE_UPLOADED = "File uploaded successfully"
SUCCESS_FILE_PROCESSED = "File processed successfully"
SUCCESS_UNIFIED_OPERATION = "✓ Upload successful | ✓ Processing complete | ✓ AI analysis done"
