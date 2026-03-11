"""
Structured Prescription Extractor V6
=====================================
Groups related fields (medicine + dose + schedule + duration)
using spatial proximity (Y-coordinate grouping).

Uses PaddleOCR (English) + YOLOv8 (9 classes).
Produces structured JSON for the MediScan Kotlin app.

Classes (9): MEDICINE, DOSE_STRENGTH, DOSAGE_SCHEDULE, DURATION,
             DOCTOR_NAME, HOSPITAL, DATE, TEST, DIAGNOSIS

Author: MediScan Project
Version: 6.0 (Feb 2026)
"""

import cv2
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
import sys

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.pipeline.extractor import PrescriptionExtractorV6, DetectedField


@dataclass
class MedicationEntry:
    """A complete medication entry with all related fields grouped together."""
    medicine: str = ""
    medicine_confidence: float = 0.0
    dose_strength: str = ""
    dose_confidence: float = 0.0
    schedule: str = ""
    schedule_confidence: float = 0.0
    duration: str = ""
    duration_confidence: float = 0.0
    y_position: int = 0  # For sorting (top to bottom)
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON/app output."""
        return {
            "medicine": self.medicine if self.medicine else None,
            "dose_strength": self.dose_strength if self.dose_strength else None,
            "schedule": self.schedule if self.schedule else None,
            "duration": self.duration if self.duration else None,
            "confidence": {
                "medicine": round(self.medicine_confidence, 2) if self.medicine else None,
                "dose_strength": round(self.dose_confidence, 2) if self.dose_strength else None,
                "schedule": round(self.schedule_confidence, 2) if self.schedule else None,
                "duration": round(self.duration_confidence, 2) if self.duration else None,
            }
        }


class StructuredPrescriptionExtractor(PrescriptionExtractorV6):
    """
    Extended V6 extractor that groups medications with their doses
    using spatial proximity (Y-coordinate grouping).
    
    This is the primary class for the MediScan app integration.
    """
    
    # Y-tolerance for considering fields on the "same row"
    ROW_TOLERANCE_PERCENT = 0.03  # 3% of image height
    
    def __init__(self, yolo_path: str = None, use_gpu: bool = True):
        """Initialize the structured extractor."""
        super().__init__(yolo_path=yolo_path, use_gpu=use_gpu)
        print("[+] Structured grouping enabled (for app integration)")
    
    def _get_y_center(self, bbox: Tuple[int, int, int, int]) -> int:
        """Get the vertical center of a bounding box."""
        return (bbox[1] + bbox[3]) // 2
    
    def _fields_on_same_row(self, field1: DetectedField, field2: DetectedField, 
                           image_height: int) -> bool:
        """Check if two fields are on the same row (similar Y position)."""
        tolerance = int(image_height * self.ROW_TOLERANCE_PERCENT)
        y1 = self._get_y_center(field1.bbox)
        y2 = self._get_y_center(field2.bbox)
        return abs(y1 - y2) <= tolerance
    
    def _group_medications(self, fields: List[DetectedField], 
                          image_height: int) -> List[MedicationEntry]:
        """
        Group fields into medication entries based on spatial proximity.
        
        Algorithm:
        1. Find all MEDICINE fields (anchors)
        2. For each medicine, find related fields on the same row
        3. Create MedicationEntry with grouped data
        """
        medications = []
        
        medicine_fields = [f for f in fields if f.field_type == 'MEDICINE']
        dose_fields = [f for f in fields if f.field_type == 'DOSE_STRENGTH']
        schedule_fields = [f for f in fields if f.field_type == 'DOSAGE_SCHEDULE']
        duration_fields = [f for f in fields if f.field_type == 'DURATION']
        
        used_doses = set()
        used_schedules = set()
        used_durations = set()
        
        for med_field in medicine_fields:
            entry = MedicationEntry(
                medicine=med_field.text,
                medicine_confidence=med_field.ocr_confidence,
                y_position=self._get_y_center(med_field.bbox)
            )
            
            for i, dose in enumerate(dose_fields):
                if i not in used_doses and self._fields_on_same_row(med_field, dose, image_height):
                    entry.dose_strength = dose.text
                    entry.dose_confidence = dose.ocr_confidence
                    used_doses.add(i)
                    break
            
            for i, sched in enumerate(schedule_fields):
                if i not in used_schedules and self._fields_on_same_row(med_field, sched, image_height):
                    entry.schedule = sched.text
                    entry.schedule_confidence = sched.ocr_confidence
                    used_schedules.add(i)
                    break
            
            for i, dur in enumerate(duration_fields):
                if i not in used_durations and self._fields_on_same_row(med_field, dur, image_height):
                    entry.duration = dur.text
                    entry.duration_confidence = dur.ocr_confidence
                    used_durations.add(i)
                    break
            
            medications.append(entry)
        
        medications.sort(key=lambda m: m.y_position)
        return medications
    
    def _extract_prescription_info(self, fields: List[DetectedField]) -> Dict:
        """Extract non-medication prescription information."""
        info = {}
        
        for field in fields:
            if field.field_type == 'DATE' and field.text:
                info['date'] = field.text
            elif field.field_type == 'DIAGNOSIS' and field.text:
                if 'diagnoses' not in info:
                    info['diagnoses'] = []
                info['diagnoses'].append(field.text)
            elif field.field_type == 'TEST' and field.text:
                if 'tests' not in info:
                    info['tests'] = []
                info['tests'].append(field.text)
        
        return info if info else None
    
    def _extract_doctor_info(self, fields: List[DetectedField]) -> Dict:
        """Extract doctor-related information."""
        info = {}
        
        for field in fields:
            if field.field_type == 'DOCTOR_NAME' and field.text:
                info['name'] = field.text
            elif field.field_type == 'HOSPITAL' and field.text:
                info['hospital'] = field.text
        
        return info if info else None
    
    def process_structured(self, image, conf_threshold: float = 0.25, 
                           skip_quality_check: bool = False) -> Dict:
        """
        Full extraction with structured medication grouping.
        
        This is the main method for Kotlin app integration.
        
        Args:
            image: Input image (BGR numpy array) or path to image file
            conf_threshold: Detection confidence threshold
            skip_quality_check: Skip quality pre-check
            
        Returns:
            Structured dictionary with grouped medications
        """
        if isinstance(image, (str, Path)):
            image = cv2.imread(str(image))
            if image is None:
                return {'error': 'Could not load image'}
        
        image_height = image.shape[0]
        
        # ── Quality Check ──
        quality_result = None
        if self.use_quality_check and not skip_quality_check:
            quality_result = self.check_quality(image)
            # Quality result is included in the response below,
            # but we never block extraction regardless of score.
        
        # ── Detection + OCR ──
        fields = self.detect_fields(image, conf_threshold)
        fields = self.extract_text(image, fields)
        medications = self._group_medications(fields, image_height)
        
        prescription_info = self._extract_prescription_info(fields)
        doctor_info = self._extract_doctor_info(fields)
        annotated = self.visualize(image, fields)
        
        result = {
            'prescription_id': datetime.now().strftime('%Y%m%d_%H%M%S'),
            'extraction_timestamp': datetime.now().isoformat(),
            'model_version': 'v6_9class_english',
            'ocr_engine': 'paddleocr',
            
            # Main output for app - grouped medications
            'medications': [m.to_dict() for m in medications],
            'medication_count': len(medications),
            
            # Prescription info
            'prescription_info': prescription_info,
            
            # Doctor info  
            'doctor': doctor_info,
            
            # Stats
            'stats': {
                'total_fields_detected': len(fields),
                'medicines_found': len([f for f in fields if f.field_type == 'MEDICINE']),
                'doses_found': len([f for f in fields if f.field_type == 'DOSE_STRENGTH']),
                'schedules_found': len([f for f in fields if f.field_type == 'DOSAGE_SCHEDULE']),
                'durations_found': len([f for f in fields if f.field_type == 'DURATION']),
            },
            
            'raw_extractions': [asdict(f) for f in fields],
            'annotated_image': annotated,
            'status': 'completed',
        }
        
        if quality_result is not None:
            result['quality_check'] = quality_result
        
        return result


# Singleton
_structured_instance = None

def get_structured_extractor(use_gpu: bool = True) -> StructuredPrescriptionExtractor:
    """Get or create structured extractor singleton."""
    global _structured_instance
    if _structured_instance is None:
        _structured_instance = StructuredPrescriptionExtractor(use_gpu=use_gpu)
    return _structured_instance

def extract_prescription_structured(image_path: str, use_gpu: bool = True) -> Dict:
    """Quick structured extraction from image file (for app integration)."""
    extractor = get_structured_extractor(use_gpu=use_gpu)
    return extractor.process_structured(image_path)
