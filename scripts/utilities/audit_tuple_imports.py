"""
Audit and fix Tuple imports across the codebase
"""

import re
from pathlib import Path
from typing import List, Tuple as TupleType

def check_file_needs_tuple_import(filepath: Path) -> TupleType[bool, bool]:
    """
    Check if file uses Tuple[...] and if it imports Tuple
    Returns: (uses_tuple, has_import)
    """
    try:
        content = filepath.read_text(encoding='utf-8')
        
        # Check if file uses Tuple[...]
        uses_tuple = bool(re.search(r'Tuple\[', content))
        
        # Check if file imports Tuple
        has_import = bool(re.search(r'from typing import.*\bTuple\b', content))
        
        return uses_tuple, has_import
    except Exception as e:
        print(f"Error reading {filepath}: {e}")
        return False, False

def fix_tuple_import(filepath: Path) -> bool:
    """
    Add Tuple to typing imports if missing
    Returns: True if file was modified
    """
    try:
        content = filepath.read_text(encoding='utf-8')
        
        # Find the typing import line
        typing_import_pattern = r'from typing import ([^\n]+)'
        match = re.search(typing_import_pattern, content)
        
        if match:
            imports = match.group(1)
            
            # Check if Tuple is already there
            if 'Tuple' in imports:
                return False
            
            # Add Tuple to the imports
            new_imports = imports.rstrip() + ', Tuple'
            new_line = f'from typing import {new_imports}'
            
            # Replace the line
            new_content = content.replace(match.group(0), new_line)
            
            # Write back
            filepath.write_text(new_content, encoding='utf-8')
            return True
        else:
            # No typing import found, add one at the top after docstring
            lines = content.split('\n')
            insert_pos = 0
            
            # Skip docstring
            in_docstring = False
            for i, line in enumerate(lines):
                if '"""' in line or "'''" in line:
                    if not in_docstring:
                        in_docstring = True
                    else:
                        insert_pos = i + 1
                        break
                elif not in_docstring and line.strip() and not line.startswith('#'):
                    insert_pos = i
                    break
            
            # Insert the import
            lines.insert(insert_pos, 'from typing import Tuple')
            new_content = '\n'.join(lines)
            
            filepath.write_text(new_content, encoding='utf-8')
            return True
            
    except Exception as e:
        print(f"Error fixing {filepath}: {e}")
        return False

def main():
    """Main audit function"""
    trading_bot_dir = Path('trading_bot')
    
    files_to_fix = []
    files_ok = []
    files_no_tuple = []
    
    # Find all Python files
    for py_file in trading_bot_dir.rglob('*.py'):
        uses_tuple, has_import = check_file_needs_tuple_import(py_file)
        
        if uses_tuple and not has_import:
            files_to_fix.append(py_file)
        elif uses_tuple and has_import:
            files_ok.append(py_file)
        else:
            files_no_tuple.append(py_file)
    
    print("="*70)
    print("TUPLE IMPORT AUDIT")
    print("="*70)
    print(f"\nFiles using Tuple with correct import: {len(files_ok)}")
    print(f"Files using Tuple WITHOUT import: {len(files_to_fix)}")
    print(f"Files not using Tuple: {len(files_no_tuple)}")
    
    if files_to_fix:
        print(f"\n{'='*70}")
        print("FIXING FILES")
        print("="*70)
        
        fixed_count = 0
        for filepath in files_to_fix:
            print(f"Fixing: {filepath}")
            if fix_tuple_import(filepath):
                fixed_count += 1
                print(f"  [FIXED]")
            else:
                print(f"  [SKIPPED - already has import or error]")
        
        print(f"\n{'='*70}")
        print(f"SUMMARY: Fixed {fixed_count}/{len(files_to_fix)} files")
        print("="*70)
    else:
        print("\n[OK] All files have correct Tuple imports!")

if __name__ == "__main__":
    main()
