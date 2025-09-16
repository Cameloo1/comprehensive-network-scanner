# Deployment Guide

This guide provides comprehensive instructions for deploying NetScan in various environments.

## 📋 Prerequisites

### System Requirements
- **Python**: 3.8 or higher
- **Operating System**: Windows, macOS, or Linux
- **Memory**: Minimum 2GB RAM (4GB+ recommended for large scans)
- **Storage**: 500MB free space for installation and scan results

### External Tools (Optional)
- **Nmap**: For advanced port scanning and service enumeration
- **Nuclei**: For safe vulnerability scanning with timeout protection
- **WhatWeb**: For web application fingerprinting (Python fallback included)
- **SSLyze**: For comprehensive TLS/SSL configuration analysis
- **TestSSL**: For additional SSL/TLS testing and cipher analysis

## 🔧 Installation Methods

### Method 1: Quick Install (Recommended)

#### Windows
```bash
# Clone the repository
git clone https://github.com/yourusername/netscan.git
cd netscan

# Run the Windows installer
install.bat
```

#### Linux/macOS
```bash
# Clone the repository
git clone https://github.com/yourusername/netscan.git
cd netscan

# Make installer executable and run
chmod +x install.sh
./install.sh
```

### Method 2: Manual Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/netscan.git
cd netscan

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install the package
pip install -e .
```

### Method 3: Direct pip Install

```bash
pip install git+https://github.com/yourusername/netscan.git
```

## 🌐 Production Deployment

### Docker Deployment

Create a `Dockerfile`:
```dockerfile
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    nmap \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Install the application
RUN pip install -e .

# Create necessary directories
RUN mkdir -p runs reports

# Expose API port
EXPOSE 8000

# Set default command
CMD ["python", "-m", "app.api.server"]
```

Build and run:
```bash
# Build the image
docker build -t netscan .

# Run the container
docker run -p 8000:8000 -v $(pwd)/data:/app/data netscan
```

### Cloud Deployment

#### AWS EC2
1. **Launch EC2 Instance**
   - AMI: Ubuntu 20.04 LTS
   - Instance Type: t3.medium or larger
   - Security Group: Allow SSH (22) and HTTP (8000)

2. **Install Dependencies**
   ```bash
   sudo apt update
   sudo apt install python3-pip git nmap
   ```

3. **Deploy Application**
   ```bash
   git clone https://github.com/yourusername/netscan.git
   cd netscan
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   pip install -e .
   ```

4. **Configure Systemd Service**
   ```bash
   sudo nano /etc/systemd/system/netscan.service
   ```
   ```ini
   [Unit]
   Description=Evolve NetScan API Server
   After=network.target

   [Service]
   Type=simple
   User=ubuntu
   WorkingDirectory=/home/ubuntu/netscan
   Environment=PATH=/home/ubuntu/netscan/venv/bin
   ExecStart=/home/ubuntu/netscan/venv/bin/python -m app.api.server
   Restart=always

   [Install]
   WantedBy=multi-user.target
   ```

5. **Start Service**
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable netscan
   sudo systemctl start netscan
   ```

#### Google Cloud Platform
1. **Create VM Instance**
   - Machine Type: e2-medium or larger
   - Boot Disk: Ubuntu 20.04 LTS
   - Firewall: Allow HTTP and HTTPS traffic

2. **Deploy using Cloud Shell**
   ```bash
   # Connect to your instance
   gcloud compute ssh your-instance-name

   # Follow the same installation steps as AWS
   ```

#### Azure
1. **Create Virtual Machine**
   - Image: Ubuntu Server 20.04 LTS
   - Size: Standard_B2s or larger
   - Network: Allow inbound port 8000

2. **Deploy Application**
   ```bash
   # SSH into the VM
   ssh azureuser@your-vm-ip

   # Follow standard installation process
   ```

## 🔧 Configuration

### Environment Variables
```bash
# Database configuration
export NETSAN_DB_PATH=/opt/netscan/data/netscan.db

# Default settings
export NETSAN_DEFAULT_WORKERS=8
export NETSAN_SAFE_MODE=true
export NETSAN_MAX_SCAN_TIME=3600

# API configuration
export NETSAN_API_HOST=0.0.0.0
export NETSAN_API_PORT=8000
export NETSAN_API_WORKERS=4
```

