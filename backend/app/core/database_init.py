"""Database initialization - creates all tables and optional test data"""
import logging
from sqlalchemy import text
from app.core.database import engine, SessionLocal, Base
from app.models import User, UploadedFile
from app.models.pr_profile import PRProfile  # ensure model is registered

logger = logging.getLogger(__name__)


def _migrate_pdf_type_enum():
    """Add missing values to the pdf_type enum in PostgreSQL (no-op for SQLite)."""
    from sqlalchemy import inspect as sa_inspect
    url = str(engine.url)
    if "postgresql" not in url and "postgres" not in url:
        return  # SQLite enforces nothing at DB level; skip

    new_values = [
        "auto_feedback",
        "client_feedback",
        "additional_feedback",
        "pdp",
        "trainings",
        "project_activity",
    ]
    with engine.connect() as conn:
        for value in new_values:
            try:
                conn.execute(
                    text(f"ALTER TYPE pdf_type ADD VALUE IF NOT EXISTS '{value}'")
                )
                conn.commit()
            except Exception as exc:
                logger.warning(f"Could not add '{value}' to pdf_type enum: {exc}")
                conn.rollback()
    logger.info("pdf_type enum migration complete")


def _migrate_add_employee_name():
    """Add employee_name column to pr_profiles if it doesn't exist yet."""
    with engine.connect() as conn:
        try:
            conn.execute(text("ALTER TABLE pr_profiles ADD COLUMN employee_name VARCHAR(255)"))
            conn.commit()
            logger.info("Added employee_name column to pr_profiles")
        except Exception:
            pass  # Column already exists – nothing to do


def _migrate_add_content_hash():
    """Add content_hash column to uploaded_files if it doesn't exist yet."""
    with engine.connect() as conn:
        try:
            conn.execute(text("ALTER TABLE uploaded_files ADD COLUMN content_hash VARCHAR(64)"))
            conn.commit()
            logger.info("Added content_hash column to uploaded_files")
        except Exception:
            pass  # Column already exists – nothing to do


def _migrate_add_yoy_analysis():
    """Add yoy_analysis column to pr_profiles if it doesn't exist yet."""
    with engine.connect() as conn:
        try:
            conn.execute(text("ALTER TABLE pr_profiles ADD COLUMN yoy_analysis TEXT"))
            conn.commit()
            logger.info("Added yoy_analysis column to pr_profiles")
        except Exception:
            pass  # Column already exists – nothing to do


def init_db():
    """Initialize database - create all tables"""
    try:
        # Migrate existing enum before create_all (PostgreSQL only)
        _migrate_pdf_type_enum()
        # Add new columns to existing tables (safe to call repeatedly)
        _migrate_add_employee_name()
        _migrate_add_content_hash()
        _migrate_add_yoy_analysis()

        # Create all tables
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
        return True
    except Exception as e:
        logger.error(f"Error initializing database: {str(e)}")
        return False


def reset_uploads_table():
    """Reset uploaded files table - useful for development"""
    try:
        with SessionLocal() as db:
            # Delete all uploads
            db.query(UploadedFile).delete()
            db.commit()
            logger.info("UploadedFile table reset successfully")
        return True
    except Exception as e:
        logger.error(f"Error resetting uploads table: {str(e)}")
        return False


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    init_db()
