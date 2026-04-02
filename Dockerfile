# ============================================================
#  MediScan AI Server — Railway Cloud Dockerfile
#  Python 3.11 + CPU-only PyTorch + YOLOv8 + PaddleOCR
# ============================================================

FROM python:3.11-slim

# Install system dependencies needed by OpenCV, PaddleOCR
# Cache bust: v2
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    libgomp1 \
    libfontconfig1 \
    wget \
    && rm -rf /var/lib/apt/lists/*

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
COPY experiments/ ./experiments/
COPY models/ ./models/

# Create data directories
RUN mkdir -p data/uploads data/results

# Expose port (Railway sets PORT env variable)
EXPOSE 8000

# Start the server
# Railway provides PORT env variable, default to 8000
CMD ["sh", "-c", "uvicorn backend.fastapi_app:app --host 0.0.0.0 --port ${PORT:-8000}"]
