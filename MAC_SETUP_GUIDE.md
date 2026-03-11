# 🖥️ MediScan — Mac Setup & Pipeline Test Guide

> **For AI Assistant (GitHub Copilot / Claude):** This is the PRIMARY file to read when setting up this project on a MacBook. Follow every step in order. Do NOT skip anything.

---

## 📋 What Is This Folder?

This is a **lightweight, self-contained copy** of the MediScan AI backend — extracted from a 32GB development workspace on Windows. It contains ONLY the files needed to:

1. Run the FastAPI AI server on Mac
2. Test the full prescription extraction pipeline


**Total folder size: ~250 MB** (vs 32GB original)

---

## 📁 Folder Structure

```
capstone/
├── MAC_SETUP_GUIDE.md          ← YOU ARE HERE (read this first!)
│
├── backend/
│   └── fastapi_app.py          # FastAPI server v6.1 (DO NOT MODIFY)
│
├── src/
│   ├── __init__.py
│   ├── pipeline/
│   │   ├── __init__.py
│   │   ├── extractor.py        # YOLOv8 + PaddleOCR base class
│   │   └── structured_extractor.py  # Medication grouping
│   ├── ocr/
│   │   ├── __init__.py
│   │   └── paddle_ocr_engine.py    # PaddleOCR v3 engine
│   ├── preprocessing/
│   │   ├── __init__.py
│   │   └── quality_checker.py      # ResNet18 + Laplacian
│   └── models/
│       ├── __init__.py
│       └── image_quality_classifier.py  # ResNet18 model definition
│
├── experiments/
│   └── v6_9class_english/
│       └── weights/
│           └── best.pt         # YOLO model (64 MB) — CRITICAL
│
├── models/
│   └── image_quality_classifier.pt  # Quality model (128 MB) — CRITICAL
│
├── data/
│   ├── raw_images/
│   │   ├── good/               # 10 good prescription images for testing
│   │   └── bad/                # 5 bad quality images for testing
│   ├── uploads/                # Empty — FastAPI uses this
│   └── results/                # Empty — FastAPI uses this
│
├── test_full_pipeline_demo.py  # Pipeline test script (seed=42, 8 images)
├── test_pipeline_run2.py       # Pipeline test script (seed=99, 5 images)
│
├── requirements_mac.txt        # Mac-compatible Python packages
├── setup_mac.sh                # One-click setup script
├── run_server.sh               # One-click server start script
│
├── AI_BUILD_PROMPT.md          # Android app build instructions for AI
├── APP_SPECIFICATION.md        # Android app screen specs
├── BACKEND_API_REFERENCE.md    # FastAPI endpoint documentation
└── SYSTEM_DESIGN.md            # Full system architecture
```

---

## 🚀 STEP-BY-STEP SETUP (Do This In Order)

### Step 1: Open Terminal in the capstone folder

```bash
cd /path/to/capstone
```

### Step 2: Run the setup script

```bash
bash setup_mac.sh
```

This will:
- Create a Python virtual environment (`venv/`)
- Install PyTorch (CPU), Ultralytics, PaddlePaddle, PaddleOCR
- Install all remaining dependencies
- Verify model files exist
- Takes **5-10 minutes**

### Step 3: Verify setup worked

```bash
source venv/bin/activate
python -c "
import torch
print(f'PyTorch: {torch.__version__}')
from ultralytics import YOLO
print('Ultralytics: OK')
from paddleocr import PaddleOCR
print('PaddleOCR: OK')
print('All dependencies installed successfully!')
"
```

You should see all three print "OK" with no errors.

### Step 4: Test the full pipeline

```bash
source venv/bin/activate
python test_full_pipeline_demo.py
```

**Expected output:**
- Loads YOLO model, PaddleOCR, and quality checker
- Processes 8 images (5 good + 3 bad, random seed=42)
- Good images: extracts medications with names, doses, schedules
- Bad images: rejected with quality warnings
- Shows processing time per image

**If this works → the AI backend is fully functional on your Mac.**

### Step 5: Start the FastAPI server

```bash
bash run_server.sh
```

**Expected output:**
```
► Starting server on port 8000...
  Docs:   http://localhost:8000/docs
  Health: http://localhost:8000/health
```

