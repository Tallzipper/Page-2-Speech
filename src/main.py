import uuid
import logging # Error handler
import tempfile
import redis.asyncio as aioredis
from fastapi import FastAPI, UploadFile, File, HTTPException, WebSocket, WebSocketDisconnect
from src.celery_app import process_pdf_task, celery_app
from celery.result import AsyncResult

logger = logging.getLogger(__name__)

app = FastAPI(title = "Page2Speech Gateway")

@app.post("/upload") # Local system route for 'app' to follow
async def upload_pdf(file: UploadFile = File(...)):

    if not file.filename.endswith(".pdf"): # Not PDF, throw Exception
        raise HTTPException(status_code=400, detail="File must be a PDF")

    job_id = str(uuid.uuid4()) # FastAPI job id

    # Send chunks to a temp file at small bits at a time and read
    with tempfile.NamedTemporaryFile(delete=True) as temp_file:
        while chunk := await file.read(1024 * 1024):
            temp_file.write(chunk)
        temp_file.flush()
        temp_file.seek(0)
        contents = temp_file.read()
        
    # Reads binary stream and processes it through Celery
    process_pdf_task.delay(job_id, contents)

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
    redis_connection = await aioredis.from_url("redis://localhost:6379/0")
    pubsub = redis_connection.pubsub()
    channel_name = f"audio_stream:{job_id}"
    await pubsub.subscribe(channel_name)

    # Grabs events while waiting for audio
    try:
        async for message in pubsub.listen():

            if message["type"] != "message":
                continue

            data = message["data"]

            # Check if celery said file is done
            if data == b"__COMPLETE__":
                await websocket.close(code=1000, reason="Stream completed")
                break

            # Send binary PCM chunk to user
            await websocket.send_bytes(data)

    #Exiting safely
    except WebSocketDisconnect:
        logger.info(f"Client disconnected from stream: {job_id}")
    except Exception as e:
        logger.error(f"Unexpected error in WebSocket stream {job_id}: {e}")
    finally:
        try:
            await pubsub.unsubscribe(channel_name)
            await pubsub.close()
            await redis_connection.close()
        except Exception:
            pass