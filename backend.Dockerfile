FROM python:3.11-slim

WORKDIR /workspace

# Install system dependencies for OpenCV and other packages
RUN apt-get update && apt-get install -y \
    build-essential \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Copy dependencies list
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir uvicorn aiosqlite celery redis passlib bcrypt pyjwt pillow

# Copy source code files
COPY backend/ /workspace/backend/

ENV PYTHONPATH=/workspace

EXPOSE 8000
