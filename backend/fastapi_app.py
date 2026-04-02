"""
FastAPI Backend Server - V6 Pipeline
=====================================
REST API for prescription processing using:
- Image Quality Pre-check (ResNet18 + Laplacian blur detection)
- YOLOv8 v6 (9 classes) for field detection
- PaddleOCR (English) for text recognition
- Structured medication grouping

Author: MediScan Project
Version: 6.1 (Feb 2026)
"""

# ── MUST BE SET BEFORE ANY PaddlePaddle imports ──
import os
os.environ['FLAGS_enable_pir_api'] = '0'
os.environ['FLAGS_enable_pir_in_executor'] = '0'
os.environ['FLAGS_pir_apply_inplace_pass'] = '0'
os.environ['PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK'] = 'True'

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from pathlib import Path
import shutil
import uuid
import json
import base64
import cv2
import numpy as np
from datetime import datetime
import logging
import torch

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="MediScan - AI Prescription Digitization API",
    description="Extract structured medication data from prescription images using Quality Check + YOLO + PaddleOCR",
    version="6.1.0"
)

# CORS middleware (allows Kotlin app to connect)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your app's domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global extractor instance
extractor = None
quality_checker = None

# Storage directories
UPLOAD_DIR = Path("data/uploads")
RESULTS_DIR = Path("data/results")
for d in [UPLOAD_DIR, RESULTS_DIR]:
    d.mkdir(parents=True, exist_ok=True)


@app.on_event("startup")
async def startup_event():
    """Initialize AI models on startup."""
    global extractor, quality_checker
    
    logger.info("=" * 70)
    logger.info("  STARTING MEDISCAN API SERVER V6.1")
    logger.info("=" * 70)
    
    # Device detection: MPS (Apple Silicon) → CUDA → CPU
    if torch.backends.mps.is_available():
        _device_name = "mps (Apple Silicon GPU)"
    elif torch.cuda.is_available():
        _device_name = f"cuda ({torch.cuda.get_device_name(0)})"
    else:
        _device_name = "cpu"
    logger.info(f"🚀 MediScan AI Backend — Device: {_device_name}")

    # Force CPU on cloud (no MPS/CUDA available)
    import os
    if os.environ.get("RAILWAY_ENVIRONMENT"):
        logger.info("☁️  Running on Railway Cloud — CPU mode")

    logger.info("Loading AI models...")
    
    # Import here to avoid import issues at module level
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent))
    
    from src.pipeline.structured_extractor import StructuredPrescriptionExtractor
    from src.preprocessing.quality_checker import get_quality_checker
    
    extractor = StructuredPrescriptionExtractor(use_gpu=torch.cuda.is_available())
    quality_checker = get_quality_checker()
    
    logger.info("=" * 70)
    logger.info("API Server Ready!")
    logger.info("  Docs: http://localhost:8000/docs")
    logger.info("  Health: http://localhost:8000/health")
    logger.info("=" * 70)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "app": "MediScan - AI Prescription Digitization",
        "version": "6.1.0",
        "pipeline": "Quality Check + YOLOv8 (9-class) + PaddleOCR (English)",
        "docs": "/docs",
        "health": "/health"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "cuda_available": torch.cuda.is_available(),
        "gpu_name": torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,
        "model_loaded": extractor is not None,
        "quality_checker_loaded": quality_checker is not None,
        "pipeline_version": "v6_9class_english",
        "ocr_engine": "paddleocr"
    }


