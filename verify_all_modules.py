"""
Verify all modules load successfully by importing main.py and checking _AVAILABLE.
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

print("=" * 80)
print("MODULE LOADING VERIFICATION")
print("=" * 80)
print()

# Import main to trigger all module imports
print("Loading all modules from main.py...")
try:
    import main
    _AVAILABLE = main._AVAILABLE
except Exception as e:
    print(f"ERROR: Failed to import main.py: {e}")
    sys.exit(1)

print(f"Successfully loaded main.py with {len(_AVAILABLE)} modules")
print()

# Count results
total = len(_AVAILABLE)
loaded = sum(1 for v in _AVAILABLE.values() if v)
failed = total - loaded
percentage = (loaded / total * 100) if total > 0 else 0

# Categorize modules
success_modules = sorted([k for k, v in _AVAILABLE.items() if v])
failed_modules = sorted([k for k, v in _AVAILABLE.items() if not v])

print("=" * 80)
print("RESULTS")
print("=" * 80)
print()
print(f"Total modules: {total}")
print(f"Loaded successfully: {loaded} ({percentage:.1f}%)")
print(f"Failed: {failed}")
print()

if failed_modules:
    print("=" * 80)
    print(f"FAILED MODULES ({len(failed_modules)})")
    print("=" * 80)
    for i, module in enumerate(failed_modules, 1):
        print(f"  {i:3d}. {module}")
    print()

if percentage == 100.0:
    print("=" * 80)
    print("*** SUCCESS! ALL MODULES LOADED (100%) ***")
    print("=" * 80)
    print()
    print(f"Individual module integration: {loaded}/{total} modules loaded successfully (100%)")
else:
    print(f"Current status: {loaded}/{total} modules loaded ({percentage:.1f}%)")
    print(f"Remaining to fix: {failed} modules")

print()
