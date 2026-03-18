#!/bin/bash
# Setup script for SDXL + LoRA integration

echo "🎨 Setting up SDXL + LoRA integration for blog image generation..."

# Check if we're in the right directory
if [ ! -f "scripts/generate_sdxl_lora_integrated.py" ]; then
    echo "❌ Please run this script from the blog project root directory"
    exit 1
fi

# Create directories
echo "📁 Creating directories..."
mkdir -p static/models/lora
mkdir -p static/content/posts

# Install dependencies
echo "📦 Installing Python dependencies..."
source venv_sdxl/bin/activate
pip install --upgrade diffusers==0.30.0 transformers accelerate safetensors torch torchvision torchaudio peft psycopg python-dotenv

# Check if LoRA file exists
LORA_FILE="static/models/lora/Aether_Watercolor_and_Ink_v1_SDXL_LoRA.safetensors"
if [ ! -f "$LORA_FILE" ]; then
    echo "⚠️  LoRA file not found at: $LORA_FILE"
    echo "📥 Please download your LoRA file and place it at:"
    echo "   $(pwd)/$LORA_FILE"
    echo ""
    echo "💡 The script expects a LoRA file named 'Aether_Watercolor_and_Ink_v1_SDXL_LoRA.safetensors'"
    echo "   If you have a different filename, update the LORA_PATH in:"
    echo "   scripts/generate_sdxl_lora_integrated.py"
else
    echo "✅ LoRA file found at: $LORA_FILE"
fi

# Test the script
echo "🧪 Testing SDXL script..."
source venv_sdxl/bin/activate
python3 scripts/generate_sdxl_lora_integrated.py --post_id 60 --section_id 790 --subject "a druid performing a ritual beneath an ancient oak" --width 1792 --height 1024 --steps 20 --cfg 5.5 --seed 42

if [ $? -eq 0 ]; then
    echo "✅ SDXL script test successful!"
    echo ""
    echo "🎉 Setup complete! You can now:"
    echo "   1. Use 'sdxl-lora' as a model option in the image generation interface"
    echo "   2. Generate images with your custom LoRA style"
    echo "   3. Adjust parameters like lora_scale, steps, cfg, etc."
else
    echo "❌ SDXL script test failed. Please check:"
    echo "   - Python dependencies are installed"
    echo "   - LoRA file is in the correct location"
    echo "   - You have sufficient disk space and memory"
fi

echo ""
echo "📋 Next steps:"
echo "   1. Place your LoRA file at: $(pwd)/$LORA_FILE"
echo "   2. Test with: source venv_sdxl/bin/activate && python3 scripts/generate_sdxl_lora_integrated.py --help"
echo "   3. Use the web interface to select 'sdxl-lora' model"

