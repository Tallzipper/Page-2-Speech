import redis
from celery import Celery # Only need Celery class
from src.parser import extract_text_chunks
from src.engine import text_to_pcm_stream

# Initializes Celery with Redis
celery_app = Celery(

    "tasks",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/0"

)

redis_client = redis.Redis(host = "localhost", port = 6379, db = 0)

@celery_app.task
def process_pdf_task(job_id: str, file_bytes: bytes):

    # Extracts each sentence from pdf to be processed
    text_chunks = extract_text_chunks(file_bytes)
    channel_name = f"audio_stream:{job_id}" 

    # Have each sentence into audio chunks and push to Redis Pub/Sub 'O(n)'
    for chunk in text_chunks:
        for pcm_bytes in text_to_pcm_stream(chunk):
            redis_client.publish(channel_name, pcm_bytes)

    return {"job_id": job_id, "status": "completed"} #Python Dictionary