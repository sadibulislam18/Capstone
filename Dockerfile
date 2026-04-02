# ============================================================
#  MediScan AI Server — Railway Cloud Dockerfile
#  Python 3.11 + CPU-only PyTorch + YOLOv8 + PaddleOCR
# ============================================================

FROM python:3.11-slim

# Install system dependencies needed by OpenCV, PaddleOCR, and Git LFS
# Cache bust: v3
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    libgomp1 \
    libfontconfig1 \
    wget \
    git \
    git-lfs \
    && git lfs install \
    && rm -rf /var/lib/apt/lists/*

# Disable PaddlePaddle PIR mode (causes crashes on Railway CPU)
ENV FLAGS_enable_pir_api=0
ENV FLAGS_enable_pir_in_executor=0
ENV PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK=True

# Set working directory
WORKDIR /app

# Copy requirements first (Docker layer caching)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy entire project
COPY backend/ ./backend/
COPY src/ ./src/

# Clone repo and pull LFS files (actual .pt model weights)
# Uses build arg for private repo access
ARG GITHUB_TOKEN
RUN git clone https://${GITHUB_TOKEN}@github.com/sadibulislam18/Capstone.git /tmp/repo && \
    cd /tmp/repo && git lfs pull && \
    cp -r /tmp/repo/experiments /app/experiments && \
    cp -r /tmp/repo/models /app/models && \
    rm -rf /tmp/repo

# Create data directories
RUN mkdir -p data/uploads data/results

# Expose port (Railway sets PORT env variable)
EXPOSE 8000

# Start the server
# Railway provides PORT env variable, default to 8000
CMD ["/bin/sh", "-c", "uvicorn backend.fastapi_app:app --host 0.0.0.0 --port ${PORT:-8000}"]
