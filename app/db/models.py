from sqlalchemy import Column, String, DateTime, Text
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
    created_at = Column(DateTime, default=datetime.utcnow)
    applied_at = Column(DateTime, nullable=True)
