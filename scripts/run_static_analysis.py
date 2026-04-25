#!/usr/bin/env python3
"""
Static Analysis Runner for Trading Bot
Runs Black, isort, Flake8, MyPy, Bandit, and Safety checks
"""

import argparse
import subprocess
import sys
from pathlib import Path
from typing import List, Tuple


class Colors:
    """Terminal colors for output formatting."""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'


def run_command(cmd: List[str], description: str) -> Tuple[bool, str]:
    """Run a command and return success status and output."""
    print(f"\n{Colors.HEADER}{'='*60}{Colors.ENDC}")
    print(f"{Colors.BOLD}Running: {description}{Colors.ENDC}")
    print(f"{Colors.HEADER}{'='*60}{Colors.ENDC}")
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False
        )
        
        if result.stdout:
            print(result.stdout)
        
        if result.stderr:
            print(f"{Colors.WARNING}Stderr: {result.stderr}{Colors.ENDC}")
        
        success = result.returncode == 0
        
        if success:
            print(f"{Colors.OKGREEN}✓ {description} passed!{Colors.ENDC}")
        else:
            print(f"{Colors.FAIL}✗ {description} failed with exit code {result.returncode}{Colors.ENDC}")
        
        return success, result.stdout + result.stderr
        
    except FileNotFoundError as e:
        print(f"{Colors.FAIL}✗ Command not found: {e}{Colors.ENDC}")
        return False, str(e)
    except Exception as e:
        print(f"{Colors.FAIL}✗ Error running {description}: {e}{Colors.ENDC}")
        return False, str(e)


def check_black(target: str, check_only: bool = True) -> Tuple[bool, str]:
    """Run Black formatter check."""
    cmd = ["black", "--line-length", "100"]
    if check_only:
        cmd.append("--check")
    cmd.append(target)
    return run_command(cmd, "Black (code formatting)")


def check_isort(target: str, check_only: bool = True) -> Tuple[bool, str]:
    """Run isort check."""
    cmd = ["isort", "--profile", "black"]
    if check_only:
        cmd.append("--check-only")
    cmd.append(target)
    return run_command(cmd, "isort (import sorting)")


def check_flake8(target: str) -> Tuple[bool, str]:
    """Run Flake8 linter."""
    cmd = [
        "flake8",
        target,
        "--max-line-length=100",
        "--extend-ignore=E203,W503"
    ]
    return run_command(cmd, "Flake8 (linting)")


def check_mypy(target: str) -> Tuple[bool, str]:
    """Run MyPy type checker."""
    cmd = [
        "mypy",
        target,
        "--ignore-missing-imports"
    ]
    return run_command(cmd, "MyPy (type checking)")


def check_bandit(target: str) -> Tuple[bool, str]:
    """Run Bandit security scanner."""
    cmd = [
        "bandit",
        "-r",
        target,
        "-ll",
        "-f", "json",
        "-o", "bandit-report.json"
    ]
    return run_command(cmd, "Bandit (security scan)")


def check_safety() -> Tuple[bool, str]:
    """Run Safety dependency check."""
    cmd = [
        "safety",
        "check",
        "--json",
        "--output",
        "safety-report.json"
    ]
    success, output = run_command(cmd, "Safety (dependency check)")
    # Safety returns non-zero when vulnerabilities found, which is informational
    return True, output


def format_code(target: str) -> Tuple[bool, str]:
    """Auto-format code with Black and isort."""
    print(f"\n{Colors.HEADER}{'='*60}{Colors.ENDC}")
    print(f"{Colors.BOLD}Auto-formatting code...{Colors.ENDC}")
    print(f"{Colors.HEADER}{'='*60}{Colors.ENDC}")
    
    # Run Black
    black_cmd = ["black", "--line-length", "100", target]
    black_success, _ = run_command(black_cmd, "Black formatting")
    
    # Run isort
    isort_cmd = ["isort", "--profile", "black", target]
    isort_success, _ = run_command(isort_cmd, "isort formatting")
    
    return black_success and isort_success, ""


