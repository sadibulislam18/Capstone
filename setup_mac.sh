#!/bin/bash
# ============================================================
#  MediScan AI Server — Mac Setup (Run ONCE)
#  Usage: bash setup_mac.sh
# ============================================================

echo ""
echo "╔══════════════════════════════════════════════════════╗"
echo "║        MediScan AI Server — Mac Setup                ║"
echo "╚══════════════════════════════════════════════════════╝"
echo ""

# Check Python
echo "► Checking Python..."
python3 --version 2>/dev/null || {
    echo "✗ Python not found! Install from https://www.python.org/downloads/"
    exit 1
}
echo "  ✓ Python found"

# Create virtual environment
echo ""
echo "► Creating virtual environment..."
if [ -d "venv" ]; then
    echo "  Already exists, skipping..."
else
    python3 -m venv venv
    echo "  ✓ Created (venv/)"
fi

# Activate
source venv/bin/activate
pip install --upgrade pip --quiet

# Install packages
echo ""
echo "► Installing packages (5-10 minutes)..."

echo "  [1/5] PyTorch (CPU)..."
pip install torch torchvision torchaudio --quiet

echo "  [2/5] Ultralytics (YOLO)..."
pip install ultralytics --quiet

echo "  [3/5] PaddlePaddle..."
pip install paddlepaddle --quiet 2>/dev/null || \
pip install paddlepaddle -i https://mirror.baidu.com/pypi/simple --quiet

echo "  [4/5] PaddleOCR..."
pip install paddleocr --quiet

echo "  [5/5] Remaining packages..."
pip install -r requirements_mac.txt --quiet

echo "  ✓ All packages installed"

# Create directories
mkdir -p data/uploads data/results

# Verify model files
echo ""
echo "► Checking model files..."

if [ -f "experiments/v6_9class_english/weights/best.pt" ]; then
    echo "  ✓ YOLO weights found"
else
    echo "  ✗ MISSING: experiments/v6_9class_english/weights/best.pt"
fi

if [ -f "models/image_quality_classifier.pt" ]; then
    echo "  ✓ Quality model found"
else
    echo "  ✗ MISSING: models/image_quality_classifier.pt"
fi

echo ""
echo "╔══════════════════════════════════════════════════════╗"
echo "║  ✅ Setup Complete!                                  ║"
echo "║  Run: bash run_server.sh                            ║"
echo "╚══════════════════════════════════════════════════════╝"
echo ""
