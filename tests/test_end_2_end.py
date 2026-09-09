from unittest.mock import patch
from fastapi.testclient import TestClient
from src.main import app
from src.celery_app import celery_app

# Create in-memory FastAPI test client (no live Uvicorn server needed)
client = TestClient(app)

@patch("src.celery_app.redis_client")
@patch("src.celery_app.text_to_pcm_stream")
@patch("src.celery_app.extract_text_chunks")
def test_end_to_end_streaming_pipeline(
    mock_extract_text_chunks, mock_text_to_pcm_stream, mock_redis_client
):
    celery_app.conf.task_always_eager = True

    # Setup test fixtures
    fake_pdf_bytes = b"%PDF-1.4 Fake PDF Data"
    mock_extract_text_chunks.return_value = ["Sentence one.", "Sentence two."]
    mock_text_to_pcm_stream.side_effect = [[b"\x00\x01"], [b"\x02\x03"]]

    # 1. POST file upload to FastAPI
    response = client.post(
        "/upload",
        files={"file": ("you_belong_with_me.pdf", fake_pdf_bytes, "application/pdf")}
    )

    # 2. Verify API response
    assert response.status_code == 200
    json_data = response.json()
    assert "job_id" in json_data
    assert json_data["status"] == "processing"

    job_id = json_data["job_id"]

    # 3. Verify parser extracted text from raw PDF bytes
    mock_extract_text_chunks.assert_called_once_with(fake_pdf_bytes)

    # 4. Verify PCM streaming engine and Redis Pub/Sub were invoked for both sentences
    assert mock_text_to_pcm_stream.call_count == 2
    assert mock_redis_client.publish.call_count == 2
    mock_redis_client.publish.assert_any_call(f"audio_stream:{job_id}", b"\x00\x01")
    mock_redis_client.publish.assert_any_call(f"audio_stream:{job_id}", b"\x02\x03")