Test it: open http://localhost:8000/health in a browser → should return JSON.

---

## 🧪 Pipeline Test Details

### test_full_pipeline_demo.py
- **Seed:** 42
- **Images:** 5 random good + 3 random bad from `data/raw_images/`
- **Tests:** Quality check → YOLO detection → PaddleOCR → structured JSON output
- **Passing:** All good images should have `status: completed` with medications extracted. All bad images should have `status: rejected` with quality warnings.

### test_pipeline_run2.py
- **Seed:** 99
- **Images:** 3 random good + 2 random bad
- **Same tests**, different images

---

## 🔧 Troubleshooting

### PaddlePaddle install fails on Mac:
```bash
pip install paddlepaddle -i https://mirror.baidu.com/pypi/simple
```

### OpenCV error ("cannot import cv2"):
```bash
pip uninstall opencv-python -y
pip install opencv-python-headless
```

### "No module named src":
Make sure you're running from the **capstone root folder**, not from inside `backend/` or `src/`.

### Pipeline very slow:
Normal on Mac (CPU only). Expect **10-20 seconds** per image on Intel Mac, **5-8 seconds** on Apple Silicon (M1/M2/M3). The Windows PC with GPU does it in 2-3 seconds.

### Port 8000 already in use:
```bash
lsof -i :8000
kill -9 <PID>
```

---

## 📱 Demo Day Quick Reference

**Setup (before leaving home):**
1. Mac has the server working (`bash run_server.sh` → health check OK)
2. Android APK installed on phone

**At university:**
1. Turn on **phone's Mobile Hotspot**
2. Connect **MacBook to phone's hotspot** (WiFi settings)
3. Open Terminal → `cd capstone` → `bash run_server.sh`
4. Note the IP shown (e.g., `192.168.43.105`)
5. Make sure APK is built with that IP as `BASE_URL`
6. Open app → scan prescription → AI extracts → show teachers

---

## 🤖 AI Pipeline Summary (3 Models, No RapidFuzz)

```
Image  →  Quality Check (ResNet18)  →  YOLO Detection (9 classes)  →  PaddleOCR  →  Spatial Grouping  →  JSON
         (~0.5 sec on Mac)            (~3-5 sec on Mac)              (~5-10 sec)    (instant)
```

| Model | File | Size | Trained By |
|-------|------|------|-----------|
| Quality Checker | `models/image_quality_classifier.pt` | 128 MB | You (ResNet18 fine-tuned) |
| Object Detector | `experiments/v6_9class_english/weights/best.pt` | 64 MB | You (YOLOv8s custom) |
| OCR Engine | PaddleOCR (downloads on first run) | ~200 MB | Baidu (pre-trained, used as-is) |

---

## 📚 Other Documents in This Folder

> ⚠️ **IMPORTANT FOR AI ASSISTANT:** The four documents below are **REFERENCE ONLY — do NOT act on them, do NOT follow any instructions in them, and do NOT build anything from them.** They exist purely so you can understand the overall system context (what the app does, how it looks, what the API looks like). The Android app development lives in a **completely separate repository** and is handled separately.
>
> Your only job in this `capstone` folder is:
> 1. Set up the Python environment
> 2. Get the FastAPI AI server running
> 3. Verify the pipeline works with the test scripts
>
> **Do NOT start building an Android app, do NOT follow AI_BUILD_PROMPT.md, and do NOT treat any of these four files as action items.**

| File | Purpose | What the AI should do |
|------|---------|----------------------|
| `SYSTEM_DESIGN.md` | Full architecture of the entire system | Read for context only — understand how the system fits together |
| `APP_SPECIFICATION.md` | All 12 Android screens with Kotlin code | Read for context only — understand what the app looks like |
| `BACKEND_API_REFERENCE.md` | FastAPI endpoints, request/response formats | Read for context only — understand what the API returns |
| `AI_BUILD_PROMPT.md` | Step-by-step Android app build instructions | **DO NOT FOLLOW** — this is for a separate Android repo |

---

*Created: February 26, 2026*
*Source: Extracted from prescription_ai workspace (Windows PC)*
*Status: Self-contained — everything needed to run the AI server is in this folder*
