#!/usr/bin/env python3
"""
AlphaAlgo Deterministic Bootstrap Script

Automates:
1. Dependency verification
2. Creating and preparing environment state
3. Running smoke tests to confirm UCA V5 system readiness
"""

import sys
import subprocess
import os

REQUIRED_PACKAGES = [
    "numpy",
    "pandas",
    "torch",
    "networkx",
    "psutil",
    "pytest"
]

def verify_dependencies():
    print("Step 1: Verifying dependencies...")
    missing = []
    for pkg in REQUIRED_PACKAGES:
        try:
            __import__(pkg)
            print(f"  [OK] {pkg}")
        except ImportError:
            missing.append(pkg)
            print(f"  [MISSING] {pkg}")

    if missing:
        print(f"❌ Error: Some required dependencies are missing: {missing}")
        return False
    return True

def create_environment_state():
    print("Step 2: Preparing local database and cache directory states...")
    os.makedirs("alphaalgo_data/hms", exist_ok=True)
    os.makedirs("temp_hms", exist_ok=True)
    print("  [OK] Directories prepared.")
    return True

def run_smoke_tests():
    print("Step 3: Running UCA V5 smoke/readiness verification...")
    # Execute the UCA integration smoke validator
    try:
        res = subprocess.run([sys.executable, "verify_audit_fixes.py"], capture_output=True, text=True)
        if res.returncode == 0:
            print("  [OK] verify_audit_fixes.py smoke test passed.")
            print(res.stdout)
            return True
        else:
            print("  [FAIL] verify_audit_fixes.py failed with output:")
            print(res.stdout)
            print(res.stderr)
            return False
    except Exception as e:
        print(f"  [FAIL] Could not execute verify_audit_fixes.py: {e}")
        return False

def main():
    print("=== STARTING DETERSMINISTIC BOOTSTRAP PROCESS ===")

    if not verify_dependencies():
        sys.exit(1)

    if not create_environment_state():
        sys.exit(1)

    if not run_smoke_tests():
        sys.exit(1)

    print("🚀 SUCCESS: System is 100% ready for development and deployment.")
    sys.exit(0)

if __name__ == "__main__":
    main()
