# 🔌 MediScan — Backend API Reference

> **For AI Assistant:** This document contains ALL backend code, endpoints, request/response formats, and connection details needed to build the Android app. The backend is **already built and working** — do NOT modify it. The Android app just needs to connect to it.

---

## 📡 Server Overview

| Property | Value |
|----------|-------|
| **Framework** | FastAPI (Python) |
| **Version** | 6.1.0 |
| **Default Port** | 8000 |
| **AI Pipeline** | Quality Check (ResNet18) → YOLOv8s (9-class) → PaddleOCR (English) → Spatial Grouping |
| **Docs UI** | `http://localhost:8000/docs` (Swagger) |

### How to Start the Server:
```bash
cd prescription_ai
python backend/fastapi_app.py
```
The server loads AI models on startup (~10-20 seconds), then is ready to accept requests.

---

## 🌐 Connection from Android

### Base URLs:

| Scenario | Base URL | When to Use |
|----------|----------|-------------|
| **Android Emulator** | `http://10.0.2.2:8000/` | Emulator → host PC (most common for dev) |
| **Physical Device (WiFi)** | `http://192.168.x.x:8000/` | Phone on same WiFi as PC |
| **Production** | `https://api.mediscan.com/` | Future: deployed server |

> **⚠️ Important:** `10.0.2.2` is a special Android emulator alias that maps to the host machine's `localhost`. A physical device cannot use this — use the PC's actual WiFi IP instead (find via `ipconfig` on Windows).

### Android Network Requirements:

**AndroidManifest.xml** — must include:
```xml
<uses-permission android:name="android.permission.INTERNET" />

<application
    android:usesCleartextTraffic="true"
    android:networkSecurityConfig="@xml/network_security_config"
    ... >
```

**res/xml/network_security_config.xml** — for development (allows HTTP):
```xml
<?xml version="1.0" encoding="utf-8"?>
<network-security-config>
    <domain-config cleartextTrafficPermitted="true">
        <domain includeSubdomains="true">10.0.2.2</domain>
        <domain includeSubdomains="true">192.168.0.0/16</domain>
    </domain-config>
</network-security-config>
```

---

## 📋 API Endpoints

---

### 1. `GET /` — Root Info

**Purpose:** Check what server is running.

**Request:** No body needed.

**Response (200):**
```json
{
    "app": "MediScan - AI Prescription Digitization",
    "version": "6.1.0",
    "pipeline": "Quality Check + YOLOv8 (9-class) + PaddleOCR (English)",
    "docs": "/docs",
    "health": "/health"
}
```

---

### 2. `GET /health` — Health Check

**Purpose:** Verify server is running and models are loaded. Call this on app startup to show connection status.

**Request:** No body needed.

**Response (200):**
```json
{
    "status": "healthy",
    "timestamp": "2026-02-24T10:30:15.123456",
    "cuda_available": true,
    "gpu_name": "NVIDIA GeForce RTX 3060",
    "model_loaded": true,
    "quality_checker_loaded": true,
    "pipeline_version": "v6_9class_english",
    "ocr_engine": "paddleocr"
}
```

**Android Usage:** Call on app launch to verify connectivity. Show green/red indicator.

---

### 3. `POST /check-quality-base64` — Quick Quality Check ⭐

**Purpose:** Fast image quality assessment (~50ms). Use for real-time camera feedback BEFORE sending for full extraction. This saves time — reject bad images early.

**Request:**
```
Content-Type: application/json

{
    "image": "<base64_encoded_image_string>"
}
```

**Response (200) — Good Quality:**
```json
{
    "is_acceptable": true,
    "quality_label": "good",
    "quality_score": 0.92,
    "issues": [],
    "recommendation": "Image quality is acceptable for processing"
}
```

**Response (200) — Bad Quality:**
```json
{
    "is_acceptable": false,
    "quality_label": "bad",
    "quality_score": 0.23,
    "issues": [
        "Image appears blurry (Laplacian variance: 15.2)",
        "CNN classified as bad quality (confidence: 0.89)"
    ],
    "recommendation": "Please retake the photo with better lighting and hold the camera steady"
}
```

**Android Usage:**
1. User captures photo with CameraX
2. Convert to base64: `Base64.encodeToString(imageBytes, Base64.NO_WRAP)`
3. Send to `/check-quality-base64`
4. If `is_acceptable == false` → show message, ask to retake
5. If `is_acceptable == true` → proceed to `/extract-base64`

---

### 4. `POST /extract-base64` — Extract Prescription ⭐⭐⭐ (MAIN ENDPOINT)

**Purpose:** The core AI endpoint. Sends a prescription image, returns structured medication data. This is the endpoint the Scan screen calls.

