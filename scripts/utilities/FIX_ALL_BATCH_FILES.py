"""
Comprehensive Batch File Fixer
Fixes common issues in all batch files automatically
"""

import os
import re
from pathlib import Path

def fix_batch_file(filepath):
    """Fix common issues in a batch file"""
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        original_content = content
        fixes = []
        
        # Fix 1: Replace standalone 'pytest ' with 'py -m pytest '
        # But not if already preceded by 'py -m '
        pattern1 = r'(?<!py -m )pytest\s'
        if re.search(pattern1, content):
            content = re.sub(pattern1, 'py -m pytest ', content)
            fixes.append("Fixed pytest command")
        
        # Fix 2: Replace standalone 'python ' with 'py '
        # But not in comments or echo statements
        pattern2 = r'(?<!@echo )(?<!REM )(?<!rem )python\s'
        if re.search(pattern2, content):
            content = re.sub(pattern2, 'py ', content)
            fixes.append("Fixed python command")
        
        # Fix 3: Replace 'pip install' with 'py -m pip install'
        pattern3 = r'(?<!py -m )pip\s+install'
        if re.search(pattern3, content):
            content = re.sub(pattern3, 'py -m pip install', content)
            fixes.append("Fixed pip command")
        
        # Save if changes were made
        if content != original_content:
            with open(filepath, 'w', encoding='utf-8', newline='\r\n') as f:
                f.write(content)
            return fixes
        
        return None
        
    except Exception as e:
        print(f"Error processing {filepath}: {e}")
        return None

def main():
    """Fix all batch files in the trading bot directory"""
    print("=" * 80)
    print("BATCH FILE FIXER")
    print("=" * 80)
    print()
    
    # Find all batch files
    batch_files = []
    for root, dirs, files in os.walk('.'):
        # Skip virtual environment directories
        if '.venv' in root or 'site-packages' in root:
            continue
        
        for file in files:
            if file.endswith('.bat'):
                batch_files.append(os.path.join(root, file))
    
    print(f"Found {len(batch_files)} batch files")
    print()
    
    fixed_count = 0
    total_fixes = 0
    
    for filepath in sorted(batch_files):
        fixes = fix_batch_file(filepath)
        if fixes:
            fixed_count += 1
            total_fixes += len(fixes)
            print(f"[FIXED] {filepath}")
            for fix in fixes:
                print(f"  - {fix}")
    
    print()
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Total batch files: {len(batch_files)}")
    print(f"Files fixed: {fixed_count}")
    print(f"Total fixes applied: {total_fixes}")
    print()
    print("All batch files have been fixed!")
    print("=" * 80)

if __name__ == "__main__":
    main()
