import os
import redis
import json
import logging
import queue

logger = logging.getLogger(__name__)

# Global in-memory queue for local testing without Redis
_local_queue = queue.Queue()

USE_LOCAL_QUEUE = os.getenv("USE_LOCAL_QUEUE", "False").lower() == "true"

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_DB = int(os.getenv("REDIS_DB", 0))

redis_client = None
if not USE_LOCAL_QUEUE:
    try:
        pool = redis.ConnectionPool(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB)
        redis_client = redis.Redis(connection_pool=pool)
    except Exception as e:
        logger.warning(f"Failed to connect to Redis: {e}. Falling back to local queue if allowed, or errors will occur.")

def push_job_to_queue(job_data: dict):
    if USE_LOCAL_QUEUE:
        logger.info("Pushing to local in-memory queue")
        _local_queue.put(json.dumps(job_data))
    else:
        if redis_client:
            redis_client.rpush("job_queue", json.dumps(job_data))
        else:
            logger.error("Redis client not initialized and local queue is disabled.")

def pop_job_from_queue():
    if USE_LOCAL_QUEUE:
        try:
            # Non-blocking get with timeout to simulate behavior
            item = _local_queue.get(timeout=1) 
            return json.loads(item)
        except queue.Empty:
            return None
    else:
        if redis_client:
            # Blocking pop
            try:
                item = redis_client.blpop("job_queue", timeout=5)
                if item:
                    return json.loads(item[1])
            except redis.exceptions.ConnectionError:
                pass
        return None

# For the worker to directly access the queue if needed in loop
def get_local_queue():
    return _local_queue
