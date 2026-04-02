# 🚀 MediScan AI Server — Deploy to Railway (Cloud)

## ⚠️ IMPORTANT CONTEXT FOR AI ASSISTANT

You are working inside the **MediScan capstone folder** — a FastAPI-based AI backend that processes prescription images using YOLOv8 + PaddleOCR + ResNet18.

### What We Are Doing
We are deploying this AI server to **Railway.app** (cloud hosting) so the MediScan Android app can connect to it over the internet — instead of relying on a local Mac server over WiFi/hotspot which is unreliable at university.

### What We Are NOT Doing
- ❌ We are NOT deleting/removing the local FastAPI server code
- ❌ We are NOT modifying the AI pipeline logic (extractor, OCR, quality checker)
- ❌ We are NOT touching the Android app code (that's handled separately)
- ✅ We ARE making this exact same server deployable to Railway cloud
- ✅ The local FastAPI will remain — we just "switch it off" locally and use the Railway URL instead

---

## 🛑 CRITICAL RULE — PHASE-BY-PHASE EXECUTION

> **You MUST follow this rule for every single phase without exception:**
>
> 1. Complete the current phase fully
> 2. Tell the user exactly what you did and confirm it is done
> 3. **STOP and ask: "✅ Phase [N] is complete! Should I move on to Phase [N+1]?"**
> 4. Wait for the user to say **YES** before starting the next phase
> 5. Do NOT skip ahead, do NOT assume permission, do NOT start the next phase automatically
>
> This rule applies to ALL 9 phases. Each phase must be confirmed by the user before proceeding.
> The user is a student — they need to verify each step manually before you continue.
> **If you proceed to the next phase without asking, you are violating this instruction.**

---

## 📁 CURRENT PROJECT STRUCTURE

```
capstone/
├── backend/
│   └── fastapi_app.py          ← Main FastAPI server (355 lines, 8 endpoints)
├── src/
│   ├── pipeline/
│   │   ├── extractor.py         ← YOLOv8 + PaddleOCR base pipeline (349 lines)
│   │   └── structured_extractor.py ← Structured medication grouping (261 lines)
│   ├── preprocessing/
│   │   └── quality_checker.py   ← ResNet18 + Laplacian quality check (314 lines)
│   ├── ocr/
│   │   └── paddle_ocr_engine.py ← PaddleOCR v3 engine (347 lines)
│   └── models/
│       └── yolo_model.py        ← YOLO model wrapper
├── experiments/
│   └── v6_9class_english/
│       └── weights/
│           └── best.pt          ← YOLOv8s model (64 MB)
├── models/
│   └── image_quality_classifier.pt ← ResNet18 model (128 MB)
├── data/
│   ├── uploads/                 ← Runtime uploads (gitignored)
│   └── results/                 ← Runtime results (gitignored)
├── requirements_mac.txt         ← Python dependencies
├── run_server.sh                ← Local Mac startup script
├── setup_mac.sh                 ← Local Mac setup script
├── .gitignore
└── venv/                        ← Local virtual env (gitignored)
```

### Key Model Files & Sizes
| File | Size | Purpose |
|------|------|---------|
| `experiments/v6_9class_english/weights/best.pt` | 64 MB | YOLOv8s 9-class detection model |
| `models/image_quality_classifier.pt` | 128 MB | ResNet18 quality classifier |
| PaddleOCR models | ~300 MB | Auto-downloaded on first run to `~/.paddleocr/` |

### Runtime Requirements
- **Python**: 3.10 or 3.11
- **RAM**: 2–3 GB minimum (3 AI models loaded in memory)
- **Disk**: ~500 MB (code + models) + ~300 MB (PaddleOCR auto-download)
- **GPU**: Not required — CPU works fine (just slower, ~5-15 sec per image)

### Current Dependencies (from requirements_mac.txt)
```
torch>=2.1.0, torchvision>=0.16.0, torchaudio>=2.1.0
ultralytics>=8.0.0
paddlepaddle>=2.6.0, paddleocr>=2.7.0
opencv-python>=4.8.0, Pillow>=10.0.0, scikit-image>=0.21.0
numpy>=1.24.0, pandas>=2.0.0, scikit-learn>=1.3.0
fastapi>=0.100.0, uvicorn[standard]>=0.23.0
python-multipart>=0.0.6, aiofiles>=23.1.0
rich>=13.4.2, tqdm>=4.65.0, python-dotenv>=1.0.0
python-dateutil>=2.8.2, regex>=2023.6.3
```

### How the Server Currently Starts (locally)
```bash
cd capstone
source venv/bin/activate
cd backend
uvicorn fastapi_app:app --host 0.0.0.0 --port 8000
```

### API Endpoints
| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/` | Root — returns server info |
| GET | `/health` | Health check — returns model status |
| POST | `/check-quality-base64` | Check image quality (base64 input) |
| POST | `/extract-base64` | Extract prescription data (base64 input) |
| GET | `/results/{task_id}` | Get extraction results |
| DELETE | `/task/{task_id}` | Delete task data |
| POST | `/check-quality` | Check quality (file upload) |
| POST | `/extract` | Extract data (file upload) |

---

# 🔧 DEPLOYMENT PHASES — STEP BY STEP

## PHASE 1: Create Railway-Compatible Requirements File

Create a new file called `requirements.txt` in the **capstone root** (not inside backend/) with cloud-optimized dependencies. The Mac requirements file uses MPS-compatible torch, but Railway uses Linux/CPU. 

Create **`capstone/requirements.txt`** with this content:

```txt
# ─── MediScan AI Server — Railway Cloud Requirements ───
# Python 3.11 recommended
# CPU-only (no GPU on Railway free tier)

# ─── Core Deep Learning (CPU-only for cloud) ───
--extra-index-url https://download.pytorch.org/whl/cpu
torch==2.1.0+cpu
torchvision==0.16.0+cpu
torchaudio==2.1.0+cpu

# ─── YOLO (Object Detection) ────────────────────
ultralytics>=8.0.0

# ─── OCR ─────────────────────────────────────────
paddlepaddle>=2.6.0
paddleocr>=2.7.0

# ─── Image Processing ───────────────────────────
opencv-python-headless>=4.8.0
Pillow>=10.0.0
scikit-image>=0.21.0

# ─── Data Science ────────────────────────────────
numpy>=1.24.0
pandas>=2.0.0
scikit-learn>=1.3.0

# ─── Text Processing ────────────────────────────
python-dateutil>=2.8.2
regex>=2023.6.3

# ─── API Framework ──────────────────────────────
fastapi>=0.100.0
uvicorn[standard]>=0.23.0
python-multipart>=0.0.6
aiofiles>=23.1.0

# ─── Utilities ──────────────────────────────────
rich>=13.4.2
tqdm>=4.65.0
python-dotenv>=1.0.0
```

### ⚠️ KEY DIFFERENCES from Mac requirements:
1. **`torch==2.1.0+cpu`** — CPU-only build (saves ~1.5 GB, Railway has no GPU)
2. **`opencv-python-headless`** — instead of `opencv-python` (no GUI needed on server, avoids Linux display library issues)
3. **Removed `torchaudio`** — not needed for image processing (but included as CPU for compatibility)

> ### 🛑 PHASE 1 CHECKPOINT
> After creating `requirements.txt`, **STOP HERE**.
> Show the user the file contents and confirm it was created successfully.
> Then ask: **"✅ Phase 1 is complete — `requirements.txt` has been created! Should I move on to Phase 2 (Create Dockerfile)?"**
> Wait for the user to say YES before continuing.

---

## PHASE 2: Create Dockerfile

Create **`capstone/Dockerfile`** in the capstone root:

```dockerfile
# ============================================================
#  MediScan AI Server — Railway Cloud Dockerfile
#  Python 3.11 + CPU-only PyTorch + YOLOv8 + PaddleOCR
# ============================================================

FROM python:3.11-slim

# Install system dependencies needed by OpenCV, PaddleOCR
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1-mesa-glx \
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

# Health check
HEALTHCHECK --interval=60s --timeout=30s --start-period=120s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

# Start the server
# Railway provides PORT env variable, default to 8000
CMD ["sh", "-c", "cd backend && uvicorn fastapi_app:app --host 0.0.0.0 --port ${PORT:-8000}"]
```

### ⚠️ IMPORTANT NOTES:
- The `start-period=120s` gives the server 2 minutes to load all 3 AI models before health checks start
- We copy only `backend/`, `src/`, `experiments/`, `models/` — NOT `venv/`, `data/uploads/`, etc.
- Railway automatically sets a `PORT` environment variable — the CMD uses it

> ### 🛑 PHASE 2 CHECKPOINT
> After creating `Dockerfile`, **STOP HERE**.
> Show the user the Dockerfile contents and confirm it was created successfully.
> Then ask: **"✅ Phase 2 is complete — `Dockerfile` has been created! Should I move on to Phase 3 (Create .dockerignore)?"**
> Wait for the user to say YES before continuing.

---

## PHASE 3: Create .dockerignore

Create **`capstone/.dockerignore`** to keep the Docker image small:

```
venv/
__pycache__/
*.pyc
*.pyo
.git/
.gitattributes
.gitignore
.DS_Store
data/uploads/
data/results/
*.log
nohup.out
test_*.py
setup_mac.sh
run_server.sh
.paddlex/
.ipynb_checkpoints/
*.md
```

> ### 🛑 PHASE 3 CHECKPOINT
> After creating `.dockerignore`, **STOP HERE**.
> Show the user the file contents and confirm it was created successfully.
> Then ask: **"✅ Phase 3 is complete — `.dockerignore` has been created! Should I move on to Phase 4 (Create railway.toml)?"**
> Wait for the user to say YES before continuing.

---

## PHASE 4: Create railway.toml Configuration

Create **`capstone/railway.toml`** for Railway-specific settings:

```toml
[build]
builder = "DOCKERFILE"
dockerfilePath = "./Dockerfile"

[deploy]
startCommand = "cd backend && uvicorn fastapi_app:app --host 0.0.0.0 --port ${PORT:-8000}"
healthcheckPath = "/health"
healthcheckTimeout = 120
restartPolicyType = "ON_FAILURE"
restartPolicyMaxRetries = 3
```

> ### 🛑 PHASE 4 CHECKPOINT
> After creating `railway.toml`, **STOP HERE**.
> Show the user the file contents and confirm it was created successfully.
> Then ask: **"✅ Phase 4 is complete — `railway.toml` has been created! Should I move on to Phase 5 (Update fastapi_app.py for cloud compatibility)?"**
> Wait for the user to say YES before continuing.

---

## PHASE 5: Update fastapi_app.py for Cloud Compatibility

Make these **small changes** to `backend/fastapi_app.py`:

### Change 1: Add PORT environment variable support
At the very bottom of `fastapi_app.py`, find the `if __name__ == "__main__":` block and update it to read the PORT from environment:

**Find this block (near the end of the file) and update it:**

```python
if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
```

If there's no `if __name__` block, ADD it at the very bottom of the file.

### Change 2: Add memory-efficient startup logging
In the `startup_event()` function, add this line after the device detection block:

```python
    # Force CPU on cloud (no MPS/CUDA available)
    import os
    if os.environ.get("RAILWAY_ENVIRONMENT"):
        logger.info("☁️  Running on Railway Cloud — CPU mode")
```

### ⚠️ DO NOT change any other logic in fastapi_app.py — it already handles CPU fallback correctly.

> ### 🛑 PHASE 5 CHECKPOINT
> After updating `fastapi_app.py`, **STOP HERE**.
> Show the user exactly what lines were changed (before vs after).
> Then ask: **"✅ Phase 5 is complete — `fastapi_app.py` has been updated for cloud! Should I move on to Phase 6 (Setup Git LFS for model files)?"**
> Wait for the user to say YES before continuing.

---

## PHASE 6: Handle Large Model Files with Git LFS

The two model files (`best.pt` = 64 MB, `image_quality_classifier.pt` = 128 MB) are large. Railway deploys from Git, so we need Git LFS (Large File Storage).

### Step 1: Check if Git LFS is installed
```bash
git lfs version
```

### Step 2: If not installed, install it
```bash
# macOS
brew install git-lfs
git lfs install
```

### Step 3: Track model files with LFS
```bash
cd /path/to/capstone
git lfs track "*.pt"
git lfs track "experiments/v6_9class_english/weights/best.pt"
git lfs track "models/image_quality_classifier.pt"
```

This creates/updates a `.gitattributes` file. Make sure it includes:
```
*.pt filter=lfs diff=lfs merge=lfs -text
```

### Step 4: Verify .gitignore does NOT ignore .pt files
Check `.gitignore` — make sure `*.pt` is NOT in there. Currently the `.gitignore` does NOT ignore `.pt` files, so we're fine.

> ### 🛑 PHASE 6 CHECKPOINT
> After setting up Git LFS, **STOP HERE**.
> Run `git lfs status` and show the user the output to confirm `.pt` files are tracked.
> Then ask: **"✅ Phase 6 is complete — Git LFS is set up for model files! Should I move on to Phase 7 (Railway account setup and deployment guide)?"**
> Wait for the user to say YES before continuing.

---

## PHASE 7: Railway Deployment — User Steps (GUIDE FOR HUMAN)

### 📋 What you (the human user) need to do:

### Step 7.1: Create a Railway Account
1. Open your browser and go to → **https://railway.app**
2. Click **"Login"** in the top right corner
3. Click **"Login with GitHub"** 
4. Authorize Railway to access your GitHub account
5. You'll land on the Railway dashboard

### Step 7.2: Install Railway CLI (Optional but Recommended)
Open your Mac terminal and run:
```bash
npm i -g @railway/cli
```
Or if you don't have npm:
```bash
brew install railway
```
Then login:
```bash
railway login
```

### Step 7.3: Create a New Railway Project
**Option A — Via Website (Easier):**
1. Go to → **https://railway.app/dashboard**
2. Click the **"+ New Project"** button (purple button, top right)
3. Select **"Deploy from GitHub repo"**
4. Find and select your **capstone repository** from the list
   - If you don't see it, click **"Configure GitHub App"** and give Railway access to the repo
5. Railway will detect the Dockerfile and start building automatically

**Option B — Via CLI:**
```bash
cd /path/to/capstone
railway init
# Select "Empty Project"
railway link
# Link to the project you just created
railway up
```

### Step 7.4: Configure Railway Project Settings
After the project is created on Railway's dashboard:

1. Click on your **service** (the purple box in the project view)
2. Go to the **"Settings"** tab
3. Under **"Networking"** section:
   - Click **"Generate Domain"** — this gives you a public URL like `mediscan-ai-production.up.railway.app`
   - **⚡ COPY THIS URL — YOU WILL NEED IT FOR THE ANDROID APP**
4. Under **"Deploy"** section:
   - Make sure **Builder** = **Dockerfile**
   - **Start Command** should be auto-detected, but if not, set it to:
     ```
     cd backend && uvicorn fastapi_app:app --host 0.0.0.0 --port ${PORT:-8000}
     ```
5. Under **"Variables"** tab:
   - Railway automatically sets `PORT` — do NOT manually add it
   - No other environment variables needed

### Step 7.5: Configure Resources
1. In the service settings, go to **"Settings"** tab
2. Under **"Resources"** or **"Scaling"**:
   - Set **Memory**: at least **2 GB** (3 GB recommended)
   - Set **vCPU**: at least **2 vCPU**
   - These settings may require the Hobby plan ($5/month)
3. The **free trial** gives you $5 credit — this is enough for testing

### Step 7.6: Monitor the First Deployment
1. After pushing code, go to the **"Deployments"** tab on your Railway service
2. Click on the latest deployment to see **build logs**
3. The build will:
   - Install system dependencies (~1 min)
   - Install Python packages (~3-5 min)
   - Copy model files (~1 min)
4. After build, the **deploy logs** will show:
   ```
   STARTING MEDISCAN API SERVER V6.1
   Loading AI models...
   API Server Ready!
   ```
5. **First startup takes ~60-120 seconds** (loading 3 AI models into RAM)
6. Once you see "API Server Ready!" — the server is LIVE! 🎉

### Step 7.7: Test the Live Server
Open your browser and go to:
```
https://YOUR-RAILWAY-URL.up.railway.app/
```
You should see:
```json
{
  "message": "MediScan API V6.1 — Prescription Digitization",
  "status": "running",
  "docs": "/docs"
}
```

Also check health:
```
https://YOUR-RAILWAY-URL.up.railway.app/health
```
You should see:
```json
{
  "status": "healthy",
  "extractor_loaded": true,
  "quality_checker_loaded": true
}
```

Also test the interactive docs:
```
https://YOUR-RAILWAY-URL.up.railway.app/docs
```

> ### 🛑 PHASE 7 CHECKPOINT
> After guiding the user through the Railway website steps, **STOP HERE**.
> Ask the user: **"Have you completed all the Railway website steps (account created, project linked, domain generated)?"**
> Wait for the user to confirm before continuing.
> Once confirmed, ask: **"✅ Phase 7 is complete — Railway project is set up! Should I move on to Phase 8 (Push everything to Git to trigger the deployment)?"**
> Wait for the user to say YES before continuing.

---

## PHASE 8: Push Everything to Git

After creating all the new files (requirements.txt, Dockerfile, .dockerignore, railway.toml) and making the small changes to fastapi_app.py:

```bash
cd /path/to/capstone
git add -A
git status
# You should see:
#   new file: requirements.txt
#   new file: Dockerfile
#   new file: .dockerignore
#   new file: railway.toml
#   modified: backend/fastapi_app.py
#   (possibly) modified: .gitattributes (from Git LFS)

git commit -m "Add Railway cloud deployment configuration"
git push origin main
```

Railway will auto-detect the push and trigger a new deployment.

> ### 🛑 PHASE 8 CHECKPOINT
> After the git push, **STOP HERE**.
> Ask the user to check the Railway dashboard and confirm the build has started.
> Then ask: **"✅ Phase 8 is complete — all files have been pushed to Git and Railway deployment has been triggered! Go to your Railway dashboard and watch the build logs. Once the build finishes and the server is live, let me know. Should I move on to Phase 9 (Verify the live server works)?"**
> Wait for the user to confirm the deployment is live before continuing.

---

## PHASE 9: Verify Full Pipeline Works

Once the server is live on Railway, test the complete pipeline:

### Test 1: Health Check
```bash
curl https://YOUR-RAILWAY-URL.up.railway.app/health
```

### Test 2: Quality Check (with a base64 image)
```bash
# Encode a test image to base64
base64 -i /path/to/test_image.jpg | tr -d '\n' > /tmp/test_b64.txt

# Send to server
curl -X POST https://YOUR-RAILWAY-URL.up.railway.app/check-quality-base64 \
  -H "Content-Type: application/json" \
  -d "{\"image_base64\": \"$(cat /tmp/test_b64.txt)\"}"
```

### Test 3: Full Extraction
```bash
curl -X POST https://YOUR-RAILWAY-URL.up.railway.app/extract-base64 \
  -H "Content-Type: application/json" \
  -d "{\"image_base64\": \"$(cat /tmp/test_b64.txt)\"}"
```

If all 3 tests return proper JSON responses — **THE AI SERVER IS FULLY LIVE ON THE CLOUD!** 🎉

> ### 🛑 PHASE 9 CHECKPOINT — FINAL
> After all 3 tests pass, **STOP HERE**.
> Show the user the test results and confirm everything is working.
> Then say:
> **"🎉 ALL 9 PHASES ARE COMPLETE! The MediScan AI Server is now live on Railway!**
> **Here is your Railway URL: `https://YOUR-RAILWAY-URL.up.railway.app`**
> **Please copy this URL and give it to the MediScan Android App AI so it can update `ApiEndpoints.kt` to point to this cloud server.**
> **The local FastAPI server is still intact — you can run it locally anytime with `bash run_server.sh`."

---

# 📌 AFTER DEPLOYMENT IS COMPLETE — IMPORTANT

## What the MediScan App AI Needs From You

Once the Railway server is live and working, **please provide the following information in the chat**:

### 1. The Railway Public URL
Example: `https://mediscan-ai-production.up.railway.app`

The Android app needs this URL to connect. The app AI will update the file:
```
app/src/main/java/com/mediscan/app/core/constants/ApiEndpoints.kt
```

Currently it connects to:
- Emulator: `http://10.0.2.2:8000/`
- Physical device: `http://10.136.147.203:8000/`

After you give us the Railway URL, we will add:
- Cloud: `https://YOUR-RAILWAY-URL.up.railway.app/` (HTTPS, no port needed)

### 2. Confirm These Endpoints Work
- `GET /health` → returns `{"status": "healthy"}`
- `POST /check-quality-base64` → returns quality assessment
- `POST /extract-base64` → returns extracted prescription data
- `GET /results/{task_id}` → returns stored results

### 3. Any Railway-Specific Notes
- Does the Railway URL use HTTPS? (It should — Railway provides free SSL)
- Is there any rate limiting?
- What's the response time for extraction? (Expected: 10-30 sec on CPU)

---

# 🔁 SWITCHING BETWEEN LOCAL AND CLOUD

After deployment, the setup will be:
- **Cloud (Railway)**: Always on, accessible from anywhere via internet
- **Local (Mac)**: Still works if you `bash run_server.sh` — useful for development/testing

You can "switch" by simply:
1. **Use Cloud**: The Android app points to `https://YOUR-RAILWAY-URL.up.railway.app/`
2. **Use Local**: Change the Android app back to `http://10.136.147.203:8000/`

The local FastAPI server files are untouched — nothing is deleted.

---

# ⚠️ TROUBLESHOOTING

### Build Fails — "Out of memory"
- Railway free tier has 8 GB RAM. PyTorch + PaddleOCR + YOLO should fit.
- If build fails, try: Railway Dashboard → Service → Settings → increase memory limit.

### Server Starts But Models Don't Load
- Check deploy logs for errors
- PaddleOCR downloads ~300 MB of model files on first run — this takes extra time
- The health check has a 120-second grace period for this

### "Module not found" Errors
- Make sure the Dockerfile copies `src/` folder correctly
- The `sys.path.insert(0, ...)` in fastapi_app.py resolves to parent of `backend/`
- In Docker, the structure is `/app/backend/` and `/app/src/`, so the parent path should resolve to `/app/`

### PaddleOCR Download Fails
- PaddleOCR auto-downloads models to `~/.paddleocr/` on first request
- This needs internet access (Railway has it)
- If it fails, check Railway logs for network errors

### Response Time is Slow (>30 seconds)
- This is normal for CPU-only with 3 AI models
- Railway CPU instances process images in ~10-30 seconds
- The Android app already has timeout handling for this

---

# 📊 SUMMARY

| Item | Value |
|------|-------|
| Platform | Railway.app |
| Plan | Free trial ($5 credit) or Hobby ($5/month) |
| Python | 3.11 |
| Compute | CPU-only |
| RAM Needed | 2-3 GB |
| Disk Needed | ~800 MB (code + models + PaddleOCR cache) |
| Build Time | ~5-8 minutes |
| Startup Time | ~60-120 seconds (model loading) |
| Response Time | ~10-30 sec per image (CPU) |
| URL Format | `https://[project-name].up.railway.app` |
| SSL/HTTPS | Free (auto-provided by Railway) |
| Auto-Deploy | Yes (on every `git push`) |

---

**Created for MediScan Capstone Project**
**Date: April 2025**
**Purpose: Guide AI assistant + human user to deploy FastAPI AI server to Railway cloud**
