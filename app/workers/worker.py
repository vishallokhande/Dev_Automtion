import asyncio
import json
import logging
import os
import signal
import sys
from app.utils.redis_client import redis_client
from app.automation.browser import BrowserAutomation

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

running = True

def signal_handler(sig, frame):
    global running
    logger.info("Shutdown signal received")
    running = False

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

async def worker_loop():
    logger.info("Worker started, waiting for jobs...")
    automation = BrowserAutomation()
    
    while running:
        try:
            # Use utility function that handles both Redis and Local Queue
            from app.utils.redis_client import pop_job_from_queue
            
            job_data = pop_job_from_queue()
            
            if job_data:
                logger.info(f"Picked up job: {job_data.get('id')}")
                
                # Update status to PROCESSING (Optional, requires DB access here)
                
                result = await automation.run_apply_flow(job_data)
                
                logger.info(f"Job finished: {result}")
                
                # Update DB
                try:
                    from app.db.database import SessionLocal
                    from app.db.models import JobModel
                    from datetime import datetime
                    
                    db = SessionLocal()
                    job = db.query(JobModel).filter(JobModel.id == job_data.get('id')).first()
                    if job:
                        job.status = result.get("status")
                        job.result_url = result.get("message") # Using message as result/url placeholder
                        job.screenshot_url = result.get("screenshot")
                        if result.get("status") == "success":
                            job.applied_at = datetime.utcnow()
                        else:
                            job.error = result.get("error")
                        db.commit()
                        logger.info(f"Updated job {job.id} in DB")
                    db.close()
                except Exception as db_err:
                    logger.error(f"Failed to update DB: {db_err}")
                
            else:
                await asyncio.sleep(1)
                
        except Exception as e:
            logger.error(f"Worker error: {e}")
            await asyncio.sleep(5)

if __name__ == "__main__":
    asyncio.run(worker_loop())
