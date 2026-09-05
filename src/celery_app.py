import time
from celery import Celery # Only need Celery class

# Initializes Celery with Redis
celery_app = Celery(

    "tasks",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/0"

)

@celery_app.task

def process_pdf_task(job_id: str, file_bytes: bytes):

    # Simulates processing delay
    time.sleep(2)

    return {"job_id": job_id, "status": "completed"} #Python Dictionary