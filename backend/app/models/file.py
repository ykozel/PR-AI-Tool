"""File upload model for tracking uploaded PDFs"""
from sqlalchemy import Column, Integer, String, Text, DateTime, Enum, Float
from sqlalchemy.sql import func

from app.core.database import Base


class UploadedFile(Base):
    """Track uploaded PDF files"""

    __tablename__ = "uploaded_files"

    id = Column(Integer, primary_key=True, index=True)
    
    # File information
    filename = Column(String(255), index=True)
    original_filename = Column(String(255))
    file_path = Column(String(500))
    file_type = Column(Enum(
        "company_function",
        "auto_feedback",
        "project_feedback",
        "client_feedback",
        "additional_feedback",
        "pdp",
        "trainings",
        "project_activity",
        "self_feedback",  # legacy value kept for backward compatibility
        name="pdf_type",
    ))
    file_size = Column(Float)  # Size in MB

    # SHA-256 hash of extracted text – used to detect duplicate content
    content_hash = Column(String(64), nullable=True, index=True)
    
    # Processing information
    pr_profile_id = Column(Integer, nullable=True)  # Link to PR profile once processed
    upload_status = Column(Enum("pending", "processing", "completed", "failed", name="upload_status"), 
                          default="pending")
    
    # Extracted content
    extracted_text = Column(Text, nullable=True)
    extraction_error = Column(Text, nullable=True)
    
    # Metadata
    uploaded_by_email = Column(String(255), nullable=True)
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())
    processed_at = Column(DateTime(timezone=True), nullable=True)
    
    def __repr__(self):
        return f"<UploadedFile {self.filename} type={self.file_type} status={self.upload_status}>"
