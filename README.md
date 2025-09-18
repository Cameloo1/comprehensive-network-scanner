# Evolve NetScan

[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Security](https://img.shields.io/badge/security-penetration--testing-red.svg)](https://github.com/yourusername/evolve-netscan)

A comprehensive, automated network penetration testing tool designed for security professionals and ethical hackers. Evolve NetScan combines multiple industry-standard tools into a unified platform with real-time progress tracking, comprehensive reporting, and concurrent scanning capabilities.

## Features

### Core Capabilities
- **Multi-Target Scanning**: Support for single IPs, CIDR ranges, and comma-separated target lists
- **Concurrent Processing**: Configurable worker threads (1-32) for optimal performance
- **Real-Time Progress Tracking**: Live progress bars with ETA calculations and worker monitoring
- **Comprehensive Reporting**: Professional HTML and PDF reports with detailed vulnerability analysis
- **Advanced Data Integration**: All tool findings consolidated into unified reports

### Integrated Tools
- **Nmap**: Advanced port scanning with service detection and version enumeration
- **WhatWeb**: Web application fingerprinting with technology detection (Python fallback included)
- **Nuclei**: Safe vulnerability scanning with timeout protection and safe templates
- **SSLyze**: Comprehensive TLS/SSL configuration analysis and certificate validation
- **TestSSL**: Additional SSL/TLS testing and cipher suite analysis
- **Custom Reconnaissance**: Reverse DNS, WHOIS, and DNS record analysis
- **Web Fingerprinting**: HTTP/HTTPS service analysis with technology detection

### Advanced Features
- **Safe Mode**: Non-destructive scanning with safe vulnerability templates
- **Timeout Protection**: Prevents hanging on filtered/unresponsive targets
- **Database Storage**: SQLite database for scan result persistence
- **API Interface**: RESTful API for integration with other tools
- **Export Options**: JSON and CSV export capabilities

### Comprehensive Reporting
- **Port Scan Results**: Detailed tables with color-coded port states (open=red, closed=orange, filtered=blue)
- **Target IPs Summary**: Overview table showing total ports found with open port breakdown
- **WHOIS Information**: Complete network ownership and contact details
- **Web Application Analysis**: Technology fingerprinting and HTTP response analysis
- **TLS/SSL Analysis**: Certificate validation, supported protocols, and cipher suites
- **Vulnerability Findings**: Source-attributed findings with severity levels and remediation
- **Executive Summary**: High-level overview with vulnerability counts and recommendations
- **Professional Formatting**: Clean HTML and PDF reports with enhanced typography and visual hierarchy

## Quick Start

### Prerequisites
- Python 3.8 or higher
- pip (Python package installer)
- For Kali Linux: System dependencies (handled by install script)

### Installation

#### Kali Linux (Quick Install)
For Kali Linux users, use the automated installation script:
```bash
# Navigate to the project directory
cd evolve-netscan

# Run automated Kali installation
chmod +x install_kali.sh
./install_kali.sh

# Test installation
chmod +x test_kali_install.sh
./test_kali_install.sh
```

#### Option 1: From Source (Recommended)
```bash
# Navigate to the project directory
cd evolve-netscan

# Install the package in development mode
python -m pip install -e . --user

# Or with pip3 on Linux/macOS
pip3 install -e . --user
```

#### Option 2: Manual Dependencies (if needed)
```bash
# Install dependencies first (usually not needed with -e .)
python -m pip install -r requirements.txt --user

# Then install the package
python -m pip install -e . --user
```

### Quick Usage
After installation, try these common commands:
```bash
# Test installation
netscan --help

# Scan a single target
netscan scan 127.0.0.1 --safe

# Start web interface
netscan web-server

# If 'netscan' command not found, use:
python -m app.core.cli --help
```

### Basic Usage

#### Single Target Scan
```bash
# Scan a single IP
netscan scan 192.168.1.1 --safe

# If command not found, use module form
python -m app.core.cli scan 192.168.1.1 --safe
```

#### Multiple Target Scan
```bash
# Scan multiple IPs
netscan scan 1.1.1.1,2.2.2.2,3.3.3.3 --safe

# Scan CIDR range
netscan scan 192.168.1.0/24 --safe

# Mixed targets
netscan scan 127.0.0.1,192.168.1.0/30,8.8.8.8 --safe
```

#### Custom Worker Configuration
```bash
# Use 4 concurrent workers
netscan scan 1.1.1.1,2.2.2.2,3.3.3.3 --safe --workers 4

# Short form
netscan scan 1.1.1.1,2.2.2.2,3.3.3.3 --safe -w 4
```

## Command Reference

### Scan Command
```bash
netscan scan <target> [OPTIONS]

Arguments:
  target    Target IP, CIDR, or comma-separated list to scan

Options:
  --safe/--no-safe    Enable safe mode (default: --safe)
  --workers, -w       Maximum concurrent workers (1-32, default: 8)
  --help             Show help message
```

### Report Generation
```bash
# Generate HTML and PDF reports
netscan report <scan_id>

# Example
netscan report a1b2c3d4-e5f6-7890-abcd-ef1234567890
```

### Data Export
```bash
# Export to JSON
netscan export-json <scan_id>

# Export to CSV
netscan export-csv <scan_id>
```

### Scan Summary
```bash
# Get scan summary
netscan summary <scan_id>
```

### Web Server
```bash
# Start web interface
netscan web-server

# Start on custom port
netscan web-server --port 8080
```

### Help
```bash
# Show detailed help
netscan help

# Show command help
netscan --help

# Show scan command help
netscan scan --help
```

## Configuration

### Environment Variables
```bash
# Database location (optional)
export NETSCAN_DB_PATH=/path/to/netscan.db

# Default worker count (optional)
export NETSCAN_DEFAULT_WORKERS=8

# Safe mode default (optional)
export NETSCAN_SAFE_MODE=true
```

### Authorization File
For non-lab targets, create an `AUTHORIZATION.txt` file:
```
# Add your authorization details here
# This file allows scanning of external targets
```

## Progress Tracking

NetScan features a comprehensive progress tracking system:

```
Progress: [████████████████████████░░░░░░]  80.0% | Completed: 4/5 | Active Workers: 1/2 | Failed: 0 | ETA: 0:00:57

Scan Complete!
   Total Targets: 5
   Completed: 5
   Failed: 0
   Success Rate: 100.0%
   Total Time: 0:03:49
   Avg Time/Target: 0:00:45
```

### Progress Features
- **Real-time progress bar** with visual completion indicator
- **Worker monitoring** showing active vs maximum workers
- **ETA calculation** based on current scan performance
- **Failure tracking** for failed targets
- **Final summary** with success rates and timing

## Report Generation

### HTML Reports
- Interactive web-based reports
- Detailed vulnerability information
- Service enumeration results
- TLS/SSL configuration analysis

### PDF Reports
- Professional PDF format
- Executive summaries
- Detailed technical findings
- Remediation recommendations

### Report Contents
- **Executive Summary**: High-level overview and risk assessment
- **Host Information**: IP addresses, reverse DNS, WHOIS data
- **Open Ports**: Discovered services and versions
- **Vulnerabilities**: Security findings with severity ratings
- **TLS Analysis**: SSL/TLS configuration assessment
- **Web Fingerprinting**: Application and service identification

## Security Considerations

### Safe Mode
NetScan operates in safe mode by default, which:
- Uses only non-destructive vulnerability templates
- Implements timeout protection to prevent hanging
- Avoids aggressive scanning techniques
- Focuses on information gathering rather than exploitation

### Authorization
- **Lab Networks**: Automatically authorized (127.x, 192.168.x, 10.x, 172.16-31.x)
- **External Targets**: Require `AUTHORIZATION.txt` file
- **Responsible Disclosure**: Always obtain proper authorization before scanning

### Best Practices
1. **Always obtain written permission** before scanning any target
2. **Use safe mode** for production environments
3. **Start with small target lists** to test performance
4. **Monitor resource usage** with large scans
5. **Review reports carefully** before taking action

## API Usage

### Starting the Web Server
```bash
# Start the web server using CLI
netscan web-server

# Or start with custom port
netscan web-server --port 8080

# Or using module form
python -m app.core.cli web-server

# Server will be available at http://localhost:8000
```

### API Endpoints
```bash
# Health check
GET /health

# Start a scan
POST /scan
{
  "target": "192.168.1.1",
  "safe_mode": true
}

# Get scan status
GET /scan/{scan_id}

# Generate report
GET /report/{scan_id}
```

## Testing

### Run Tests
```bash
# Install development dependencies
python -m pip install pytest pytest-asyncio --user

# Run tests
python -m pytest

# Run specific test files
python -m pytest tests/test_smoke.py
python -m pytest tests/test_e2e.py
```

### Test Coverage
- Unit tests for core functionality
- Integration tests for scanning tools
- API endpoint testing
- Report generation validation

## Project Structure

```
evolve-netscan/
├── app/
│   ├── api/                 # REST API implementation
│   ├── core/               # Core functionality (CLI, database)
│   ├── report/             # Report generation
│   ├── scans/              # Scanning modules
│   ├── ui/                 # Web interface templates
│   └── utils/              # Utility functions
├── runs/                   # Scan output directory
├── reports/                # Generated reports
├── requirements.txt        # Python dependencies
├── setup.py               # Package setup
├── README.md              # This file
└── LICENSE                # MIT License
```

## Contributing

We welcome contributions! Please see our [Contributing Guidelines](CONTRIBUTING.md) for details.

### Development Setup
```bash
# Navigate to project directory
cd evolve-netscan

# Create virtual environment (optional but recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode
python -m pip install -e . --user

# Install development dependencies
python -m pip install pytest pytest-asyncio black flake8 --user

# Run tests
python -m pytest
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Troubleshooting

### Common Installation Issues

#### Command not found after installation
```bash
# Solution 1: Restart terminal and try again
# Solution 2: Add to PATH manually
export PATH="$HOME/.local/bin:$PATH"
source ~/.bashrc

# Solution 3: Use module form
python -m app.core.cli --help
```

#### Cairo dependency errors (Linux)
```bash
# Install system dependencies
sudo apt install libcairo2-dev libpango1.0-dev pkg-config python3-dev build-essential

# On CentOS/RHEL
sudo yum install cairo-devel pango-devel pkgconfig python3-devel gcc
```

#### Permission errors
```bash
# Use --user flag
python -m pip install -e . --user

# Or create virtual environment
python -m venv venv
source venv/bin/activate
pip install -e .
```

#### Module import errors
```bash
# Ensure you're in the correct directory
cd evolve-netscan

# Check Python path
python -c "import sys; print(sys.path)"

# Try running directly
python -m app.core.cli --help
```

### Getting Help

If you encounter issues:
1. Check the [KALI_INSTALL.md](KALI_INSTALL.md) for Kali Linux specific instructions
2. Run the test script: `./test_kali_install.sh`
3. Use the module form: `python -m app.core.cli --help`
4. Check that all system dependencies are installed

## Legal Disclaimer

**IMPORTANT**: This tool is for authorized penetration testing and security research only. Users are responsible for:

- Obtaining proper written authorization before scanning any target
- Complying with all applicable laws and regulations
- Using the tool responsibly and ethically
- Respecting system resources and network bandwidth

The authors and contributors are not responsible for any misuse of this tool.

## Tools Used
- **Nmap**: Network discovery and security auditing
- **Nuclei**: Vulnerability scanner with community templates
- **SSLyze**: Fast SSL/TLS configuration analyzer
- **WhatWeb**: Web technology identifier
- **FastAPI**: Modern web framework for building APIs
- **Typer**: Great developer experience for CLI applications



