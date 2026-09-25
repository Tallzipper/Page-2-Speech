# Page2Speech: Async Document-to-Audio Engine

  This project sets up an asynchronous document-to-speech microservice to convert multi-page PDF files into real-time spoken audio streams. By capturing text internally and processing sentence-level chunks, it eliminates long waits for full audio file rendering. The program directly normalizes text, synthesizes raw PCM audio bytes via a local neural TTS model, and streams them in real time to your browser over WebSockets. 

  The core parsing, worker queue, Redis caching, and WebSocket streaming modules are fully functional, and multi-service Docker orchestration is also done. The last phase before maintaining and adding features is scaling up the infrastructure

  ---

## Demo

- **In Progress:** A live demonstration video/audio sample featuring Page2Speech processing and reading its own project `README` file in real time will be added here.

## Technical Stack

- **Languages:** Python 3.12, C++
- **Frameworks & Tools:** FastAPI, PyMuPDF, PyTorch, Celery, Redis, Uvicorn, Asyncio
- **Hardware & Protocols:** WebSockets, Redis Pub/Sub & Streams

## Roadmap 

- [x] **Local PDF Ingestion & Text Normalization:** Built multi-page PDF parsing via PyMuPDF with custom RegEx normalization for abbreviations, numbers, and currencies.
- [x] **Neural Audio Pipeline:** Integrated local Kokoro-82M TTS engine to generate 16-bit PCM audio byte streams.
- [x] **FastAPI & Celery Integration:** REST endpoints (`/upload`, `/status`) offloading heavy PyTorch execution off main threads into background Celery workers.
- [x] **Real-Time WebSocket Streaming:** Direct chunked audio streaming over WebSockets powered by Redis Streams.
- [x] **Sentence-Level Caching:** SHA-256 sentence hashing stored in Redis to bypass neural model execution on repeated text chunks.
- [x] **Containerized Orchestration:** Multi-stage Docker Compose pipeline binding API gateway, Celery worker, and Redis instances together.
- [ ] **ONNX INT8 Quantization:** Model quantization using ONNX Runtime to reduce RAM footprint and lower inference latency.
- [ ] **Load Testing & Observability:** Locust performance testing suite and Prometheus metrics export for tracking queue depth and P95/P99 latencies.

## Installation Guide (User)

```bash
# Current local setup
git clone https://github.com/your-username/page2speech.git
cd page2speech
docker compose up -d
```

When finished you can open this in your browser through http://localhost:8000/

## Installation Guide (Developers)

```bash
git clone https://github.com/your-username/page2speech.git
cd page2speech
python3.12 -m venv venv

source venv/bin/activate      # if on Linux/macOS:
.\venv\Scripts\Activate.ps1   # or if on Windows PowerShell

pip install -r requirements.txt
pytest tests/test_end_2_end.py::test_pipeline -v -s

```


### Known Issues

> **Note on Issue Tracking:** Core pipeline logic and system completion are prioritized ahead of external issue tracking. The problems below will be made into official 'issues' after it's finished to ensure that nothing is messed with before its entirely what I envisioned

* **Inflexible Input Format:** The API gateway exclusively accepts PDF files (`.pdf`) and rejects other document types like `.docx` or `.txt`.
* **Inaccurate Duration Display:** The media player displays an approximate total file time because raw PCM audio chunks stream dynamically before full synthesis completes.
* **No Direct Download:** The system streams real-time PCM audio chunks directly to browser buffers, with no current option to export or download compiled audio files (`.wav` or `.mp3`).
* **Initial Delay on Large Files:** Multi-page PDF documents require initial sequential parsing and sentence extraction before the first audio chunk starts streaming.

## Author's Note

- The core parsing, task offloading, caching logic, and real-time streaming are fully functional. I want to make sure that this works better for textbooks which is one of my biggest inspirations for making this and I've developed a small plan to ignore page names and other quirks.
