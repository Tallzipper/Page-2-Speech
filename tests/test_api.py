import io
from fastapi.testclient import TestClient # Testing for FastAPI
from src.main import app # creates the app instance
from unittest.mock import patch # Used to make mock objects

# Creates a mock HTTP connected to the FastAPI
client = TestClient(app) 

def test_upload_pdf_success():

    # Creates an in-memory pdf
    fake_pdf_bytes = b"%PDF-1.4 Fake PDF Content"
    fake_file = io.BytesIO(fake_pdf_bytes)

    # send a similated HTTP request with the file to /upload
    response = client.post(
        "/upload",
        files={"file": ("sample.pdf", fake_file, "application/pdf")}
    )

    # Verifies that the API returned HTTP 200 and a valid job string ID
    assert response.status_code == 200
    data = response.json()
    assert "job_id" in data
    assert isinstance(data["job_id"], str)

def test_upload_non_pdf_fails():

    # create non-pdf file
    fake_txt_bytes = b"This is a text file"
    fake_file = io.BytesIO(fake_txt_bytes)

    # Upload non-pdf file
    response = client.post(
        "/upload",
        files = {"file": ("document.txt", fake_file, "text/plain")}
    )

    # Expect an error
    assert response.status_code == 400
    assert response.json()["detail"] == "File must be a PDF"


def test_upload_pdf_dispatches_celery_task():

    # Arrange fake text
    fake_pdf_bytes = b"%PDF-1.4 Fake PDF Content"
    fake_file = io.BytesIO(fake_pdf_bytes)

    # Mock Celery task delay
    with patch("src.main.process_pdf_task.delay") as mock_celery_task:
        response = client.post(
            "/upload",
            files={"file": ("sample.pdf", fake_file, "application/pdf")}
        )

        # Verify task was triggered
        # Needs to be in patch for mock obj to be alive
        assert response.status_code == 200
        assert mock_celery_task.called


def test_get_job_status_returns_state():
    #Tests what will be returned after a job is completed

    fake_job_id = "test-job-12345"
    
    with patch("src.main.AsyncResult") as mock_async_result:
        mock_instance = mock_async_result.return_value
        mock_instance.state = "SUCCESS"
        mock_instance.result = {"job_id": fake_job_id, "status": "completed"}

        response = client.get(f"/status/{fake_job_id}")

        assert response.status_code == 200 # Ok status symbol
        assert response.json() == {
            "job_id": fake_job_id,
            "status": "SUCCESS",
            "result": {"job_id": fake_job_id, "status": "completed"}
        }