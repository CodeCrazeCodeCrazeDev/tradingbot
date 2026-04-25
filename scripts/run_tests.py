#!/usr/bin/env python3
"""
Test Runner for Trading Bot
Provides convenient commands for running different test suites
"""

import argparse
import subprocess
import sys
from pathlib import Path
from typing import List, Optional


class Colors:
    """Terminal colors for output."""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'


def run_pytest(
    args: List[str],
    description: str,
    timeout: Optional[int] = None
) -> int:
    """Run pytest with given arguments."""
    print(f"\n{Colors.HEADER}{'='*60}{Colors.ENDC}")
    print(f"{Colors.BOLD}{description}{Colors.ENDC}")
    print(f"{Colors.HEADER}{'='*60}{Colors.ENDC}")
    
    cmd = ["pytest"] + args
    print(f"Running: {' '.join(cmd)}\n")
    
    try:
        result = subprocess.run(
            cmd,
            check=False,
            capture_output=False,
            text=True,
            timeout=timeout
        )
        
        if result.returncode == 0:
            print(f"\n{Colors.OKGREEN}✓ {description} passed!{Colors.ENDC}")
        else:
            print(f"\n{Colors.FAIL}✗ {description} failed (exit {result.returncode}){Colors.ENDC}")
        
        return result.returncode
        
    except subprocess.TimeoutExpired:
        print(f"\n{Colors.FAIL}✗ {description} timed out!{Colors.ENDC}")
        return 1
    except FileNotFoundError:
        print(f"\n{Colors.FAIL}✗ pytest not found. Run: pip install pytest{Colors.ENDC}")
        return 1
    except Exception as e:
        print(f"\n{Colors.FAIL}✗ Error: {e}{Colors.ENDC}")
        return 1


def run_unit_tests(fast: bool = True, parallel: bool = True) -> int:
    """Run unit tests only."""
    args = ["-m", "unit", "-v"]
    
    if fast:
        args.extend(["--timeout=30", "-x"])
    else:
        args.append("--timeout=180")
    
    if parallel:
        args.extend(["-n", "auto"])
    
    return run_pytest(args, "Unit Tests", timeout=600 if not fast else 300)


def run_integration_tests() -> int:
    """Run integration tests."""
    args = [
        "-m", "integration",
        "-v",
        "--timeout=300"
    ]
    return run_pytest(args, "Integration Tests", timeout=600)


def run_system_tests() -> int:
    """Run system tests."""
    args = [
        "-m", "system",
        "-v",
        "--timeout=300"
    ]
    return run_pytest(args, "System Tests", timeout=600)


def run_simulation_tests() -> int:
    """Run simulation tests."""
    args = [
        "-m", "simulation",
        "-v",
        "--timeout=600"
    ]
    return run_pytest(args, "Simulation Tests", timeout=1200)


def run_stress_tests() -> int:
    """Run stress tests."""
    args = [
        "-m", "stress",
        "-v",
        "--timeout=600"
    ]
    return run_pytest(args, "Stress Tests", timeout=1200)


def run_risk_tests() -> int:
    """Run risk management tests."""
    args = [
        "-m", "risk",
        "-v",
        "--timeout=300"
    ]
    return run_pytest(args, "Risk Tests", timeout=600)


def run_performance_tests() -> int:
    """Run performance tests."""
    args = [
        "-m", "performance",
        "-v",
        "--benchmark-only",
        "--timeout=300"
    ]
    return run_pytest(args, "Performance Tests", timeout=600)


def run_ml_tests() -> int:
    """Run ML-specific tests."""
    args = [
        "-m", "ml",
        "-v",
        "--timeout=180",
        "-n", "2"  # Limited parallelization for ML tests
    ]
    return run_pytest(args, "ML Tests", timeout=600)


def run_all_tests(coverage: bool = False) -> int:
    """Run all tests."""
    args = ["-v", "--timeout=300"]
    
    if coverage:
        args.extend([
            "--cov=trading_bot",
            "--cov-report=term-missing",
            "--cov-report=html",
            "--cov-report=xml"
        ])
    
    return run_pytest(args, "All Tests", timeout=1800)


def run_fast_tests() -> int:
    """Run fast tests only (unit + no slow)."""
    args = [
        "-m", "unit and not slow",
        "-v",
        "--timeout=30",
        "-n", "auto",
        "-x"
    ]
    return run_pytest(args, "Fast Tests", timeout=300)


def run_smoke_tests() -> int:
    """Run smoke tests."""
    args = [
        "tests/smoke_tests.py",
        "-v",
        "--timeout=60"
    ]
    return run_pytest(args, "Smoke Tests", timeout=120)


def run_failed_tests() -> int:
    """Re-run previously failed tests."""
    args = ["--lf", "-v"]
    return run_pytest(args, "Failed Tests", timeout=600)