**Request:**
```
Content-Type: application/json

{
    "image": "<base64_encoded_image_string>"
}
```

**Processing time:** 2-8 seconds depending on image size and GPU availability.

**Response (200) — Successful Extraction:**
```json
{
    "prescription_id": "rx_20260224_103015",
    "extraction_timestamp": "2026-02-24T10:30:15",
    "model_version": "yolov8s_v6_9class",
    "ocr_engine": "paddleocr_3.2.2",
    "status": "completed",
    "task_id": "a1b2c3d4",

    "medications": [
        {
            "medicine": "TAB NAPA EXTEND 665MG",
            "dose_strength": "665mg",
            "schedule": "1+0+1",
            "duration": "7 days",
            "confidence": {
                "medicine": 0.95,
                "dose_strength": 0.89,
                "schedule": 0.91,
                "duration": 0.88
            }
        },
        {
            "medicine": "CAP OMEPRAZOLE 20MG",
            "dose_strength": "20mg",
            "schedule": "1+0+0",
            "duration": "14 days",
            "confidence": {
                "medicine": 0.93,
                "dose_strength": 0.87,
                "schedule": 0.90,
                "duration": 0.85
            }
        },
        {
            "medicine": "SYP HISTACIN",
            "dose_strength": null,
            "schedule": "2 TSF at night",
            "duration": "5 days",
            "confidence": {
                "medicine": 0.88,
                "dose_strength": null,
                "schedule": 0.82,
                "duration": 0.79
            }
        }
    ],
    "medication_count": 3,

    "doctor": {
        "name": "Dr. Ahmed Hossain",
        "hospital": "Dhaka Medical College"
    },

    "prescription_info": {
        "date": "15-02-2026",
        "diagnoses": ["Fever", "Gastritis"],
        "tests": ["CBC", "Urine R/E"]
    },

    "quality_check": {
        "is_acceptable": true,
        "quality_label": "good",
        "quality_score": 0.91,
        "issues": [],
        "recommendation": "Image quality is acceptable for processing"
    },

    "stats": {
        "total_detections": 12,
        "processing_time_seconds": 3.45
    }
}
```

**Response (200) — Rejected (quality too poor):**
```json
{
    "prescription_id": "rx_20260224_103200",
    "extraction_timestamp": "2026-02-24T10:32:00",
    "model_version": "yolov8s_v6_9class",
    "ocr_engine": "paddleocr_3.2.2",
    "status": "rejected",
    "task_id": "e5f6g7h8",
    "message": "Image quality too poor for reliable extraction",
    "medications": [],
    "medication_count": 0,
    "quality_check": {
        "is_acceptable": false,
        "quality_label": "bad",
        "quality_score": 0.18,
        "issues": ["Image appears blurry"],
        "recommendation": "Please retake with better lighting"
    }
}
```

**⚠️ Key Points for Android:**
- `status` field tells you if extraction worked: `"completed"` = success, `"rejected"` = failed
- `medications` is always an array (can be empty)
- `confidence` values are 0.0 to 1.0 (show as percentage in UI if desired)
- Some fields may be `null` if not detected (dose_strength, schedule, duration)
- `doctor` and `prescription_info` may be `null` if not found in image
- The `quality_check` object is always included (extraction does quality check first)

---

### 5. `POST /check-quality` — Quality Check (Multipart Upload)

**Purpose:** Same as `/check-quality-base64` but accepts file upload instead of base64. Less commonly used from Android.

**Request:**
```
Content-Type: multipart/form-data
Body: file=<image_file>
```

**Response:** Same format as `/check-quality-base64`.

---

### 6. `POST /extract` — Extract (Multipart Upload)

**Purpose:** Same as `/extract-base64` but accepts file upload. Less commonly used from Android.

**Request:**
```
Content-Type: multipart/form-data
Body: file=<image_file>
```

**Response:** Same format as `/extract-base64`.

---

### 7. `GET /results/{task_id}` — Get Saved Results

**Purpose:** Retrieve previously saved extraction results by task ID.

**Request:** No body. Task ID in URL path.

**Example:** `GET /results/a1b2c3d4`

**Response (200):** Same JSON as the original extraction result.

**Response (404):**
```json
{
    "detail": "Task not found"
}
```

---

### 8. `DELETE /task/{task_id}` — Delete Task Data

**Purpose:** Clean up uploaded images and results for a task.

**Request:** No body. Task ID in URL path.

**Response (200):**
```json
{
    "message": "Deleted",
    "task_id": "a1b2c3d4",
    "files_deleted": 3
}
```

---

## 🔧 Retrofit2 Interface (Copy-Paste Ready)

