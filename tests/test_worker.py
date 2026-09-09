from unittest.mock import patch
from src.celery_app import process_pdf_task

# Mock object of the parser created to scan test with a mock neural engine on a mock redis server
@patch("src.celery_app.redis_client")
@patch("src.celery_app.text_to_pcm_stream")
@patch("src.celery_app.extract_text_chunks")
def test_multi_sentence_pdf_task_success(
    mock_extract_text_chunks, mock_text_to_pcm_stream, mock_redis_client
):
    # Setting up test variables and values
    fake_job_id = "job-456" 
    fake_pdf_bytes = b"%PDF-1.4 Fake PDF Data" # File signature to know how to exteact 
    mock_extract_text_chunks.return_value = ["Sentence one.", "Sentence two."]
    mock_text_to_pcm_stream.side_effect = [[b"\x00\x01"], [b"\x02\x03"]] # Calling behavior dynamically alloiwing for loop

    process_pdf_task(fake_job_id, fake_pdf_bytes) # Runs the Celery worker

    # Ensures two sentences were found with the same bytes and sentence content
    mock_extract_text_chunks.assert_called_once_with(fake_pdf_bytes)
    assert mock_text_to_pcm_stream.call_count == 2
    assert mock_redis_client.publish.call_count == 2
    mock_redis_client.publish.assert_any_call(f"audio_stream:{fake_job_id}", b"\x00\x01")
    mock_redis_client.publish.assert_any_call(f"audio_stream:{fake_job_id}", b"\x02\x03")