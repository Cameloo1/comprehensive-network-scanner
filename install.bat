@echo off
REM Evolve NetScan Installation Script for Windows
REM This script installs Evolve NetScan and its dependencies

echo 🔍 Evolve NetScan Installation Script
echo =====================================

REM Check Python version
echo 📋 Checking Python version...
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python not found. Please install Python 3.8+ first.
    pause
    exit /b 1
)

for /f "tokens=2" %%i in ('python --version 2^>^&1') do set python_version=%%i
echo ✅ Python %python_version% detected

REM Check if pip is available
echo 📋 Checking pip...
python -m pip --version >nul 2>&1
if errorlevel 1 (
    echo ❌ pip not found. Please install pip first.
    pause
    exit /b 1
)
echo ✅ pip found

REM Create virtual environment
echo 📋 Creating virtual environment...
if not exist "venv" (
    python -m venv venv
    echo ✅ Virtual environment created
) else (
    echo ✅ Virtual environment already exists
)

REM Activate virtual environment
echo 📋 Activating virtual environment...
call venv\Scripts\activate.bat
echo ✅ Virtual environment activated

REM Upgrade pip
echo 📋 Upgrading pip...
python -m pip install --upgrade pip
echo ✅ pip upgraded

REM Install dependencies
echo 📋 Installing dependencies...
if exist "requirements.txt" (
    python -m pip install -r requirements.txt
    echo ✅ Dependencies installed from requirements.txt
) else (
    echo ❌ requirements.txt not found
    pause
    exit /b 1
)

REM Install the package in development mode
echo 📋 Installing Evolve NetScan...
if exist "setup.py" (
    python -m pip install -e .
    echo ✅ Evolve NetScan installed in development mode
) else (
    echo ❌ setup.py not found
    pause
    exit /b 1
)

REM Check installation
echo 📋 Verifying installation...
python -c "import app.core.cli; print('✅ Core modules import successfully')" 2>nul
if errorlevel 1 (
    echo ❌ Installation verification failed
    pause
    exit /b 1
)
echo ✅ Basic functionality test passed

REM Create necessary directories
echo 📋 Creating necessary directories...
if not exist "runs" mkdir runs
if not exist "reports" mkdir reports
echo ✅ Directories created

echo.
echo 🎉 Installation completed successfully!
echo.
echo 📋 Next steps:
echo 1. Activate the virtual environment: venv\Scripts\activate.bat
echo 2. Run a test scan: netscan scan 127.0.0.1 --safe
echo 3. Get help: netscan help
echo.
echo 📚 Documentation:
echo - README.md: Complete usage guide
echo - CONTRIBUTING.md: Development guidelines
echo - GitHub: https://github.com/yourusername/evolve-netscan
echo.
echo ⚠️  Important:
echo - Always obtain proper authorization before scanning targets
echo - Use safe mode for production environments
echo - Review the legal disclaimer in README.md
echo.
echo Happy scanning! 🔍
pause