```kotlin
// data/remote/FastApiService.kt

interface FastApiService {

    @GET("health")
    suspend fun healthCheck(): Map<String, Any>

    @POST("check-quality-base64")
    suspend fun checkQuality(
        @Body request: Map<String, String>   // {"image": "base64..."}
    ): QualityCheckResponse

    @POST("extract-base64")
    suspend fun extractPrescription(
        @Body request: Map<String, String>   // {"image": "base64..."}
    ): ExtractionResult
}
```

### How to Call from ViewModel:

```kotlin
// Step 1: Convert CameraX ImageProxy to ByteArray
fun ImageProxy.toByteArray(): ByteArray {
    val buffer = planes[0].buffer
    val bytes = ByteArray(buffer.remaining())
    buffer.get(bytes)
    return bytes
}

// Step 2: Convert bitmap to byte array (alternative)
fun Bitmap.toByteArray(): ByteArray {
    val stream = ByteArrayOutputStream()
    compress(Bitmap.CompressFormat.JPEG, 85, stream)
    return stream.toByteArray()
}

// Step 3: Send to API
val base64Image = Base64.encodeToString(imageBytes, Base64.NO_WRAP)
val request = mapOf("image" to base64Image)
val result = fastApiService.extractPrescription(request)

// Step 4: Check result
when (result.status) {
    "completed" -> {
        // Show medications in bottom sheet
        // result.medications, result.doctor, etc.
    }
    "rejected" -> {
        // Show error: result.message
        // Offer to retake photo
    }
}
```

---

## 🧩 NetworkResult Sealed Class

```kotlin
// core/utils/NetworkResult.kt

sealed class NetworkResult<out T> {
    object Idle : NetworkResult<Nothing>()
    object Loading : NetworkResult<Nothing>()
    data class Success<T>(val data: T) : NetworkResult<T>()
    data class Error(val message: String) : NetworkResult<Nothing>()
}
```

---

## 🔥 Firebase Integration (No Backend Changes Needed)

The FastAPI server handles **AI processing only**. All user data, auth, and storage go directly through Firebase from the Android app:

| Feature | Where It Happens |
|---------|-----------------|
| User registration/login | Android ↔ Firebase Auth (direct) |
| User profile CRUD | Android ↔ Firestore (direct) |
| Prescription storage | Android ↔ Firestore (direct) |
| Image storage | Android ↔ Firebase Storage (direct) |
| Appointment management | Android ↔ Firestore (direct) |
| AI prescription extraction | Android → FastAPI server → returns JSON |

**The FastAPI server does NOT:**
- Store user data
- Handle authentication
- Connect to any database
- Store images permanently

It receives an image, runs AI, returns structured JSON — that's all.

---

## 🔑 Future: Firebase Auth Token Verification on FastAPI

If we later want to **protect** the FastAPI endpoints (prevent unauthorized access), add this to `fastapi_app.py`:

```python
# pip install firebase-admin
import firebase_admin
from firebase_admin import auth as firebase_auth, credentials

# Initialize once at startup
cred = credentials.Certificate("path/to/serviceAccountKey.json")
firebase_admin.initialize_app(cred)

# Middleware or dependency to verify tokens
async def verify_firebase_token(authorization: str = Header(...)):
    try:
        token = authorization.replace("Bearer ", "")
        decoded = firebase_auth.verify_id_token(token)
        return decoded  # Contains uid, email, etc.
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")
```

**For now:** The API is open (no auth required) — perfect for development. Add token verification before production deployment.

---

## 📊 9 YOLO Detection Classes

The AI pipeline detects these 9 field types in prescription images:

| Class ID | Class Name | Description |
|----------|-----------|-------------|
| 0 | `medicine` | Medicine name (TAB NAPA, CAP OMEPRAZOLE, etc.) |
| 1 | `dose_strength` | Dosage (500mg, 20mg, 10ml, etc.) |
| 2 | `schedule` | Frequency (1+0+1, TDS, BD, etc.) |
| 3 | `duration` | How long to take (7 days, 2 weeks, etc.) |
| 4 | `doctor_name` | Doctor's name |
| 5 | `hospital` | Hospital/clinic name |
| 6 | `date` | Prescription date |
| 7 | `diagnosis` | Diagnosis text |
| 8 | `test` | Recommended tests |

These get grouped by Y-coordinate proximity into medication rows (medicine + dose + schedule + duration per row).

---

## 📦 Complete FastAPI Code

Below is the **complete** `backend/fastapi_app.py` source code for reference. The Android AI assistant should NOT modify this file — it's already working. This is included so the AI understands exactly what the server does:

