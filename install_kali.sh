#!/bin/bash

# Kali Linux Installation Script for NetScan
# This script installs all system dependencies and sets up the Python environment

echo "======================================"
echo "NetScan Kali Linux Installation Script"
echo "======================================"

# Check if running as root (for apt operations)
if [[ $EUID -eq 0 ]]; then
   echo "This script should not be run as root. Please run as a regular user."
   echo "The script will prompt for sudo password when needed."
   exit 1
fi

# Fix common Kali Linux issues first
echo "Checking and fixing common Kali Linux package manager issues..."

# Fix interrupted dpkg installations
echo "Fixing interrupted dpkg installations..."
sudo dpkg --configure -a || true

# Fix broken packages
echo "Fixing broken packages..."
sudo apt --fix-broken install -y || true

# Remove problematic packages if they exist
echo "Checking for problematic packages..."
if dpkg -l | grep -q "splunk"; then
    echo "Removing problematic splunk package..."
    sudo dpkg --remove --force-remove-reinstreq splunk || true
fi

# Update GPG keys for Kali
echo "Updating Kali Linux GPG keys..."
sudo apt-key adv --keyserver keyserver.ubuntu.com --recv-keys ED65462EC8D5E4C5 || true
sudo apt-key adv --keyserver hkp://keys.gnupg.net --recv-keys ED65462EC8D5E4C5 || true

# Clean package cache
echo "Cleaning package cache..."
sudo apt clean
sudo apt autoclean

# Update package lists (with error handling)
echo "Updating package lists..."
sudo apt update || echo "Warning: Some repositories may have issues, continuing..."

# Install system dependencies for Cairo and other native libraries
echo "Installing system dependencies..."

# Install packages in groups to handle potential failures
echo "Installing essential build tools..."
sudo apt install -y build-essential python3-dev pkg-config || {
    echo "Warning: Some essential packages failed to install"
}

echo "Installing Cairo and graphics libraries..."
sudo apt install -y \
    libcairo2-dev \
    libpango1.0-dev \
    libgdk-pixbuf2.0-dev \
    libffi-dev \
    shared-mime-info || {
    echo "Warning: Some Cairo libraries failed to install"
}

echo "Installing Python and development tools..."
sudo apt install -y \
    python3-pip \
    python3-venv \
    python3-tk || {
    echo "Warning: Some Python tools failed to install"
}

echo "Installing additional libraries..."
sudo apt install -y \
    libssl-dev \
    libxml2-dev \
    libxslt1-dev \
    zlib1g-dev \
    libjpeg-dev \
    libfreetype6-dev \
    liblcms2-dev \
    libwebp-dev \
    tcl8.6-dev \
    tk8.6-dev || {
    echo "Warning: Some additional libraries failed to install"
}

# Ensure pip is properly installed
echo "Ensuring pip is properly installed..."

# Try different methods to ensure pip is available
if ! python3 -m pip --version >/dev/null 2>&1; then
    echo "pip not found, installing..."
    
    # Method 1: ensurepip
    python3 -m ensurepip --default-pip --user 2>/dev/null || \
    
    # Method 2: system pip
    sudo apt install -y python3-pip 2>/dev/null || \
    
    # Method 3: get-pip.py
    {
        echo "Downloading get-pip.py..."
        curl -sS https://bootstrap.pypa.io/get-pip.py -o /tmp/get-pip.py
        python3 /tmp/get-pip.py --user
        rm -f /tmp/get-pip.py
    }
fi

# Upgrade pip
echo "Upgrading pip..."
python3 -m pip install --upgrade pip --user 2>/dev/null || {
    echo "Warning: Could not upgrade pip, but continuing..."
}

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
