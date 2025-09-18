# Kali Linux Troubleshooting Guide

This guide addresses the specific issues encountered during NetScan installation on Kali Linux.

## Quick Fix for Your Current Issues

Based on the errors you encountered, run these commands in order:

### Step 1: Fix System Package Manager Issues

```bash
# Fix the interrupted dpkg installation
sudo dpkg --configure -a

# Remove the problematic splunk package
sudo dpkg --remove --force-remove-reinstreq splunk

# Fix broken packages
sudo apt --fix-broken install -y

# Clean package cache
sudo apt clean && sudo apt autoclean
```

### Step 2: Fix GPG Key Issues

```bash
# Add missing Kali GPG keys
sudo apt-key adv --keyserver keyserver.ubuntu.com --recv-keys ED65462EC8D5E4C5
sudo apt-key adv --keyserver hkp://keys.gnupg.net --recv-keys ED65462EC8D5E4C5

# Update package lists
sudo apt update
```

### Step 3: Install Missing Dependencies

```bash
# Install Cairo dependencies
sudo apt install -y libcairo2-dev libpango1.0-dev pkg-config python3-dev build-essential

# Install pip properly
sudo apt install -y python3-pip
python3 -m pip install --upgrade pip --user
```

### Step 4: Fix PATH and Install NetScan

```bash
# Add ~/.local/bin to PATH
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc

# Install NetScan
cd netscan-master  # or evolve-netscan
python3 -m pip install -e . --user
```

## Automated Fix Script

Use the automated fix script we created:

```bash
# Make scripts executable
chmod +x fix_kali_system.sh
chmod +x install_kali.sh
chmod +x test_kali_install.sh

# Run system repair first
./fix_kali_system.sh

# Then run installation
./install_kali_sh

# Test installation
./test_kali_install.sh
```

## Common Error Solutions

### Error: "dpkg was interrupted"
```bash
sudo dpkg --configure -a
sudo apt --fix-broken install -y
```

### Error: "splunk needs to be reinstalled"
```bash
sudo dpkg --remove --force-remove-reinstreq splunk
sudo apt --fix-broken install -y
```

### Error: "GPG signatures couldn't be verified"
```bash
sudo apt-key adv --keyserver keyserver.ubuntu.com --recv-keys ED65462EC8D5E4C5
sudo apt update
```

### Error: "bc: command not found" (in test script)
This is now fixed in the updated test script, but if you encounter it:
```bash
sudo apt install -y bc
```

### Error: "pip not found" or "ensurepip failed"
```bash
sudo apt install -y python3-pip
python3 -m pip install --upgrade pip --user
```

### Error: "Cairo libraries not found"
```bash
sudo apt install -y libcairo2-dev libpango1.0-dev libgdk-pixbuf2.0-dev
sudo apt install -y pkg-config python3-dev build-essential
```

### Error: "netscan command not found"
```bash
# Add to PATH
export PATH="$HOME/.local/bin:$PATH"
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc

# Or use module form
python3 -m app.core.cli --help
```

## Manual Installation Steps

If the automated scripts don't work, follow these manual steps:

### 1. System Cleanup
```bash
sudo dpkg --configure -a
sudo apt --fix-broken install -y
sudo apt clean && sudo apt autoclean
sudo apt update
```

### 2. Install System Dependencies
```bash
sudo apt install -y \
    build-essential \
    python3-dev \
    python3-pip \
    pkg-config \
    libcairo2-dev \
    libpango1.0-dev \
    libgdk-pixbuf2.0-dev \
    libffi-dev \
    libssl-dev
```

### 3. Setup Python Environment
```bash
python3 -m pip install --upgrade pip --user
export PATH="$HOME/.local/bin:$PATH"
```

### 4. Install NetScan
```bash
cd evolve-netscan  # or netscan-master
python3 -m pip install -e . --user
```

### 5. Verify Installation
```bash
netscan --help
# If command not found:
python3 -m app.core.cli --help
```

## Repository Issues

If you continue having repository/GPG issues:

### Option 1: Update Kali Sources
```bash
sudo nano /etc/apt/sources.list
# Ensure you have:
deb http://http.kali.org/kali kali-rolling main non-free contrib
```

### Option 2: Full System Update
```bash
sudo apt update && sudo apt full-upgrade -y
```

### Option 3: Reset Repository Keys
```bash
sudo apt-key del ED65462EC8D5E4C5
wget -q -O - https://archive.kali.org/archive-key.asc | sudo apt-key add
sudo apt update
```

## Testing Your Installation

After fixing the issues, test with:

```bash
# Test basic functionality
python3 -c "import app.core.cli; print('Import successful')"

# Test CLI
netscan --help

# Test scan (safe)
netscan scan 127.0.0.1 --safe

# Test web server
netscan web-server --port 8080
```

## Still Having Issues?

If problems persist:

1. **Reboot your system** - Sometimes package manager issues require a restart
2. **Check disk space** - Ensure you have enough free space: `df -h`
3. **Check system logs** - Look for errors: `sudo journalctl -xe`
4. **Try virtual environment** - Isolate Python dependencies:
   ```bash
   python3 -m venv netscan_env
   source netscan_env/bin/activate
   pip install -e .
   ```

5. **Use Docker** - If all else fails, consider using Docker:
   ```bash
   # Create a Dockerfile for NetScan
   docker build -t netscan .
   docker run -it netscan
   ```

## Contact Support

If none of these solutions work, please provide:
- Output of `lsb_release -a`
- Output of `python3 --version`
- Complete error messages
- Output of `sudo apt update 2>&1 | head -20`
