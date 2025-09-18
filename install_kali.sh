#!/bin/bash

# Kali Linux Installation Script for NetScan
# This script installs all system dependencies and sets up the Python environment

set -e  # Exit on any error

echo "======================================"
echo "NetScan Kali Linux Installation Script"
echo "======================================"

# Check if running as root (for apt operations)
if [[ $EUID -eq 0 ]]; then
   echo "This script should not be run as root. Please run as a regular user."
   echo "The script will prompt for sudo password when needed."
   exit 1
fi

# Update package lists
echo "Updating package lists..."
sudo apt update

# Install system dependencies for Cairo and other native libraries
echo "Installing system dependencies..."
sudo apt install -y \
    libcairo2-dev \
    libpango1.0-dev \
    libgdk-pixbuf2.0-dev \
    libffi-dev \
    shared-mime-info \
    pkg-config \
    python3-dev \
    python3-pip \
    python3-venv \
    build-essential \
    libssl-dev \
    libxml2-dev \
    libxslt1-dev \
    zlib1g-dev \
    libjpeg-dev \
    libfreetype6-dev \
    liblcms2-dev \
    libwebp-dev \
    tcl8.6-dev \
    tk8.6-dev \
    python3-tk

# Ensure pip is properly installed
echo "Ensuring pip is properly installed..."
python3 -m ensurepip --default-pip --user || true
python3 -m pip install --upgrade pip --user

# Add ~/.local/bin to PATH if not already there
if ! echo $PATH | grep -q "$HOME/.local/bin"; then
    echo "Adding ~/.local/bin to PATH..."
    echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
    export PATH="$HOME/.local/bin:$PATH"
fi

# Install the package in development mode
echo "Installing NetScan package..."
python3 -m pip install -e . --user

# Verify installation
echo "Verifying installation..."
if command -v netscan &> /dev/null; then
    echo "✓ NetScan installed successfully!"
    echo "You can now use: netscan --help"
else
    echo "⚠ Installation completed but 'netscan' command not found in PATH."
    echo "Please restart your terminal or run: source ~/.bashrc"
fi

# Create a desktop shortcut (optional)
read -p "Create desktop shortcut? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    cat > ~/Desktop/NetScan.desktop << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=NetScan
Comment=Network Penetration Testing Tool
Exec=gnome-terminal -- netscan --help
Icon=applications-internet
Terminal=true
Categories=Network;Security;
EOF
    chmod +x ~/Desktop/NetScan.desktop
    echo "✓ Desktop shortcut created"
fi

echo ""
echo "======================================"
echo "Installation Complete!"
echo "======================================"
echo "Usage examples:"
echo "  netscan scan 192.168.1.1 --safe"
echo "  netscan web-server"
echo "  netscan --help"
echo ""
echo "If you encounter any issues, please check:"
echo "1. PATH includes ~/.local/bin"
echo "2. Restart your terminal"
echo "3. Run: source ~/.bashrc"
