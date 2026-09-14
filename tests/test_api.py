import io
import pathlib
from fastapi.testclient import TestClient  # Testing for FastAPI
from src.main import app  # creates the app instance
from unittest.mock import patch  # Used to make mock objects

# Creates a mock HTTP connected to the FastAPI
client = TestClient(app) 

@patch("src.main.process_pdf_task.apply_async")
def test_upload_pdf_pipeline(mock_celery_async):

    # Creates an in-memory pdf
    fake_pdf_content = b"%PDF-1.4 Fake PDF Content"
    files = {"file": ("sample.pdf", fake_pdf_content, "application/pdf")}

    response = client.post("/upload", files=files)

    assert response.status_code == 200
    data = response.json()
    assert "job_id" in data
    assert data["status"] == "processing"

    # Verify apply_async was called and inspect the actual arguments passed by main.py
    assert mock_celery_async.called
    call_kwargs = mock_celery_async.call_args.kwargs

    called_job_id, called_path_str = call_kwargs["args"]
    
    # Assert the task was dispatched with the same job_id returned to the client
    assert called_job_id == data["job_id"]
    assert call_kwargs["task_id"] == data["job_id"]
    
    # Construct OS-native path using pathlib to ensure Windows & Linux compatibility
    expected_path_str = str(pathlib.Path("/tmp/uploads") / f"{data['job_id']}.pdf")
    assert called_path_str == expected_path_str

# Non-PDF upload rejection test
def test_upload_non_pdf_fails():

    # create non-pdf file
    fake_pdf_content = b"Fake PDF Content"
    files = {"file": ("document.txt", fake_pdf_content, "text/plain")}

    # Upload non-pdf file
    response = client.post("/upload", files=files)

    assert response.status_code == 400
    assert response.json() == {"detail": "File must be a PDF"}