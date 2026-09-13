import io
from fastapi.testclient import TestClient # Testing for FastAPI
from src.main import app # creates the app instance
from unittest.mock import patch # Used to make mock objects

# Creates a mock HTTP connected to the FastAPI
client = TestClient(app) 

@patch("src.main.process_pdf_task.delay")
def test_upload_pdf_pipeline(mock_celery_delay):

    # Creates an in-memory pdf
    fake_pdf_content = b"%PDF-1.4 Fake PDF Content"
    files = {"file": ("sample.pdf", fake_pdf_content, "application/pdf")}

    mock_celery_delay.return_value.id = "mock-task-id-143"
    
    response = client.post("/upload", files=files)

    assert response.status_code == 200
    data = response.json()
    assert "job_id" in data
    assert data["status"] == "processing"

    mock_celery_delay.assert_called_once_with(data["job_id"], fake_pdf_content)

# Intentionally failing
def test_upload_non_pdf_fails():

    # create non-pdf file
    fake_pdf_content = b"Fake PDF Content"
    files = {"file": ("document.txt", fake_pdf_content, "text/plain")}

    # Upload non-pdf file
    response = client.post("/upload", files=files)

    assert response.status_code == 400
    assert response.json()["detail"] == "File must be a PDF"