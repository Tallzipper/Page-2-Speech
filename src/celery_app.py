import hashlib
import pathlib
import logging 
import redis
import os
from celery import Celery # Only need Celery class
from src.parser import extract_text_chunks
from src.engine import text_to_pcm_stream

logger = logging.getLogger(__name__)

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# Initializes Celery with Redis
celery_app = Celery(
    "tasks",
    broker=REDIS_URL,
    backend=REDIS_URL
)

redis_client = redis.Redis.from_url(REDIS_URL)

@celery_app.task
def process_pdf_task(job_id: str, file_path: str):

    if isinstance(file_path, bytes):
        file_path = file_path.decode("utf-8")

    path = pathlib.Path(file_path)
    stream_key = f"audio_stream:{job_id}"

    try:
        with open(path, "rb") as f:
            pdf_bytes = f.read()

        text_chunks = extract_text_chunks(pdf_bytes)

        # Gets hash sentence cache and checks Redis to see if each sentence was at one point processed
        for chunk in text_chunks:
            sentence_hash = hashlib.sha256(chunk.encode("utf-8")).hexdigest()
            cache_key = f"cache:audio:{sentence_hash}"

            cached_pcm = redis_client.get(cache_key)

            if cached_pcm is not None: # Scanned before, send existing sentence
                redis_client.xadd(stream_key, {"data": cached_pcm})
            else: # Never scanned, process it
                accumulated_pcm = bytearray()
                for pcm_bytes in text_to_pcm_stream(chunk):
                    redis_client.xadd(stream_key, {"data": pcm_bytes})
                    accumulated_pcm.extend(pcm_bytes)

                if accumulated_pcm: # If now exists, store it for 24 hours
                    redis_client.setex(cache_key, 86400, bytes(accumulated_pcm))

        redis_client.xadd(stream_key, {"data": b"__COMPLETE__"})
        redis_client.expire(stream_key, 3600)

        return {"job_id": job_id, "status": "completed"} 
    except Exception as e:
        logger.error(f"Task failed for job {job_id}: {e}")
        raise e
    # Cleanup
    finally: 
        if path.exists():
            path.unlink()