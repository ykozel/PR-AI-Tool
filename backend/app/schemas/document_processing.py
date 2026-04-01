"""Pydantic schemas for document processing"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


class SectionContent(BaseModel):
    """Extracted section content"""
    section_name: str
    content: str
    confidence: float = Field(default=0.8, ge=0.0, le=1.0)

    class Config:
        from_attributes = True


class DocumentProcessingResult(BaseModel):
    """Result of processing a document"""
    upload_id: int
    feedback_type: str
    sections_found: int
    parsing_quality: float = Field(ge=0.0, le=1.0)
    sections: List[SectionContent]
    processed_at: datetime
    
    class Config:
        from_attributes = True


class ExtractedSectionData(BaseModel):
    """Extracted structured data from a section"""
    section_name: str
    content: str
    items: List[str] = []

    class Config:
        from_attributes = True


class ProjectActivityData(BaseModel):
    """Structured project activity data"""
    project_name: str
    responsibilities_description: Optional[str] = None
    key_contributions: Optional[str] = None
    duration_start: Optional[str] = None
    duration_end: Optional[str] = None
    
    class Config:
        from_attributes = True


class FunctionActivityData(BaseModel):
    """Structured function activity data"""
    function_name: str
    activity_description: Optional[str] = None
    key_contributions: Optional[str] = None
    involvement_level: str = "Contributor"
    
    class Config:
        from_attributes = True


class DocumentAnalysisRequest(BaseModel):
    """Request to process/analyze an uploaded document"""
    upload_id: int
    pr_profile_id: Optional[int] = None
    feedback_type: Optional[str] = Field(default="unknown", description="project|self|function")


class DocumentAnalysisResponse(BaseModel):
    """Response from document analysis"""
    success: bool
    upload_id: int
    parsing_quality: float
    sections_found: int
    extracted_sections: Dict[str, Optional[str]]
    structured_data: Dict[str, Any]
    message: str
    
    class Config:
        from_attributes = True


class BulkProcessingRequest(BaseModel):
    """Request to process multiple documents"""
    upload_ids: List[int]
    pr_profile_id: Optional[int] = None


class BulkProcessingResponse(BaseModel):
    """Response from bulk processing"""
    total_documents: int
    successfully_processed: int
    failed_documents: int
    results: List[DocumentAnalysisResponse]


class SectionExtractionRequest(BaseModel):
    """Request to extract a specific section"""
    upload_id: int
    section_name: str = Field(..., description="Name of the section to extract")


class SectionExtractionResponse(BaseModel):
    """Response with extracted section"""
    section_name: str
    content: str
    items: List[str]
    confidence: float
