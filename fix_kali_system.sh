#!/bin/bash

# Fix Kali Linux System Issues Script
# This script fixes common Kali Linux package manager and system issues

echo "=========================================="
echo "Kali Linux System Repair Script"
echo "=========================================="

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
NC='\033[0m' # No Color

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
    echo "You may need to fix repository configurations manually later."
else
    echo -e "${GREEN}Package lists updated successfully!${NC}"
fi

echo -e "${YELLOW}Step 7: Installing essential tools...${NC}"
sudo apt install -y curl wget gnupg2 software-properties-common

echo -e "${YELLOW}Step 8: Final system check...${NC}"
sudo apt update --fix-missing || true

echo ""
echo -e "${GREEN}=========================================="
echo "System repair completed!"
echo "=========================================="
echo -e "${NC}"
echo "Next steps:"
echo "1. Run: ./install_kali.sh"
echo "2. If issues persist, reboot and try again"
echo "3. For repository issues, you may need to:"
echo "   - Check /etc/apt/sources.list"
echo "   - Update Kali Linux: sudo apt full-upgrade"

# Clean up temp files
rm -f /tmp/apt_update.log
