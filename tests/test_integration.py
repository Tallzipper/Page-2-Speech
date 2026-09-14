import io
import pathlib
import pymupdf
import pytest 
import redis 

from src.celery_app import celery_app, process_pdf_task

def is_redis_available() -> bool:
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
def test_pdf_processing_integration(tmp_path):

    # Setup
    job_id = "test-integration-session"
    stream_key = f"audio_stream:{job_id}"
    pdf_bytes = create_sample_pdf_bytes()

    # Save bytes to a temporary path on disk as expected by process_pdf_task
    file_path = tmp_path / f"{job_id}.pdf"
    file_path.write_bytes(pdf_bytes)

    # Connect to live Redis
    r = redis.Redis(host="localhost", port=6379, db=0)

    # Start and verify Celery task execution
    result = process_pdf_task(job_id, str(file_path))
    assert result["status"] == "completed"

    # Reads audio chunks from Redis Stream (xread) instead of Pub/Sub
    audio_chunks = []
    stream_data = r.xread({stream_key: "0-0"}, count=100, block=2000)

    if stream_data:
        for stream_name, messages in stream_data:
            for message_id, fields in messages:
                # Extract payload bytes from stream record
                payload = fields.get(b"data")
                if payload:
                    audio_chunks.append(payload)

    # Ensure audio bytes and completion signals were generated and pushed to stream
    assert len(audio_chunks) > 0
    assert any(chunk == b"__COMPLETE__" for chunk in audio_chunks)