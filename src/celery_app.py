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

    # Get the audio chunks and if you can't send an error
    try:
        with open(path, "rb") as f:
            pdf_bytes = f.read()

        text_chunks = extract_text_chunks(pdf_bytes)

        # Have each sentence into audio chunks and push to Redis Pub/Sub 'O(n)'
        for chunk in text_chunks:
            for pcm_bytes in text_to_pcm_stream(chunk):
                redis_client.xadd(stream_key, {"data": pcm_bytes})

        redis_client.xadd(stream_key, {"data": b"__COMPLETE__"}) # Notifies gateway its done
        redis_client.expire(stream_key, 3600) # 1 hour experation

        return {"job_id": job_id, "status": "completed"} 
    except Exception as e:
        logger.error(f"Task failed for job {job_id}: {e}")
        raise e
    # Cleanup
    finally: 
        if path.exists():
            path.unlink()