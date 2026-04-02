"""
Prescription Extractor - V6 Pipeline
=====================================
Combines YOLOv8 detection (9 classes) with PaddleOCR for English prescription digitization.
Includes image quality pre-check using hybrid CNN + traditional CV.

Components:
- Image Quality Checker (ResNet18 + Laplacian blur detection)
- YOLOv8s for field detection (v6 - 9 classes, English focus)
- PaddleOCR for text recognition (English-only, high accuracy)

Classes (9): MEDICINE, DOSE_STRENGTH, DOSAGE_SCHEDULE, DURATION,
             DOCTOR_NAME, HOSPITAL, DATE, TEST, DIAGNOSIS

Author: MediScan Project
Version: 6.1 (Feb 2026)
"""

import os
import sys
import cv2
import json
import numpy as np
import torch
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, asdict
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


@dataclass
class DetectedField:
    """Represents a detected field in the prescription"""
    field_type: str
    bbox: Tuple[int, int, int, int]  # x1, y1, x2, y2
    confidence: float
    text: str = ""
    ocr_confidence: float = 0.0
    matched_text: str = ""        # After fuzzy matching (for MEDICINE)
    match_score: float = 0.0      # Fuzzy match similarity


class PrescriptionExtractorV6:
    """
    V6 Prescription Extraction Pipeline.
    
    Uses:
    - YOLOv8s (9 classes) for field detection
    - PaddleOCR (English) for text recognition
    - Smart Medicine Matcher for fuzzy correction
    """
    
    # V6 class names (9 classes - English focus)
    CLASS_NAMES = [
        'MEDICINE',          # 0
        'DOSE_STRENGTH',     # 1
        'DOSAGE_SCHEDULE',   # 2
        'DURATION',          # 3
        'DOCTOR_NAME',       # 4
        'HOSPITAL',          # 5
        'DATE',              # 6
        'TEST',              # 7
        'DIAGNOSIS',         # 8
    ]
    
    def __init__(self, yolo_path: str = None, use_gpu: bool = True,
                 use_medicine_matcher: bool = False, use_quality_check: bool = True):
        """
        Initialize the V6 prescription extractor.
        
        Args:
            yolo_path: Path to YOLO v6 model weights
            use_gpu: Whether to use GPU
            use_medicine_matcher: Whether to use fuzzy medicine matching (disabled by default)
            use_quality_check: Whether to run image quality pre-check (default: True)
        """
        print("=" * 60)
        print("PRESCRIPTION EXTRACTOR V6 (9-Class, PaddleOCR)")
        print("=" * 60)
        
        if yolo_path is None:
            v6_path = project_root / "experiments" / "v6_9class_english" / "weights" / "best.pt"
            v4_path = project_root / "experiments" / "v4_updated_augmentation" / "best.pt"
            if v6_path.exists():
                yolo_path = v6_path
                print(f"  Using V6 model")
            elif v4_path.exists():
                yolo_path = v4_path
                print(f"  [!] V6 not ready, using V4 fallback")
            else:
                raise FileNotFoundError("No YOLO model found! Train v6 first.")
        
        self.yolo_path = Path(yolo_path)
        self.use_medicine_matcher = use_medicine_matcher
        self.use_quality_check = use_quality_check
        self.yolo_model = None
        self.ocr_engine = None
        self.medicine_matcher = None
        self.quality_checker = None

        # Device selection: MPS (Apple Silicon) → CUDA → CPU
        if torch.backends.mps.is_available():
            self.device = 'mps'
        elif torch.cuda.is_available():
            self.device = 'cuda'
        else:
            self.device = 'cpu'
        
        if use_quality_check:
            self._init_quality_checker()
        self._init_yolo()
        self._init_ocr(use_gpu)
        if use_medicine_matcher:
            self._init_matcher()
        
        print("=" * 60)
        print("EXTRACTOR V6 READY")
        print("=" * 60)
    
    def _init_quality_checker(self):
        """Initialize image quality checker (CNN + traditional CV)."""
        print(f"\n[0] Loading Quality Checker...")
        try:
            from src.preprocessing.quality_checker import get_quality_checker
            self.quality_checker = get_quality_checker()
            print("    [OK] Quality checker ready (ResNet18 + Laplacian)")
        except Exception as e:
            print(f"    [WARN] Quality checker failed: {e}")
            self.quality_checker = None
    
    def _init_yolo(self):
        """Initialize YOLO detection model"""
        print(f"\n[1] Loading YOLO: {self.yolo_path.name}")
        from ultralytics import YOLO
        self.yolo_model = YOLO(str(self.yolo_path))
        self.yolo_model.to(self.device)
        print(f"    [OK] YOLO loaded ({len(self.CLASS_NAMES)} classes) → device: {self.device}")
    
    def _init_ocr(self, use_gpu: bool):
        """Initialize PaddleOCR v3 engine"""
        print("\n[2] Loading OCR engine...")
        try:
            from src.ocr.paddle_ocr_engine import get_paddle_ocr
            self.ocr_engine = get_paddle_ocr()
            print("    [OK] PaddleOCR v3 ready (English)")
        except Exception as e:
            print(f"    [ERROR] PaddleOCR failed: {e}")
            raise
    
    def _init_matcher(self):
        """Initialize medicine name matcher"""
        print("\n[3] Loading Medicine Matcher...")
        try:
            from src.ocr.smart_medicine_matcher import get_matcher
            self.medicine_matcher = get_matcher()
            print(f"    [OK] {len(self.medicine_matcher.medicines):,} medicines loaded")
        except Exception as e:
            print(f"    [WARN] Matcher failed: {e}")
            self.medicine_matcher = None
    
    def detect_fields(self, image: np.ndarray, conf_threshold: float = 0.25) -> List[DetectedField]:
        """Detect prescription fields using YOLO v6."""
        results = self.yolo_model(image, conf=conf_threshold, verbose=False, device=self.device)
        detected = []
        for result in results:
            for box in result.boxes:
                x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
                conf = float(box.conf[0])
                cls_id = int(box.cls[0])
                field_type = self.CLASS_NAMES[cls_id] if cls_id < len(self.CLASS_NAMES) else f"UNKNOWN_{cls_id}"
                detected.append(DetectedField(
                    field_type=field_type, bbox=(x1, y1, x2, y2), confidence=conf
                ))
        detected.sort(key=lambda f: (f.bbox[1], f.bbox[0]))
        return detected
    
    def extract_text(self, image: np.ndarray, fields: List[DetectedField]) -> List[DetectedField]:
        """Extract text from detected fields using PaddleOCR."""
        h, w = image.shape[:2]
        for field in fields:
            x1, y1, x2, y2 = field.bbox
            box_h, box_w = y2 - y1, x2 - x1
            pad_x, pad_y = max(5, int(box_w * 0.02)), max(5, int(box_h * 0.02))
            x1, y1 = max(0, x1 - pad_x), max(0, y1 - pad_y)
            x2, y2 = min(w, x2 + pad_x), min(h, y2 + pad_y)
            
            crop = image[y1:y2, x1:x2]
            if crop.size == 0:
                continue
            
            ocr_result = self.ocr_engine.recognize(crop, field_type=field.field_type)
            field.text = ocr_result.get('text', '')
            field.ocr_confidence = ocr_result.get('confidence', 0.0)
            
            if field.field_type == 'MEDICINE' and field.text and self.medicine_matcher:
                match = self.medicine_matcher.match(field.text, min_confidence='low')
                field.matched_text = match.matched_name
                field.match_score = match.similarity_score
        return fields
    
    def check_quality(self, image) -> Dict:
        """
        Check image quality before processing.
        
        Args:
            image: BGR numpy array or file path
        
        Returns:
            Quality assessment dict with is_acceptable, quality_score, issues, etc.
        """
        if isinstance(image, (str, Path)):
            image = cv2.imread(str(image))
            if image is None:
                return {
                    'is_acceptable': False,
                    'quality_label': 'bad',
                    'quality_score': 0.0,
                    'issues': ['unreadable_file'],
                    'recommendation': 'Could not read the image file.',
                }
        
        if self.quality_checker is not None:
            return self.quality_checker.check(image)
        
        # Fallback: no quality checker loaded
        return {
            'is_acceptable': True,
            'quality_label': 'unknown',
            'quality_score': 0.5,
            'issues': [],
            'recommendation': 'Quality check unavailable.',
        }
    
    def process(self, image, conf_threshold: float = 0.25, skip_quality_check: bool = False) -> Dict:
        """
        Full extraction pipeline: quality check + detect + OCR + matching.
        
        Args:
            image: BGR numpy array or file path
            conf_threshold: YOLO confidence threshold
            skip_quality_check: Skip quality pre-check (default: False)
        """
        if isinstance(image, (str, Path)):
            image = cv2.imread(str(image))
            if image is None:
                return {'error': 'Could not load image', 'extractions': [], 'summary': {}}
        
        # ── Quality Check ──
        quality_result = None
        if self.use_quality_check and not skip_quality_check:
            quality_result = self.check_quality(image)
            
            if not quality_result['is_acceptable']:
                # Return early with quality warning — don't waste time on YOLO+OCR
                return {
                    'extractions': [],
                    'summary': {},
                    'annotated_image': image,
                    'timestamp': datetime.now().isoformat(),
                    'model_version': 'v6_9class_english',
                    'ocr_engine': 'paddleocr',
                    'total_fields': 0,
                    'quality_check': quality_result,
                    'status': 'rejected',
                    'message': quality_result['recommendation'],
                }
        
        # ── Detection + OCR ──
        fields = self.detect_fields(image, conf_threshold)
        fields = self.extract_text(image, fields)
        annotated = self.visualize(image, fields)
        
        result = {
            'extractions': [asdict(f) for f in fields],
            'summary': self._create_summary(fields),
            'annotated_image': annotated,
            'timestamp': datetime.now().isoformat(),
            'model_version': 'v6_9class_english',
            'ocr_engine': 'paddleocr',
            'total_fields': len(fields),
            'status': 'completed',
        }
        
        if quality_result is not None:
            result['quality_check'] = quality_result
        
        return result
    
    def _create_summary(self, fields: List[DetectedField]) -> Dict:
        """Create summary grouped by field type."""
        summary = {}
        for field in fields:
            if not field.text:
                continue
            if field.field_type not in summary:
                summary[field.field_type] = []
            entry = {'text': field.text, 'confidence': round(field.ocr_confidence, 2)}
            summary[field.field_type].append(entry)
        return summary
    
    def visualize(self, image: np.ndarray, fields: List[DetectedField], 
                  output_path: str = None) -> np.ndarray:
        """Draw detection results on image."""
        vis = image.copy()
        colors = {
            'MEDICINE': (0, 255, 0), 'DOSE_STRENGTH': (0, 200, 255),
            'DOSAGE_SCHEDULE': (255, 100, 0), 'DURATION': (255, 0, 255),
            'DOCTOR_NAME': (0, 255, 255), 'HOSPITAL': (255, 255, 0),
            'DATE': (200, 200, 200), 'TEST': (100, 255, 100),
            'DIAGNOSIS': (100, 100, 255),
        }
        for field in fields:
            x1, y1, x2, y2 = field.bbox
            color = colors.get(field.field_type, (128, 128, 128))
            cv2.rectangle(vis, (x1, y1), (x2, y2), color, 2)
            display = field.text
            if len(display) > 25:
                display = display[:22] + "..."
            label = f"{field.field_type}: {display}"
            (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.45, 1)
            cv2.rectangle(vis, (x1, y1 - th - 6), (x1 + tw + 4, y1), color, -1)
            cv2.putText(vis, label, (x1 + 2, y1 - 4), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 0, 0), 1)
        if output_path:
            cv2.imwrite(output_path, vis)
        return vis


# Backward-compatible alias
PrescriptionExtractor = PrescriptionExtractorV6

# Singleton
_extractor_instance = None

def get_extractor(use_gpu: bool = True) -> PrescriptionExtractorV6:
    """Get or create extractor singleton."""
    global _extractor_instance
    if _extractor_instance is None:
        _extractor_instance = PrescriptionExtractorV6(use_gpu=use_gpu)
    return _extractor_instance

def extract_prescription(image_path: str, use_gpu: bool = True) -> Dict:
    """Quick extraction from image file."""
    extractor = get_extractor(use_gpu=use_gpu)
    return extractor.process(image_path)
