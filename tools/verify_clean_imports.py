import os
import re
import sys

def verify_imports():
    print("================================================================================")
    print("AST / IMPORT VERIFICATION SCANNER FOR ROOT LEVEL COPY DUPLICATES")
    print("================================================================================")

    # Active directories to scan
    scan_dirs = ["trading_bot", "tests", "utils", "validation", "broker"]

    # Banned root level copy duplicate patterns (with space, strictly matching active import lines)
    banned_patterns = [
        re.compile(r"^\s*import\s+.*agents\s+2"),
        re.compile(r"^\s*from\s+.*agents\s+2"),
        re.compile(r"^\s*import\s+.*advanced_systems\s+2"),
        re.compile(r"^\s*from\s+.*advanced_systems\s+2")
    ]

    violations = 0
    scanned_files = 0

    for directory in scan_dirs:
        if not os.path.exists(directory):
            continue
        for root, _, files in os.walk(directory):
            for file in files:
                if not file.endswith(".py"):
                    continue
                filepath = os.path.join(root, file)
                scanned_files += 1
                try:
                    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                        lines = f.readlines()
                    for idx, line in enumerate(lines, 1):
                        for pattern in banned_patterns:
                            if pattern.search(line):
                                print(f"[VIOLATION] {filepath}:{idx} - Banned duplicate import detected: {line.strip()}")
                                violations += 1
                except Exception as e:
                    print(f"Error reading {filepath}: {e}")

    print(f"\nScan complete. Scanned {scanned_files} files.")
    if violations == 0:
        print("✅ SUCCESS: No active files reference archived duplicates or legacy leftovers!")
        sys.exit(0)
    else:
        print(f"❌ FAILURE: Found {violations} banned import violations!")
        sys.exit(1)

if __name__ == "__main__":
    verify_imports()
