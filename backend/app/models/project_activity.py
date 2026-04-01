"""Project Activity model"""
from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime
from sqlalchemy.sql import func

from app.core.database import Base


class ProjectActivity(Base):
    """Project activity and responsibilities"""

    __tablename__ = "project_activities"

    id = Column(Integer, primary_key=True, index=True)
    pr_profile_id = Column(Integer, ForeignKey("pr_profiles.id"), index=True)
    
    project_name = Column(String)
    responsibilities_description = Column(Text)
    key_contributions = Column(Text)
    duration_start = Column(String, nullable=True)
    duration_end = Column(String, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    def __repr__(self):
        return f"<ProjectActivity {self.project_name}>"
