from fastapi import APIRouter, HTTPException, Depends
from typing import List
from sqlalchemy.orm import Session
from app.models.job import JobCreate, Job, JobStatus
from app.db.database import get_db
from app.db.models import JobModel
from app.utils.redis_client import push_job_to_queue
import uuid
from datetime import datetime
import json

router = APIRouter()

@router.post("/jobs", response_model=Job)
async def create_job(job: JobCreate, db: Session = Depends(get_db)):
    # Create DB record
    new_job = JobModel(
        id=str(uuid.uuid4()),
        title=job.title,
        location=job.location,
        keywords=json.dumps(job.keywords),
        status=JobStatus.PENDING,
        created_at=datetime.utcnow()
    )
    db.add(new_job)
    db.commit()
    db.refresh(new_job)
    
    # Push to Redis
    # Convert SQLAlchemy model to dict for Redis
    job_payload = {
        "id": new_job.id,
        "title": new_job.title,
        "location": new_job.location,
        "keywords": job.keywords
    }
    push_job_to_queue(job_payload)
    
    return Job(
        id=new_job.id,
        title=new_job.title,
        location=new_job.location,
        keywords=job.keywords,
        status=new_job.status,
        created_at=new_job.created_at
    )

@router.get("/jobs/{job_id}", response_model=Job)
async def get_job(job_id: str, db: Session = Depends(get_db)):
    job = db.query(JobModel).filter(JobModel.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return Job(
        id=job.id,
        title=job.title,
        location=job.location,
        keywords=json.loads(job.keywords) if job.keywords else [],
        status=job.status,
        result_url=job.result_url,
        screenshot_url=job.screenshot_url,
        applied_at=job.applied_at,
        error=job.error,
        created_at=job.created_at
    )

@router.get("/jobs", response_model=List[Job])
async def list_jobs(db: Session = Depends(get_db)):
    jobs = db.query(JobModel).all()
    return [
        Job(
            id=job.id,
            title=job.title,
            location=job.location,
            keywords=json.loads(job.keywords) if job.keywords else [],
            status=job.status,
            result_url=job.result_url,
            screenshot_url=job.screenshot_url,
            applied_at=job.applied_at,
            error=job.error,
            created_at=job.created_at
        )
        for job in jobs
    ]
