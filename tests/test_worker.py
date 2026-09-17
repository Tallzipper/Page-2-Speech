import hashlib
import pytest
from unittest.mock import call, patch
from src.celery_app import process_pdf_task

# Mock objects for test
@pytest.fixture
def mock_extract():
    with patch("src.celery_app.extract_text_chunks") as mock:
        yield mock

@pytest.fixture
def mock_tts():
    with patch("src.celery_app.text_to_pcm_stream") as mock:
        yield mock

@pytest.fixture
def mock_redis():
    with patch("src.celery_app.redis_client") as mock:
        yield mock

# Mock object of the parser created to scan test with a mock neural engine on a mock redis server
def test_multi_sentence_pdf_task_success(mock_extract, mock_tts, mock_redis, tmp_path):
    # Setting up test variables and values
    fake_job_id = "job-456" 
    
    # Create temporary file to pass as file path
    fake_file = tmp_path / "test.pdf"
    fake_file.write_bytes(b"%PDF-1.4 Fake PDF Data") # File signature to know how to exteact

    sentences = ["Sentence one.", "Sentence two."]
    mock_extract.return_value = sentences
    mock_tts.side_effect = [ # Calling behavietor dynamically alloiwing for loop
        (chunk for chunk in [b"\x00\x01"]),
        (chunk for chunk in [b"\x02\x03"])
    ]
    mock_redis.get.return_value = None

    process_pdf_task(fake_job_id, str(fake_file)) # Runs the Celery worker

    # Ensures two sentences were found with the same bytes and sentence content
    mock_extract.assert_called_once_with(b"%PDF-1.4 Fake PDF Data")
    # CHANGED: Replaced invalid `assert mock_tts.assert_has_calls(...)` with valid `mock_tts.assert_has_calls([call(...)])` syntax.
    mock_tts.assert_has_calls([
        call(sentences[0]),
        call(sentences[1])
    ])

    # Verify Redis' stream output, ordered
    stream_key = f"audio_stream:{fake_job_id}"
    # CHANGED: Replaced raw tuples with `call(...)` objects so `assert_has_calls` correctly evaluates argument signatures and keyword dicts.
    expected_stream_calls = [
        call(stream_key, {"data": b"\x00\x01"}),
        call(stream_key, {"data": b"\x02\x03"}),
        call(stream_key, {"data": b"__COMPLETE__"}),
    ]
    # CHANGED: Removed invalid `assert` prefix from mock method call (`mock_redis.xadd.assert_has_calls` returns None).
    mock_redis.xadd.assert_has_calls(expected_stream_calls, any_order=False)

# Verifys that a sentence wasn't created so it creates a hash, caches it, and sends it out
def test_sha256_cache_miss_stores_audio(mock_extract, mock_tts, mock_redis, tmp_path):

    # Fake file setup
    fake_job_id = "job-cache-miss"
    fake_file = tmp_path / "test.pdf"
    fake_file.write_bytes(b"%PDF-1.4 Fake PDF Data")

    # Creating a hex hash for the fake sentense to be tested
    sentence = "Testing cache miss behavior."
    expected_hash = hashlib.sha256(sentence.encode("utf-8")).hexdigest()
    expected_cache_key = f"cache:audio:{expected_hash}"

    # Set the value to be returned and creates fake audio bytes
    mock_extract.return_value = [sentence]
    mock_tts.side_effect = [(chunk for chunk in [b"\x10\x20"])]
    mock_redis.get.return_value = None

    # Execute Celery
    process_pdf_task(fake_job_id, str(fake_file))

    # Since the cache doesn't exist, checks if one was created for it 
    mock_tts.assert_called_once_with(sentence) 
    mock_redis.get.assert_called_once_with(expected_cache_key)
    mock_redis.setex.assert_called_once_with(expected_cache_key, 86400, b"\x10\x20")

    # Checks if the new audio was pushed to the stream 
    stream_key = f"audio_stream:{fake_job_id}"
    mock_redis.xadd.assert_any_call(stream_key, {"data": b"\x10\x20"})    


# Demonstrates a cached sentences bypasses TTS since already synthesized and reuses existing Redis audio
def test_sha256_cache_hit_bypasses_tts(mock_extract, mock_tts, mock_redis, tmp_path):

    # Fake File set up
    fake_job_id = "job-cache-hit"
    fake_file = tmp_path / "test.pdf"
    fake_file.write_bytes(b"%PDF-1.4 Fake PDF Data")

    # Encodes a sentence into a SHA-256 Hex hash for test sentence
    sentence = "Testing cache hit behavior."
    expected_hash = hashlib.sha256(sentence.encode("utf-8")).hexdigest()
    expected_cache_key = f"cache:audio:{expected_hash}"

    # Simulate a redis cache by returning pre-cached audio
    mock_extract.return_value = [sentence]
    mock_redis.get.return_value = b"\x10\x20"
    process_pdf_task(fake_job_id, str(fake_file))

    mock_tts.assert_not_called() # Pytorch TTS bypassed
    mock_redis.get.assert_called_once_with(expected_cache_key)  # Redis cache was checked
    mock_redis.setex.assert_not_called() # No new cache was written

    # Pre-cached auio pushed to Redis
    stream_key = f"audio_stream:{fake_job_id}"
    mock_redis.xadd.assert_any_call(stream_key, {"data": b"\x10\x20"})