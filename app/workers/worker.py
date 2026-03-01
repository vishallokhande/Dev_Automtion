import asyncio
import json
import logging
from app.automation.browser import BrowserAutomation

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# NOTE: signal.signal() is deliberately NOT called here.
# This module is imported and run in a background thread when using run_local.py,
# and signal handlers can only be registered in the main thread.
# Graceful shutdown is handled by the thread being a daemon thread.

async def worker_loop():
    logger.info("Worker started, waiting for jobs...")
    automation = BrowserAutomation()

    while True:
        try:
            from app.utils.redis_client import pop_job_from_queue
            job_data = pop_job_from_queue()

            if not job_data:
                await asyncio.sleep(1)
                continue

            job_id = job_data.get('id')
            logger.info(f"Picked up job: {job_id}")

            from app.db.database import SessionLocal
            from app.db.models import JobModel
            from app.db.user_models import UserModel
            from datetime import datetime

            db = SessionLocal()
            try:
                job = db.query(JobModel).filter(JobModel.id == job_id).first()

                if not job:
                    logger.error(f"Job {job_id} not found in DB")
                    db.close()
                    continue

                # CRITICAL: Mark job as processing so UI shows it's running
                job.status = "processing"
                db.commit()
                logger.info(f"Job {job_id} status set to 'processing'")

                # Load full user object (with profile relationship)
                user = None
                if job.user_id:
                    user = db.query(UserModel).filter(UserModel.id == job.user_id).first()
                    if user:
                        # Eagerly access profile so SQLAlchemy loads the related object
                        # before we close the DB session
                        _ = user.profile
                        if user.profile:
                            _ = user.profile.linkedin_cookie
                            _ = user.profile.full_name
                            _ = user.profile.resume_path

                # Make sure job_data has the settings from DB (in case they weren't in the queue)
                if job.time_filter:
                    job_data['time_filter'] = job.time_filter
                if job.max_applications:
                    job_data['max_applications'] = job.max_applications

            except Exception as db_err:
                logger.error(f"Failed to read job from DB: {db_err}", exc_info=True)
                db.close()
                continue

            # Run automation OUTSIDE the DB session (Playwright is async/long-running)
            try:
                result = await automation.run_apply_flow(job_data, user)
                logger.info(f"Job {job_id} finished: status={result.get('status')}")
            except Exception as auto_err:
                logger.error(f"Automation error for job {job_id}: {auto_err}", exc_info=True)
                result = {
                    "status": "failed",
                    "error": str(auto_err)
                }

            # Write results back to DB
            try:
                job.status = result.get("status", "failed")
                job.result_url = result.get("message")
                job.screenshot_url = result.get("screenshot")

                if result.get("link_opened_at"):
                    job.link_opened_at = result["link_opened_at"]
                    
                if "applied_jobs_details" in result:
                    job.applied_jobs_details = result["applied_jobs_details"]

                if result.get("status") == "success":
                    job.applied_at = result.get("applied_at") or datetime.utcnow()
                else:
                    job.error = result.get("error")

                db.commit()
                logger.info(f"Job {job_id} DB updated: {job.status}")
            except Exception as save_err:
                logger.error(f"Failed to save job result: {save_err}", exc_info=True)
            finally:
                db.close()

        except Exception as e:
            logger.error(f"Worker loop error: {e}", exc_info=True)
            await asyncio.sleep(3)


if __name__ == "__main__":
    asyncio.run(worker_loop())
