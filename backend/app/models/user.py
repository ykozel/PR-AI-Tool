"""User model"""
from sqlalchemy import Column, Integer, String, Enum
from sqlalchemy.sql import func
from sqlalchemy import DateTime

from app.core.database import Base


class User(Base):
    """User model for employees, managers, and colleagues"""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    full_name = Column(String)
    hashed_password = Column(String)
    role = Column(Enum("employee", "manager", "colleague", name="user_role"), default="employee")
    department = Column(String, nullable=True)
    is_active = Column(Integer, default=1)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<User {self.username}>"
