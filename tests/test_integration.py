import io
import pymupdf
import pytest 
import redis 

from src.celery_app import celery_app, process_pdf_task

def is_redis_available()->bool:
    try:
        r = redis.Redis(host="localhost", port=6379, db=0, socket_timeout=1.0)
        return r.ping()
    except (redis.exceptions.ConnectionError, redis.exceptions.TimeoutError):
        return False
        

@pytest.fixture(autouse=True)
def setup_celery_eager():
    celery_app.conf.task_always_eager = True
    celery_app.conf.task_eager_propagates = True

def create_sample_pdf_bytes() -> bytes:
    doc = pymupdf.open()
    page = doc.new_page()
    page.insert_text((50, 50), "Hello world. Testing integration pipeline.")
    pdf_bytes = doc.write()
    doc.close() 
    return pdf_bytes 

# test will only work if Redis is currently active
@pytest.mark.skipif(
    not is_redis_available(),
    reason = "Live Redis instance not running on localhost:6379"
)
def test_pdf_processing_integration():

    # Setup
    job_id = "test-integration-session"
    channel_name = f"audio_stream:{job_id}"
    pdf_bytes = create_sample_pdf_bytes()

    # Connect to live Redis
    r = redis.Redis(host="localhost", port=6379, db=0)
    pubsub = r.pubsub()
    pubsub.subscribe(channel_name)

    # Check if connection was established
    sub_msg = pubsub.get_message(timeout=1.0)
    assert sub_msg is not None and sub_msg["type"] == "subscribe"

    # Start and verify Celery
    result = process_pdf_task(job_id, pdf_bytes)
    assert result["status"] == "completed"

    # Reads audio chunks from Redis
    audio_chunks = []
    while True:
        msg = pubsub.get_message(timeout=2.0)
        if not msg:
            break
        if msg["type"] == "message":
            audio_chunks.append(msg["data"])

   #Close and ensure audio bytes were generated and pushed
    pubsub.unsubscribe(channel_name)
    assert len(audio_chunks) > 0
    assert all(isinstance(chunk, bytes) and len(chunk) > 0 for chunk in audio_chunks)