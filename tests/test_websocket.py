from unittest.mock import AsyncMock, MagicMock, patch # Mocks for Redis
from fastapi.testclient import TestClient 
from src.main import app # FastAPI instance brought over

client = TestClient(app) # connection simulation

async def mock_listen_generator():
    yield {"type": "message", "data": b"\x00\x01\x02\x03"}
    yield {"type": "message", "data": b"\x04\x05\x06\x07"}
    yield {"type": "message", "data": b"__COMPLETE__"}

@patch("src.main.aioredis.from_url")
def test_websocket_stream_audio(mock_from_url):

    # Redis and Pub/Sub objects to be tested
    mock_redis = MagicMock()
    mock_pubsub = MagicMock()

    # Set up to return mock objects when called
    async def fake_from_url(url):
        return mock_redis

    mock_from_url.side_effect = fake_from_url
    mock_redis.pubsub = MagicMock(return_value=mock_pubsub)
    mock_redis.close = AsyncMock()

    # Allow async calls on subscribe/unsubscribe/close
    mock_pubsub.subscribe = AsyncMock()
    mock_pubsub.unsubscribe = AsyncMock()
    mock_pubsub.close = AsyncMock()

    # Two simulated audio data byte strings in form of 16-bit PCM
    fake_pcm_chunk_1 = b"\x00\x01\x02\x03"
    fake_pcm_chunk_2 = b"\x04\x05\x06\x07"

    # Simulates Redis messages returned to the WebSocket polling loop
    mock_pubsub.listen = mock_listen_generator

    job_id = "test-session-143"

    # Open a connection and verify everything was read properly
    with client.websocket_connect(f"/stream/{job_id}") as websocket:
        received_1 = websocket.receive_bytes()
        received_2 = websocket.receive_bytes()

        assert received_1 == fake_pcm_chunk_1
        assert received_2 == fake_pcm_chunk_2

    # Verify the correct job id was found and that there are no memory leaks
    mock_pubsub.subscribe.assert_awaited_once_with(f"audio_stream:{job_id}")
    mock_pubsub.unsubscribe.assert_awaited_once_with(f"audio_stream:{job_id}")
    mock_pubsub.close.assert_awaited_once()
    mock_redis.close.assert_awaited_once()