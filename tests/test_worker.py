from unittest.mock import patch
from src.celery_app import process_pdf_task

# Mock object of the parser created to scan test with a mock neural engine on a mock redis server
@patch("src.celery_app.redis_client")
@patch("src.celery_app.text_to_pcm_stream")
@patch("src.celery_app.extract_text_chunks")
def test_multi_sentence_pdf_task_success(mock_extract, mock_tts, mock_redis, tmp_path):
    # Setting up test variables and values
    fake_job_id = "job-456" 
    
    # Create temporary file to pass as file path
    fake_file = tmp_path / "test.pdf"
    fake_file.write_bytes(b"%PDF-1.4 Fake PDF Data") # File signature to know how to exteact

    mock_extract.return_value = ["Sentence one.", "Sentence two."]
    mock_tts.side_effect = [[b"\x00\x01"], [b"\x02\x03"]] # Calling behavior dynamically alloiwing for loop

    process_pdf_task(fake_job_id, str(fake_file)) # Runs the Celery worker

    # Ensures two sentences were found with the same bytes and sentence content
    mock_extract.assert_called_once_with(b"%PDF-1.4 Fake PDF Data")
    
    assert mock_tts.call_count == 2
    assert mock_redis.xadd.call_count == 3 # 3 since checking for "__COMPLETE"

    stream_key = f"audio_stream:{fake_job_id}"
    mock_redis.xadd.assert_any_call(stream_key, {"data": b"\x00\x01"})
    mock_redis.xadd.assert_any_call(stream_key, {"data": b"\x02\x03"})
    mock_redis.xadd.assert_any_call(stream_key, {"data": b"__COMPLETE__"})