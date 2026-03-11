"""
Image quality classifier model based on ResNet18.

Binary classification: good (class 1) vs bad (class 0) prescription images.
"""

import torch
import torch.nn as nn
from torchvision import models
from torchvision.models import ResNet18_Weights


def get_quality_classifier(pretrained: bool = True, num_classes: int = 2) -> nn.Module:
    """
    Create ResNet18-based binary classifier for image quality.
    
    Args:
        pretrained: Whether to use pretrained ImageNet weights (default: True)
        num_classes: Number of output classes (default: 2 for bad/good)
    
    Returns:
        ResNet18 model with modified final layer
    
    Class mapping (consistent with dataloaders):
        - bad  → 0
        - good → 1
    """
    # Load pretrained ResNet18
    if pretrained:
        weights = ResNet18_Weights.IMAGENET1K_V1
        model = models.resnet18(weights=weights)
    else:
        model = models.resnet18(weights=None)
    
    # Get the number of input features for the final fully connected layer
    num_features = model.fc.in_features
    
    # Replace the final fully connected layer with dropout + FC
    model.fc = nn.Sequential(
        nn.Dropout(p=0.3),
        nn.Linear(num_features, num_classes)
    )
    
    return model


class ImageQualityClassifier(nn.Module):
    """
    Wrapper class for image quality classification.
    
    Attributes:
        model: ResNet18 backbone
        num_classes: Number of output classes (2)
        class_names: List of class names ['bad', 'good']
    """
    
    def __init__(self, pretrained: bool = True):
        super().__init__()
        self.model = get_quality_classifier(pretrained=pretrained)
        self.num_classes = 2
        self.class_names = ['bad', 'good']
    
    def forward(self, x):
        """Forward pass."""
        return self.model(x)
    
    def predict(self, x):
        """
        Predict class for input tensor.
        
        Args:
            x: Input tensor of shape (batch_size, 3, 224, 224)
        
        Returns:
            Predicted class indices (0 for bad, 1 for good)
        """
        self.eval()
        with torch.no_grad():
            logits = self.forward(x)
            predictions = torch.argmax(logits, dim=1)
        return predictions
    
    def predict_proba(self, x):
        """
        Predict class probabilities for input tensor.
        
        Args:
            x: Input tensor of shape (batch_size, 3, 224, 224)
        
        Returns:
            Class probabilities of shape (batch_size, 2)
        """
        self.eval()
        with torch.no_grad():
            logits = self.forward(x)
            probabilities = torch.softmax(logits, dim=1)
        return probabilities


if __name__ == "__main__":
    """Test the model."""
    print("=" * 70)
    print("TESTING IMAGE QUALITY CLASSIFIER MODEL")
    print("=" * 70)
    
    # Create model
    print("\n📦 Creating ResNet18-based classifier...")
    model = ImageQualityClassifier(pretrained=True)
    print(f"✓ Model created")
    print(f"  - Backbone: ResNet18 (pretrained on ImageNet)")
    print(f"  - Output classes: {model.num_classes}")
    print(f"  - Class names: {model.class_names}")
    
    # Count parameters
    total_params = sum(p.numel() for p in model.parameters())
    trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    print(f"  - Total parameters: {total_params:,}")
    print(f"  - Trainable parameters: {trainable_params:,}")
    
    # Test forward pass
    print("\n🧪 Testing forward pass...")
    dummy_input = torch.randn(4, 3, 224, 224)  # Batch of 4 images
    print(f"  - Input shape: {dummy_input.shape}")
    
    output = model(dummy_input)
    print(f"  - Output shape: {output.shape}")
    print(f"  - Output (logits): {output}")
    
    # Test prediction
    print("\n🎯 Testing prediction...")
    predictions = model.predict(dummy_input)
    print(f"  - Predicted classes: {predictions}")
    print(f"  - Predicted labels: {[model.class_names[p] for p in predictions]}")
    
    # Test probability prediction
    print("\n📊 Testing probability prediction...")
    probabilities = model.predict_proba(dummy_input)
    print(f"  - Probabilities shape: {probabilities.shape}")
    print(f"  - Probabilities:\n{probabilities}")
    
    print("\n" + "=" * 70)
    print("✅ MODEL WORKING CORRECTLY")
    print("=" * 70)
