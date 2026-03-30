"""Pydantic schemas for file upload API requests and responses"""
from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, Field

# Re-export the canonical enums from constants to avoid duplication
from app.core.constants import UploadType as UploadTypeEnum, UploadStatus as UploadStatusEnum


class FileUploadRequest(BaseModel):
    """Request schema for file upload"""
    upload_type: UploadTypeEnum = Field(
        ...,
        description="Type of document: company_function, auto_feedback, project_feedback, client_feedback, additional_feedback, pdp, trainings, or project_activity"
    )
    pr_profile_id: Optional[int] = Field(
        None, 
        description="Optional PR Profile ID to associate with this upload"
    )
    uploaded_by_email: Optional[str] = Field(
        None,
        description="Email of the person uploading the file"
    )


class ExtractedSectionsResponse(BaseModel):
    """Response containing all sections extracted from a document (dynamic, name-independent)"""
    sections: Optional[dict] = Field(
        default=None,
        description="Dictionary of all extracted sections keyed by normalised section name"
    )


class FileUploadResponse(BaseModel):
    """Response after successful file upload"""
    id: int
    filename: str
    original_filename: str
    file_type: UploadTypeEnum
    file_size: float = Field(..., description="File size in MB")
    upload_status: UploadStatusEnum
    uploaded_at: datetime
    message: str = "File uploaded successfully"

    class Config:
        from_attributes = True


class FileProcessingResponse(BaseModel):
    """Response after file processing completion"""
    id: int
    filename: str
    file_type: UploadTypeEnum
    upload_status: UploadStatusEnum
    num_pages: Optional[int] = None
    extracted_text_length: Optional[int] = None
    extracted_sections: Optional[ExtractedSectionsResponse] = None
    processed_at: Optional[datetime] = None
    extraction_error: Optional[str] = None

    class Config:
        from_attributes = True


class FileListResponse(BaseModel):
    """Response with list of uploads"""
    total: int
    items: List[FileUploadResponse]


class UploadStatusResponse(BaseModel):
    """Response with current upload status"""
    id: int
    filename: str
    file_type: UploadTypeEnum
    upload_status: UploadStatusEnum
    uploaded_at: datetime
    processed_at: Optional[datetime] = None
    extraction_error: Optional[str] = None

    class Config:
        from_attributes = True

class SmartUploadResponse(BaseModel):
    """Response for the smart upload endpoint that auto-manages the person+year HTML profile."""
    upload_id: int = Field(description="ID of the newly created upload record")
    pr_profile_id: int = Field(description="ID of the PR profile (created or reused)")
    employee_name: str
    review_year: int
    files_in_profile: int = Field(description="Total files now linked to this person+year profile")
    html_updated: bool = Field(description="Whether the HTML report was successfully (re)generated")
    message: str = "File uploaded successfully"


class UploadAndProcessResponse(BaseModel):
    """Response for unified upload + processing in one call"""
    # Upload info
    id: int
    filename: str
    original_filename: str
    file_type: UploadTypeEnum
    file_size: float = Field(..., description="File size in MB")
    uploaded_at: datetime
    
    # Processing info
    processing_status: UploadStatusEnum = Field(default=UploadStatusEnum.COMPLETED)
    parsing_quality: float = Field(default=0.0, ge=0.0, le=1.0, description="Quality score 0.0-1.0")
    sections_found: int = Field(default=0, ge=0, description="Number of sections extracted")

    # Extracted sections
    extracted_sections: Optional[dict] = Field(
        default=None,
        description="Dictionary with all extracted sections"
    )
    
    # Structured data
    structured_data: Optional[dict] = Field(
        default=None,
        description="Parsed structured data from sections"
    )
    
    # Metadata
    processed_at: Optional[datetime] = None
    extraction_error: Optional[str] = None
    message: str = "File uploaded and processed successfully"

    class Config:
        from_attributes = True


class UploadProcessAnalyzeResponse(BaseModel):
    """Response for unified upload + processing + AI analysis in one call"""
    # =========================
    # Upload & Processing Info
    # =========================
    id: int
    filename: str
    original_filename: str
    file_type: UploadTypeEnum
    file_size: float = Field(..., description="File size in MB")
    uploaded_at: datetime
    
    # Processing metadata
    processing_status: UploadStatusEnum = Field(default=UploadStatusEnum.COMPLETED)
    parsing_quality: float = Field(default=0.0, ge=0.0, le=1.0, description="Document parsing quality 0.0-1.0")
    sections_found: int = Field(default=0, ge=0, description="Number of sections extracted")
    extracted_sections: Optional[dict] = Field(
        default=None,
        description="All extracted sections regardless of their names"
    )
    structured_data: Optional[dict] = Field(
        default=None,
        description="Parsed structured data from sections"
    )
    processed_at: Optional[datetime] = None
    
    # =========================
    # AI Analysis Results
    # =========================
    identified_skills: List[dict] = Field(
        default_factory=list,
        description="Skills identified by AI analysis"
    )
    identified_achievements: List[dict] = Field(
        default_factory=list,
        description="Achievements identified with impact metrics"
    )
    competency_gaps: List[str] = Field(
        default_factory=list,
        description="Skills to develop for growth"
    )
    growth_areas: List[str] = Field(
        default_factory=list,
        description="Recommended focus areas"
    )
    leadership_indicators: List[str] = Field(
        default_factory=list,
        description="Evidence of leadership capability"
    )
    technical_strength: float = Field(
        default=0.0, 
        ge=0.0, 
        le=1.0,
        description="Technical capability score (0.0-1.0)"
    )
    leadership_strength: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0, 
        description="Leadership capability score (0.0-1.0)"
    )
    ai_overall_score: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Overall professional capability score (0.0-1.0)"
    )
    recommendations: List[str] = Field(
        default_factory=list,
        description="Personalized career development recommendations"
    )
    analyzed_at: Optional[datetime] = None
    
    # Status message
    message: str = "File uploaded, processed, and analyzed successfully"

    class Config:
        from_attributes = True
