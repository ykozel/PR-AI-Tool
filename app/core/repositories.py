"""Data Access Object (DAO) / Repository layer for database operations (Single Responsibility)"""
import logging
from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from app.models.file import UploadedFile
from app.models.feedback import Feedback
from app.models.project_activity import ProjectActivity
from app.models.function_activity import FunctionActivity
from app.models.pr_profile import PRProfile

logger = logging.getLogger(__name__)


class UploadedFileRepository:
    """Repository for UploadedFile model - encapsulates database queries"""
    
    def __init__(self, db: Session):
        """Initialize with database session"""
        self.db = db
    
    def get_by_id(self, file_id: int) -> Optional[UploadedFile]:
        """Retrieve uploaded file by ID"""
        return self.db.query(UploadedFile).filter(UploadedFile.id == file_id).first()
    
    def get_by_pr_profile(self, pr_profile_id: int) -> List[UploadedFile]:
        """Retrieve all files for a PR profile"""
        return self.db.query(UploadedFile).filter(
            UploadedFile.pr_profile_id == pr_profile_id
        ).all()
    
    def create(self, **kwargs) -> UploadedFile:
        """Create new uploaded file record"""
        file = UploadedFile(**kwargs)
        self.db.add(file)
        self.db.commit()
        self.db.refresh(file)
        logger.info(f"Created UploadedFile record: ID={file.id}, filename={file.filename}")
        return file
    
    def update(self, file_id: int, **kwargs) -> Optional[UploadedFile]:
        """Update file record"""
        file = self.get_by_id(file_id)
        if not file:
            return None
        
        for key, value in kwargs.items():
            if hasattr(file, key):
                setattr(file, key, value)
        
        self.db.add(file)
        self.db.commit()
        self.db.refresh(file)
        return file
    
    def set_completed(self, file_id: int, parsing_quality: float) -> Optional[UploadedFile]:
        """Mark file as completed with quality score"""
        return self.update(
            file_id,
            upload_status="completed",
            processing_status="completed",
            parsing_quality=parsing_quality,
            processed_at=datetime.utcnow()
        )
    
    def set_failed(self, file_id: int, error_message: str) -> Optional[UploadedFile]:
        """Mark file as failed with error message"""
        return self.update(
            file_id,
            upload_status="failed",
            processing_status="failed",
            extraction_error=error_message
        )
    
    def delete(self, file_id: int) -> bool:
        """Delete file record"""
        file = self.get_by_id(file_id)
        if file:
            self.db.delete(file)
            self.db.commit()
            return True
        return False


class FeedbackRepository:
    """Repository for Feedback model"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_by_pr_profile(self, pr_profile_id: int) -> List[Feedback]:
        """Get all feedback for a PR profile"""
        return self.db.query(Feedback).filter(
            Feedback.pr_profile_id == pr_profile_id
        ).all()
    
    def create(self, **kwargs) -> Feedback:
        """Create new feedback record"""
        feedback = Feedback(**kwargs)
        self.db.add(feedback)
        self.db.commit()
        self.db.refresh(feedback)
        return feedback
    
    def get_by_upload(self, upload_id: int) -> Optional[Feedback]:
        """Get feedback associated with upload"""
        return self.db.query(Feedback).filter(
            Feedback.upload_id == upload_id
        ).first()


class ProjectActivityRepository:
    """Repository for ProjectActivity model"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create(self, **kwargs) -> ProjectActivity:
        """Create new project activity record"""
        activity = ProjectActivity(**kwargs)
        self.db.add(activity)
        self.db.commit()
        self.db.refresh(activity)
        return activity
    
    def get_by_feedback(self, feedback_id: int) -> List[ProjectActivity]:
        """Get all project activities for feedback"""
        return self.db.query(ProjectActivity).filter(
            ProjectActivity.feedback_id == feedback_id
        ).all()


