# 📋 MediScan Backend — Technical Report

## 1. Model & Framework

### Models Used (3 local models, zero cloud API calls)

| # | Model | Architecture | Purpose | File | Size |
|---|-------|-------------|---------|------|------|
| 1 | **Quality Checker** | ResNet18 (fine-tuned) | Binary classification: good vs bad image | `models/image_quality_classifier.pt` | **128 MB** |
| 2 | **Object Detector** | YOLOv8s (custom trained) | Detect 9 prescription field types | `experiments/v6_9class_english/weights/best.pt` | **64 MB** |
| 3 | **OCR Engine** | PaddleOCR v5 (PP-OCRv5) | English text recognition | Downloaded to `~/.paddlex/official_models/` on first run | **~96 MB** (det + rec models combined) |

### Frameworks/Libraries

| Library | Version | Role |
|---------|---------|------|
| **PyTorch** 2.8.0 | ResNet18 inference + YOLO backend |
| **Ultralytics** 8.4.18 | YOLOv8s object detection |
| **PaddlePaddle** 3.3.0 | PaddleOCR deep learning backend |
| **PaddleOCR** 3.4.0 | OCR text detection + recognition |
| **OpenCV** 4.13.0 | Image preprocessing |

### ❌ No Cloud APIs
Everything runs **locally on this machine**. There are no OpenAI, Google, Gemini, Tesseract, or any external API calls. All 3 models are loaded into RAM at server startup and run inference locally.

---

## 2. Processing Pipeline

### `/extract-base64` — Full Pipeline (Step-by-Step)

This is the main endpoint the Android app calls. Here's exactly what happens:

```
Phone sends POST /extract-base64 { "image": "<base64 string>" }
│
├─ Step 1: Base64 Decode
│   base64.b64decode(image_b64)  →  raw bytes
│   np.frombuffer(bytes)  →  numpy array
│   cv2.imdecode(array)  →  BGR image at FULL RESOLUTION (no resize)
│
├─ Step 2: Quality Check (ResNet18 + Laplacian)  ~50ms
│   ├─ Resize to 224×224 for CNN
│   ├─ ResNet18 forward pass → good_prob / bad_prob
│   ├─ Laplacian variance (blur detection)
│   ├─ Brightness + contrast analysis
│   └─ Returns quality_result (BUT never blocks — extraction continues)
│
├─ Step 3: YOLO Detection  ~3-5 sec on CPU
│   ├─ self.yolo_model(image, conf=0.25)
│   ├─ Detects bounding boxes for 9 classes:
│   │   MEDICINE, DOSE_STRENGTH, DOSAGE_SCHEDULE, DURATION,
│   │   DOCTOR_NAME, HOSPITAL, DATE, TEST, DIAGNOSIS
│   └─ Returns List[DetectedField] with bbox + confidence
│
├─ Step 4: PaddleOCR Text Extraction  ~5-10 sec on CPU
│   ├─ For EACH detected field:
│   │   ├─ Crop image region (bbox + 2% padding)
│   │   ├─ Attempt 1: Field-specific preprocessing
│   │   │   ├─ Grayscale → Upscale (2-3×) → Denoise → CLAHE → Sharpen
│   │   │   └─ PaddleOCR predict()
│   │   ├─ Attempt 2 (if conf < 0.6): Raw upscaled image → OCR
│   │   └─ Attempt 3 (if conf < 0.5): Otsu binary threshold → OCR
│   └─ Each field now has: text + ocr_confidence
│
├─ Step 5: Spatial Grouping  ~instant
│   ├─ Find all MEDICINE fields as "anchors"
│   ├─ For each medicine, find DOSE/SCHEDULE/DURATION on same Y-row
│   │   (tolerance: 3% of image height)
│   └─ Returns List[MedicationEntry]
│
├─ Step 6: Build Response JSON
│   ├─ Structured medications array
│   ├─ Doctor info, prescription info
│   ├─ Quality check result, stats
│   └─ status: "completed"
│
└─ Return JSON to phone
```

### `/check-quality-base64` — Quick Quality Check Only

```
Base64 decode → cv2.imdecode → ResNet18 (224×224) + Laplacian + brightness/contrast → JSON
```
Takes ~50ms. Used for real-time camera feedback in the app.

---

## 3. Performance & Hardware

### Device

| Setting | Value |
|---------|-------|
| **Compute Device** | `cpu` (no GPU) |
| **MPS (Apple Silicon)** | ❌ Not enabled |
| **CUDA** | ❌ Not available (no NVIDIA GPU on Mac) |
| **CoreML / Metal** | ❌ Not used |

The code checks `torch.cuda.is_available()` at startup and falls back to CPU. There is **no MPS (Apple Metal) acceleration** configured.

### Model Sizes

| Model | Parameters | File Size | RAM at Runtime |
|-------|-----------|-----------|---------------|
| ResNet18 (quality) | **11,689,512** (~11.7M) | 128 MB | ~45 MB |
| YOLOv8s (detection) | ~**11.2M** | 64 MB | ~30 MB |
| PP-OCRv5 det+rec | ~**15M** combined | ~96 MB | ~100 MB |

### Approximate Processing Time (Mac CPU)