@app.post("/check-quality")
async def check_image_quality(file: UploadFile = File(...)):
    """
    Check image quality before full extraction.
    
    Quick check (~50ms) to determine if the image is clear enough
    for reliable prescription extraction. Use this for real-time
    camera feedback in the Kotlin app.
    
    Returns:
        JSON with quality assessment including:
        - is_acceptable: bool
        - quality_label: 'good' or 'bad'
        - quality_score: 0-1 confidence
        - issues: list of detected problems
        - recommendation: user-facing message
    """
    if quality_checker is None:
        raise HTTPException(status_code=503, detail="Quality checker not loaded yet")
    
    if not file.content_type or not file.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    try:
        # Read image
        contents = await file.read()
        img_array = np.frombuffer(contents, dtype=np.uint8)
        image = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
        
        if image is None:
            raise HTTPException(status_code=400, detail="Could not decode image")
        
        # Run quality check
        result = quality_checker.check(image)
        
        # Remove CNN internal details from response
        cnn = result.pop('cnn_prediction', None)
        
        return JSONResponse(content=result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Quality check error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/check-quality-base64")
async def check_quality_base64(data: dict):
    """
    Check quality from base64-encoded image (for Kotlin app).
    
    Args:
        data: {"image": "base64_encoded_image_string"}
    """
    if quality_checker is None:
        raise HTTPException(status_code=503, detail="Quality checker not loaded yet")
    
    image_b64 = data.get("image", "")
    if not image_b64:
        raise HTTPException(status_code=400, detail="No image data provided")
    
    try:
        img_bytes = base64.b64decode(image_b64)
        img_array = np.frombuffer(img_bytes, dtype=np.uint8)
        image = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
        
        if image is None:
            raise HTTPException(status_code=400, detail="Could not decode image")
        
        result = quality_checker.check(image)
        result.pop('cnn_prediction', None)
        
        return JSONResponse(content=result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Quality check base64 error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/extract")
async def extract_prescription(file: UploadFile = File(...)):
    """
    Extract structured data from a prescription image.
    
    Returns grouped medications with dose, schedule, duration,
    plus doctor info and prescription metadata.
    
    Args:
        file: Prescription image (JPG, PNG)
    
    Returns:
        JSON with structured prescription data
    """
    if extractor is None:
        raise HTTPException(status_code=503, detail="Models not loaded yet")
    
    if not file.content_type or not file.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    try:
        # Generate task ID
        task_id = str(uuid.uuid4())[:8]
        logger.info(f"[{task_id}] Processing: {file.filename}")
        
        # Save uploaded file
        upload_path = UPLOAD_DIR / f"{task_id}_{file.filename}"
        with open(upload_path, "wb") as f:
            shutil.copyfileobj(file.file, f)
        
        # Run structured extraction (includes quality check)
        result = extractor.process_structured(str(upload_path))
        
        # Remove numpy image from response (not JSON serializable)
        annotated_image = result.pop('annotated_image', None)
        # Remove CNN prediction internal details
        if 'quality_check' in result and result['quality_check']:
            result['quality_check'].pop('cnn_prediction', None)
        
        # Add task metadata
        result['task_id'] = task_id
        result['filename'] = file.filename
        result['status'] = 'completed'
        
        # Save annotated image  
        if annotated_image is not None:
            annotated_path = RESULTS_DIR / f"{task_id}_annotated.jpg"
            cv2.imwrite(str(annotated_path), annotated_image)
            result['annotated_image_path'] = str(annotated_path)
        
        # Save result JSON
        result_path = RESULTS_DIR / f"{task_id}.json"
        with open(result_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False, default=str)
        
        logger.info(f"[{task_id}] Done: {result.get('medication_count', 0)} medications found")
        
        return JSONResponse(content=result)
        
    except Exception as e:
        logger.error(f"Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/extract-base64")
async def extract_from_base64(data: dict):
    """
    Extract from base64-encoded image (for Flutter app).
    
    Args:
        data: {"image": "base64_encoded_image_string"}
    
    Returns:
        Structured prescription data
    """
    if extractor is None:
        raise HTTPException(status_code=503, detail="Models not loaded yet")
    
    image_b64 = data.get("image", "")
    if not image_b64:
        raise HTTPException(status_code=400, detail="No image data provided")
    
    try:
        # Decode base64 to image
        img_bytes = base64.b64decode(image_b64)
        img_array = np.frombuffer(img_bytes, dtype=np.uint8)
        image = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
        
        if image is None:
            raise HTTPException(status_code=400, detail="Could not decode image")
        
        # Run extraction
        result = extractor.process_structured(image)
        result.pop('annotated_image', None)
        if 'quality_check' in result and result['quality_check']:
            result['quality_check'].pop('cnn_prediction', None)
        
        task_id = str(uuid.uuid4())[:8]
        result['task_id'] = task_id
        result['status'] = 'completed'
        
        return JSONResponse(content=result)
        
    except Exception as e:
        logger.error(f"Base64 extraction error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/results/{task_id}")
async def get_results(task_id: str):
    """Get saved results for a task."""
    result_path = RESULTS_DIR / f"{task_id}.json"
    if not result_path.exists():
        raise HTTPException(status_code=404, detail="Task not found")
    
    with open(result_path, 'r', encoding='utf-8') as f:
        return JSONResponse(content=json.load(f))


@app.delete("/task/{task_id}")
async def delete_task(task_id: str):
    """Delete all data for a task."""
    deleted = 0
    for d in [UPLOAD_DIR, RESULTS_DIR]:
        for f in d.glob(f"{task_id}*"):
            f.unlink()
            deleted += 1
    
    if not deleted:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"message": "Deleted", "task_id": task_id, "files_deleted": deleted}


def start_server(host: str = "0.0.0.0", port: int = 8000):
    """Start the FastAPI server."""
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 8000))
    print("=" * 70)
    print("  MEDISCAN API SERVER V6.1")
    print("  Pipeline: Quality Check + YOLOv8 (9-class) + PaddleOCR")
    print("=" * 70)
    print()
    print(f"  Local:   http://localhost:{port}")
    print(f"  Docs:    http://localhost:{port}/docs")
    print(f"  Health:  http://localhost:{port}/health")
    print()
    start_server(port=port)