### Configuration File
Create `config.yaml`:
```yaml
database:
  path: "/opt/netscan/data/netscan.db"
  backup_interval: 86400  # 24 hours

scanning:
  default_workers: 8
  max_workers: 32
  safe_mode: true
  max_scan_time: 3600
  timeout_protection: true

api:
  host: "0.0.0.0"
  port: 8000
  workers: 4
  cors_origins: ["*"]

reporting:
  default_format: "html"
  include_pdf: true
  template_path: "app/ui/templates"
  
# Comprehensive Report Features
# - Port scan results with detailed state information
# - WHOIS data with network ownership details
# - Web application fingerprinting and technology detection
# - TLS/SSL analysis with certificate validation
# - Vulnerability findings with source attribution
# - Professional HTML and PDF formatting
```

## 🔒 Security Considerations

### Network Security
- Use HTTPS in production
- Implement proper firewall rules
- Restrict API access to authorized networks
- Use VPN for remote access

### Authentication
```python
# Add to app/api/server.py
from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer

security = HTTPBearer()

async def verify_token(token: str = Depends(security)):
    if token.credentials != "your-secret-token":
        raise HTTPException(status_code=401, detail="Invalid token")
    return token
```

### Data Protection
- Encrypt sensitive scan results
- Implement data retention policies
- Regular database backups
- Secure credential storage

## 📊 Monitoring and Logging

### Logging Configuration
```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('netscan.log'),
        logging.StreamHandler()
    ]
)
```

### Health Checks
```bash
# Check API health
curl http://localhost:8000/health

# Check scan queue
curl http://localhost:8000/scans/status
```

### Monitoring with Prometheus
```python
from prometheus_client import Counter, Histogram, generate_latest

scan_counter = Counter('netscan_scans_total', 'Total number of scans')
scan_duration = Histogram('netscan_scan_duration_seconds', 'Scan duration')

@app.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type="text/plain")
```

## 🔄 Backup and Recovery

### Database Backup
```bash
# Create backup script
#!/bin/bash
BACKUP_DIR="/opt/netscan/backups"
DB_PATH="/opt/netscan/data/netscan.db"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR
sqlite3 $DB_PATH ".backup $BACKUP_DIR/netscan_$DATE.db"
```

### Automated Backups
```bash
# Add to crontab
0 2 * * * /opt/netscan/scripts/backup.sh
```

### Recovery Process
```bash
# Restore from backup
sqlite3 /opt/netscan/data/netscan.db < backup_file.sql
```

## 🚀 Performance Optimization

### Scaling Options
- **Horizontal Scaling**: Multiple API instances behind load balancer
- **Vertical Scaling**: Increase CPU/memory resources
- **Database Optimization**: Use PostgreSQL for high-volume deployments
- **Caching**: Implement Redis for scan result caching

### Load Balancer Configuration (Nginx)
```nginx
upstream evolve_netscan {
    server 127.0.0.1:8000;
    server 127.0.0.1:8001;
    server 127.0.0.1:8002;
}

server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://evolve_netscan;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## 🔧 Troubleshooting

### Common Issues

#### Installation Issues
```bash
# Permission errors
sudo chown -R $USER:$USER /opt/netscan

# Missing dependencies
pip install --upgrade pip setuptools wheel
```

#### Runtime Issues
```bash
# Check logs
tail -f netscan.log

# Verify installation
python -c "import app.core.cli; print('OK')"

# Test basic functionality
netscan help
```

#### Performance Issues
```bash
# Monitor resource usage
htop
iotop

# Check database size
du -h netscan.db

# Optimize database
sqlite3 netscan.db "VACUUM;"
```

### Support
- **Documentation**: Check README.md and inline help
- **Issues**: Report on GitHub Issues
- **Community**: GitHub Discussions
- **Email**: security@evolve.com

## 📈 Scaling Guidelines

### Small Deployment (1-10 users)
- Single server with 2-4 CPU cores
- 4-8GB RAM
- Local SQLite database
- Basic monitoring

### Medium Deployment (10-100 users)
- Load balancer with 2-3 API servers
- 8-16 CPU cores per server
- 16-32GB RAM per server
- PostgreSQL database
- Comprehensive monitoring

### Large Deployment (100+ users)
- Multi-region deployment
- Kubernetes orchestration
- Microservices architecture
- Distributed database
- Advanced monitoring and alerting

---

**Remember**: Always test deployments in a staging environment before production!
