# 🐛 BUG REPORT: PaddleOCR Returns Empty Text on Railway

## ⚠️ CRITICAL RULE — DO NOT SKIP
> **Complete each step fully before moving to the next.**
> After each step, show what you found and ask: **"Should I continue to the next step?"**
> Wait for the user to say YES before proceeding.

---

## Summary

The Railway server is **live and working** — YOLO detection works perfectly, the server starts correctly, and all API endpoints respond. However, **PaddleOCR returns empty text for every detected field**, causing the MediScan Android app to show blank medication fields after scanning.

---

## Proof — Raw Server Response

I tested with `curl` by sending a real prescription image to:
```
POST https://capstone-production-59e8.up.railway.app/extract-base64
```

The response was:

```json
{
    "medications": [
        {
            "medicine": null,
            "dose_strength": null,
            "schedule": null,
            "duration": null
        }
    ],
    "medication_count": 2,
    "prescription_info": null,
    "doctor": null,
    "stats": {
        "total_fields_detected": 3,
        "medicines_found": 2,
        "doses_found": 1,
        "schedules_found": 0,
        "durations_found": 0
    },
    "raw_extractions": [
        {
            "field_type": "MEDICINE",
            "bbox": [7, 3, 407, 100],
            "confidence": 0.8686,
            "text": "",
            "ocr_confidence": 0.0,
            "matched_text": "",
            "match_score": 0.0
        },
        {
            "field_type": "MEDICINE",
            "bbox": [7, 224, 432, 316],
            "confidence": 0.8697,
            "text": "",
            "ocr_confidence": 0.0,
            "matched_text": "",
            "match_score": 0.0
        },
        {
            "field_type": "DOSE_STRENGTH",
            "bbox": [366, 243, 431, 292],
            "confidence": 0.5034,
            "text": "",
            "ocr_confidence": 0.0,
            "matched_text": "",
            "match_score": 0.0
        }
    ]
}
```

### What this tells us:
| Component | Status | Evidence |
|-----------|--------|----------|
| **YOLO Detection** | ✅ Working | Found 3 fields, confidence 0.86+ |
| **PaddleOCR** | ❌ **BROKEN** | `"text": ""` and `"ocr_confidence": 0.0` for ALL fields |
| **FastAPI Server** | ✅ Working | Returns proper JSON structure |
| **Android App** | ✅ Working | Correct data classes, correct parsing |

---

## Where the Bug Is

**File:** `src/ocr/paddle_ocr_engine.py`

**Method:** `_run_ocr()` — approximately lines 160–195

**Current broken code:**
```python
def _run_ocr(self, image: np.ndarray) -> List[Tuple[str, float]]:
    try:
        results = self.ocr.predict(image)      # ← PaddleOCR v3 API

        if not results:
            return []

        text_results = []
        for page_result in results:
            rec_texts = page_result.get('rec_texts', [])    # ← expects THIS format
            rec_scores = page_result.get('rec_scores', [])  # ← expects THIS format

            for text, score in zip(rec_texts, rec_scores):
                if text and text.strip():
                    text_results.append((text.strip(), float(score)))

        return text_results

    except Exception as e:
        print(f"[PaddleOCR Error] {e}")
        return []
```

**The problem:** The code uses the **PaddleOCR v3 API** (`ocr.predict()`) and expects results with keys `rec_texts` and `rec_scores`. On Railway, the installed PaddleOCR version may:
1. Return results in a **completely different format** (different key names)
2. Be a newer/older version where the `predict()` API changed
3. Return a list-of-lists structure like the old v2 API instead of a dict

Since the `try/except` catches all errors silently and returns `[]`, the OCR fails completely but no error is logged — it just returns empty text for every field.

---

## Steps to Fix

### Step 1: Add Debug Logging to See the Actual PaddleOCR Output

In `src/ocr/paddle_ocr_engine.py`, update the `_run_ocr()` method to log the raw output BEFORE parsing:

```python
def _run_ocr(self, image: np.ndarray) -> List[Tuple[str, float]]:
    try:
        results = self.ocr.predict(image)

        # ── DEBUG: Log raw output to understand the format ──
        print(f"[PaddleOCR DEBUG] Raw result type: {type(results)}")
        print(f"[PaddleOCR DEBUG] Raw result: {results}")

        if not results:
            print("[PaddleOCR DEBUG] results is empty/None")
            return []

        text_results = []
        for i, page_result in enumerate(results):
            print(f"[PaddleOCR DEBUG] page_result[{i}] type: {type(page_result)}")
            print(f"[PaddleOCR DEBUG] page_result[{i}]: {page_result}")

            rec_texts = page_result.get('rec_texts', [])
            rec_scores = page_result.get('rec_scores', [])

            for text, score in zip(rec_texts, rec_scores):
                if text and text.strip():
                    text_results.append((text.strip(), float(score)))

        return text_results

    except Exception as e:
        print(f"[PaddleOCR Error] {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return []
```

Push this to Railway, wait for redeploy, then **check the Railway deployment logs** to see what PaddleOCR actually returns.

> ### 🛑 STEP 1 CHECKPOINT
> After adding the debug logging and pushing to Railway:
> 1. Wait for Railway to redeploy (~3-5 minutes)
> 2. Check the Railway logs (Dashboard → Service → Deployments → View Logs)
> 3. Show the user the log output that appears when a scan is done
> 4. Ask: **"✅ Step 1 complete — I can see the PaddleOCR debug output in logs. Should I continue to Step 2 (fix the parsing)?"**
> Wait for the user to say YES.

