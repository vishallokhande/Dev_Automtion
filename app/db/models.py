from sqlalchemy import Column, String, DateTime, Text, ForeignKey, Integer
from sqlalchemy.orm import relationship
from app.db.database import Base
from datetime import datetime
import uuid

class JobModel(Base):
    __tablename__ = "jobs"

    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    title = Column(String, index=True)
    location = Column(String)
    keywords = Column(Text) # Stored as comma-separated or JSON string
    status = Column(String, default="pending")
    result_url = Column(String, nullable=True)
    screenshot_url = Column(String, nullable=True)
    error = Column(Text, nullable=True)
    time_filter = Column(String, default="any")  # any, r86400, r259200, r604800
    max_applications = Column(Integer, default=5)
    applied_jobs_details = Column(Text, nullable=True) # JSON list of applied roles
    created_at = Column(DateTime, default=datetime.utcnow)
    applied_at = Column(DateTime, nullable=True)
    link_opened_at = Column(DateTime, nullable=True)
    
    user_id = Column(String, ForeignKey("users.id"), nullable=True)
    user = relationship("UserModel", back_populates="jobs")
