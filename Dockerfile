FROM python:3.12-slim

# No .pyc files and unbuffered logging enabled
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install PyMuPDF / C++ Build requirements
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install python dependancies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Starting command, overrides original to isolate each service
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