def run_specific_test(test_path: str) -> int:
    """Run a specific test file or directory."""
    args = [test_path, "-v", "--timeout=180"]
    return run_pytest(args, f"Specific Test: {test_path}")


def run_coverage() -> int:
    """Run tests with coverage report."""
    args = [
        "-v",
        "--cov=trading_bot",
        "--cov-report=term-missing",
        "--cov-report=html",
        "--cov-report=xml",
        "--timeout=300"
    ]
    
    result = run_pytest(args, "Coverage Report", timeout=1800)
    
    # Print coverage summary
    print(f"\n{Colors.OKBLUE}Coverage Report Generated:{Colors.ENDC}")
    print(f"  - HTML: htmlcov/index.html")
    print(f"  - XML: coverage.xml")
    print(f"  - Terminal: See above")
    
    return result


def list_test_markers() -> None:
    """List all available test markers."""
    print(f"\n{Colors.BOLD}Available Test Markers:{Colors.ENDC}")
    print(f"{Colors.HEADER}{'='*60}{Colors.ENDC}")
    
    markers = [
        ("unit", "Fast unit tests (< 1s each)"),
        ("integration", "Component integration tests"),
        ("system", "Full system integration tests"),
        ("e2e", "End-to-end tests"),
        ("ml", "Machine learning model tests"),
        ("slow", "Tests requiring > 10s to run"),
        ("asyncio", "Async/await tests"),
        ("broker", "Tests requiring broker connection"),
        ("database", "Tests requiring database"),
        ("network", "Tests requiring network access"),
        ("performance", "Performance benchmark tests"),
        ("stress", "Stress and load tests"),
        ("risk", "Risk management tests"),
        ("simulation", "Paper trading and simulation tests"),
        ("security", "Security-related tests"),
    ]
    
    for marker, description in markers:
        print(f"  {Colors.OKCYAN}{marker:15}{Colors.ENDC} - {description}")
    
    print(f"\n{Colors.BOLD}Usage Examples:{Colors.ENDC}")
    print(f"  pytest -m unit          # Run unit tests only")
    print(f"  pytest -m 'not slow'    # Skip slow tests")
    print(f"  pytest -m 'unit and not slow'  # Fast unit tests")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Test Runner for Trading Bot",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s unit              # Run unit tests
  %(prog)s integration       # Run integration tests
  %(prog)s fast              # Run fast tests only
  %(prog)s coverage          # Run tests with coverage
  %(prog)s all               # Run all tests
  %(prog)s list-markers      # List available markers
        """
    )
    
    parser.add_argument(
        "command",
        choices=[
            "unit", "integration", "system", "simulation", "stress",
            "risk", "performance", "ml", "all", "fast", "smoke",
            "failed", "coverage", "list-markers", "specific"
        ],
        help="Test command to run"
    )
    
    parser.add_argument(
        "--slow",
        action="store_true",
        help="Include slow tests"
    )
    
    parser.add_argument(
        "--no-parallel",
        action="store_true",
        help="Disable parallel execution"
    )
    
    parser.add_argument(
        "--path",
        type=str,
        help="Path to specific test (for 'specific' command)"
    )
    
    args = parser.parse_args()
    
    # Check if pytest is available
    try:
        subprocess.run(["pytest", "--version"], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print(f"{Colors.FAIL}Error: pytest not found.{Colors.ENDC}")
        print(f"Install with: pip install pytest pytest-asyncio pytest-cov")
        return 1
    
    # Execute command
    if args.command == "unit":
        return run_unit_tests(fast=not args.slow, parallel=not args.no_parallel)
    
    elif args.command == "integration":
        return run_integration_tests()
    
    elif args.command == "system":
        return run_system_tests()
    
    elif args.command == "simulation":
        return run_simulation_tests()
    
    elif args.command == "stress":
        return run_stress_tests()
    
    elif args.command == "risk":
        return run_risk_tests()
    
    elif args.command == "performance":
        return run_performance_tests()
    
    elif args.command == "ml":
        return run_ml_tests()
    
    elif args.command == "all":
        return run_all_tests(coverage=False)
    
    elif args.command == "fast":
        return run_fast_tests()
    
    elif args.command == "smoke":
        return run_smoke_tests()
    
    elif args.command == "failed":
        return run_failed_tests()
    
    elif args.command == "coverage":
        return run_coverage()
    
    elif args.command == "list-markers":
        list_test_markers()
        return 0
    
    elif args.command == "specific":
        if not args.path:
            print(f"{Colors.FAIL}Error: --path required for 'specific' command{Colors.ENDC}")
            return 1
        return run_specific_test(args.path)
    
    return 1


if __name__ == "__main__":
    sys.exit(main())
