# =============================================================================
# TRADING BOT - MAKEFILE
# =============================================================================
# Development convenience commands
# Usage: make <command>
# =============================================================================

.PHONY: help install install-dev test test-unit test-integration test-coverage lint format clean docker-build docker-run setup pre-commit security profile docs

PYTHON := python
PIP := pip
PYTEST := pytest
BLACK := black
ISORT := isort
FLAKE8 := flake8
MYPY := mypy
BANDIT := bandit
SAFETY := safety

# Default target
help:
	@echo "Trading Bot Development Commands"
	@echo "================================"
	@echo ""
	@echo "Setup & Installation:"
	@echo "  make install         Install production dependencies"
	@echo "  make install-dev     Install development dependencies"
	@echo "  make setup           Full setup (install + dev + pre-commit)"
	@echo ""
	@echo "Testing:"
	@echo "  make test            Run all tests"
	@echo "  make test-unit       Run unit tests only"
	@echo "  make test-integration Run integration tests"
	@echo "  make test-system     Run system tests"
	@echo "  make test-coverage   Run tests with coverage report"
	@echo "  make test-smoke      Run smoke tests (fast)"
	@echo ""
	@echo "Code Quality:"
	@echo "  make lint            Run all linters"
	@echo "  make lint-black      Check code formatting"
	@echo "  make lint-isort      Check import sorting"
	@echo "  make lint-flake8     Run Flake8 linter"
	@echo "  make lint-mypy       Run MyPy type checker"
	@echo "  make format          Auto-format code (black + isort)"
	@echo ""
	@echo "Security:"
	@echo "  make security        Run security checks (bandit + safety)"
	@echo "  make bandit          Run Bandit security scan"
	@echo "  make safety          Check dependencies for CVEs"
	@echo ""
	@echo "Performance:"
	@echo "  make profile         Run performance profiling"
	@echo "  make benchmark       Run performance benchmarks"
	@echo ""
	@echo "Maintenance:"
	@echo "  make clean           Clean build artifacts and caches"
	@echo "  make pre-commit      Install and run pre-commit hooks"
	@echo "  make update          Update all dependencies"
	@echo ""
	@echo "Docker:"
	@echo "  make docker-build    Build Docker image"
	@echo "  make docker-run      Run Docker container"
	@echo "  make docker-test     Run tests in Docker"
	@echo ""
	@echo "Documentation:"
	@echo "  make docs            Build documentation"
	@echo "  make docs-serve      Serve documentation locally"
	@echo ""

# =============================================================================
# Setup & Installation
# =============================================================================

install:
	$(PIP) install -r requirements.txt

install-dev: install
	$(PIP) install -r requirements-dev.txt

setup: install-dev
	$(PYTHON) -m pre_commit install
	@echo "Setup complete! Run 'make test' to verify."

pre-commit:
	$(PYTHON) -m pre_commit install
	$(PYTHON) -m pre_commit run --all-files

update:
	$(PIP) install --upgrade -r requirements.txt
	$(PIP) install --upgrade -r requirements-dev.txt

# =============================================================================
# Testing
# =============================================================================

test:
	$(PYTEST) tests/ -v --timeout=180 -x

test-unit:
	$(PYTEST) -m "unit and not slow" -v --timeout=30 -n auto

test-integration:
	$(PYTEST) -m integration -v --timeout=300

test-system:
	$(PYTEST) -m system -v --timeout=300

test-coverage:
	$(PYTEST) tests/ -v --cov=trading_bot --cov-report=term-missing --cov-report=html --cov-report=xml --timeout=300

test-smoke:
	$(PYTEST) tests/smoke_tests.py -v --timeout=60

test-fast:
	$(PYTEST) -m "unit and not slow" -x --timeout=30 -n auto -q

test-parallel:
	$(PYTEST) tests/ -v --timeout=180 -n auto --dist=loadgroup

test-failed:
	$(PYTEST) --lf -v

# =============================================================================
# Code Quality
# =============================================================================

lint: lint-black lint-isort lint-flake8 lint-mypy
	@echo "All linting checks passed!"

lint-black:
	@echo "Checking Black formatting..."
	$(BLACK) --check --line-length=100 trading_bot/

lint-isort:
	@echo "Checking import sorting..."
	$(ISORT) --check-only --profile black trading_bot/

