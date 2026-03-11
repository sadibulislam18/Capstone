"""
Full Pipeline Visual Demo — MediScan v6.1
==========================================
Picks random images, runs through the complete pipeline,
saves annotated images + JSON results for visual inspection.

Output: data/results/full_pipeline_demo/
"""

import os
import sys
import cv2
import json
import random
import time
import numpy as np
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))


def run_full_demo():
    """Run the complete pipeline demo with visual results."""
    
    # ═══════════════════════════════════════════════════════════════
    # Setup
    # ═══════════════════════════════════════════════════════════════
    
    OUTPUT_DIR = PROJECT_ROOT / "data" / "results" / "full_pipeline_demo"
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    GOOD_DIR = PROJECT_ROOT / "data" / "raw_images" / "good"
    BAD_DIR = PROJECT_ROOT / "data" / "raw_images" / "bad"
    
    print("=" * 70)
    print("🏥 MediScan v6.1 — Full Pipeline Visual Demo")
    print("=" * 70)
    print(f"  Output: {OUTPUT_DIR}")
    print()
    
    # Pick random images
    good_images = sorted(GOOD_DIR.glob("*.jpg"))
    bad_images = sorted(BAD_DIR.glob("*.jpg"))
    
    random.seed(42)  # Reproducible
    selected_good = random.sample(good_images, min(5, len(good_images)))
    selected_bad = random.sample(bad_images, min(3, len(bad_images)))
    
    print(f"  Selected {len(selected_good)} good images + {len(selected_bad)} bad images")
    print()
    
    # ═══════════════════════════════════════════════════════════════
    # Load Pipeline
    # ═══════════════════════════════════════════════════════════════
    
    print("Loading pipeline components...")
    from src.pipeline.structured_extractor import StructuredPrescriptionExtractor
    
    extractor = StructuredPrescriptionExtractor(use_gpu=True)
    print()
    
    # ═══════════════════════════════════════════════════════════════
    # Process All Images
    # ═══════════════════════════════════════════════════════════════
    
    all_results = []
    
    # --- GOOD images ---
    print("=" * 70)
    print("📸 PROCESSING GOOD IMAGES (expect: quality pass → detection → OCR)")
    print("=" * 70)
    
    for i, img_path in enumerate(selected_good, 1):
        print(f"\n{'─' * 60}")
        print(f"  [{i}/{len(selected_good)}] {img_path.name}")
        print(f"{'─' * 60}")
        
        image = cv2.imread(str(img_path))
        if image is None:
            print(f"  ❌ Could not read image")
            continue
        
        h, w = image.shape[:2]
        print(f"  📐 Size: {w}x{h}")
        
        start = time.time()
        result = extractor.process_structured(image)
        elapsed = time.time() - start
        
        status = result.get('status', 'unknown')
        quality = result.get('quality_check', {})
        q_label = quality.get('quality_label', 'N/A')
        q_score = quality.get('quality_score', 0)
        q_issues = quality.get('issues', [])
        q_blur = quality.get('blur_score', 0)
        q_bright = quality.get('brightness', 0)
        q_contrast = quality.get('contrast', 0)
        q_rec = quality.get('recommendation', '')
        
        print(f"\n  🔍 QUALITY CHECK:")
        print(f"     Label: {q_label} (score={q_score:.3f})")
        print(f"     Blur: {q_blur:.1f} | Brightness: {q_bright:.3f} | Contrast: {q_contrast:.3f}")
        print(f"     Issues: {q_issues if q_issues else 'None'}")
        print(f"     Recommendation: {q_rec}")
        
        if status == 'rejected':
            print(f"\n  ❌ REJECTED — Pipeline stopped here")
            print(f"  ⏱ Time: {elapsed:.2f}s")
            
            # Save rejected image with overlay
            vis = image.copy()
            cv2.putText(vis, f"REJECTED - Quality: {q_label} ({q_score:.2f})", 
                       (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 0, 255), 3)
            cv2.putText(vis, f"Issues: {', '.join(q_issues) if q_issues else 'CNN score too low'}", 
                       (20, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
            out_path = OUTPUT_DIR / f"good_{i:02d}_{img_path.stem}_REJECTED.jpg"
            cv2.imwrite(str(out_path), vis)
            
            all_results.append({
                'filename': img_path.name,
                'category': 'good',
                'status': 'rejected',
                'quality': quality,
                'time': round(elapsed, 2),
            })
            continue
        
        # Successful extraction
        medications = result.get('medications', [])
        doctor_info = result.get('doctor_info', {})
        other = result.get('other_fields', {})
        total_fields = result.get('total_fields', 0)
        
        print(f"\n  🎯 YOLO DETECTION: {total_fields} fields detected")
        
        # Print field breakdown
        extractions = result.get('extractions', [])
        field_counts = {}
        for f in extractions:
            ft = f.get('field_type', 'UNKNOWN')
            field_counts[ft] = field_counts.get(ft, 0) + 1
        for ft, count in sorted(field_counts.items()):
            print(f"     {ft}: {count}")
        
        print(f"\n  📝 OCR EXTRACTION:")
        
        # Print medications
        if medications:
            print(f"     💊 Medications ({len(medications)}):")
            for j, med in enumerate(medications, 1):
                name = med.get('medicine', 'N/A')
                dose = med.get('dose_strength', 'N/A')
                sched = med.get('schedule', 'N/A')
                dur = med.get('duration', 'N/A')
                print(f"        {j}. {name}")
                print(f"           Dose: {dose} | Schedule: {sched} | Duration: {dur}")
        
        # Print other info
        if doctor_info:
            doc_name = doctor_info.get('name', '')
            doc_hosp = doctor_info.get('hospital', '')
            if doc_name:
                print(f"     👨‍⚕️ Doctor: {doc_name}")
            if doc_hosp:
                print(f"     🏥 Hospital: {doc_hosp}")
        
        if other:
            for key, vals in other.items():
                if vals:
                    print(f"     📋 {key}: {vals}")
        
        # Print confidence stats
        confs = [f.get('ocr_confidence', 0) for f in extractions if f.get('text')]
        if confs:
            avg_conf = sum(confs) / len(confs)
            min_conf = min(confs)
            max_conf = max(confs)
            print(f"\n  📊 OCR CONFIDENCE:")
            print(f"     Average: {avg_conf:.1%} | Min: {min_conf:.1%} | Max: {max_conf:.1%}")
        
        print(f"\n  ⏱ Total time: {elapsed:.2f}s")
        
        # Save annotated image
        annotated = result.get('annotated_image', image)
        if annotated is not None:
            # Add quality info overlay at top
            overlay = annotated.copy()
            cv2.rectangle(overlay, (0, 0), (overlay.shape[1], 35), (0, 0, 0), -1)
            cv2.putText(overlay, f"Quality: {q_label} ({q_score:.2f}) | Fields: {total_fields} | Meds: {len(medications)} | Time: {elapsed:.1f}s", 
                       (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
            
            out_path = OUTPUT_DIR / f"good_{i:02d}_{img_path.stem}_ANNOTATED.jpg"
            cv2.imwrite(str(out_path), overlay)
            print(f"  💾 Saved: {out_path.name}")
        
        # Save JSON result
        json_result = {
            'filename': img_path.name,
            'category': 'good',
            'status': status,
            'quality': quality,
            'total_fields': total_fields,
            'medications': medications,
            'doctor_info': doctor_info,
            'other_fields': other,
            'field_counts': field_counts,
            'ocr_stats': {
                'avg_confidence': round(avg_conf, 4) if confs else 0,
                'min_confidence': round(min_conf, 4) if confs else 0,
                'max_confidence': round(max_conf, 4) if confs else 0,
            },
            'time': round(elapsed, 2),
        }
        
        json_path = OUTPUT_DIR / f"good_{i:02d}_{img_path.stem}_result.json"
        with open(json_path, 'w') as f:
            json.dump(json_result, f, indent=2, default=str)
        
        all_results.append(json_result)
    
    # --- BAD images ---
    print(f"\n\n{'=' * 70}")
    print("📸 PROCESSING BAD IMAGES (expect: quality REJECT → instant return)")
    print("=" * 70)
    
    for i, img_path in enumerate(selected_bad, 1):
        print(f"\n{'─' * 60}")
        print(f"  [{i}/{len(selected_bad)}] {img_path.name}")
        print(f"{'─' * 60}")
        
        image = cv2.imread(str(img_path))
        if image is None:
            print(f"  ❌ Could not read image")
            continue
        
        h, w = image.shape[:2]
        print(f"  📐 Size: {w}x{h}")
        
        start = time.time()
        result = extractor.process_structured(image)
        elapsed = time.time() - start
        
        status = result.get('status', 'unknown')
        quality = result.get('quality_check', {})
        q_label = quality.get('quality_label', 'N/A')
        q_score = quality.get('quality_score', 0)
        q_issues = quality.get('issues', [])
        q_blur = quality.get('blur_score', 0)
        q_rec = quality.get('recommendation', '')
        
        print(f"\n  🔍 QUALITY CHECK:")
        print(f"     Label: {q_label} (score={q_score:.3f})")
        print(f"     Blur: {q_blur:.1f}")
        print(f"     Issues: {q_issues if q_issues else 'CNN score too low'}")
        print(f"     Recommendation: {q_rec}")
        
        if status == 'rejected':
            print(f"\n  ✅ CORRECTLY REJECTED (saved {elapsed:.2f}s of YOLO+OCR processing)")
        else:
            print(f"\n  ⚠️ UNEXPECTEDLY PASSED — this bad image was NOT rejected!")
        
        print(f"  ⏱ Time: {elapsed:.2f}s")
        
        # Save rejected image with overlay
        vis = image.copy()
        color = (0, 0, 255) if status == 'rejected' else (0, 165, 255)
        label_text = "REJECTED" if status == 'rejected' else "PASSED (unexpected)"
        cv2.putText(vis, f"{label_text} — Quality: {q_label} ({q_score:.2f})", 
                   (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 1.0, color, 3)
        if q_issues:
            cv2.putText(vis, f"Issues: {', '.join(q_issues)}", 
                       (20, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
        cv2.putText(vis, f"Recommendation: {q_rec}", 
                   (20, 130), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 2)
        
        out_path = OUTPUT_DIR / f"bad_{i:02d}_{img_path.stem}_{label_text.split()[0]}.jpg"
        cv2.imwrite(str(out_path), vis)
        print(f"  💾 Saved: {out_path.name}")
        
        all_results.append({
            'filename': img_path.name,
            'category': 'bad',
            'status': status,
            'quality': quality,
            'time': round(elapsed, 2),
        })
    
    # ═══════════════════════════════════════════════════════════════
    # Summary
    # ═══════════════════════════════════════════════════════════════
    
    print(f"\n\n{'=' * 70}")
    print("📊 DEMO SUMMARY")
    print(f"{'=' * 70}")
    
    good_results = [r for r in all_results if r['category'] == 'good']
    bad_results = [r for r in all_results if r['category'] == 'bad']
    
    good_passed = [r for r in good_results if r['status'] == 'completed']
    good_rejected = [r for r in good_results if r['status'] == 'rejected']
    bad_rejected = [r for r in bad_results if r['status'] == 'rejected']
    bad_passed = [r for r in bad_results if r['status'] != 'rejected']
    
    print(f"\n  Good images: {len(good_passed)}/{len(good_results)} correctly processed")
    if good_rejected:
        print(f"     ⚠️ {len(good_rejected)} good image(s) falsely rejected")
    
    print(f"  Bad images:  {len(bad_rejected)}/{len(bad_results)} correctly rejected")
    if bad_passed:
        print(f"     ⚠️ {len(bad_passed)} bad image(s) incorrectly passed")
    
    # Extraction stats for passed good images
    if good_passed:
        total_meds = sum(len(r.get('medications', [])) for r in good_passed)
        total_fields = sum(r.get('total_fields', 0) for r in good_passed)
        avg_time = sum(r.get('time', 0) for r in good_passed) / len(good_passed)
        avg_confs = [r.get('ocr_stats', {}).get('avg_confidence', 0) for r in good_passed if r.get('ocr_stats', {}).get('avg_confidence', 0) > 0]
        
        print(f"\n  📈 Extraction Stats (good images):")
        print(f"     Total fields detected: {total_fields}")
        print(f"     Total medications found: {total_meds}")
        print(f"     Avg time per image: {avg_time:.1f}s")
        if avg_confs:
            print(f"     Avg OCR confidence: {sum(avg_confs)/len(avg_confs):.1%}")
    
    if bad_rejected:
        avg_reject_time = sum(r.get('time', 0) for r in bad_rejected) / len(bad_rejected)
        print(f"\n  ⚡ Bad image avg rejection time: {avg_reject_time:.3f}s (instant!)")
    
    # Save overall summary
    summary = {
        'demo_timestamp': datetime.now().isoformat(),
        'pipeline_version': 'v6.1',
        'total_images': len(all_results),
        'good_images': {
            'total': len(good_results),
            'correctly_processed': len(good_passed),
            'falsely_rejected': len(good_rejected),
        },
        'bad_images': {
            'total': len(bad_results),
            'correctly_rejected': len(bad_rejected),
            'falsely_passed': len(bad_passed),
        },
        'results': all_results,
    }
    
    summary_path = OUTPUT_DIR / "demo_summary.json"
    with open(summary_path, 'w') as f:
        json.dump(summary, f, indent=2, default=str)
    
    print(f"\n  📁 All results saved to:")
    print(f"     {OUTPUT_DIR}")
    print(f"\n  Files:")
    for f in sorted(OUTPUT_DIR.glob("*")):
        size = f.stat().st_size
        if size > 1024 * 1024:
            size_str = f"{size / 1024 / 1024:.1f} MB"
        elif size > 1024:
            size_str = f"{size / 1024:.1f} KB"
        else:
            size_str = f"{size} B"
        print(f"     {f.name} ({size_str})")
    
    print(f"\n{'=' * 70}")
    print(f"✅ DEMO COMPLETE — Open the annotated images to see results!")
    print(f"{'=' * 70}")


if __name__ == "__main__":
    run_full_demo()
