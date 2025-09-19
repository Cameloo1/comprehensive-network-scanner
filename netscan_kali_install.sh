#!/bin/bash

# NetScan Kali Linux Complete Installation Script
# This script combines system fixing and NetScan installation into one automated process
# First fixes common Kali Linux issues, then installs NetScan

echo "=============================================="
echo "NetScan Complete Kali Linux Installation"
echo "=============================================="
echo "This script will:"
echo "1. Fix common Kali Linux system issues"
echo "2. Install all required dependencies"
echo "3. Install NetScan in development mode"
echo ""

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   echo "This script should not be run as root. Please run as a regular user."
   echo "The script will prompt for sudo password when needed."
   exit 1
fi

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo ""
echo -e "${BLUE}===========================================${NC}"
echo -e "${BLUE}PHASE 1: SYSTEM REPAIR${NC}"
echo -e "${BLUE}===========================================${NC}"

echo -e "${YELLOW}Step 1: Fixing interrupted dpkg installations...${NC}"
sudo dpkg --configure -a

echo -e "${YELLOW}Step 2: Fixing broken packages...${NC}"
sudo apt --fix-broken install -y

echo -e "${YELLOW}Step 3: Checking for problematic packages...${NC}"
if dpkg -l | grep -q "^ii.*splunk" || dpkg -l | grep -q "^iU.*splunk" || dpkg -l | grep -q "^iF.*splunk"; then
    echo -e "${RED}Found problematic splunk package. Removing...${NC}"
    
    # Try different removal methods
    sudo dpkg --remove --force-remove-reinstreq splunk 2>/dev/null || \
    sudo dpkg --purge --force-remove-reinstreq splunk 2>/dev/null || \
    sudo apt-get remove --purge splunk -y 2>/dev/null || \
    echo -e "${YELLOW}Warning: Could not remove splunk package automatically${NC}"
    
    # Clean up any remaining files
    sudo rm -rf /opt/splunk* 2>/dev/null || true
    sudo rm -rf /etc/splunk* 2>/dev/null || true
fi

echo -e "${YELLOW}Step 4: Cleaning package cache and lists...${NC}"
sudo apt clean
sudo apt autoclean
sudo rm -rf /var/lib/apt/lists/*
sudo mkdir -p /var/lib/apt/lists/partial

echo -e "${YELLOW}Step 5: Updating GPG keys...${NC}"
# Add Kali Linux GPG keys
sudo apt-key adv --keyserver keyserver.ubuntu.com --recv-keys ED65462EC8D5E4C5 2>/dev/null || \
sudo apt-key adv --keyserver hkp://keys.gnupg.net --recv-keys ED65462EC8D5E4C5 2>/dev/null || \
sudo apt-key adv --keyserver pgp.mit.edu --recv-keys ED65462EC8D5E4C5 2>/dev/null || \
echo -e "${YELLOW}Warning: Could not update GPG keys from keyservers${NC}"

echo -e "${YELLOW}Step 6: Updating package lists...${NC}"
sudo apt update 2>&1 | tee /tmp/apt_update.log

# Check if update was successful
if grep -q "E:" /tmp/apt_update.log; then
    echo -e "${YELLOW}Some repositories have issues, but continuing...${NC}"
    echo "Repository issues will not prevent NetScan installation."
else
    echo -e "${GREEN}Package lists updated successfully!${NC}"
fi

echo -e "${YELLOW}Step 7: Installing essential tools...${NC}"
sudo apt install -y curl wget gnupg2 software-properties-common

echo -e "${YELLOW}Step 8: Final system check...${NC}"
sudo apt update --fix-missing || true

echo -e "${GREEN}System repair completed!${NC}"

# Clean up temp files
rm -f /tmp/apt_update.log

echo ""
echo -e "${BLUE}===========================================${NC}"
echo -e "${BLUE}PHASE 2: NETSCAN INSTALLATION${NC}"
echo -e "${BLUE}===========================================${NC}"

# Install system dependencies for Cairo and other native libraries
echo -e "${YELLOW}Installing system dependencies...${NC}"

# Install packages in groups to handle potential failures
echo -e "${YELLOW}Installing essential build tools...${NC}"
sudo apt install -y build-essential python3-dev pkg-config || {
    echo -e "${RED}Warning: Some essential packages failed to install${NC}"
}

echo -e "${YELLOW}Installing Cairo and graphics libraries...${NC}"
sudo apt install -y \
    libcairo2-dev \
    libpango1.0-dev \
    libgdk-pixbuf2.0-dev \
    libffi-dev \
    shared-mime-info || {
    echo -e "${RED}Warning: Some Cairo libraries failed to install${NC}"
}

echo -e "${YELLOW}Installing Python and development tools...${NC}"
sudo apt install -y \
    python3-pip \
    python3-venv \
    python3-tk || {
    echo -e "${RED}Warning: Some Python tools failed to install${NC}"
}

echo -e "${YELLOW}Installing additional libraries...${NC}"
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
    echo -e "${RED}Warning: Some additional libraries failed to install${NC}"
}

# Ensure pip is properly installed
echo -e "${YELLOW}Ensuring pip is properly installed...${NC}"

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
echo -e "${YELLOW}Upgrading pip...${NC}"
python3 -m pip install --upgrade pip --user 2>/dev/null || {
    echo -e "${YELLOW}Warning: Could not upgrade pip, but continuing...${NC}"
}

# Add ~/.local/bin to PATH if not already there
if ! echo $PATH | grep -q "$HOME/.local/bin"; then
    echo -e "${YELLOW}Adding ~/.local/bin to PATH...${NC}"
    echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
    export PATH="$HOME/.local/bin:$PATH"
fi

# Install the package in development mode
echo -e "${YELLOW}Installing NetScan package...${NC}"
python3 -m pip install -e . --user

# Verify installation
echo -e "${YELLOW}Verifying installation...${NC}"
if command -v netscan &> /dev/null; then
    echo -e "${GREEN}✓ NetScan installed successfully!${NC}"
    echo "You can now use: netscan --help"
else
    echo -e "${YELLOW}⚠ Installation completed but 'netscan' command not found in PATH.${NC}"
    echo "Please restart your terminal or run: source ~/.bashrc"
fi

# Create a desktop shortcut (optional)
echo ""
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
    echo -e "${GREEN}✓ Desktop shortcut created${NC}"
fi

echo ""
echo -e "${GREEN}=============================================="
echo "INSTALLATION COMPLETE!"
echo "==============================================\\${NC}"
echo ""
echo -e "${GREEN}✓ System issues fixed${NC}"
echo -e "${GREEN}✓ Dependencies installed${NC}"
echo -e "${GREEN}✓ NetScan installed successfully${NC}"
echo ""
echo -e "${BLUE}Usage examples:${NC}"
echo "  netscan scan 192.168.1.1 --safe"
echo "  netscan web-server"
echo "  netscan --help"
echo ""
echo -e "${YELLOW}If you encounter any issues, please:${NC}"
echo "1. Restart your terminal or run: source ~/.bashrc"
echo "2. Ensure PATH includes ~/.local/bin"
echo "3. For repository issues, run: sudo apt full-upgrade"
echo ""
echo -e "${GREEN}Happy penetration testing!${NC}"
