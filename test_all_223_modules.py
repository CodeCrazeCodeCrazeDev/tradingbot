"""
Test ALL 223 modules from main.py and generate comprehensive report.
This script extracts all module imports from main.py and tests each one.
"""
import sys
import re
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def extract_modules_from_main():
    """Extract all module imports from main.py."""
    main_file = project_root / "main.py"
    
    with open(main_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find all _AVAILABLE assignments
    pattern = r"_AVAILABLE\['([^']+)'\]\s*=\s*(True|False)"
    matches = re.findall(pattern, content)
    
    return [module_name for module_name, _ in matches]

def test_module_availability():
    """Test all modules by checking _AVAILABLE dictionary after imports."""
    # Import main.py's module section
    import importlib.util
    spec = importlib.util.spec_from_file_location("main_imports", project_root / "main.py")
    main_module = importlib.util.module_from_spec(spec)
    
    try:
        # Execute only the import section (before def main)
        with open(project_root / "main.py", 'r', encoding='utf-8') as f:
            content = f.read()
            # Find where def main starts
            main_start = content.find('def main(')
            if main_start > 0:
                import_section = content[:main_start]
                exec(import_section, main_module.__dict__)
    except Exception as e:
        print(f"Error loading main.py imports: {e}")
        return {}
    
    return main_module.__dict__.get('_AVAILABLE', {})

print("=" * 80)
print("COMPREHENSIVE MODULE TEST - ALL 223 MODULES")
print("=" * 80)
print()
print("Extracting module list from main.py...")

modules = extract_modules_from_main()
print(f"Found {len(modules)} module entries in main.py")
print()

print("Testing module availability...")
print()

_AVAILABLE = test_module_availability()

if not _AVAILABLE:
    print("ERROR: Could not load _AVAILABLE dictionary from main.py")
    sys.exit(1)

# Count results
total = len(_AVAILABLE)
loaded = sum(1 for v in _AVAILABLE.values() if v)
failed = total - loaded
percentage = (loaded / total * 100) if total > 0 else 0

# Categorize modules
success_modules = [k for k, v in _AVAILABLE.items() if v]
failed_modules = [k for k, v in _AVAILABLE.items() if not v]

print("=" * 80)
print("MODULE LOADING STATUS")
print("=" * 80)
print()

# Show first 50 successful modules
print("[SUCCESS] First 50 loaded modules:")
for i, module in enumerate(success_modules[:50], 1):
    print(f"  {i:3d}. {module}")

if len(success_modules) > 50:
    print(f"  ... and {len(success_modules) - 50} more")

print()

if failed_modules:
    print("[FAILED] Modules that failed to load:")
    for i, module in enumerate(failed_modules, 1):
        print(f"  {i:3d}. {module}")
    print()

print("=" * 80)
print("FINAL SUMMARY")
print("=" * 80)
print(f"Total modules: {total}")
print(f"Loaded successfully: {loaded} ({percentage:.1f}%)")
print(f"Failed: {failed}")
print()

if percentage == 100.0:
    print("=" * 80)
    print("SUCCESS! ALL MODULES LOADED (100%)")
    print("=" * 80)
    print()
    print("Individual module integration: {}/{} modules loaded successfully (100%)".format(loaded, total))
else:
    print(f"Current status: {percentage:.1f}% modules loaded")
    print(f"Remaining to fix: {failed} modules")

print()
print("=" * 80)
