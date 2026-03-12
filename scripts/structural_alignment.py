"""
Structural Alignment Script for Trading Bot
Automatically fixes __init__.py exports and validates module structure
"""

import os
import ast
import sys
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional

BASE_DIR = Path(r"c:\Users\peterson\trading bot\trading_bot")

# Directories to skip
SKIP_DIRS = {
    '__pycache__', 'backup', 'auto_fix_backups', 'autonomous_backups',
    'complete_work_backups', '.git', 'node_modules', 'venv', '.venv'
}

def should_skip_dir(dirname: str) -> bool:
    """Check if directory should be skipped"""
    return dirname in SKIP_DIRS or dirname.startswith('.')

def get_module_exports(filepath: Path) -> Set[str]:
    """Extract all public exports from a Python file"""
    exports = set()
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        tree = ast.parse(content)
        
        for node in ast.iter_child_nodes(tree):
            # Classes
            if isinstance(node, ast.ClassDef) and not node.name.startswith('_'):
                exports.add(node.name)
            # Functions
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and not node.name.startswith('_'):
                exports.add(node.name)
            # Top-level assignments (constants, etc.)
            elif isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and not target.id.startswith('_'):
                        # Skip common non-export names
                        if target.id not in {'logger', 'log', 'logging', 'os', 'sys', 'typing'}:
                            exports.add(target.id)
    except Exception as e:
        pass
    return exports

def get_init_exports(init_path: Path) -> Tuple[Set[str], List[str]]:
    """Get current exports from __init__.py and the raw content"""
    exports = set()
    lines = []
    try:
        with open(init_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            lines = content.split('\n')
        tree = ast.parse(content)
        
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                for alias in node.names:
                    name = alias.asname if alias.asname else alias.name
                    exports.add(name)
            elif isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id == '__all__':
                        if isinstance(node.value, ast.List):
                            for elt in node.value.elts:
                                if isinstance(elt, ast.Constant):
                                    exports.add(elt.value)
    except:
        pass
    return exports, lines

def generate_init_content(package_path: Path, submodules: Dict[str, Set[str]]) -> str:
    """Generate proper __init__.py content with lazy imports"""
    lines = ['"""']
    pkg_name = package_path.name
    lines.append(f'{pkg_name} package')
    lines.append('"""')
    lines.append('')
    
    # Collect all exports
    all_exports = []
    import_lines = []
    
    for module_name, exports in sorted(submodules.items()):
        if exports:
            # Use try-except for robustness
            export_list = sorted(exports)
            all_exports.extend(export_list)
            
            if len(export_list) <= 3:
                import_lines.append(f"from .{module_name} import {', '.join(export_list)}")
            else:
                import_lines.append(f"from .{module_name} import (")
                for i, exp in enumerate(export_list):
                    comma = ',' if i < len(export_list) - 1 else ''
                    import_lines.append(f"    {exp}{comma}")
                import_lines.append(")")
    
    # Add imports with try-except wrapper
    if import_lines:
        lines.append("try:")
        for imp_line in import_lines:
            lines.append(f"    {imp_line}")
        lines.append("except ImportError as e:")
        lines.append("    import logging")
        lines.append(f"    logging.getLogger(__name__).debug(f'Optional import failed in {pkg_name}: {{e}}')")
        lines.append("")
    
    # Add __all__
    if all_exports:
        lines.append("__all__ = [")
        for exp in sorted(set(all_exports)):
            lines.append(f"    '{exp}',")
        lines.append("]")
    
    return '\n'.join(lines)

def analyze_package(package_path: Path) -> Dict[str, Set[str]]:
    """Analyze a package and return submodule exports"""
    submodules = {}
    
    for item in package_path.iterdir():
        if item.is_file() and item.suffix == '.py' and item.name != '__init__.py':
            module_name = item.stem
            exports = get_module_exports(item)
            if exports:
                submodules[module_name] = exports
    
    return submodules

def fix_package_init(package_path: Path, dry_run: bool = False) -> Tuple[bool, str]:
    """Fix a package's __init__.py file"""
    init_path = package_path / '__init__.py'
    
    if not init_path.exists():
        return False, "No __init__.py found"
    
    submodules = analyze_package(package_path)
    
    if not submodules:
        return False, "No submodules with exports"
    
    # Check current exports
    current_exports, _ = get_init_exports(init_path)
    
    # Calculate missing exports
    all_needed = set()
    for exports in submodules.values():
        all_needed.update(exports)
    
    missing = all_needed - current_exports
    
    if not missing:
        return False, "All exports present"
    
    # Generate new content
    new_content = generate_init_content(package_path, submodules)
    
    if not dry_run:
        with open(init_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
    
    return True, f"Fixed {len(missing)} missing exports"

def scan_all_packages() -> List[Path]:
    """Scan all packages in the trading_bot directory"""
    packages = []
    
    for root, dirs, files in os.walk(BASE_DIR):
        # Filter directories
        dirs[:] = [d for d in dirs if not should_skip_dir(d)]
        
        if '__init__.py' in files:
            packages.append(Path(root))
    
    return packages

def main():
    print("=" * 60)
    print("STRUCTURAL ALIGNMENT - Trading Bot Module Fixer")
    print("=" * 60)
    
    packages = scan_all_packages()
    print(f"\nFound {len(packages)} packages to analyze")
    
    fixed = 0
    skipped = 0
    errors = []
    
    for pkg in packages:
        rel_path = pkg.relative_to(BASE_DIR.parent)
        try:
            was_fixed, msg = fix_package_init(pkg, dry_run=False)
            if was_fixed:
                print(f"[FIXED] {rel_path}: {msg}")
                fixed += 1
            else:
                skipped += 1
        except Exception as e:
            errors.append((rel_path, str(e)))
            print(f"[ERROR] {rel_path}: {e}")
    
    print("\n" + "=" * 60)
    print(f"SUMMARY:")
    print(f"  Packages fixed: {fixed}")
    print(f"  Packages skipped: {skipped}")
    print(f"  Errors: {len(errors)}")
    print("=" * 60)
    
    return fixed, skipped, errors

if __name__ == "__main__":
    main()
