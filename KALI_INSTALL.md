# Kali Linux Installation Guide

This guide addresses the specific installation issues encountered on Kali Linux.

## Quick Fix (Automated)

Run the automated installation script:

```bash
cd /path/to/netscan-master
chmod +x install_kali.sh
./install_kali.sh
```

## Manual Installation Steps

If you prefer to install manually or the script fails, follow these steps:

### 1. Install System Dependencies

```bash
# Update package lists
sudo apt update

# Install Cairo and other system dependencies
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
    libwebp-dev
```

### 2. Fix pip Installation

```bash
# Ensure pip is properly installed
python3 -m ensurepip --default-pip --user
python3 -m pip install --upgrade pip --user
```

### 3. Fix PATH Environment

```bash
# Add ~/.local/bin to PATH
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

### 4. Install NetScan

```bash
# Install in development mode
python3 -m pip install -e . --user
```

### 5. Verify Installation

```bash
# Check if command is available
netscan --help

# If not found, restart terminal or run:
source ~/.bashrc
```

## Common Issues and Solutions

### Issue 1: Cairo dependency error
**Error:** `ERROR: Dependency "cairo" not found`

**Solution:** Install system Cairo libraries:
```bash
sudo apt install -y libcairo2-dev libpango1.0-dev pkg-config
```

### Issue 2: sqlite3 pip error
**Error:** `ERROR: Could not find a version that satisfies the requirement sqlite3`

**Solution:** This is already fixed in the updated requirements.txt. sqlite3 is built into Python.

### Issue 3: No module named pip
**Error:** `/usr/bin/python3: No module named pip`

**Solution:**
```bash
python3 -m ensurepip --default-pip --user
python3 -m pip install --upgrade pip --user
```

### Issue 4: Script location warnings
**Warning:** `WARNING: The script X is installed in '/home/user/.local/bin' which is not on PATH`

**Solution:** Add ~/.local/bin to your PATH:
```bash
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

### Issue 5: Command not found after installation
**Error:** `netscan: command not found`

**Solution:** 
1. Restart your terminal
2. Or run: `source ~/.bashrc`
3. If still not working, try: `python3 -m app.core.cli --help`

## Usage Examples

Once installed successfully:

```bash
# Basic scan
netscan scan 192.168.1.1 --safe

# Multiple targets
netscan scan 192.168.1.1,192.168.1.2 --safe

# CIDR range
netscan scan 192.168.1.0/24 --safe

# Custom worker count
netscan scan 192.168.1.1 --safe --workers 4

# Generate report
netscan report <scan-id>

# Show help
netscan --help
```

## Troubleshooting

If you continue to have issues:

1. Make sure you're using Python 3.8 or higher: `python3 --version`
2. Check if all dependencies are installed: `python3 -m pip list`
3. Try running directly: `python3 -m app.core.cli scan --help`
4. Check the logs in the terminal for specific error messages

## Support

If you encounter issues not covered here, please:
1. Check the error message carefully
2. Ensure all system dependencies are installed
3. Verify your Python version is 3.8+
4. Try the manual installation steps above
