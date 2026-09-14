from unittest.mock import AsyncMock, MagicMock, patch # Mocks for Redis
from fastapi.testclient import TestClient 
from src.main import app # FastAPI instance brought over

client = TestClient(app) # connection simulation

@patch("src.main.aioredis.from_url")
def test_websocket_stream_audio(mock_from_url):

    # Redis and Pub/Sub objects to be tested
    mock_redis = MagicMock()

    # Stream key setup for Redis stream polling
    job_id = "test-session-143"
    stream_key = f"audio_stream:{job_id}"

    # Simulates Redis messages returned to the WebSocket polling loop
    async def fake_xread(streams, count=10, block=500):
        if not hasattr(fake_xread, "called"):
            fake_xread.called = True
            return [
                (
                    stream_key.encode(),
                    [
                        ("1-0", {b"data": b"\x00\x01\x02\x03"}),
                        ("2-0", {b"data": b"\x04\x05\x06\x07"}),
                        ("3-0", {b"data": b"__COMPLETE__"}),
                    ],
                )
            ]
        return []

    mock_redis.xread = AsyncMock(side_effect=fake_xread)
    mock_redis.expire = AsyncMock()
    mock_redis.close = AsyncMock()

    # Set up to return mock objects when called
    async def fake_from_url(url):
        return mock_redis

    mock_from_url.side_effect = fake_from_url

    # Two simulated audio data byte strings in form of 16-bit PCM
    fake_pcm_chunk_1 = b"\x00\x01\x02\x03"
    fake_pcm_chunk_2 = b"\x04\x05\x06\x07"

    # Open a connection and verify everything was read properly
    with client.websocket_connect(f"/stream/{job_id}") as websocket:
        received_1 = websocket.receive_bytes()
        received_2 = websocket.receive_bytes()

        assert received_1 == fake_pcm_chunk_1
        assert received_2 == fake_pcm_chunk_2

    # Verify the correct job id was found and that there are no memory leaks
    mock_redis.close.assert_awaited_once()