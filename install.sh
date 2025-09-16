#!/bin/bash

# Evolve NetScan Installation Script
# This script installs Evolve NetScan and its dependencies

set -e  # Exit on any error

echo "🔍 Evolve NetScan Installation Script"
echo "====================================="

# Check Python version
echo "📋 Checking Python version..."
python_version=$(python3 --version 2>&1 | grep -oE '[0-9]+\.[0-9]+' | head -1)
required_version="3.8"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" = "$required_version" ]; then
    echo "✅ Python $python_version detected (>= $required_version required)"
else
    echo "❌ Python $required_version or higher is required. Found: $python_version"
    exit 1
fi

# Check if pip is available
echo "📋 Checking pip..."
if command -v pip3 &> /dev/null; then
    echo "✅ pip3 found"
    PIP_CMD="pip3"
elif command -v pip &> /dev/null; then
    echo "✅ pip found"
    PIP_CMD="pip"
else
    echo "❌ pip not found. Please install pip first."
    exit 1
fi

# Create virtual environment
echo "📋 Creating virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "✅ Virtual environment created"
else
    echo "✅ Virtual environment already exists"
fi

# Activate virtual environment
echo "📋 Activating virtual environment..."
source venv/bin/activate
echo "✅ Virtual environment activated"

# Upgrade pip
echo "📋 Upgrading pip..."
$PIP_CMD install --upgrade pip
echo "✅ pip upgraded"

# Install dependencies
echo "📋 Installing dependencies..."
if [ -f "requirements.txt" ]; then
    $PIP_CMD install -r requirements.txt
    echo "✅ Dependencies installed from requirements.txt"
else
    echo "❌ requirements.txt not found"
    exit 1
fi

# Install the package in development mode
echo "📋 Installing Evolve NetScan..."
if [ -f "setup.py" ]; then
    $PIP_CMD install -e .
    echo "✅ Evolve NetScan installed in development mode"
else
    echo "❌ setup.py not found"
    exit 1
fi

# Check installation
echo "📋 Verifying installation..."
if command -v evolve-netscan &> /dev/null; then
    echo "✅ evolve-netscan command available"
elif command -v netscan &> /dev/null; then
    echo "✅ netscan command available"
else
    echo "❌ Installation verification failed"
    exit 1
fi

# Create necessary directories
echo "📋 Creating necessary directories..."
mkdir -p runs reports
echo "✅ Directories created"

# Test basic functionality
echo "📋 Testing basic functionality..."
if python -c "import app.core.cli; print('✅ Core modules import successfully')" 2>/dev/null; then
    echo "✅ Basic functionality test passed"
else
    echo "❌ Basic functionality test failed"
    exit 1
fi

echo ""
echo "🎉 Installation completed successfully!"
echo ""
echo "📋 Next steps:"
echo "1. Activate the virtual environment: source venv/bin/activate"
echo "2. Run a test scan: netscan scan 127.0.0.1 --safe"
echo "3. Get help: netscan help"
echo ""
echo "📚 Documentation:"
echo "- README.md: Complete usage guide"
echo "- CONTRIBUTING.md: Development guidelines"
echo "- GitHub: https://github.com/yourusername/evolve-netscan"
echo ""
echo "⚠️  Important:"
echo "- Always obtain proper authorization before scanning targets"
echo "- Use safe mode for production environments"
echo "- Review the legal disclaimer in README.md"
echo ""
echo "Happy scanning! 🔍"
