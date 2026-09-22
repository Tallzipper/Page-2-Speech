import io 
import os
import pytest
import pymupdf
import asyncio
import requests 
import websockets 
from websockets.exceptions import ConnectionClosedOK
import time

API_URL = os.getenv("API_URL", "http://localhost:8000")
WS_URL = os.getenv("WS_URL", "ws://localhost:8000")

def generate_in_memory_pdf() -> bytes:
    doc = pymupdf.open()
    page = doc.new_page()
    page.insert_text((50, 50), "Welcome to Page 2 Speech! Testing audio pipeline.")
    pdf_bytes = doc.write()
    doc.close()
    return pdf_bytes

# If server isn't up, fail
@pytest.fixture(scope="module", autouse=True)
def ensure_api_online():
    try: # Given three seconds to confirm server
        response = requests.get(f"{API_URL}/docs", timeout=3)
        assert response.status_code == 200
    except (requests.exceptions.ConnectionError, AssertionError):
        pytest.fail(f"API service is unreachable at {API_URL}. Ensure 'docker compose up' is running.")

@pytest.mark.asyncio
async def test_e2e_pipeline():

    pdf_bytes = generate_in_memory_pdf()
    files = {"file": ("sample.pdf", pdf_bytes, "application/pdf")}

    response = requests.post(f"{API_URL}/upload", files=files)
    assert response.status_code == 200, f"Upload failed: {response.text}"

    data = response.json()
    assert "job_id" in data
    job_id = data["job_id"]

    uri = f"{WS_URL}/stream/{job_id}"
    start_time = time.time()

    chunk_count = 0
    total_bytes = 0                         

    async with websockets.connect(uri) as websocket:
        try:
            while True:
                data = await asyncio.wait_for(websocket.recv(), timeout=30.0)

                if data == b"__COMPLETE__":
                    break

                chunk_count += 1
                total_bytes += len(data)

        except ConnectionClosedOK:
            pass 
        except asyncio.TimeoutError:
            pytest.fail(f"WebSocket timed out waiting for audio on job {job_id}")

    assert chunk_count > 0,"No audio chunks received from worker"
    assert total_bytes > 0,"Received empty audio stream payload"
