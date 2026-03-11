"""
Pipeline Test Run #2 — MediScan v6.1
=====================================
Tests 5 specific images (4 good + 1 bad) through the complete pipeline.
Saves annotated images + JSON results to a timestamped folder.

Images tested:
  Good: img_0824, img_0800, img_0348, img_1211
  Bad:  img_0462

Output: data/results/pipeline_run2_<timestamp>/
"""

import os
import sys
import cv2
import json
import time
import numpy as np
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

# ── Timestamped output folder ──────────────────────────────────────────────
TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M%S")
OUTPUT_DIR = PROJECT_ROOT / "data" / "results" / f"pipeline_run2_{TIMESTAMP}"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# ── The 5 test images ──────────────────────────────────────────────────────
TEST_IMAGES = [
    {"path": PROJECT_ROOT / "data" / "raw_images" / "good" / "img_0824.jpg", "label": "good"},
    {"path": PROJECT_ROOT / "data" / "raw_images" / "good" / "img_0800.jpg", "label": "good"},
    {"path": PROJECT_ROOT / "data" / "raw_images" / "good" / "img_0348.jpg", "label": "good"},
    {"path": PROJECT_ROOT / "data" / "raw_images" / "good" / "img_1211.jpg", "label": "good"},
    {"path": PROJECT_ROOT / "data" / "raw_images" / "bad"  / "img_0462.jpg", "label": "bad"},
]

# ── Color palette for YOLO field boxes ────────────────────────────────────
COLORS = {
    "MEDICINE":         (50,  205,  50),   # lime green
    "DOSE_STRENGTH":    (0,   191, 255),   # deep sky blue
    "DOSAGE_SCHEDULE":  (255, 140,   0),   # orange
    "DURATION":         (238,  18, 137),   # pink
    "DOCTOR_NAME":      (0,   255, 255),   # cyan
    "HOSPITAL":         (255, 255,   0),   # yellow
    "DATE":             (180, 180, 180),   # light grey
    "TEST":             (144, 238, 144),   # pale green
    "DIAGNOSIS":        (147, 112, 219),   # medium purple
}


def draw_rich_annotation(image, fields, quality, status, elapsed):
    """Draw a detailed annotation overlay on the image."""
    vis = image.copy()
    h, w = vis.shape[:2]

    # ── Draw bounding boxes + field labels ───────────────────────────────
    for f in fields:
        x1, y1, x2, y2 = f["bbox"]
        ft   = f.get("field_type", "")
        text = f.get("text", "")
        conf = f.get("yolo_confidence", f.get("confidence", 0))
        oconf = f.get("ocr_confidence", 0)
        color = COLORS.get(ft, (200, 200, 200))

        cv2.rectangle(vis, (x1, y1), (x2, y2), color, 2)

        # Label background
        short_text = (text[:22] + "…") if len(text) > 25 else text
        label = f"{ft}: {short_text}"
        (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.42, 1)
        cv2.rectangle(vis, (x1, y1 - th - 6), (x1 + tw + 4, y1), color, -1)
        cv2.putText(vis, label, (x1 + 2, y1 - 4),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.42, (0, 0, 0), 1)

        # OCR confidence badge at bottom-right of box
        badge = f"{oconf:.0%}"
        (bw, bh), _ = cv2.getTextSize(badge, cv2.FONT_HERSHEY_SIMPLEX, 0.38, 1)
        cv2.rectangle(vis, (x2 - bw - 4, y2 - bh - 4), (x2, y2), (0, 0, 0), -1)
        cv2.putText(vis, badge, (x2 - bw - 2, y2 - 3),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.38, (255, 255, 255), 1)

    # ── Top info banner ──────────────────────────────────────────────────
    banner_h = 44
    banner = np.zeros((banner_h, w, 3), dtype=np.uint8)
    q_score = quality.get("quality_score", 0)
    q_label = quality.get("quality_label", "?")
    issues  = quality.get("issues", [])
    issues_str = ", ".join(issues) if issues else "none"
    n_fields = len(fields)

    if status == "rejected":
        banner[:] = (0, 0, 160)   # red banner
        msg = (f"REJECTED  |  Quality: {q_label} ({q_score:.2f})  |"
               f"  Issues: {issues_str}  |  Time: {elapsed:.2f}s")
    else:
        banner[:] = (0, 80, 0)    # dark green banner
        msg = (f"ACCEPTED  |  Quality: {q_label} ({q_score:.2f})  |"
               f"  Fields: {n_fields}  |  Time: {elapsed:.2f}s")

    cv2.putText(banner, msg, (10, 28),
                cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 1)
    vis = np.vstack([banner, vis])

    # ── Legend strip at bottom ───────────────────────────────────────────
    legend_h = 28
    legend = np.zeros((legend_h, w, 3), dtype=np.uint8)
    legend[:] = (30, 30, 30)
    x_off = 8
    for cls, col in COLORS.items():
        short = cls[:4]
        (tw2, th2), _ = cv2.getTextSize(short, cv2.FONT_HERSHEY_SIMPLEX, 0.36, 1)
        cv2.rectangle(legend, (x_off, 6), (x_off + 12, 22), col, -1)
        cv2.putText(legend, short, (x_off + 15, 20),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.36, (220, 220, 220), 1)
        x_off += tw2 + 30
        if x_off > w - 80:
            break
    vis = np.vstack([vis, legend])

    return vis


