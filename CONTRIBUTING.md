# Contributing to NetScan

Thank you for your interest in contributing to NetScan! This document provides guidelines and information for contributors.

## Getting Started

### Prerequisites
- Python 3.8 or higher
- Git
- Basic understanding of network security and penetration testing

### Development Setup

1. **Fork and Clone**
   ```bash
   git clone https://github.com/yourusername/evolve-netscan.git
   cd evolve-netscan
   ```

2. **Create Virtual Environment**
   ```bash
   python -m venv venv
   
   # On Windows
   venv\Scripts\activate
   
   # On macOS/Linux
   source venv/bin/activate
   ```

3. **Install Dependencies**
   ```bash
   pip install -e ".[dev]"
   ```

4. **Run Tests**
   ```bash
   pytest
   ```

## 📋 Contribution Guidelines

### Code Style
- Follow PEP 8 style guidelines
- Use Black for code formatting: `black .`
- Use Flake8 for linting: `flake8 .`
- Maximum line length: 88 characters

### Commit Messages
Use clear, descriptive commit messages:
```
feat: add new vulnerability scanner integration
fix: resolve timeout issue in SSLyze module
docs: update installation instructions
test: add unit tests for progress tracking
```

### Pull Request Process

1. **Create Feature Branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make Changes**
   - Write clean, documented code
   - Add tests for new functionality
   - Update documentation as needed

3. **Test Your Changes**
   ```bash
   pytest
   black .
   flake8 .
   ```

4. **Submit Pull Request**
   - Provide clear description of changes
   - Reference any related issues
   - Include screenshots for UI changes

## Testing

### Running Tests
```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_scanner.py

# Run with coverage
pytest --cov=app --cov-report=html
```

### Writing Tests
- Place tests in `tests/` directory
- Use descriptive test names
- Test both success and failure cases
- Mock external dependencies

Example test:
```python
def test_scan_single_ip():
    """Test scanning a single IP address."""
    result = scan_ip("127.0.0.1")
    assert result is not None
    assert "ports" in result
```

## Documentation

### Code Documentation
- Use docstrings for all functions and classes
- Follow Google docstring format
- Include type hints where appropriate

Example:
```python
def scan_target(target: str, safe_mode: bool = True) -> dict:
    """
    Scan a target IP address for vulnerabilities.
    
    Args:
        target: IP address or hostname to scan
        safe_mode: Enable safe mode for non-destructive scanning
        
    Returns:
        Dictionary containing scan results
        
    Raises:
        ValueError: If target is invalid
        TimeoutError: If scan times out
    """
```

### README Updates
- Update README.md for new features
- Include usage examples
- Update installation instructions if needed

## Bug Reports

### Before Submitting
1. Check existing issues
2. Test with latest version
3. Gather relevant information

### Bug Report Template
```markdown
**Bug Description**
Clear description of the bug

**Steps to Reproduce**
1. Step 1
2. Step 2
3. Step 3

**Expected Behavior**
What should happen

**Actual Behavior**
What actually happens

**Environment**
- OS: [e.g., Windows 10, Ubuntu 20.04]
- Python Version: [e.g., 3.9.7]
- Package Version: [e.g., 1.0.0]

**Additional Context**
Any other relevant information
```

## Feature Requests

### Before Submitting
1. Check existing feature requests
2. Consider security implications
3. Think about implementation complexity

### Feature Request Template
```markdown
**Feature Description**
Clear description of the feature

**Use Case**
Why is this feature needed?

**Proposed Solution**
How should this feature work?

**Alternatives Considered**
Other solutions you've considered

**Additional Context**
Any other relevant information
```

## Security

### Security Considerations
- All contributions must maintain security best practices
- New scanning modules must include timeout protection
- Avoid hardcoded credentials or sensitive information
- Follow responsible disclosure for security vulnerabilities

### Security Vulnerabilities
If you discover a security vulnerability, please:
1. **DO NOT** create a public issue
2. Email
3. Include detailed reproduction steps
4. Allow time for response before public disclosure

## 📋 Code Review Process

### Review Criteria
- Code quality and style
- Test coverage
- Documentation completeness
- Security considerations
- Performance impact

### Review Process
1. Automated checks (tests, linting)
2. Manual code review
3. Security review (if applicable)
4. Final approval and merge

## Release Process

### Version Numbering
We use [Semantic Versioning](https://semver.org/):
- **MAJOR**: Breaking changes
- **MINOR**: New features (backward compatible)
- **PATCH**: Bug fixes (backward compatible)

### Release Steps
1. Update version numbers
2. Update CHANGELOG.md
3. Create release tag
4. Build and test package
5. Publish to PyPI

## Community Guidelines

### Code of Conduct
- Be respectful and inclusive
- Focus on constructive feedback
- Help others learn and grow
- Follow the golden rule

### Getting Help
- Check documentation first
- Search existing issues
- Ask questions in discussions

## Recognition

Contributors will be:
- Listed in CONTRIBUTORS.md
- Mentioned in release notes
- Given credit in documentation

Thank you for contributing to NetScan!