```python
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

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="MediScan - AI Prescription Digitization API",
    description="Extract structured medication data from prescription images",
    version="6.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

extractor = None
quality_checker = None

UPLOAD_DIR = Path("data/uploads")
RESULTS_DIR = Path("data/results")
for d in [UPLOAD_DIR, RESULTS_DIR]:
    d.mkdir(parents=True, exist_ok=True)


@app.on_event("startup")
async def startup_event():
    global extractor, quality_checker
    logger.info("Loading AI models...")
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from src.pipeline.structured_extractor import StructuredPrescriptionExtractor
    from src.preprocessing.quality_checker import get_quality_checker
    extractor = StructuredPrescriptionExtractor(use_gpu=torch.cuda.is_available())
    quality_checker = get_quality_checker()
    logger.info("API Server Ready! Docs: http://localhost:8000/docs")


@app.get("/")
async def root():
    return {
        "app": "MediScan - AI Prescription Digitization",
        "version": "6.1.0",
        "pipeline": "Quality Check + YOLOv8 (9-class) + PaddleOCR (English)",
    }


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "cuda_available": torch.cuda.is_available(),
        "gpu_name": torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,
        "model_loaded": extractor is not None,
        "quality_checker_loaded": quality_checker is not None,
    }


@app.post("/check-quality-base64")
async def check_quality_base64(data: dict):
    if quality_checker is None:
        raise HTTPException(status_code=503, detail="Quality checker not loaded")
    image_b64 = data.get("image", "")
    if not image_b64:
        raise HTTPException(status_code=400, detail="No image data")
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
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/extract-base64")
async def extract_from_base64(data: dict):
    if extractor is None:
        raise HTTPException(status_code=503, detail="Models not loaded")
    image_b64 = data.get("image", "")
    if not image_b64:
        raise HTTPException(status_code=400, detail="No image data")
    try:
        img_bytes = base64.b64decode(image_b64)
        img_array = np.frombuffer(img_bytes, dtype=np.uint8)
        image = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
        if image is None:
            raise HTTPException(status_code=400, detail="Could not decode image")
        result = extractor.process_structured(image)
        result.pop('annotated_image', None)
        if 'quality_check' in result and result['quality_check']:
            result['quality_check'].pop('cnn_prediction', None)
        task_id = str(uuid.uuid4())[:8]
        result['task_id'] = task_id
        result['status'] = 'completed'
        return JSONResponse(content=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/results/{task_id}")
async def get_results(task_id: str):
    result_path = RESULTS_DIR / f"{task_id}.json"
    if not result_path.exists():
        raise HTTPException(status_code=404, detail="Task not found")
    with open(result_path, 'r', encoding='utf-8') as f:
        return JSONResponse(content=json.load(f))


@app.delete("/task/{task_id}")
async def delete_task(task_id: str):
    deleted = 0
    for d in [UPLOAD_DIR, RESULTS_DIR]:
        for f in d.glob(f"{task_id}*"):
            f.unlink()
            deleted += 1
    if not deleted:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"message": "Deleted", "task_id": task_id, "files_deleted": deleted}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

---

## ⚠️ Error Responses

All errors follow this format:
```json
{
    "detail": "Error message here"
}
```

| Status Code | Meaning | When It Happens |
|-------------|---------|-----------------|
| **400** | Bad Request | Invalid image, no image data, wrong format |
| **404** | Not Found | Task ID doesn't exist |
| **500** | Server Error | AI model crashed, unexpected error |
| **503** | Service Unavailable | Models still loading (server just started) |

### Retrofit Error Handling:
```kotlin
try {
    val result = fastApiService.extractPrescription(request)
    // success
} catch (e: HttpException) {
    when (e.code()) {
        400 -> "Invalid image"
        503 -> "Server starting up, please wait..."
        500 -> "Server error, try again"
        else -> "Unknown error: ${e.code()}"
    }
} catch (e: IOException) {
    "Cannot connect to server. Make sure the FastAPI server is running."
}
```

---

## 🏃 Quick Start for Testing

1. **Start FastAPI server:**
   ```bash
   cd N:\Capstone Project\prescription_ai
   python backend/fastapi_app.py
   ```

2. **Wait for "API Server Ready!"** message (~10-20 sec)

3. **Test health endpoint:**
   ```bash
   curl http://localhost:8000/health
   ```

4. **Test from Android Emulator:**
   - Use `http://10.0.2.2:8000/` as base URL in Retrofit
   - Run the app, take a photo, watch Logcat for Retrofit logs

---

*Document Created: February 24, 2026*
*Server Version: 6.1.0*
*Status: Backend is COMPLETE and WORKING — do not modify*