def print_section(title):
    print(f"\n{'═'*66}")
    print(f"  {title}")
    print(f"{'═'*66}")


def run_pipeline_test():
    print_section("🏥 MediScan v6.1 — Pipeline Test Run #2")
    print(f"  Output folder : {OUTPUT_DIR}")
    print(f"  Test images   : {len(TEST_IMAGES)} (4 good + 1 bad)")
    print(f"  Timestamp     : {TIMESTAMP}")

    # ── Load pipeline ──────────────────────────────────────────────────
    print_section("Loading Pipeline Components")
    from src.pipeline.structured_extractor import StructuredPrescriptionExtractor
    extractor = StructuredPrescriptionExtractor(use_gpu=True)

    all_results = []
    total_start = time.time()

    # ── Process each image ─────────────────────────────────────────────
    for idx, item in enumerate(TEST_IMAGES, 1):
        img_path = item["path"]
        true_label = item["label"]

        print(f"\n{'─'*66}")
        print(f"  [{idx}/5]  {img_path.name}  (actual: {true_label.upper()})")
        print(f"{'─'*66}")

        image = cv2.imread(str(img_path))
        if image is None:
            print(f"  ❌ Could not read image — skipping")
            continue

        h, w = image.shape[:2]
        print(f"  📐 Dimensions : {w} × {h} px")

        t0 = time.time()
        result = extractor.process_structured(image)
        elapsed = time.time() - t0

        status    = result.get("status", "unknown")
        quality   = result.get("quality_check", {})
        q_label   = quality.get("quality_label", "N/A")
        q_score   = quality.get("quality_score", 0)
        q_blur    = quality.get("blur_score", 0)
        q_bright  = quality.get("brightness", 0)
        q_contrast= quality.get("contrast", 0)
        q_issues  = quality.get("issues", [])
        q_rec     = quality.get("recommendation", "")

        # ── Quality result ───────────────────────────────────────────
        print(f"\n  🔍 QUALITY CHECK")
        print(f"     Decision    : {'✅ ACCEPTED' if status != 'rejected' else '❌ REJECTED'}")
        print(f"     Score       : {q_score:.3f}  ({q_label})")
        print(f"     Blur        : {q_blur:.1f}  (≥50 = sharp)")
        print(f"     Brightness  : {q_bright:.3f}  (0.15–0.85 = ok)")
        print(f"     Contrast    : {q_contrast:.3f}  (≥0.05 = ok)")
        print(f"     Issues      : {q_issues if q_issues else 'none'}")
        print(f"     Message     : {q_rec}")

        # ── Collect field data for annotation ────────────────────────
        raw_fields = result.get("extractions", [])  # list of dicts from asdict()

        if status == "rejected":
            print(f"\n  ⛔ Pipeline stopped — YOLO + OCR skipped (saved ~10s)")
            print(f"  ⏱  Time : {elapsed:.3f}s")

            vis = draw_rich_annotation(image, [], quality, status, elapsed)
            out_img = OUTPUT_DIR / f"{idx:02d}_{img_path.stem}_REJECTED.jpg"
            cv2.imwrite(str(out_img), vis)
            print(f"  💾 Saved : {out_img.name}")

            all_results.append({
                "idx": idx, "filename": img_path.name,
                "true_label": true_label, "pipeline_status": status,
                "quality": quality, "time_s": round(elapsed, 3),
                "fields": [], "medications": [],
            })
            continue

        # ── YOLO + OCR results ───────────────────────────────────────
        medications = result.get("medications", [])
        doctor_info = result.get("doctor_info", {})
        other       = result.get("other_fields", {})
        total_fields = result.get("total_fields", 0)

        # Field type breakdown
        field_counts = {}
        for f in raw_fields:
            ft = f.get("field_type", "?")
            field_counts[ft] = field_counts.get(ft, 0) + 1

        print(f"\n  🎯 YOLO DETECTION  ({total_fields} fields)")
        for ft, cnt in sorted(field_counts.items()):
            color_tag = "  "
            print(f"     {color_tag}{ft:<22} × {cnt}")

        # OCR confidence stats
        confs = [f.get("ocr_confidence", 0) for f in raw_fields if f.get("text")]
        avg_conf = (sum(confs) / len(confs)) if confs else 0
        min_conf = min(confs) if confs else 0
        max_conf = max(confs) if confs else 0

        print(f"\n  📝 OCR EXTRACTION")
        if medications:
            print(f"     💊 Medications detected: {len(medications)}")
            for j, med in enumerate(medications, 1):
                name  = med.get("medicine")    or "—"
                dose  = med.get("dose_strength") or "—"
                sched = med.get("schedule")    or "—"
                dur   = med.get("duration")    or "—"
                m_conf = med.get("confidence", {}).get("medicine", 0) or 0
                print(f"        {j:>2}. {name:<30}  (YOLO conf {m_conf:.0%})")
                print(f"            Dose: {dose:<12} Schedule: {sched:<12} Duration: {dur}")
        else:
            print(f"     No structured medications found")

        if doctor_info.get("name"):
            print(f"     👨‍⚕️ Doctor   : {doctor_info['name']}")
        if doctor_info.get("hospital"):
            print(f"     🏥 Hospital : {doctor_info['hospital']}")
        for key, vals in (other or {}).items():
            if vals:
                print(f"     📋 {key:<10} : {vals}")

        print(f"\n  📊 OCR CONFIDENCE")
        print(f"     Average : {avg_conf:.1%}   Min : {min_conf:.1%}   Max : {max_conf:.1%}")
        print(f"  ⏱  Time    : {elapsed:.2f}s")

        # ── Annotated image ──────────────────────────────────────────
        annotated_raw = result.get("annotated_image", image)
        vis = draw_rich_annotation(image, raw_fields, quality, status, elapsed)
        out_img = OUTPUT_DIR / f"{idx:02d}_{img_path.stem}_ANNOTATED.jpg"
        cv2.imwrite(str(out_img), vis)
        print(f"  💾 Saved : {out_img.name}")

        # ── Per-image JSON ───────────────────────────────────────────
        img_result = {
            "idx": idx, "filename": img_path.name,
            "true_label": true_label, "pipeline_status": status,
            "dimensions": {"width": w, "height": h},
            "quality": quality,
            "total_fields": total_fields,
            "field_counts": field_counts,
            "medications": medications,
            "doctor_info": doctor_info,
            "other_fields": other,
            "ocr_stats": {
                "avg_confidence": round(avg_conf, 4),
                "min_confidence": round(min_conf, 4),
                "max_confidence": round(max_conf, 4),
                "fields_with_text": len(confs),
            },
            "time_s": round(elapsed, 2),
        }
        json_path = OUTPUT_DIR / f"{idx:02d}_{img_path.stem}_result.json"
        with open(json_path, "w", encoding="utf-8") as jf:
            json.dump(img_result, jf, indent=2, default=str)

        all_results.append(img_result)

    # ── Overall summary ────────────────────────────────────────────────
    total_time = time.time() - total_start
    print_section("📊 FINAL SUMMARY")

    accepted = [r for r in all_results if r["pipeline_status"] == "completed"]
    rejected = [r for r in all_results if r["pipeline_status"] == "rejected"]

    print(f"  Total images  : {len(all_results)}")
    print(f"  ✅ Accepted   : {len(accepted)}")
    print(f"  ❌ Rejected   : {len(rejected)}")
    print()

    for r in all_results:
        s = "✅ PASS" if r["pipeline_status"] == "completed" else "❌ REJECTED"
        q = r["quality"]
        n_meds = len(r.get("medications", []))
        t = r["time_s"]
        qs = q.get("quality_score", 0)
        print(f"  {r['idx']:>2}. {r['filename']:<20}  {s:<12}  "
              f"score={qs:.2f}  meds={n_meds}  {t:.1f}s")

    if accepted:
        all_confs = []
        for r in accepted:
            st = r.get("ocr_stats", {})
            if st.get("avg_confidence", 0) > 0:
                all_confs.append(st["avg_confidence"])
        overall_conf = sum(all_confs) / len(all_confs) if all_confs else 0
        total_meds   = sum(len(r.get("medications", [])) for r in accepted)
        avg_t        = sum(r["time_s"] for r in accepted) / len(accepted)
        print(f"\n  Overall OCR confidence : {overall_conf:.1%}")
        print(f"  Total medications found: {total_meds}")
        print(f"  Avg time (good images) : {avg_t:.1f}s")

    if rejected:
        avg_reject_t = sum(r["time_s"] for r in rejected) / len(rejected)
        print(f"  Avg rejection time     : {avg_reject_t:.3f}s  (instant ⚡)")

    print(f"\n  Total wall time : {total_time:.1f}s")

    # ── Save master summary JSON ──────────────────────────────────────
    summary = {
        "run": "pipeline_run2",
        "timestamp": TIMESTAMP,
        "pipeline_version": "v6.1",
        "images_tested": len(all_results),
        "accepted": len(accepted),
        "rejected": len(rejected),
        "results": all_results,
    }
    summary_path = OUTPUT_DIR / "summary.json"
    with open(summary_path, "w", encoding="utf-8") as sf:
        json.dump(summary, sf, indent=2, default=str)

    # ── List saved files ──────────────────────────────────────────────
    print(f"\n{'─'*66}")
    print(f"  📁 Results saved to:")
    print(f"     {OUTPUT_DIR}")
    print(f"\n  Files:")
    for f in sorted(OUTPUT_DIR.iterdir()):
        size = f.stat().st_size
        size_str = (f"{size/1024/1024:.1f} MB" if size > 1_048_576
                    else f"{size/1024:.1f} KB")
        icon = "🖼 " if f.suffix == ".jpg" else "📄"
        print(f"     {icon} {f.name:<52} ({size_str})")

    print(f"\n{'═'*66}")
    print(f"  ✅ TEST COMPLETE — open the folder above to view annotated images")
    print(f"{'═'*66}\n")


if __name__ == "__main__":
    run_pipeline_test()
