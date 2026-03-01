import os
import json
import logging
import queue

logger = logging.getLogger(__name__)

# CRITICAL: The local queue MUST be a module-level singleton that is shared
# between the API thread (pusher) and the Worker thread (consumer).
# Both threads import this module — Python's import system caches modules,
# so they see the same _local_queue object.
_local_queue: queue.Queue = queue.Queue()

USE_LOCAL_QUEUE = os.getenv("USE_LOCAL_QUEUE", "False").lower() == "true"

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_DB = int(os.getenv("REDIS_DB", 0))

redis_client = None
if not USE_LOCAL_QUEUE:
    try:
        import redis as _redis
        pool = _redis.ConnectionPool(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB)
        redis_client = _redis.Redis(connection_pool=pool)
        redis_client.ping()  # Test connection
        logger.info("Redis connection established")
    except Exception as e:
        logger.warning(f"Redis unavailable: {e}. Falling back to local in-memory queue.")
        USE_LOCAL_QUEUE = True


def push_job_to_queue(job_data: dict):
    if USE_LOCAL_QUEUE:
        logger.info(f"[LocalQueue] Pushing job {job_data.get('id')} — queue size now {_local_queue.qsize() + 1}")
        _local_queue.put(json.dumps(job_data))
    else:
        redis_client.rpush("job_queue", json.dumps(job_data))
        logger.info(f"[Redis] Pushed job {job_data.get('id')}")


def pop_job_from_queue():
    if USE_LOCAL_QUEUE:
        try:
            item = _local_queue.get(timeout=1)
            data = json.loads(item)
            logger.info(f"[LocalQueue] Popped job {data.get('id')} — queue size now {_local_queue.qsize()}")
            return data
        except queue.Empty:
            return None
    else:
        try:
            item = redis_client.blpop("job_queue", timeout=5)
            if item:
                return json.loads(item[1])
        except Exception as e:
            logger.warning(f"Redis pop error: {e}")
        return None


def get_queue_size() -> int:
    """Returns number of pending jobs in the queue."""
    if USE_LOCAL_QUEUE:
        return _local_queue.qsize()
    try:
        return redis_client.llen("job_queue") if redis_client else 0
    except Exception:
        return 0