def run_all_checks(target: str, fail_fast: bool = False) -> int:
    """Run all static analysis checks."""
    checks = [
        ("Black", lambda: check_black(target)),
        ("isort", lambda: check_isort(target)),
        ("Flake8", lambda: check_flake8(target)),
        ("MyPy", lambda: check_mypy(target)),
        ("Bandit", lambda: check_bandit(target)),
        ("Safety", lambda: check_safety()),
    ]
    
    results = {}
    failed_checks = []
    
    for name, check_func in checks:
        try:
            success, output = check_func()
            results[name] = {"success": success, "output": output}
            
            if not success:
                failed_checks.append(name)
                if fail_fast:
                    break
        except Exception as e:
            results[name] = {"success": False, "output": str(e)}
            failed_checks.append(name)
            if fail_fast:
                break
    
    # Print summary
    print(f"\n{Colors.HEADER}{'='*60}{Colors.ENDC}")
    print(f"{Colors.BOLD}Static Analysis Summary{Colors.ENDC}")
    print(f"{Colors.HEADER}{'='*60}{Colors.ENDC}")
    
    for name, result in results.items():
        status = f"{Colors.OKGREEN}✓ PASS{Colors.ENDC}" if result["success"] else f"{Colors.FAIL}✗ FAIL{Colors.ENDC}"
        print(f"  {name}: {status}")
    
    print(f"{Colors.HEADER}{'='*60}{Colors.ENDC}")
    
    if failed_checks:
        print(f"\n{Colors.FAIL}Failed checks: {', '.join(failed_checks)}{Colors.ENDC}")
        return 1
    else:
        print(f"\n{Colors.OKGREEN}All checks passed! ✓{Colors.ENDC}")
        return 0


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Run static analysis checks on the trading bot codebase"
    )
    parser.add_argument(
        "target",
        nargs="?",
        default="trading_bot/",
        help="Target directory or file to check (default: trading_bot/)"
    )
    parser.add_argument(
        "--format", "-f",
        action="store_true",
        help="Auto-format code instead of just checking"
    )
    parser.add_argument(
        "--fail-fast",
        action="store_true",
        help="Stop on first failure"
    )
    parser.add_argument(
        "--black",
        action="store_true",
        help="Run only Black check"
    )
    parser.add_argument(
        "--isort",
        action="store_true",
        help="Run only isort check"
    )
    parser.add_argument(
        "--flake8",
        action="store_true",
        help="Run only Flake8 check"
    )
    parser.add_argument(
        "--mypy",
        action="store_true",
        help="Run only MyPy check"
    )
    parser.add_argument(
        "--bandit",
        action="store_true",
        help="Run only Bandit security check"
    )
    parser.add_argument(
        "--safety",
        action="store_true",
        help="Run only Safety dependency check"
    )
    
    args = parser.parse_args()
    
    # Check if any specific tool was requested
    specific_tools = [args.black, args.isort, args.flake8, args.mypy, args.bandit, args.safety]
    
    if args.format:
        success, _ = format_code(args.target)
        return 0 if success else 1
    
    if any(specific_tools):
        # Run only requested tools
        results = []
        
        if args.black:
            success, _ = check_black(args.target)
            results.append(("Black", success))
        
        if args.isort:
            success, _ = check_isort(args.target)
            results.append(("isort", success))
        
        if args.flake8:
            success, _ = check_flake8(args.target)
            results.append(("Flake8", success))
        
        if args.mypy:
            success, _ = check_mypy(args.target)
            results.append(("MyPy", success))
        
        if args.bandit:
            success, _ = check_bandit(args.target)
            results.append(("Bandit", success))
        
        if args.safety:
            success, _ = check_safety()
            results.append(("Safety", success))
        
        # Print results
        print(f"\n{Colors.HEADER}{'='*60}{Colors.ENDC}")
        for name, success in results:
            status = f"{Colors.OKGREEN}✓ PASS{Colors.ENDC}" if success else f"{Colors.FAIL}✗ FAIL{Colors.ENDC}"
            print(f"  {name}: {status}")
        print(f"{Colors.HEADER}{'='*60}{Colors.ENDC}")
        
        return 0 if all(success for _, success in results) else 1
    
    # Run all checks
    return run_all_checks(args.target, args.fail_fast)


if __name__ == "__main__":
    sys.exit(main())
