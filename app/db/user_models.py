from sqlalchemy import Column, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.db.database import Base
from datetime import datetime
import uuid

class UserModel(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=True)  # Display name set at signup
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    profile = relationship("UserProfileModel", back_populates="user", uselist=False)
    jobs = relationship("JobModel", back_populates="user")

class UserProfileModel(Base):
    __tablename__ = "user_profiles"

    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"))
    full_name = Column(String, nullable=True)
    resume_path = Column(String, nullable=True)
    additional_details = Column(Text, nullable=True)
    linkedin_cookie = Column(Text, nullable=True)  # LinkedIn li_at session cookie

    user = relationship("UserModel", back_populates="profile")