lint-flake8:
	@echo "Running Flake8..."
	$(FLAKE8) trading_bot/ --max-line-length=100 --extend-ignore=E203,W503

lint-mypy:
	@echo "Running MyPy..."
	$(MYPY) trading_bot/ --ignore-missing-imports

format:
	@echo "Formatting code with Black and isort..."
	$(BLACK) --line-length=100 trading_bot/
	$(ISORT) --profile black trading_bot/
	@echo "Formatting complete!"

format-check:
	@echo "Checking if code is formatted..."
	$(BLACK) --check --line-length=100 trading_bot/
	$(ISORT) --check-only --profile black trading_bot/

# =============================================================================
# Security
# =============================================================================

security: bandit safety
	@echo "Security checks complete!"

bandit:
	@echo "Running Bandit security scan..."
	$(BANDIT) -r trading_bot/ -ll -f txt

bandit-json:
	@echo "Running Bandit with JSON output..."
	$(BANDIT) -r trading_bot/ -ll -f json -o bandit-report.json

safety:
	@echo "Checking dependencies for known vulnerabilities..."
	$(SAFETY) check --json --output safety-report.json || true

# =============================================================================
# Performance
# =============================================================================

profile:
	@echo "Running performance profiling..."
	$(PYTHON) -m cProfile -o profile.stats -m pytest tests/ -x --timeout=60
	$(PYTHON) -c "import pstats; p = pstats.Stats('profile.stats'); p.sort_stats('cumulative'); p.print_stats(50)"

benchmark:
	$(PYTEST) -m performance --benchmark-only

memory-profile:
	@echo "Running memory profiling..."
	$(PYTHON) -m memory_profiler scripts/profile_memory.py

# =============================================================================
# Docker
# =============================================================================

docker-build:
	docker build -t trading-bot:latest .

docker-build-prod:
	docker build -f Dockerfile.production -t trading-bot:production .

docker-run:
	docker-compose up -d

docker-stop:
	docker-compose down

docker-test:
	docker-compose -f docker-compose.yml run --rm test

docker-logs:
	docker-compose logs -f trading-bot

# =============================================================================
# Documentation
# =============================================================================

docs:
	mkdocs build

docs-serve:
	mkdocs serve

docs-deploy:
	mkdocs gh-deploy

# =============================================================================
# Maintenance
# =============================================================================

clean:
	@echo "Cleaning build artifacts and caches..."
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .eggs/
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf coverage.xml
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	rm -rf __pycache__/
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.pyd" -delete
	find . -type f -name ".coverage" -delete
	find . -type f -name "profile.stats" -delete
	find . -type f -name "bandit-report.json" -delete
	find . -type f -name "safety-report.json" -delete
	@echo "Clean complete!"

clean-all: clean
	@echo "Removing virtual environment..."
	rm -rf venv/
	rm -rf .venv/

# =============================================================================
# CI/CD Helpers
# =============================================================================

ci-test:
	$(PYTEST) tests_new/ -v --cov=trading_bot --cov-report=xml --cov-report=term -m "unit or integration" --timeout=180

ci-lint:
	$(BLACK) --check --line-length=100 trading_bot/
	$(ISORT) --check-only --profile black trading_bot/
	$(FLAKE8) trading_bot/ --max-line-length=100 --extend-ignore=E203,W503
	$(MYPY) trading_bot/ --ignore-missing-imports

ci-security:
	$(BANDIT) -r trading_bot/ -ll
	$(SAFETY) check || true

# =============================================================================
# Trading Bot Specific
# =============================================================================

run:
	$(PYTHON) main.py

run-simulation:
	$(PYTHON) main.py --mode simulation --duration 3600 --max-trades 10

run-paper:
	$(PYTHON) main.py --mode paper

run-production:
	$(PYTHON) main.py --mode production

validate-config:
	$(PYTHON) -c "from trading_bot.config import validate_config; validate_config()"

check-health:
	$(PYTHON) -c "from trading_bot.health import check_health; check_health()"

# =============================================================================
# Build & Release
# =============================================================================

build:
	$(PYTHON) -m build

build-wheel:
	$(PYTHON) setup.py bdist_wheel

upload-test:
	twine upload --repository-url https://test.pypi.org/legacy/ dist/*

upload:
	twine upload dist/*
