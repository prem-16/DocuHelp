#!/bin/bash

# Smart Surgical Report Generator - Setup Script
# Run this to set up your development environment

set -e

echo "🏥 Setting up Surgical Report Generator..."

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "📦 Installing uv package manager..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.cargo/bin:$PATH"
fi

# Create virtual environment
echo "🐍 Creating virtual environment..."
uv venv

# Activate virtual environment
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    source .venv/Scripts/activate
else
    source .venv/bin/activate
fi

# Install dependencies
echo "📚 Installing dependencies..."
uv pip install -e ".[dev]"

# Create necessary directories
echo "📁 Creating directory structure..."
mkdir -p data/raw/videos data/raw/sops
mkdir -p data/processed/frames data/processed/annotations
mkdir -p data/reports
mkdir -p models/vlm models/segmentation models/cache
mkdir -p logs tmp

# Create .gitkeep files
touch data/raw/videos/.gitkeep
touch data/raw/sops/.gitkeep
touch data/processed/frames/.gitkeep
touch data/processed/annotations/.gitkeep
touch data/reports/.gitkeep
touch models/.gitkeep

# Copy .env.example to .env if it doesn't exist
if [ ! -f .env ]; then
    echo "⚙️  Creating .env file..."
    cp .env.example .env
    echo "⚠️  Please edit .env with your Firebase credentials!"
fi

# Create __init__.py files
echo "📝 Creating __init__.py files..."
touch src/__init__.py
touch src/dataset/__init__.py
touch src/vlm/__init__.py
touch src/processing/__init__.py
touch src/ui/__init__.py
touch src/ui/api/__init__.py
touch src/ui/api/routes/__init__.py
touch src/report/__init__.py
touch src/testing/__init__.py
touch src/utils/__init__.py

# Initialize git if not already initialized
if [ ! -d .git ]; then
    echo "🔧 Initializing git repository..."
    git init
    git add .
    git commit -m "Initial commit: Smart Surgical Report Generator"
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit .env with your Firebase credentials"
echo "2. Run: source .venv/bin/activate (or .venv\\Scripts\\activate on Windows)"
echo "3. Start the API: cd src/ui/api && uvicorn main:app --reload"
echo "4. Visit: http://localhost:8000/docs for API documentation"
echo ""
echo "Team assignments:"
echo "- Simon: src/dataset/ - Dataset curation and SOP management"
echo "- Anish: src/vlm/ - Vision Language Model development"
echo "- Prem: src/processing/ - Frame extraction and annotation"
echo "- Sanjeev: src/ui/, src/report/ - UI, feedback, and report generation"
echo ""
echo "Happy hacking! 🚀"