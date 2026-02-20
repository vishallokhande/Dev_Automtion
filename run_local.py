import uvicorn
import os
import threading
import asyncio
import logging
from app.workers.worker import worker_loop

# Configuration for Local Run
os.environ["DATABASE_URL"] = "sqlite:///./local_db.sqlite"
os.environ["USE_LOCAL_QUEUE"] = "true"
os.environ["LOG_LEVEL"] = "INFO"

# Setup basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("LocalRunner")

def run_worker():
    logger.info("Starting Worker implementation in background thread...")
    # Create new event loop for the worker thread
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(worker_loop())

def main():
    logger.info("Starting AUTOAPPLY-OPS in Local Simulation Mode")
    logger.info("Using SQLite database and In-Memory Queue")
    
    # Start worker in a separate thread
    t = threading.Thread(target=run_worker, daemon=True)
    t.start()
    
    # Start API
    logger.info("Starting API on http://localhost:8000")
    uvicorn.run("app.api.main:app", host="0.0.0.0", port=8000, reload=False)

if __name__ == "__main__":
    main()