---

### Step 2: Fix the Response Parsing

Based on what the logs show in Step 1, fix the `_run_ocr()` method.

**The fix should handle BOTH the v3 API format AND the v2 API format as a fallback:**

```python
def _run_ocr(self, image: np.ndarray) -> List[Tuple[str, float]]:
    try:
        results = self.ocr.predict(image)

        if not results:
            return []

        text_results = []

        for page_result in results:
            # ── Try PaddleOCR v3 dict format ──
            if isinstance(page_result, dict):
                rec_texts = page_result.get('rec_texts', [])
                rec_scores = page_result.get('rec_scores', [])

                for text, score in zip(rec_texts, rec_scores):
                    if text and str(text).strip():
                        text_results.append((str(text).strip(), float(score)))

            # ── Try PaddleOCR v2 list-of-lists format ──
            # v2 returns: [[[box_points, (text, confidence)], ...]]
            elif isinstance(page_result, list):
                for line in page_result:
                    if isinstance(line, (list, tuple)) and len(line) == 2:
                        text_info = line[1]
                        if isinstance(text_info, (list, tuple)) and len(text_info) == 2:
                            text, score = text_info
                            if text and str(text).strip():
                                text_results.append((str(text).strip(), float(score)))

        return text_results

    except Exception as e:
        print(f"[PaddleOCR Error] {type(e).__name__}: {e}")
        return []
```

> ### 🛑 STEP 2 CHECKPOINT
> After fixing the `_run_ocr()` method:
> 1. Push to Railway and wait for redeploy
> 2. Test with a real prescription image (you can use the curl command below)
> 3. Check if `"text"` fields in `raw_extractions` now have actual text
> 4. Ask: **"✅ Step 2 complete — the parsing fix is pushed. Should I continue to Step 3 (test the full pipeline)?"**
> Wait for the user to say YES.

---

### Step 3: Test the Full Pipeline

Run this test from the terminal to verify the fix works:

```bash
# Encode a test prescription image
base64 -i /path/to/prescription_image.jpg | tr -d '\n' > /tmp/test_b64.txt

# Send to Railway server
curl -s -X POST https://capstone-production-59e8.up.railway.app/extract-base64 \
  -H "Content-Type: application/json" \
  -d "{\"image\": \"$(cat /tmp/test_b64.txt)\"}" | python3 -m json.tool
```

**Expected result after fix:**
```json
{
    "medications": [
        {
            "medicine": "Amoxicillin",
            "dose_strength": "500mg",
            "schedule": "1+0+1",
            "duration": "7 days"
        }
    ],
    "raw_extractions": [
        {
            "field_type": "MEDICINE",
            "text": "Amoxicillin",
            "ocr_confidence": 0.87
        }
    ]
}
```

The key thing to confirm: **`"text"` fields must have actual text** (not `""`) and **`"ocr_confidence"` must be > 0**.

> ### 🛑 STEP 3 CHECKPOINT
> After testing:
> 1. Show the user the curl response
> 2. If medications have real text → fix is confirmed ✅
> 3. If still empty → go back to Step 1 logs and investigate further
> 4. Ask: **"✅ Step 3 complete — the server now returns real extracted text! Should I remove the debug logging (Step 4)?"**
> Wait for the user to say YES.

---

### Step 4: Remove Debug Logging and Final Push

Once the fix is confirmed working, remove the debug print statements from `_run_ocr()` to keep logs clean:

Remove these lines:
```python
print(f"[PaddleOCR DEBUG] Raw result type: {type(results)}")
print(f"[PaddleOCR DEBUG] Raw result: {results}")
print(f"[PaddleOCR DEBUG] results is empty/None")
print(f"[PaddleOCR DEBUG] page_result[{i}] type: {type(page_result)}")
print(f"[PaddleOCR DEBUG] page_result[{i}]: {page_result}")
```

Then push the final clean version to Railway.

> ### 🛑 STEP 4 CHECKPOINT — FINAL
> After pushing the clean version:
> 1. Wait for Railway to redeploy
> 2. Do one final test with a prescription image
> 3. Confirm the Android app now shows real extracted text after scanning
> 4. Say: **"🎉 ALL DONE! The PaddleOCR bug is fixed. The MediScan server is now fully working on Railway. Please test the Android app by scanning a real prescription."**

---

## Additional Notes

### DO NOT touch these — they are working correctly:
- ❌ Do NOT modify `fastapi_app.py`
- ❌ Do NOT modify `structured_extractor.py`
- ❌ Do NOT modify `extractor.py` (the `extract_text` method is correct)
- ❌ Do NOT modify `quality_checker.py`
- ❌ Do NOT touch the Android app code
- ✅ Only fix `src/ocr/paddle_ocr_engine.py` — specifically the `_run_ocr()` method

### If Step 2 fix still doesn't work:

Try switching from `predict()` to the old `ocr()` API entirely in `_init_paddleocr()`:

```python
def _init_paddleocr(self):
    from paddleocr import PaddleOCR
    # Try v2 API (more compatible across versions)
    self.ocr = PaddleOCR(
        use_angle_cls=False,
        lang='en',
        show_log=False
    )
    # Override predict method to use v2 ocr() call
    self._use_v2_api = True
```

And in `_run_ocr()`, check `self._use_v2_api` and use `self.ocr.ocr(image, cls=False)` instead.

---

**Created for MediScan Capstone Project**
**Date: April 2, 2026**
**Purpose: Fix PaddleOCR empty text bug on Railway cloud deployment**
