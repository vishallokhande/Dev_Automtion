"""
AutoApply-Ops Local Development Server
Run with: python run_local.py
"""
import os
import sys

# Load environment variables from .env file (for SMTP credentials etc.)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# ---- Must set env vars BEFORE importing any app modules ----
os.environ.setdefault("DATABASE_URL", "sqlite:///./local_db.sqlite")
os.environ.setdefault("USE_LOCAL_QUEUE", "true")
os.environ.setdefault("LOG_LEVEL", "INFO")
os.environ.setdefault("SECRET_KEY", "dev-secret-key-change-in-production-b30366dc7e3dd4840fe1dd8b73f2fa15c")

import threading
import asyncio
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger("LocalRunner")


# CRITICAL: Pre-import the queue module HERE in the main thread.
# This ensures the _local_queue singleton is created once and shared
# by both the API thread and the worker thread via Python's module cache.
from app.utils.redis_client import _local_queue, push_job_to_queue, pop_job_from_queue
logger.info(f"Queue singleton initialized: id={id(_local_queue)}")


def run_worker():
    """Run the automation worker in a background thread with its own event loop."""
    # Verify the worker sees the SAME queue object
    from app.utils.redis_client import _local_queue as wq
    logger.info(f"Worker thread queue id={id(wq)} (must match main thread)")

    from app.workers.worker import worker_loop
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(worker_loop())
    except Exception as e:
        logger.error(f"Worker crashed: {e}", exc_info=True)
    finally:
        loop.close()


def main():
    import uvicorn

    logger.info("=" * 50)
    logger.info("  AutoApply-Ops — Local Development Server")
    logger.info("=" * 50)
    logger.info(f"  Python: {sys.version.split()[0]}")
    logger.info(f"  DB:     SQLite (local_db.sqlite)")
    logger.info(f"  Queue:  In-Memory (no Redis required)")
    logger.info(f"  URL:    http://localhost:8000")
    logger.info("=" * 50)

    # Start worker in background daemon thread
    worker_thread = threading.Thread(target=run_worker, daemon=True, name="AutomationWorker")
    worker_thread.start()
    logger.info(f"Worker thread started (id={worker_thread.ident})")

    # Start FastAPI — this blocks until Ctrl+C
    uvicorn.run(
        "app.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info"
    )


if __name__ == "__main__":
    main()