class FunctionActivityRepository:
    """Repository for FunctionActivity model"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create(self, **kwargs) -> FunctionActivity:
        """Create new function activity record"""
        activity = FunctionActivity(**kwargs)
        self.db.add(activity)
        self.db.commit()
        self.db.refresh(activity)
        return activity
    
    def get_by_feedback(self, feedback_id: int) -> List[FunctionActivity]:
        """Get all function activities for feedback"""
        return self.db.query(FunctionActivity).filter(
            FunctionActivity.feedback_id == feedback_id
        ).all()


class PRProfileRepository:
    """Repository for PRProfile model – find/create by (employee_name, year)."""

    def __init__(self, db: Session):
        self.db = db

    def get_by_name_year(self, employee_name: str, year: int) -> Optional[PRProfile]:
        return (
            self.db.query(PRProfile)
            .filter(PRProfile.employee_name == employee_name, PRProfile.year == year)
            .first()
        )

    def get_most_recent_previous_year(self, employee_name: str, year: int) -> Optional[PRProfile]:
        """Find the most recent profile for this employee with year < given year."""
        return (
            self.db.query(PRProfile)
            .filter(
                PRProfile.employee_name == employee_name, 
                PRProfile.year < year
            )
            .order_by(PRProfile.year.desc())
            .first()
        )

    def find_or_create(self, employee_name: str, year: int) -> PRProfile:
        profile = self.get_by_name_year(employee_name, year)
        if profile:
            return profile
        
        # Find most recent previous year profile to link (not just year - 1)
        # This allows linking 2027 to 2025 even if 2026 doesn't exist
        previous_year_profile = self.get_most_recent_previous_year(employee_name, year)
        
        profile = PRProfile(
            employee_name=employee_name, 
            year=year,
            previous_year_profile_id=previous_year_profile.id if previous_year_profile else None
        )
        self.db.add(profile)
        self.db.commit()
        self.db.refresh(profile)
        logger.info(f"Created PRProfile: employee_name={employee_name}, year={year}, id={profile.id}, "
                   f"previous_year_id={profile.previous_year_profile_id} (linked to year {previous_year_profile.year if previous_year_profile else 'N/A'})")
        return profile

    def update_html(self, profile: PRProfile, html_content: str) -> PRProfile:
        profile.html_report = html_content
        self.db.add(profile)
        self.db.commit()
        self.db.refresh(profile)
        return profile

    def list_all(self) -> List[PRProfile]:
        return (
            self.db.query(PRProfile)
            .filter(PRProfile.employee_name.isnot(None))
            .order_by(PRProfile.employee_name, PRProfile.year)
            .all()
        )
    
    def get_all_years_for_person(self, employee_name: str) -> List[int]:
        """Get all years for a person, sorted ascending"""
        profiles = (
            self.db.query(PRProfile.year)
            .filter(PRProfile.employee_name == employee_name)
            .order_by(PRProfile.year)
            .all()
        )
        return [p[0] for p in profiles]
    
    def get_year_hierarchy(self, employee_name: str, year: int) -> dict:
        """Get year navigation info: previous_year, next_year, all_years"""
        all_years = self.get_all_years_for_person(employee_name)
        if year not in all_years:
            return {"current_year": year, "all_years": all_years, "previous_year": None, "next_year": None}
        
        idx = all_years.index(year)
        return {
            "current_year": year,
            "all_years": all_years,
            "previous_year": all_years[idx - 1] if idx > 0 else None,
            "next_year": all_years[idx + 1] if idx < len(all_years) - 1 else None,
        }


class RepositoryFactory:
    """Factory to provide repository instances with dependency injection"""
    """Factory to provide repository instances with dependency injection"""
    
    def __init__(self, db: Session):
        self.db = db
        self._repositories = {}
    
    def get_uploaded_file_repo(self) -> UploadedFileRepository:
        """Get or create UploadedFileRepository"""
        if "uploaded_file" not in self._repositories:
            self._repositories["uploaded_file"] = UploadedFileRepository(self.db)
        return self._repositories["uploaded_file"]
    
    def get_feedback_repo(self) -> FeedbackRepository:
        """Get or create FeedbackRepository"""
        if "feedback" not in self._repositories:
            self._repositories["feedback"] = FeedbackRepository(self.db)
        return self._repositories["feedback"]
    
    def get_project_activity_repo(self) -> ProjectActivityRepository:
        """Get or create ProjectActivityRepository"""
        if "project_activity" not in self._repositories:
            self._repositories["project_activity"] = ProjectActivityRepository(self.db)
        return self._repositories["project_activity"]
    
    def get_function_activity_repo(self) -> FunctionActivityRepository:
        """Get or create FunctionActivityRepository"""
        if "function_activity" not in self._repositories:
            self._repositories["function_activity"] = FunctionActivityRepository(self.db)
        return self._repositories["function_activity"]

    def get_pr_profile_repo(self) -> PRProfileRepository:
        """Get or create PRProfileRepository"""
        if "pr_profile" not in self._repositories:
            self._repositories["pr_profile"] = PRProfileRepository(self.db)
        return self._repositories["pr_profile"]
