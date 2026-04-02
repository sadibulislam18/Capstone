"""
Image Quality Checker - Hybrid CNN + Traditional CV
====================================================
Combines ResNet18 deep learning with Laplacian variance (blur detection)
and brightness/contrast analysis for robust prescription image quality assessment.

Usage:
    from src.preprocessing.quality_checker import get_quality_checker
    
    checker = get_quality_checker()
    result = checker.check(image)
    # result = {
    #     'is_acceptable': True/False,
    #     'quality_label': 'good'/'bad',
    #     'quality_score': 0.85,        # 0-1 confidence
    #     'blur_score': 120.5,           # Laplacian variance (higher = sharper)
    #     'brightness': 0.45,            # Mean brightness (0-1)
    #     'contrast': 0.35,              # Std of brightness (0-1)
    #     'issues': ['too_blurry'],      # List of detected issues
    #     'recommendation': '...',       # User-facing message
    # }

Author: MediScan Project
Version: 1.0 (Feb 2026)
"""

import cv2
import numpy as np
import torch
from torchvision import transforms
from pathlib import Path
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)

# Project root
PROJECT_ROOT = Path(__file__).parent.parent.parent


class ImageQualityChecker:
    """
    Hybrid image quality checker combining:
    1. ResNet18 CNN classifier (learned features)
    2. Laplacian variance (blur detection)
    3. Brightness/contrast analysis
    
    The CNN provides the primary quality score, while traditional CV
    metrics catch obvious issues the CNN might miss on edge cases.
    """
    
    # Thresholds for traditional CV checks
    BLUR_THRESHOLD = 50.0       # Laplacian variance below this = blurry
    BRIGHTNESS_LOW = 0.15       # Too dark
    BRIGHTNESS_HIGH = 0.85      # Too bright/washed out
    CONTRAST_LOW = 0.05         # Too low contrast
    
    # CNN confidence threshold for "good" classification
    CNN_THRESHOLD = 0.55        # Probability of "good" class
    
    def __init__(self, model_path: str = None, device: str = None):
        """
        Initialize the quality checker.
        
        Args:
            model_path: Path to trained ResNet18 model weights
            device: 'mps', 'cuda', or 'cpu' (auto-detected if None)
        """
        if device is None:
            if torch.backends.mps.is_available():
                self.device = torch.device('mps')
            elif torch.cuda.is_available():
                self.device = torch.device('cuda')
            else:
                self.device = torch.device('cpu')
        else:
            self.device = torch.device(device)
        
        if model_path is None:
            model_path = PROJECT_ROOT / "models" / "image_quality_classifier.pt"
        self.model_path = Path(model_path)
        
        self.model = None
        self.transform = transforms.Compose([
            transforms.ToPILImage(),
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406],
                               std=[0.229, 0.224, 0.225]),
        ])
        
        self._load_model()
    
    def _load_model(self):
        """Load the trained CNN model."""
        if not self.model_path.exists():
            logger.warning(f"Quality model not found at {self.model_path}")
            logger.warning("Will use traditional CV checks only (no CNN)")
            return
        
        try:
            from src.models.image_quality_classifier import ImageQualityClassifier
            
            self.model = ImageQualityClassifier(pretrained=False)
            checkpoint = torch.load(str(self.model_path), map_location=self.device, weights_only=False)
            self.model.load_state_dict(checkpoint['model_state_dict'])
            self.model = self.model.to(self.device)
            self.model.eval()
            
            val_acc = checkpoint.get('val_acc', 0)
            epoch = checkpoint.get('epoch', 0)
            logger.info(f"Quality classifier loaded (epoch {epoch}, val_acc={val_acc:.1f}%)")
            
        except Exception as e:
            logger.error(f"Failed to load quality model: {e}")
            self.model = None
    
    def _compute_blur_score(self, image: np.ndarray) -> float:
        """
        Compute Laplacian variance as a blur metric.
        Higher values = sharper image, lower = blurrier.
        """
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
        laplacian = cv2.Laplacian(gray, cv2.CV_64F)
        return float(laplacian.var())
    
    def _compute_brightness(self, image: np.ndarray) -> float:
        """Compute mean brightness (0-1 scale)."""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
        return float(gray.mean() / 255.0)
    
    def _compute_contrast(self, image: np.ndarray) -> float:
        """Compute contrast as std of pixel values (0-1 scale)."""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
        return float(gray.std() / 255.0)
    
    def _cnn_predict(self, image: np.ndarray) -> Dict:
        """
        Run CNN prediction on the image.
        
        Returns:
            Dict with 'label', 'confidence', 'good_prob', 'bad_prob'
        """
        if self.model is None:
            return None
        
        try:
            # Convert BGR to RGB for the model
            rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            tensor = self.transform(rgb).unsqueeze(0).to(self.device)
            
            with torch.no_grad():
                logits = self.model(tensor)
                probs = torch.softmax(logits, dim=1)[0]
            
            bad_prob = float(probs[0])
            good_prob = float(probs[1])
            label = 'good' if good_prob > bad_prob else 'bad'
            confidence = max(good_prob, bad_prob)
            
            return {
                'label': label,
                'confidence': confidence,
                'good_prob': good_prob,
                'bad_prob': bad_prob,
            }
        except Exception as e:
            logger.error(f"CNN prediction failed: {e}")
            return None
    
    def check(self, image, threshold: float = None) -> Dict:
        """
        Check image quality using hybrid CNN + traditional CV approach.
        
        Args:
            image: BGR numpy array or file path
            threshold: Override CNN threshold (default: self.CNN_THRESHOLD)
        
        Returns:
            Dict with quality assessment results
        """
        # Load image if path
        if isinstance(image, (str, Path)):
            image = cv2.imread(str(image))
            if image is None:
                return {
                    'is_acceptable': False,
                    'quality_label': 'bad',
                    'quality_score': 0.0,
                    'issues': ['unreadable_file'],
                    'recommendation': 'Could not read the image file. Please try again.',
                }
        
        if threshold is None:
            threshold = self.CNN_THRESHOLD
        
        # ── Traditional CV metrics ──
        blur_score = self._compute_blur_score(image)
        brightness = self._compute_brightness(image)
        contrast = self._compute_contrast(image)
        
        # Detect issues
        issues = []
        if blur_score < self.BLUR_THRESHOLD:
            issues.append('too_blurry')
        if brightness < self.BRIGHTNESS_LOW:
            issues.append('too_dark')
        if brightness > self.BRIGHTNESS_HIGH:
            issues.append('too_bright')
        if contrast < self.CONTRAST_LOW:
            issues.append('low_contrast')
        
        # ── CNN prediction ──
        cnn_result = self._cnn_predict(image)
        
        # ── Combine results ──
        if cnn_result is not None:
            good_prob = cnn_result['good_prob']
            cnn_label = cnn_result['label']
            cnn_confidence = cnn_result['confidence']
            
            # Primary decision: CNN
            # Override: if traditional CV finds severe issues, downgrade
            if good_prob >= threshold and len(issues) == 0:
                is_acceptable = True
                quality_label = 'good'
                quality_score = good_prob
            elif good_prob >= threshold and len(issues) > 0:
                # CNN says good but CV found issues — trust CNN but flag warnings
                is_acceptable = True
                quality_label = 'good'
                quality_score = good_prob * 0.9  # Slight penalty
            elif good_prob < threshold and len(issues) > 0:
                # Both CNN and CV agree it's bad
                is_acceptable = False
                quality_label = 'bad'
                quality_score = good_prob
            else:
                # CNN says bad but no CV issues — trust CNN
                is_acceptable = False
                quality_label = 'bad'
                quality_score = good_prob
        else:
            # No CNN — fall back to traditional CV only
            is_acceptable = len(issues) == 0
            quality_label = 'good' if is_acceptable else 'bad'
            # Heuristic score from CV metrics
            blur_norm = min(1.0, blur_score / 200.0)
            bright_ok = 1.0 if self.BRIGHTNESS_LOW <= brightness <= self.BRIGHTNESS_HIGH else 0.5
            contrast_ok = 1.0 if contrast >= self.CONTRAST_LOW else 0.5
            quality_score = blur_norm * 0.6 + bright_ok * 0.2 + contrast_ok * 0.2
            cnn_label = None
            cnn_confidence = 0.0
        
        # Build recommendation
        recommendation = self._build_recommendation(is_acceptable, issues)
        
        return {
            'is_acceptable': is_acceptable,
            'quality_label': quality_label,
            'quality_score': round(quality_score, 4),
            'blur_score': round(blur_score, 2),
            'brightness': round(brightness, 4),
            'contrast': round(contrast, 4),
            'issues': issues,
            'recommendation': recommendation,
            'cnn_prediction': cnn_result,
        }
    
    def _build_recommendation(self, is_acceptable: bool, issues: list) -> str:
        """Build user-facing recommendation message."""
        if is_acceptable and not issues:
            return "Image quality is good. Processing..."
        
        if is_acceptable and issues:
            msgs = []
            if 'too_blurry' in issues:
                msgs.append("slightly blurry")
            if 'too_dark' in issues:
                msgs.append("a bit dark")
            if 'too_bright' in issues:
                msgs.append("a bit bright")
            return f"Image is acceptable but {', '.join(msgs)}. Results may vary."
        
        # Not acceptable
        msgs = []
        if 'too_blurry' in issues:
            msgs.append("The image is too blurry. Please hold your camera steady.")
        if 'too_dark' in issues:
            msgs.append("The image is too dark. Please ensure good lighting.")
        if 'too_bright' in issues:
            msgs.append("The image is overexposed. Avoid direct light on the prescription.")
        if 'low_contrast' in issues:
            msgs.append("The image has very low contrast.")
        
        if not msgs:
            msgs.append("The image quality is poor. Please retake the photo.")
        
        return " ".join(msgs)


# ═══════════════════════════════════════════════════════════════════════
# Singleton
# ═══════════════════════════════════════════════════════════════════════

_checker_instance = None

def get_quality_checker(model_path: str = None) -> ImageQualityChecker:
    """Get or create quality checker singleton."""
    global _checker_instance
    if _checker_instance is None:
        _checker_instance = ImageQualityChecker(model_path=model_path)
    return _checker_instance
