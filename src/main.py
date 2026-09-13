import uuid
import logging # Error handler
import pathlib
import redis.asyncio as aioredis
from fastapi import FastAPI, UploadFile, File, HTTPException, WebSocket, WebSocketDisconnect
from src.celery_app import process_pdf_task, celery_app
from celery.result import AsyncResult
from fastapi.middleware.cors import CORSMiddleware

logger = logging.getLogger(__name__)

# Storage for PDFs uploaded
UPLOAD_DIR = pathlib.Path("/tmp/uploads")
UPLOAD_DIR.mkdir(parents = True, exist_ok = True)

# Ceiling to not take too many resources
MAX_FILE_SIZE = 100 * 1024 * 1024

app = FastAPI(title = "Page2Speech Gateway")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/upload") # Local system route for 'app' to follow
async def upload_pdf(file: UploadFile = File(...)):

    if not file.filename.endswith(".pdf"): # Not PDF, throw Exception
        raise HTTPException(status_code=400, detail="File must be a PDF")

    job_id = str(uuid.uuid4()) # FastAPI job id
    file_path = UPLOAD_DIR / f"{job_id}.pdf"
    total_bytes = 0

    try:
        with open(file_path, "wb") as buffer:
            while chunk := await file.read(1024 * 1024):
                total_bytes += len(chunk)
                if total_bytes > MAX_FILE_SIZE:
                    raise HTTPException(
                        status_code=413, 
                        detail="File exceeds 100MB limit"
                    )
                buffer.write(chunk)
    except HTTPException:
        file_path.unlink(missing_ok=True)
        raise
    except Exception as e:
        file_path.unlink(missing_ok=True)
        logger.error(f"Failed to save upload for {job_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error during upload")

    # Reads binary stream and processes it through Celery
    process_pdf_task.delay(job_id, str(file_path))

    return {"job_id": job_id, "status": "processing"} # Sends back job id and status


# Getting the job's status returned to the user from Redis after attempting too complete it
@app.get("/status/{job_id}")
def get_job_status(job_id: str):
    task_result = AsyncResult(job_id, app=celery_app)

    return{
        "job_id": job_id,
        "status": task_result.state,
        "result": task_result.result
    }


# Bridges Pub/Sub events to a WebSocket connection to reduce latency
@app.websocket("/stream/{job_id}")
async def stream_audio(websocket: WebSocket, job_id: str):

    await websocket.accept() # Handshake

    # Connects to the redis server and defines channel name 
    
    redis_connection = None
    stream_key = f"audio_stream:{job_id}"
    last_id = "0-0" # start of stream

    # Grabs events while waiting for audio
    try:
        redis_connection = await aioredis.from_url("redis://localhost:6379/0") 
        while True: # Until out of audio or disconnection

            response = await redis_connection.xread(
                {stream_key: last_id}, count=10, block=1000
            )
            if not response:
                continue

            for stream_name, messages in response:
                for message_id, fields in messages:
                    last_id = message_id  # Advance stream cursor to prevent duplicate sends
                    data = fields[b"data"]

                    if data == b"__COMPLETE__":
                        await websocket.close(code=1000, reason="Stream completed")
                        return

                    await websocket.send_bytes(data)

    #Exiting safely
    except WebSocketDisconnect:
        logger.info(f"Client disconnected from stream: {job_id}")
    except aioredis.RedisError as re:
        logger.error(f"Redis stream error for job {job_id}: {re}")
        await websocket.close(code=1011, reason="Stream storage failure")
    except Exception as e:
        logger.error(f"Unexpected error in WebSocket stream {job_id}: {e}")
        await websocket.close(code=1011, reason="Internal server error")
    finally:
        if redis_connection:
            await redis_connection.close()