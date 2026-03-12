# Trading Bot - Testing & Code Quality Guide

## Overview
This guide covers comprehensive testing, debugging, code quality improvements, and maintenance practices for the trading bot.

## Table of Contents
1. [Unit Testing](#unit-testing)
2. [Integration Testing](#integration-testing)
3. [Edge Case Testing](#edge-case-testing)
4. [Automated Testing](#automated-testing)
5. [Debugging Tools](#debugging-tools)
6. [Code Quality](#code-quality)
7. [Performance Optimization](#performance-optimization)
8. [Version Control](#version-control)

---

## 1. Unit Testing

### Running Unit Tests
```bash
# Run all unit tests
py -m pytest tests/ -v

# Run specific test file
py -m pytest tests/test_risk_manager.py -v

# Run with coverage
py -m pytest tests/ --cov=trading_bot --cov-report=html

# Run tests in parallel
py -m pytest tests/ -n auto
```

### Test Structure
```
tests/
├── unit/                    # Unit tests for individual modules
│   ├── test_data/          # Data layer tests
│   ├── test_strategy/      # Strategy tests
│   ├── test_risk/          # Risk management tests
│   └── test_execution/     # Execution tests
├── integration/            # Integration tests
├── e2e/                    # End-to-end tests
└── performance/            # Performance benchmarks
```

### Writing Unit Tests
See `tests/unit/test_examples.py` for templates and best practices.

---

## 2. Integration Testing

### Test Scenarios
- Data → Strategy → Risk → Execution pipeline
- Multi-symbol trading coordination
- Safety system interactions
- ML model integration

### Running Integration Tests
```bash
py -m pytest tests/integration/ -v --tb=short
```

---

## 3. Edge Case Testing

### Critical Edge Cases
- Zero/negative prices
- Extreme volatility
- Network failures
- API rate limits
- Memory constraints
- Concurrent operations

### Stress Testing
```bash
py tests/stress_test_runner.py --duration 3600 --threads 10
```

---

## 4. Automated Testing

### CI/CD Pipeline
- Pre-commit hooks (see `.pre-commit-config.yaml`)
- GitHub Actions workflow (see `.github/workflows/ci.yml`)
- Automated test runs on push/PR

### Test Automation
```bash
# Run automated test suite
py run_automated_tests.py

# Run with different configurations
py run_automated_tests.py --config paper
py run_automated_tests.py --config live --dry-run
```

---

## 5. Debugging Tools

### Logging
- Structured logging with loguru
- Log levels: DEBUG, INFO, WARNING, ERROR, CRITICAL
- Log files in `logs/` directory

### Debugging Commands
```bash
# Run with debug logging
py main.py --log-level DEBUG

# Enable profiling
py main.py --profile

# Memory profiling
py -m memory_profiler main.py
```

### Debug Utilities
```python
from trading_bot.utils.debug_tools import (
    debug_trace,
    memory_snapshot,
    performance_profile
)

# Trace function execution
@debug_trace
def my_function():
    pass

# Take memory snapshot
memory_snapshot("checkpoint_1")

# Profile performance
with performance_profile("critical_section"):
    # code here
```

---

## 6. Code Quality

### Code Analysis
```bash
# Run linters
py -m flake8 trading_bot/
py -m pylint trading_bot/
py -m mypy trading_bot/

# Format code
py -m black trading_bot/
py -m isort trading_bot/

# Security scan
py -m bandit -r trading_bot/
```

### Code Metrics
```bash
# Complexity analysis
py -m radon cc trading_bot/ -a

# Maintainability index
py -m radon mi trading_bot/

# Code duplication
py -m pylint trading_bot/ --disable=all --enable=duplicate-code
```

### Refactoring Checklist
- [ ] Remove duplicate code
- [ ] Improve variable/function names
- [ ] Simplify complex logic
- [ ] Add type hints
- [ ] Update docstrings
- [ ] Remove unused imports
- [ ] Extract magic numbers to constants

---

## 7. Performance Optimization

### Profiling
```bash
# CPU profiling
py -m cProfile -o profile.stats main.py
py -m pstats profile.stats

# Line profiling
kernprof -l -v main.py

# Memory profiling
py -m memory_profiler main.py
```

### Performance Monitoring
```bash
# Run performance benchmarks
py tests/performance_benchmarks.py

# Monitor in real-time
py tools/performance_monitor.py
```

### Optimization Targets
- Reduce latency in execution path
- Optimize memory usage for large datasets
- Improve ML model inference speed
- Minimize database query overhead

---

## 8. Version Control

### Git Workflow
```bash
# Initialize repository
git init
git add .
git commit -m "Initial commit: Trading bot v1.0"

# Create feature branch
git checkout -b feature/new-strategy

# Commit with descriptive message
git commit -m "feat: Add momentum strategy with ML enhancement"

# Push to remote
git push origin feature/new-strategy
```

### Commit Message Format
```
<type>(<scope>): <subject>

<body>

<footer>
```

Types: feat, fix, docs, style, refactor, test, chore

### Git Hooks
Pre-commit hooks automatically run:
- Code formatting (black, isort)
- Linting (flake8, pylint)
- Type checking (mypy)
- Tests (pytest)

---

## Quick Reference

### Daily Development Workflow
1. Pull latest changes: `git pull origin main`
2. Create feature branch: `git checkout -b feature/name`
3. Write code with tests
4. Run tests: `py -m pytest tests/ -v`
5. Check code quality: `py -m flake8 trading_bot/`
6. Commit: `git commit -m "feat: description"`
7. Push: `git push origin feature/name`
8. Create PR for review

### Before Deployment
1. Run full test suite: `py run_automated_tests.py`
2. Check coverage: `py -m pytest --cov=trading_bot --cov-report=term-missing`
3. Run performance benchmarks: `py tests/performance_benchmarks.py`
4. Security scan: `py -m bandit -r trading_bot/`
5. Update documentation
6. Tag release: `git tag -a v1.0.0 -m "Release v1.0.0"`

### Troubleshooting
- Check logs in `logs/` directory
- Run with `--log-level DEBUG`
- Use `--profile` flag for performance issues
- Check `tests/test_system_health.py` for system diagnostics

---

## Additional Resources
- Test examples: `tests/unit/test_examples.py`
- Performance tools: `tools/performance_tools.py`
- Debug utilities: `trading_bot/utils/debug_tools.py`
- CI/CD config: `.github/workflows/ci.yml`
