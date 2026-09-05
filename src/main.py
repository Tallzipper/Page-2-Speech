import uuid
from fastapi import FastAPI, UploadFile, File, HTTPException
from src.celery_app import process_pdf_task, celery_app
from celery.result import AsyncResult

app = FastAPI(title = "Page2Speech Gateway")
@app.post("/upload") # Local system route for 'app' to follow

async def upload_pdf(file: UploadFile = File(...)):

    if not file.filename.endswith(".pdf"): # Not PDF, throw Exception
        raise HTTPException(status_code=400, detail="File must be a PDF")

    job_id = str(uuid.uuid4()) # FastAPI job id

    #reads binary stream and processes it
    contents = await file.read()
    process_pdf_task.delay(job_id, contents)

    return{"job_id": job_id, "status": "processing"} # Sends back job id and status

#Getting the job's status returned to the user from Redis after attempting too complete it
@app.get("/status/{job_id}")
def get_job_status(job_id: str):
    task_result = AsyncResult(job_id, app=celery_app)

    return{
        "job_id": job_id,
        "status": task_result.state,
        "result": task_result.result
    }