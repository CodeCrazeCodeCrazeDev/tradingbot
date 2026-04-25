# Contributing to AlphaAlgo Trading Bot

Thank you for your interest in contributing to AlphaAlgo! This document provides guidelines and instructions for contributing.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [How to Contribute](#how-to-contribute)
- [Pull Request Process](#pull-request-process)
- [Coding Standards](#coding-standards)
- [Testing Guidelines](#testing-guidelines)
- [Documentation](#documentation)

## Code of Conduct

Please read and follow our [Code of Conduct](CODE_OF_CONDUCT.md) to maintain a welcoming and inclusive community.

## Getting Started

### Prerequisites

- Python 3.10 or higher
- Git
- Docker (optional, for containerized development)
- PostgreSQL (for database features)
- Redis (for caching features)

### Fork and Clone

1. Fork the repository on GitHub
2. Clone your fork locally:
   ```bash
   git clone https://github.com/YOUR_USERNAME/trading-bot.git
   cd trading-bot
   ```
3. Add the upstream repository:
   ```bash
   git remote add upstream https://github.com/alphaalgo/trading-bot.git
   ```

## Development Setup

### Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate (Windows)
.\venv\Scripts\activate

# Activate (Linux/Mac)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

### Pre-commit Hooks

We use pre-commit hooks to ensure code quality:

```bash
pip install pre-commit
pre-commit install
```

### Environment Variables

Copy the example environment file:

```bash
cp .env.template .env
```

Edit `.env` with your configuration.

## How to Contribute

### Reporting Bugs

1. Check existing issues to avoid duplicates
2. Use the bug report template
3. Include:
   - Python version
   - Operating system
   - Steps to reproduce
   - Expected vs actual behavior
   - Error messages and stack traces

### Suggesting Features

1. Check existing feature requests
2. Use the feature request template
3. Describe the use case and benefits
4. Consider implementation complexity

### Contributing Code

1. **Find an issue** to work on or create one
2. **Comment** on the issue to claim it
3. **Create a branch** from `develop`:
   ```bash
   git checkout develop
   git pull upstream develop
   git checkout -b feature/your-feature-name
   ```
4. **Make changes** following our coding standards
5. **Write tests** for new functionality
6. **Update documentation** as needed
7. **Submit a pull request**

## Pull Request Process

### Before Submitting

- [ ] Code follows project style guidelines
- [ ] All tests pass locally
- [ ] New tests added for new features
- [ ] Documentation updated
- [ ] Commit messages are clear and descriptive
- [ ] Branch is up to date with `develop`

### PR Guidelines

1. **Title**: Clear, concise description of changes
2. **Description**: 
   - What changes were made
   - Why changes were needed
   - How to test the changes
3. **Link related issues**: Use `Fixes #123` or `Relates to #123`

### Review Process

1. Automated checks must pass
2. At least one maintainer approval required
3. Address review feedback promptly
4. Squash commits before merge if requested

## Coding Standards

### Python Style

We follow PEP 8 with some modifications:

```python
# Maximum line length: 120 characters
# Use 4 spaces for indentation
# Use type hints for function signatures

def calculate_position_size(
    account_balance: float,
    risk_percentage: float,
    stop_loss_pips: int
) -> float:
    """
    Calculate position size based on risk parameters.
    
    Args:
        account_balance: Current account balance in USD
        risk_percentage: Maximum risk per trade (0-100)
        stop_loss_pips: Stop loss distance in pips
    
    Returns:
        Position size in lots
    
    Raises:
        ValueError: If parameters are invalid
    """
    if risk_percentage <= 0 or risk_percentage > 100:
        raise ValueError("Risk percentage must be between 0 and 100")
    
    risk_amount = account_balance * (risk_percentage / 100)
    position_size = risk_amount / (stop_loss_pips * 10)
    
    return round(position_size, 2)
```

### Imports

```python
# Standard library imports
import asyncio
import logging
from typing import Dict, List, Optional

# Third-party imports
import numpy as np
import pandas as pd

# Local imports
from trading_bot.brokers import BrokerAdapter
from trading_bot.risk import RiskManager
```

### Naming Conventions

- **Classes**: `PascalCase` (e.g., `OrderManager`)
- **Functions/Methods**: `snake_case` (e.g., `calculate_pnl`)
- **Constants**: `UPPER_SNAKE_CASE` (e.g., `MAX_POSITION_SIZE`)
- **Private**: Prefix with underscore (e.g., `_internal_method`)

### Docstrings

Use Google-style docstrings:

```python
def process_signal(
    signal: Dict[str, Any],
    validate: bool = True
) -> Optional[Order]:
    """
    Process a trading signal and generate an order.
    
    Args:
        signal: Signal dictionary containing direction, symbol, etc.
        validate: Whether to validate the signal before processing.
    
    Returns:
        Order object if signal is valid, None otherwise.
    
    Raises:
        SignalValidationError: If signal validation fails.
    
    Example:
        >>> signal = {'symbol': 'EURUSD', 'direction': 'buy'}
        >>> order = process_signal(signal)
    """
```

## Testing Guidelines

### Test Structure

```
tests/
├── unit/                 # Unit tests
│   ├── test_brokers.py
│   ├── test_risk.py
│   └── test_signals.py
├── integration/          # Integration tests
│   ├── test_broker_integration.py
│   └── test_database.py
├── e2e/                  # End-to-end tests
│   └── test_trading_cycle.py
└── conftest.py           # Shared fixtures
```

### Writing Tests

```python
import pytest
from trading_bot.risk import RiskManager

class TestRiskManager:
    """Tests for RiskManager class."""
    
    @pytest.fixture
    def risk_manager(self):
        """Create RiskManager instance for testing."""
        return RiskManager(max_risk_per_trade=2.0)
    
    def test_calculate_position_size(self, risk_manager):
        """Test position size calculation."""
        size = risk_manager.calculate_position_size(
            account_balance=10000,
            stop_loss_pips=50
        )
        assert size > 0
        assert size <= 1.0  # Max 1 lot
    
    @pytest.mark.asyncio
    async def test_async_risk_check(self, risk_manager):
        """Test async risk validation."""
        result = await risk_manager.validate_trade(
            symbol='EURUSD',
            size=0.1
        )
        assert result.is_valid
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=trading_bot --cov-report=html

# Run specific test file
pytest tests/unit/test_risk.py

# Run tests matching pattern
pytest -k "test_position"

# Run with verbose output
pytest -v
```

### Test Coverage

- Aim for >80% code coverage
- Critical paths (trading, risk) should have >95% coverage
- All new features must include tests

## Documentation

### Code Documentation

- All public functions/classes must have docstrings
- Complex algorithms should include inline comments
- Update README.md for significant changes

### API Documentation

- Document all REST endpoints
- Include request/response examples
- Update OpenAPI spec for API changes

### User Documentation

- Update user guides for new features
- Include screenshots where helpful
- Keep examples up to date

## Questions?

- Open a [Discussion](https://github.com/alphaalgo/trading-bot/discussions)
- Join our [Discord](https://discord.gg/alphaalgo)
- Email: contributors@alphaalgo.com

Thank you for contributing! 🚀