| Step | Intel Mac | Apple Silicon (M1/M2/M3) |
|------|-----------|-------------------------|
| Quality Check | ~50ms | ~30ms |
| YOLO Detection | 3-5 sec | 1-2 sec |
| PaddleOCR (per field) | 1-3 sec | 0.5-1 sec |
| **Total per image** | **10-20 sec** | **5-8 sec** |
| **On Windows GPU (RTX)** | — | **2-3 sec** |

**🔴 The major bottleneck is PaddleOCR** — it runs up to 3 attempts per field (field-preprocessed, raw upscaled, binary thresholded), and each attempt calls `ocr.predict()` which runs both a text detection and recognition model.

---

## 4. Image Handling

### ❌ NO Resize Before Processing

```python
# In /extract-base64 endpoint (fastapi_app.py line ~298):
img_bytes = base64.b64decode(image_b64)
img_array = np.frombuffer(img_bytes, dtype=np.uint8)
image = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
# image is at FULL RESOLUTION — no resize happens
result = extractor.process_structured(image)
```

The image is decoded from base64 and passed **at full camera resolution** (e.g., 4000×3000 from a Samsung S25 Ultra = **12 megapixels**) directly to YOLO and OCR.

### What Each Model Actually Needs

| Model | Input Size | What's Happening Now |
|-------|-----------|---------------------|
| ResNet18 (quality) | 224×224 | ✅ Resized internally via `transforms.Resize((224, 224))` |
| YOLOv8s | 640×640 (default) | ✅ Ultralytics auto-resizes internally, but processes the full image first |
| PaddleOCR | Any size (crops) | ⚠️ Receives crops from full-res image, then **upscales 2-3×** on top of that |

### 🔴 Problem: PaddleOCR Double-Upscaling
The OCR engine crops a field region from the full-res image (which could already be ~500×100px from a 4K photo), then **upscales it 2-3× more** before running OCR. On a 4K image this creates unnecessarily large crops.

---

## 5. Dependencies

### AI/ML Packages (from `requirements_mac.txt`)

| Package | Required Version | Installed Version | Purpose |
|---------|-----------------|-------------------|---------|
| `torch` | ≥2.1.0 | **2.8.0** | ResNet18 + YOLO backend |
| `torchvision` | ≥0.16.0 | (bundled) | Image transforms |
| `torchaudio` | ≥2.1.0 | (bundled) | Not used |
| `ultralytics` | ≥8.0.0 | **8.4.18** | YOLOv8s |
| `paddlepaddle` | ≥2.6.0 | **3.3.0** | PaddleOCR backend |
| `paddleocr` | ≥2.7.0 | **3.4.0** | OCR engine |
| `opencv-python` | ≥4.8.0 | **4.13.0** (headless) | Image processing |
| `Pillow` | ≥10.0.0 | **11.3.0** | Image loading |
| `numpy` | ≥1.24.0 | **2.0.2** | Array ops |
| `fastapi` | ≥0.100.0 | **0.128.8** | API framework |
| `uvicorn[standard]` | ≥0.23.0 | **0.39.0** | ASGI server |
| `python-multipart` | ≥0.0.6 | (installed) | File uploads |

---

## 6. Server Configuration

### Uvicorn Config

```bash
# run_server.sh runs:
python backend/fastapi_app.py
# which calls:
uvicorn.run(app, host="0.0.0.0", port=8000)
```

| Setting | Value |
|---------|-------|
| **Workers** | **1** (single process, default) |
| **Host** | `0.0.0.0` (all interfaces) |
| **Port** | `8000` |
| **Reload** | No |
| **Access log** | Yes (default) |

### Async/Await

All endpoint handlers are declared `async`:
```python
@app.post("/extract-base64")
async def extract_from_base64(data: dict):
```
**However**, the actual model inference (`extractor.process_structured(image)`) is **synchronous blocking code** — it runs on the main event loop thread. This means:
- While one image is processing (~10-20 sec), **all other requests are blocked**
- The server cannot handle concurrent requests

### Caching / Optimization

| Optimization | Present? |
|-------------|----------|
| Model singleton (load once) | ✅ Yes — loaded at startup, reused |
| Image resize before pipeline | ❌ No — full resolution |
| Response caching | ❌ No |
| Background task / thread pool | ❌ No |
| Multiple uvicorn workers | ❌ No (1 worker) |
| GPU / MPS acceleration | ❌ No |
| PaddleOCR batch processing | ❌ No — fields processed one by one |
| Limit OCR retry attempts | ❌ No — always tries up to 3× per field |

---

## 🔴 Identified Bottlenecks (Ranked)

1. **PaddleOCR multi-attempt** — Each field gets up to **3 full OCR passes** (preprocessed → raw → binary). With ~5-10 fields per prescription, that's **15-30 OCR calls** per image.
2. **No image downscaling** — Full 4K phone images flow through the entire pipeline. YOLO only needs 640×640, OCR crops are already large enough.
3. **CPU-only** — No MPS/Metal acceleration on Apple Silicon.
4. **Synchronous blocking** — `async def` handlers but sync model inference blocks the event loop.
5. **Single worker** — Only 1 uvicorn process, can't handle concurrent requests.

---

*Generated: March 11, 2026*
*Source: Analysis of MediScan capstone backend codebase*
