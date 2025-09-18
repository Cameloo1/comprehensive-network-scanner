#!/bin/bash

# Test script for Kali Linux installation
# This script tests the installation and basic functionality

set -e

echo "======================================"
echo "NetScan Kali Installation Test Script"
echo "======================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test functions
test_python_version() {
    echo -n "Testing Python version... "
    PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
    if (( $(echo "$PYTHON_VERSION >= 3.8" | bc -l) )); then
        echo -e "${GREEN}✓ Python $PYTHON_VERSION${NC}"
        return 0
    else
        echo -e "${RED}✗ Python $PYTHON_VERSION (requires >= 3.8)${NC}"
        return 1
    fi
}

test_system_dependencies() {
    echo "Testing system dependencies..."
    DEPS=("pkg-config" "python3-dev" "build-essential")
    
    for dep in "${DEPS[@]}"; do
        echo -n "  Checking $dep... "
        if dpkg -l | grep -q "^ii  $dep "; then
            echo -e "${GREEN}✓${NC}"
        else
            echo -e "${RED}✗ (install with: sudo apt install $dep)${NC}"
            return 1
        fi
    done
    
    # Check Cairo libraries
    echo -n "  Checking Cairo libraries... "
    if pkg-config --exists cairo; then
        echo -e "${GREEN}✓${NC}"
    else
        echo -e "${RED}✗ (install with: sudo apt install libcairo2-dev)${NC}"
        return 1
    fi
    
    return 0
}

test_pip_installation() {
    echo -n "Testing pip installation... "
    if python3 -m pip --version > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC}"
        return 0
    else
        echo -e "${RED}✗ (run: python3 -m ensurepip --user)${NC}"
        return 1
    fi
}

test_path_setup() {
    echo -n "Testing PATH setup... "
    if echo $PATH | grep -q "$HOME/.local/bin"; then
        echo -e "${GREEN}✓${NC}"
        return 0
    else
        echo -e "${YELLOW}⚠ ~/.local/bin not in PATH${NC}"
        echo "  Add to ~/.bashrc: export PATH=\"\$HOME/.local/bin:\$PATH\""
        return 1
    fi
}

test_package_installation() {
    echo -n "Testing package installation... "
    if python3 -c "import app.core.cli" > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC}"
        return 0
    else
        echo -e "${RED}✗ (run: python3 -m pip install -e . --user)${NC}"
        return 1
    fi
}

test_cli_command() {
    echo -n "Testing CLI command... "
    if command -v netscan > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC}"
        return 0
    else
        echo -e "${YELLOW}⚠ Command not found in PATH${NC}"
        echo "  Try: python3 -m app.core.cli --help"
        return 1
    fi
}

test_cli_functionality() {
    echo -n "Testing CLI functionality... "
    if python3 -m app.core.cli --help > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC}"
        return 0
    else
        echo -e "${RED}✗ CLI not working${NC}"
        return 1
    fi
}

test_dependencies() {
    echo "Testing Python dependencies..."
    DEPS=("typer" "fastapi" "sqlalchemy" "requests")
    
    for dep in "${DEPS[@]}"; do
        echo -n "  Checking $dep... "
        if python3 -c "import $dep" > /dev/null 2>&1; then
            echo -e "${GREEN}✓${NC}"
        else
            echo -e "${RED}✗${NC}"
            return 1
        fi
    done
    
    return 0
}

# Run all tests
TESTS_PASSED=0
TOTAL_TESTS=8

echo "Running installation tests..."
echo

test_python_version && ((TESTS_PASSED++)) || true
test_system_dependencies && ((TESTS_PASSED++)) || true
test_pip_installation && ((TESTS_PASSED++)) || true
test_path_setup && ((TESTS_PASSED++)) || true
test_package_installation && ((TESTS_PASSED++)) || true
test_cli_command && ((TESTS_PASSED++)) || true
test_cli_functionality && ((TESTS_PASSED++)) || true
test_dependencies && ((TESTS_PASSED++)) || true

echo
echo "======================================"
echo "Test Results: $TESTS_PASSED/$TOTAL_TESTS passed"

if [ $TESTS_PASSED -eq $TOTAL_TESTS ]; then
    echo -e "${GREEN}✓ All tests passed! Installation successful.${NC}"
    echo
    echo "Try running:"
    echo "  netscan --help"
    echo "  netscan scan 127.0.0.1 --safe"
    exit 0
else
    echo -e "${RED}✗ Some tests failed. Please fix the issues above.${NC}"
    echo
    echo "Quick fixes:"
    echo "1. Run the installation script: ./install_kali.sh"
    echo "2. Restart your terminal: source ~/.bashrc"
    echo "3. Install missing dependencies as shown above"
    exit 1
fi
