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
    time_filter: str = "any"  # any | r86400 (24h) | r259200 (3d) | r604800 (1w)
    max_applications: int = 5

class JobResult(BaseModel):
    job_id: str
    status: JobStatus
    result_url: Optional[str] = None
    screenshot_url: Optional[str] = None
    applied_at: Optional[datetime] = None
    link_opened_at: Optional[datetime] = None
    error: Optional[str] = None

class Job(JobCreate):
    id: str
    status: JobStatus
    created_at: datetime
    user_id: Optional[str] = None
    result_url: Optional[str] = None
    screenshot_url: Optional[str] = None
    applied_at: Optional[datetime] = None
    link_opened_at: Optional[datetime] = None
    error: Optional[str] = None
    time_filter: str = "any"
    max_applications: int = 5
    applied_jobs_details: Optional[List[dict]] = None
