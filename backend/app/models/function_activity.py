"""Company Function Activity model"""
from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime
from sqlalchemy.sql import func

from app.core.database import Base


class FunctionActivity(Base):
    """Company internal function activities and contributions"""

    __tablename__ = "function_activities"

    id = Column(Integer, primary_key=True, index=True)
    pr_profile_id = Column(Integer, ForeignKey("pr_profiles.id"), index=True)
    
    function_name = Column(String)
    activity_description = Column(Text)
    key_contributions = Column(Text)
    involvement_level = Column(String, nullable=True)  # e.g., Lead, Contributor, Support
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    def __repr__(self):
        return f"<FunctionActivity {self.function_name}>"
