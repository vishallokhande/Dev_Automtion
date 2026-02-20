from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from enum import Enum

class JobStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class JobCreate(BaseModel):
    title: str
    location: str
    keywords: List[str]
    platform: str = "linkedin"  # Default to linkedin for now

class JobResult(BaseModel):
    job_id: str
    status: JobStatus
    result_url: Optional[str] = None
    screenshot_url: Optional[str] = None
    applied_at: Optional[datetime] = None
    error: Optional[str] = None

class Job(JobCreate):
    id: str
    status: JobStatus
    created_at: datetime
