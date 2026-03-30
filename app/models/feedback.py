"""Feedback model"""
from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, Enum
from sqlalchemy.sql import func

from app.core.database import Base


class Feedback(Base):
    """Feedback from different sources"""

    __tablename__ = "feedback"

    id = Column(Integer, primary_key=True, index=True)
    pr_profile_id = Column(Integer, ForeignKey("pr_profiles.id"), index=True)
    source = Column(Enum("project", "self", "function", name="feedback_source"))
    
    # Obligatory sections from PDF
    certifications = Column(Text, nullable=True)
    learning = Column(Text, nullable=True)
    project_activity = Column(Text, nullable=True)
    project_responsibilities = Column(Text, nullable=True)
    key_contributions = Column(Text, nullable=True)
    function_activity = Column(Text, nullable=True)
    function_contributions = Column(Text, nullable=True)
    
    # Raw feedback text
    feedback_text = Column(Text, nullable=True)
    
    # Metadata
    submitted_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<Feedback {self.source} pr_profile_id={self.pr_profile_id}>"
