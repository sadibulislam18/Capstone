"""
PaddleOCR Engine for Prescription Text Extraction (PaddleOCR v3 API)
=====================================================================
Wrapper around PaddleOCR v3 (3.2.x) for English prescription text recognition.

Features:
- English-only recognition (optimized for prescriptions)
- Adaptive preprocessing per field type  
- Multi-attempt recognition with different preprocessing strategies
- Confidence-based result filtering

PaddleOCR v3 API Notes:
- Use `ocr.predict(img)` not `ocr.ocr(img)`
- Results are OCRResult dicts with 'rec_texts', 'rec_scores'
- No more use_gpu, show_log, det_db_thresh etc. params

Author: MediScan Project  
Version: 6.1 (Feb 2026) - Updated for PaddleOCR v3
"""

import os
import sys
import cv2
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple, Optional

# Suppress PaddlePaddle logging noise
os.environ['GLOG_v'] = '0'
os.environ['FLAGS_log_dir'] = ''

# Disable PaddlePaddle PIR mode (causes NotImplementedError on Railway CPU)
os.environ['FLAGS_enable_pir_api'] = '0'
os.environ['FLAGS_enable_pir_in_executor'] = '0'

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


class PaddleOCREngine:
    """
    PaddleOCR v3 engine optimized for English prescription text.
    
    Features:
    - English-only recognition (cleaner output for prescriptions)
    - Adaptive preprocessing per field type
    - Multiple recognition attempts with different preprocessing
    - Confidence-based result filtering
    """
    
    # Preprocessing profiles per field type
    FIELD_PROFILES = {
        # Medicine names: typically printed, need sharp text
        'MEDICINE': {'contrast': 2.5, 'denoise': 8, 'sharpen': True, 'upscale': 2.0},
        'DOSE_STRENGTH': {'contrast': 2.5, 'denoise': 8, 'sharpen': True, 'upscale': 2.0},
        
        # Schedules: often handwritten, need more denoising
        'DOSAGE_SCHEDULE': {'contrast': 2.0, 'denoise': 12, 'sharpen': False, 'upscale': 2.5},
        'DURATION': {'contrast': 2.0, 'denoise': 12, 'sharpen': False, 'upscale': 2.5},
        
        # Doctor/hospital: printed text, standard processing
        'DOCTOR_NAME': {'contrast': 2.0, 'denoise': 10, 'sharpen': True, 'upscale': 2.0},
        'HOSPITAL': {'contrast': 2.0, 'denoise': 10, 'sharpen': True, 'upscale': 2.0},
        
        # Other fields
        'DATE': {'contrast': 2.0, 'denoise': 10, 'sharpen': True, 'upscale': 2.0},
        'TEST': {'contrast': 2.0, 'denoise': 10, 'sharpen': False, 'upscale': 2.0},
        'DIAGNOSIS': {'contrast': 2.0, 'denoise': 12, 'sharpen': False, 'upscale': 2.5},
    }
    
    DEFAULT_PROFILE = {'contrast': 2.0, 'denoise': 10, 'sharpen': False, 'upscale': 2.0}
    
    def __init__(self):
        """Initialize PaddleOCR v3 engine (English)."""
        print("=" * 60)
        print("INITIALIZING PADDLEOCR v3 ENGINE (English)")
        print("=" * 60)
        
        self.ocr = None
        self._init_paddleocr()
        
        print("=" * 60)
        print("PADDLEOCR READY")
        print("=" * 60)
    
    def _init_paddleocr(self):
        """Initialize PaddleOCR with English model (supports both v2 and v3 API)."""
        print("\nLoading PaddleOCR (English-only)...")
        self._use_v3_api = False
        
        try:
            from paddleocr import PaddleOCR
            import paddleocr
            version = getattr(paddleocr, '__version__', '0.0.0')
            major_ver = int(version.split('.')[0])
            print(f"  PaddleOCR version: {version}")
            
            if major_ver >= 3:
                # PaddleOCR v3 API
                try:
                    self.ocr = PaddleOCR(
                        lang='en',
                        use_doc_orientation_classify=False,
                        use_doc_unwarping=False,
                        use_textline_orientation=False,
                    )
                    # Quick test to see if predict() actually works
                    test_img = np.zeros((50, 150, 3), dtype=np.uint8) + 255
                    cv2.putText(test_img, "test", (5, 35), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 0), 2)
                    test_result = self.ocr.predict(test_img)
                    if test_result and len(test_result) > 0:
                        r = test_result[0]
                        texts = r.get('rec_texts', []) if hasattr(r, 'get') else []
                        if texts:
                            self._use_v3_api = True
                            print(f"  [OK] PaddleOCR v3 API verified (test returned: {texts})")
                        else:
                            print("  [WARN] v3 API returned empty, falling back to v2 API...")
                            raise RuntimeError("v3 API returned empty text")
                    else:
                        raise RuntimeError("v3 API returned no results")
                except Exception as e:
                    print(f"  [WARN] v3 predict() failed: {e}")
                    print("  Falling back to PaddleOCR v2 API...")
                    self.ocr = PaddleOCR(
                        use_angle_cls=False,
                        lang='en',
                        show_log=False,
                    )
                    self._use_v3_api = False
            else:
                # PaddleOCR v2 API
                self.ocr = PaddleOCR(
                    use_angle_cls=False,
                    lang='en',
                    show_log=False,
                )
                self._use_v3_api = False
            
            api_label = "v3 (predict)" if self._use_v3_api else "v2 (ocr)"
            print(f"[OK] PaddleOCR loaded (English model, using {api_label} API)")
            
        except Exception as e:
            print(f"[ERROR] PaddleOCR failed to load: {e}")
            raise
    
    def preprocess_for_field(self, image: np.ndarray, field_type: str = None) -> np.ndarray:
        """
        Field-specific preprocessing for better OCR.
        
        Args:
            image: Input image (BGR or grayscale)
            field_type: Type of prescription field
            
        Returns:
            Preprocessed image (BGR, upscaled)
        """
        profile = self.FIELD_PROFILES.get(field_type, self.DEFAULT_PROFILE)
        
        # Convert to grayscale for processing
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()
        
        h, w = gray.shape[:2]
        
        # 1. Upscale small crops (PaddleOCR works better with larger images)
        upscale = profile['upscale']
        if h < 50 or w < 100:
            upscale = max(upscale, 3.0)  # Extra upscaling for tiny crops
        
        if upscale > 1.0:
            gray = cv2.resize(gray, None, fx=upscale, fy=upscale, 
                            interpolation=cv2.INTER_CUBIC)
        
        # 2. Denoise
        denoise_strength = profile['denoise']
        if denoise_strength > 0:
            gray = cv2.fastNlMeansDenoising(gray, None, denoise_strength, 7, 21)
        
        # 3. Contrast enhancement (CLAHE)
        clip_limit = profile['contrast']
        clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=(8, 8))
        gray = clahe.apply(gray)
        
        # 4. Sharpening (for printed text like medicine names)
        if profile['sharpen']:
            kernel = np.array([[-1, -1, -1],
                             [-1,  9, -1],
                             [-1, -1, -1]])
            gray = cv2.filter2D(gray, -1, kernel)
        
        # 5. Normalize for very low/high contrast images
        mean_val = np.mean(gray)
        if mean_val < 80 or mean_val > 200:
            gray = cv2.normalize(gray, None, 0, 255, cv2.NORM_MINMAX)
        
        # Convert back to BGR (PaddleOCR expects color images)
        result = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
        
        return result
    
    def _run_ocr(self, image: np.ndarray) -> List[Tuple[str, float]]:
        """
        Run PaddleOCR on image and return text+confidence pairs.
        Automatically uses v3 or v2 API based on what worked during init.
        
        Args:
            image: BGR image
            
        Returns:
            List of (text, confidence) tuples
        """
        try:
            if self._use_v3_api:
                return self._run_ocr_v3(image)
            else:
                return self._run_ocr_v2(image)
        except Exception as e:
            print(f"[PaddleOCR Error] {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def _run_ocr_v3(self, image: np.ndarray) -> List[Tuple[str, float]]:
        """Run OCR using PaddleOCR v3 predict() API."""
        results = self.ocr.predict(image)
        
        if not results:
            return []
        
        text_results = []
        for page_result in results:
            # Dict-like access (OCRResult)
            if hasattr(page_result, 'get'):
                rec_texts = page_result.get('rec_texts', [])
                rec_scores = page_result.get('rec_scores', [])
                if rec_texts:
                    for text, score in zip(rec_texts, rec_scores):
                        if text and str(text).strip():
                            text_results.append((str(text).strip(), float(score)))
                    continue
            
            # Attribute access
            if hasattr(page_result, 'rec_texts') and hasattr(page_result, 'rec_scores'):
                rec_texts = page_result.rec_texts
                rec_scores = page_result.rec_scores
                if rec_texts:
                    for text, score in zip(rec_texts, rec_scores):
                        if text and str(text).strip():
                            text_results.append((str(text).strip(), float(score)))
        
        return text_results
    
    def _run_ocr_v2(self, image: np.ndarray) -> List[Tuple[str, float]]:
        """Run OCR using PaddleOCR v2 ocr() API."""
        results = self.ocr.ocr(image, cls=False)
        
        if not results:
            return []
        
        text_results = []
        for page_result in results:
            if page_result is None:
                continue
            # v2 format: [[box, (text, confidence)], ...]
            if isinstance(page_result, list):
                for line in page_result:
                    if isinstance(line, (list, tuple)) and len(line) == 2:
                        text_info = line[1]
                        if isinstance(text_info, (list, tuple)) and len(text_info) == 2:
                            text, score = text_info
                            if text and str(text).strip():
                                text_results.append((str(text).strip(), float(score)))
        
        return text_results
    
    def recognize(self, image: np.ndarray, field_type: str = None) -> Dict:
        """
        Recognize text from an image crop.
        
        Uses field-specific preprocessing and multi-attempt strategy:
        1. Field-optimized preprocessing
        2. If low confidence, try with raw upscaled image
        3. If still low, try binary thresholding
        
        Args:
            image: Input image crop (BGR or grayscale)
            field_type: Optional field type for optimized preprocessing
            
        Returns:
            Dictionary with 'text', 'confidence', 'raw_text', 'field_type'
        """
        result = {
            'text': '',
            'confidence': 0.0,
            'raw_text': '',
            'field_type': field_type,
            'engine': 'paddleocr_v3'
        }
        
        if image is None or image.size == 0:
            return result
        
        # Ensure BGR format
        if len(image.shape) == 2:
            image = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
        
        # Attempt 1: Field-specific preprocessing
        processed = self.preprocess_for_field(image, field_type)
        ocr_results = self._run_ocr(processed)
        
        if ocr_results:
            texts = [t for t, c in ocr_results]
            confidences = [c for t, c in ocr_results]
            avg_conf = sum(confidences) / len(confidences)
            
            result['text'] = ' '.join(texts)
            result['raw_text'] = ' '.join(texts)
            result['confidence'] = avg_conf
        
        # Attempt 2: If low confidence, try with raw image (just upscaled)
        if result['confidence'] < 0.6:
            h, w = image.shape[:2]
            if h < 50 or w < 100:
                upscaled = cv2.resize(image, None, fx=3.0, fy=3.0, 
                                     interpolation=cv2.INTER_CUBIC)
            else:
                upscaled = cv2.resize(image, None, fx=2.0, fy=2.0, 
                                     interpolation=cv2.INTER_CUBIC)
            
            ocr_results2 = self._run_ocr(upscaled)
            
            if ocr_results2:
                texts2 = [t for t, c in ocr_results2]
                confidences2 = [c for t, c in ocr_results2]
                avg_conf2 = sum(confidences2) / len(confidences2)
                
                if avg_conf2 > result['confidence']:
                    result['text'] = ' '.join(texts2)
                    result['raw_text'] = ' '.join(texts2)
                    result['confidence'] = avg_conf2
        
        # Attempt 3: If still low, try binary thresholding
        if result['confidence'] < 0.5:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
            gray = cv2.resize(gray, None, fx=2.5, fy=2.5, interpolation=cv2.INTER_CUBIC)
            _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            binary_bgr = cv2.cvtColor(binary, cv2.COLOR_GRAY2BGR)
            
            ocr_results3 = self._run_ocr(binary_bgr)
            
            if ocr_results3:
                texts3 = [t for t, c in ocr_results3]
                confidences3 = [c for t, c in ocr_results3]
                avg_conf3 = sum(confidences3) / len(confidences3)
                
                if avg_conf3 > result['confidence']:
                    result['text'] = ' '.join(texts3)
                    result['raw_text'] = ' '.join(texts3)
                    result['confidence'] = avg_conf3
        
        return result
    
    def recognize_batch(self, images: List[np.ndarray], 
                       field_types: List[str] = None) -> List[Dict]:
        """
        Recognize text from multiple image crops.
        
        Args:
            images: List of image crops
            field_types: Optional list of field types
            
        Returns:
            List of recognition results
        """
        if field_types is None:
            field_types = [None] * len(images)
        
        results = []
        for img, ft in zip(images, field_types):
            result = self.recognize(img, field_type=ft)
            results.append(result)
        
        return results


# ═══════════════════════════════════════════════════════════════════════════════
# Singleton instance
# ═══════════════════════════════════════════════════════════════════════════════

_engine_instance = None

def get_paddle_ocr() -> PaddleOCREngine:
    """Get or create PaddleOCR engine singleton."""
    global _engine_instance
    if _engine_instance is None:
        _engine_instance = PaddleOCREngine()
    return _engine_instance


# ═══════════════════════════════════════════════════════════════════════════════
# Test
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("TESTING PADDLEOCR v3 ENGINE")
    print("=" * 60)
    
    engine = get_paddle_ocr()
    
    # Find test images
    test_dir = project_root / "data" / "raw_images" / "good"
    test_images = list(test_dir.glob("*.jpg"))[:3]
    
    if test_images:
        for img_path in test_images:
            print(f"\nTesting: {img_path.name}")
            img = cv2.imread(str(img_path))
            
            if img is not None:
                result = engine.recognize(img, field_type='MEDICINE')
                text = result['text']
                print(f"  Text: {text[:80]}..." if len(text) > 80 else f"  Text: {text}")
                print(f"  Confidence: {result['confidence']:.2%}")
    else:
        print("No test images found!")
    
    print("\n[DONE] PaddleOCR v3 engine test complete!")
