"""API endpoints for application information and versioning"""
import logging
from datetime import datetime
from fastapi import APIRouter, Request
from pydantic import BaseModel

from app.core.version import get_version_info, get_version_string, GIT_COMMIT, GIT_BRANCH

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/info", tags=["application-info"])


# ==================== SCHEMAS ====================

class VersionResponse(BaseModel):
    """Version information response"""
    app_name: str
    version: str
    description: str
    release_date: str
    release_channel: str
    build_number: str
    git_commit: str
    git_branch: str


class HealthCheckResponse(BaseModel):
    """Health check response"""
    status: str
    version: str
    timestamp: datetime
    uptime_seconds: float = None


class AppInfoResponse(BaseModel):
    """Complete application information"""
    app_name: str
    version: str
    description: str
    status: str
    timestamp: datetime
    release_date: str
    release_channel: str
    build_number: str
    git_info: dict


# ==================== ENDPOINTS ====================

@router.get("/version", response_model=VersionResponse, summary="Get application version", description="Returns the version and build information of the PR Profile application")
def get_version():
    """Get application version and build information"""
    version_info = get_version_info()
    return version_info.to_dict()


@router.get("/version/simple", response_model=str, summary="Get simple version string", description="Returns just the version number (e.g., '1.0.0')")
def get_version_simple():
    """Get simple version string"""
    return get_version_string()


@router.get("/health", response_model=HealthCheckResponse, summary="Health check endpoint", description="Check if the application is running and retrieve basic health information")
def health_check():
    """Check application health status"""
    version_info = get_version_info()
    return {
        "status": "healthy",
        "version": version_info.version,
        "timestamp": datetime.utcnow(),
    }


@router.get("/", response_model=AppInfoResponse, summary="Get complete application information", description="Returns comprehensive application information including version, build details, and git metadata")
def get_app_info():
    """Get complete application information"""
    version_info = get_version_info()
    return {
        "app_name": version_info.app_name,
        "version": version_info.version,
        "description": version_info.description,
        "status": "running",
        "timestamp": datetime.utcnow(),
        "release_date": version_info.release_date,
        "release_channel": version_info.release_channel,
        "build_number": version_info.build_number,
        "git_info": {
            "commit": version_info.git_commit,
            "branch": version_info.git_branch,
        },
    }


@router.get("/status/detailed", summary="Get detailed status", description="Returns detailed status information including version and environment")
def get_detailed_status(request: Request):
    """Get detailed application status"""
    version_info = get_version_info()
    return {
        "app_name": version_info.app_name,
        "version": version_info.version,
        "status": "running",
        "timestamp": datetime.utcnow().isoformat(),
        "release_channel": version_info.release_channel,
        "build_number": version_info.build_number,
        "git": {
            "commit": version_info.git_commit,
            "branch": version_info.git_branch,
        },
        "deployment": "production" if version_info.release_channel == "stable" else "development",
    }
