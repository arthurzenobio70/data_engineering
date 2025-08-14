# Contributing to Stock Market Data Pipeline

Thank you for your interest in contributing to this project! This document provides guidelines for contributing to the Stock Market Data Pipeline.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Workflow](#development-workflow)
- [Coding Standards](#coding-standards)
- [Testing Guidelines](#testing-guidelines)
- [Documentation](#documentation)
- [Pull Request Process](#pull-request-process)
- [Release Process](#release-process)

## Code of Conduct

This project adheres to a code of conduct adapted from the [Contributor Covenant](https://www.contributor-covenant.org/). By participating, you are expected to uphold this code.

### Our Standards

- Use welcoming and inclusive language
- Be respectful of differing viewpoints and experiences
- Gracefully accept constructive criticism
- Focus on what is best for the community
- Show empathy towards other community members

## Getting Started

### Prerequisites

Before contributing, ensure you have:

1. **Python 3.11+** installed
2. **uv** package manager (recommended) or pip
3. **Docker** and Docker Compose
4. **Git** for version control
5. **Make** for automation (optional but recommended)

### Development Setup

1. **Fork and Clone**
   ```bash
   git clone https://github.com/your-username/stock-market-pipeline.git
   cd stock-market-pipeline
   ```

2. **Set Up Development Environment**
   ```bash
   make dev-setup
   ```
   This will:
   - Install development dependencies
   - Set up pre-commit hooks
   - Configure the environment

3. **Verify Setup**
   ```bash
   make check
   make test
   ```

### Development Tools

The project uses several tools to maintain code quality:

- **uv**: Fast Python package management
- **black**: Code formatting
- **ruff**: Linting and code analysis
- **mypy**: Type checking
- **pytest**: Testing framework
- **pre-commit**: Git hooks for code quality

## Development Workflow

### 1. Create a Feature Branch

```bash
git checkout -b feature/your-feature-name
# or
git checkout -b bugfix/issue-description
```

### 2. Make Changes

Follow the coding standards and add tests for new functionality.

### 3. Run Quality Checks

```bash
# Format code
make format

# Run linting
make lint

# Type checking
make type-check

# Run tests
make test

# All checks
make validate
```

### 4. Commit Changes

The project uses conventional commit messages:

```bash
git add .
git commit -m "feat: add new stock data validator"
# or
git commit -m "fix: resolve date parsing issue in transformer"
# or
git commit -m "docs: update deployment guide"
```

### Commit Message Types

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

### 5. Push and Create Pull Request

```bash
git push origin feature/your-feature-name
```

Then create a pull request through GitHub.

## Coding Standards

### Python Code Style

The project follows PEP 8 with these specific guidelines:

1. **Line Length**: Maximum 88 characters (configured in black)
2. **Imports**: Use absolute imports, group by standard library, third-party, local
3. **Type Hints**: All functions must have type hints
4. **Docstrings**: All modules, classes, and functions must have docstrings

### Code Structure

```python
"""Module docstring describing the purpose."""

import os
import sys
from typing import Dict, List, Optional

import pandas as pd
from google.cloud import storage

from src.config.settings import Config


class ExampleClass:
    """Class docstring describing the class purpose."""
    
    def __init__(self, config: Config) -> None:
        """Initialize the class.
        
        Args:
            config: Configuration object
        """
        self.config = config
    
    def process_data(self, data: List[Dict]) -> pd.DataFrame:
        """Process input data and return DataFrame.
        
        Args:
            data: List of dictionaries containing raw data
            
        Returns:
            Processed data as pandas DataFrame
            
        Raises:
            ValueError: If data is empty or invalid
        """
        if not data:
            raise ValueError("Data cannot be empty")
        
        # Processing logic here
        return pd.DataFrame(data)
```

### Configuration Management

- Use the centralized configuration system in `src/config/settings.py`
- Environment variables should be documented
- Default values should be provided where appropriate
- Validate configuration on startup

### Error Handling

```python
import logging

logger = logging.getLogger(__name__)

def risky_operation() -> Optional[str]:
    """Example of proper error handling."""
    try:
        # Risky operation
        result = perform_operation()
        return result
    except SpecificException as e:
        logger.error(f"Operation failed: {e}")
        return None
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        raise
```

### Logging

- Use structured logging with appropriate levels
- Include contextual information
- No sensitive data in logs
- Use logger names based on module names

## Testing Guidelines

### Test Structure

Tests are organized in the `tests/` directory:

```
tests/
├── unit/           # Unit tests
├── integration/    # Integration tests
├── fixtures/       # Test data and fixtures
└── conftest.py     # Pytest configuration
```

### Writing Tests

```python
"""Test module docstring."""

import pytest
from unittest.mock import Mock, patch

from src.extractors.yahoo_finance import YahooFinanceExtractor


class TestYahooFinanceExtractor:
    """Test class for YahooFinanceExtractor."""
    
    def test_extract_single_stock_success(self):
        """Test successful stock data extraction."""
        # Arrange
        extractor = YahooFinanceExtractor("test-bucket")
        
        # Act
        result = extractor.extract_single_stock("AAPL", "2024-01-01")
        
        # Assert
        assert result is True
    
    @patch('src.extractors.yahoo_finance.yf.Ticker')
    def test_extract_single_stock_no_data(self, mock_ticker):
        """Test extraction when no data is available."""
        # Arrange
        mock_ticker.return_value.history.return_value.empty = True
        extractor = YahooFinanceExtractor("test-bucket")
        
        # Act
        result = extractor.extract_single_stock("INVALID", "2024-01-01")
        
        # Assert
        assert result is False
```

### Test Categories

1. **Unit Tests**: Test individual functions/methods
2. **Integration Tests**: Test component interactions
3. **System Tests**: Test end-to-end workflows
4. **Performance Tests**: Test performance characteristics

### Running Tests

```bash
# All tests
make test

# Specific test file
uv run pytest tests/test_config.py -v

# With coverage
uv run pytest --cov=src --cov-report=html

# Integration tests only
uv run pytest tests/integration/ -v

# Skip slow tests
uv run pytest -m "not slow"
```

## Documentation

### Types of Documentation

1. **Code Documentation**: Docstrings, type hints, comments
2. **API Documentation**: Auto-generated from docstrings
3. **User Documentation**: README, deployment guides
4. **Architecture Documentation**: High-level design docs

### Documentation Standards

- All public APIs must be documented
- Examples should be provided for complex functions
- Keep documentation up-to-date with code changes
- Use clear, concise language

### Building Documentation

```bash
# Generate API documentation
uv run sphinx-build -b html docs/ docs/_build/

# Serve documentation locally
cd docs/_build && python -m http.server 8000
```

## Pull Request Process

### Before Submitting

1. Ensure all tests pass locally
2. Update documentation if needed
3. Add tests for new functionality
4. Follow the commit message conventions
5. Rebase on the latest main branch

### PR Template

When creating a pull request, include:

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] Manual testing performed

## Checklist
- [ ] Code follows project style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] Tests pass locally
```

### Review Process

1. **Automated Checks**: CI/CD pipeline runs automatically
2. **Code Review**: At least one maintainer must approve
3. **Testing**: All tests must pass
4. **Documentation**: Documentation must be updated if needed

### Merging

- Use "Squash and merge" for feature branches
- Use "Merge commit" for important milestones
- Delete feature branches after merging

## Release Process

### Versioning

The project follows [Semantic Versioning](https://semver.org/):

- **MAJOR**: Breaking changes
- **MINOR**: New features (backward compatible)
- **PATCH**: Bug fixes (backward compatible)

### Release Steps

1. **Update Version**
   ```bash
   # Update version in pyproject.toml
   # Create release notes
   ```

2. **Tag Release**
   ```bash
   git tag -a v1.0.0 -m "Release version 1.0.0"
   git push origin v1.0.0
   ```

3. **Create Release**
   - Create GitHub release
   - Include changelog
   - Attach release artifacts

## Infrastructure Changes

### Terraform Changes

1. **Test Locally**
   ```bash
   make tf-plan
   ```

2. **Validate**
   ```bash
   terraform validate
   terraform fmt -check
   ```

3. **Document Changes**
   - Update variable descriptions
   - Update outputs documentation
   - Update deployment guide if needed

### DAG Changes

1. **Test Syntax**
   ```bash
   python -m py_compile dags/your_dag.py
   ```

2. **Test Logic**
   - Use Airflow test commands
   - Test in development environment
   - Validate dependencies

## Getting Help

### Communication Channels

- **GitHub Issues**: Bug reports and feature requests
- **GitHub Discussions**: Questions and general discussion
- **Email**: For sensitive security issues

### Resources

- [Project Documentation](README.md)
- [Architecture Guide](ARCHITECTURE.md)
- [Deployment Guide](DEPLOYMENT.md)
- [Issue Templates](.github/ISSUE_TEMPLATE/)

## Recognition

Contributors will be recognized in:

- GitHub contributors list
- Release notes
- Project documentation

Thank you for contributing to the Stock Market Data Pipeline! 🚀
