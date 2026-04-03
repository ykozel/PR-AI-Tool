"""
Application versioning and build information

This module centralizes version management for both frontend and backend.
Version is maintained as semantic versioning (MAJOR.MINOR.PATCH).
"""

# ==================== VERSION CONSTANTS ====================

# Backend version (updated on each release)
__version__ = "1.0.0"
__app_name__ = "PR Profile"
__description__ = "Employee Performance Review Tool"

# Version tuple for comparison
VERSION_TUPLE = tuple(map(int, __version__.split(".")))

# Release information
RELEASE_DATE = "2027-04-01"  # ISO 8601 format
RELEASE_CHANNEL = "stable"  # stable, beta, alpha, rc, dev
BUILD_NUMBER = "20270401.001"  # YYYYMMDD.seq format

# Git commit hash (set during build/deployment)
GIT_COMMIT = "add-previous-year-link"
GIT_BRANCH = "main"


# ==================== VERSION INFO SCHEMA ====================

class VersionInfo:
    """Enhanced version information with metadata"""

    def __init__(self):
        self.app_name = __app_name__
        self.version = __version__
        self.description = __description__
        self.release_date = RELEASE_DATE
        self.release_channel = RELEASE_CHANNEL
        self.build_number = BUILD_NUMBER
        self.git_commit = GIT_COMMIT
        self.git_branch = GIT_BRANCH

    def to_dict(self):
        """Convert to dictionary (for API response)"""
        return {
            "app_name": self.app_name,
            "version": self.version,
            "description": self.description,
            "release_date": self.release_date,
            "release_channel": self.release_channel,
            "build_number": self.build_number,
            "git_commit": self.git_commit,
            "git_branch": self.git_branch,
        }

    def __str__(self):
        return f"{self.app_name} v{self.version} ({self.release_channel})"

    def __repr__(self):
        return f"<VersionInfo {self.version}>"


# ==================== PUBLIC API ====================

def get_version_info() -> VersionInfo:
    """Get version information object"""
    return VersionInfo()


def get_version_string() -> str:
    """Get simple version string (e.g. '1.0.0')"""
    return __version__


def get_version_tuple() -> tuple:
    """Get version as tuple for comparison (e.g. (1, 0, 0))"""
    return VERSION_TUPLE


def is_compatible(required_version: str) -> bool:
    """
    Check if current version is compatible with required version.
    
    Args:
        required_version: Minimum required version string (e.g. '1.0.0')
    
    Returns:
        True if current version >= required_version
    
    Example:
        >>> is_compatible("0.9.0")  # True
        >>> is_compatible("1.1.0")  # False (if current is 1.0.0)
    """
    required_tuple = tuple(map(int, required_version.split(".")))
    return VERSION_TUPLE >= required_tuple
