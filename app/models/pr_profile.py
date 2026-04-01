"""PR Profile model"""
from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, UniqueConstraint
from sqlalchemy.sql import func

from app.core.database import Base


class PRProfile(Base):
    """Annual PR Profile record for employees"""

    __tablename__ = "pr_profiles"
    __table_args__ = (
        UniqueConstraint("employee_name", "year", name="uq_profile_name_year"),
    )

    id = Column(Integer, primary_key=True, index=True)
    employee_name = Column(String(255), index=True, nullable=True)
    employee_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=True)
    year = Column(Integer)
    
    # Link to previous year profile (for year navigation)
    previous_year_profile_id = Column(Integer, ForeignKey("pr_profiles.id"), nullable=True)
    
    # Summary sections
    skills_summary = Column(Text, nullable=True)
    
    # HTML report
    html_report = Column(Text, nullable=True)
    
    # Comparison with previous year
    comparison_summary = Column(Text, nullable=True)
    new_achievements = Column(Text, nullable=True)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<PRProfile year={self.year} employee_name={self.employee_name}>"
