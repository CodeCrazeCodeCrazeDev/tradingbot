#!/usr/bin/env python3
"""
Fix Corrupted Imports Script
=============================

This script fixes the corrupted Python files caused by the DeepSeek auto-fixer
incorrectly inserting import statements in the middle of:
1. Multi-line import blocks (from x import (...))
2. Try-except blocks
3. Function/method bodies
4. Docstrings

The pattern is always: random "import X" statements inserted at wrong indentation.
"""

import os
import re
import ast
import shutil
from pathlib import Path
from datetime import datetime
from typing import List, Optional, Tuple

# Backup directory
BACKUP_DIR = Path(__file__).parent.parent.parent / "syntax_fix_backups" / datetime.now().strftime("%Y%m%d_%H%M%S")


def find_syntax_errors(workspace: Path) -> List[Tuple[Path, str, int]]:
    """Find all Python files with syntax errors."""
    errors = []
    
    for root, dirs, files in os.walk(workspace):
        # Skip pycache and other non-essential dirs
        dirs[:] = [d for d in dirs if d not in ('__pycache__', '.git', 'venv', '.venv', 'node_modules')]
        
        for f in files:
            if f.endswith('.py'):
                fp = Path(root) / f
                try:
                    content = fp.read_text(encoding='utf-8', errors='ignore')
                    ast.parse(content)
                except SyntaxError as e:
                    errors.append((fp, e.msg, e.lineno))
    
    return errors


def fix_corrupted_file(file_path: Path) -> Tuple[bool, str]:
    """
    Fix a corrupted Python file by removing incorrectly inserted imports.
    
    Returns:
        (success, message)
    """
    try:
        content = file_path.read_text(encoding='utf-8', errors='ignore')
        original = content
        lines = content.split('\n')
        fixed_lines = []
        
        # Patterns for incorrectly inserted imports
        bad_import_patterns = [
            r'^import logging$',
            r'^import asyncio$',
            r'^import datetime$',
            r'^import numpy$',
            r'^import pandas$',
            r'^from enum import auto$',
            r'^from typing import Any$',
            r'^from typing import Dict$',
            r'^from typing import List$',
            r'^from typing import Optional$',
        ]
        
        in_multiline_import = False
        in_try_block = False
        paren_depth = 0
        i = 0
        
        while i < len(lines):
            line = lines[i]
            stripped = line.strip()
            
            # Track multi-line imports
            if not in_multiline_import:
                if stripped.startswith('from ') and '(' in line and ')' not in line:
                    in_multiline_import = True
                    paren_depth = line.count('(') - line.count(')')
            else:
                paren_depth += line.count('(') - line.count(')')
                if paren_depth <= 0:
                    in_multiline_import = False
            
            # Check if this line is a bad import inserted in wrong place
            is_bad_import = False
            
            for pattern in bad_import_patterns:
                if re.match(pattern, stripped):
                    # Check context - is this import in a bad location?
                    if in_multiline_import:
                        is_bad_import = True
                        break
                    
                    # Check if previous line suggests we're inside a block
                    if i > 0:
                        prev_line = lines[i-1].rstrip()
                        prev_stripped = prev_line.strip()
                        
                        # Inside a try block (import after try: but before except)
                        if prev_stripped.endswith(':') and not prev_stripped.startswith(('import ', 'from ')):
                            is_bad_import = True
                            break
                        
                        # Import with wrong indentation (should be at column 0 or match previous)
                        if stripped.startswith('import ') or stripped.startswith('from '):
                            current_indent = len(line) - len(line.lstrip())
                            prev_indent = len(prev_line) - len(prev_line.lstrip())
                            
                            # If previous line is indented and this import is at column 0
                            if prev_indent > 0 and current_indent == 0 and prev_stripped and not prev_stripped.startswith('#'):
                                # Check if next line is also indented (we're in a block)
                                if i + 1 < len(lines):
                                    next_line = lines[i+1]
                                    next_indent = len(next_line) - len(next_line.lstrip())
                                    if next_indent > 0:
                                        is_bad_import = True
                                        break
            
            if not is_bad_import:
                fixed_lines.append(line)
            else:
                print(f"  Removing bad import at line {i+1}: {stripped}")
            
            i += 1
        
        new_content = '\n'.join(fixed_lines)
        
        # Verify the fix works
        try:
            ast.parse(new_content)
        except SyntaxError:
            # If still broken, try more aggressive fix
            new_content = aggressive_fix(content)
            try:
                ast.parse(new_content)
            except SyntaxError as e:
                return False, f"Could not fix: {e.msg} at line {e.lineno}"
        
        if new_content != original:
            # Create backup
            BACKUP_DIR.mkdir(parents=True, exist_ok=True)
            rel_path = file_path.relative_to(file_path.parent.parent.parent)
            backup_path = BACKUP_DIR / rel_path
            backup_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(file_path, backup_path)
            
            # Write fixed content
            file_path.write_text(new_content, encoding='utf-8')
            return True, "Fixed"
        
        return False, "No changes needed"
        
    except Exception as e:
        return False, f"Error: {e}"


def aggressive_fix(content: str) -> str:
    """
    More aggressive fix that removes all incorrectly placed imports.
    """
    lines = content.split('\n')
    fixed_lines = []
    
    # Track state
    in_multiline = False
    paren_depth = 0
    in_docstring = False
    docstring_char = None
    in_indented_block = False
    
    for i, line in enumerate(lines):
        stripped = line.strip()
        current_indent = len(line) - len(line.lstrip())
        
        # Track docstrings
        if not in_docstring:
            if stripped.startswith('"""') or stripped.startswith("'''"):
                docstring_char = stripped[:3]
                if stripped.count(docstring_char) < 2:
                    in_docstring = True
        else:
            if docstring_char in stripped:
                in_docstring = False
            fixed_lines.append(line)
            continue
        
        # Track multi-line constructs
        paren_depth += line.count('(') - line.count(')')
        paren_depth += line.count('[') - line.count(']')
        paren_depth += line.count('{') - line.count('}')
        
        in_multiline = paren_depth > 0
        
        # Check if this is a misplaced import
        is_misplaced = False
        
        if stripped.startswith('import ') or (stripped.startswith('from ') and 'import' in stripped):
            # Imports should be at column 0 (unless in a function doing lazy import)
            if current_indent == 0:
                # Check if we're in the middle of something
                if in_multiline:
                    is_misplaced = True
                elif i > 0:
                    prev_stripped = lines[i-1].strip()
                    # After a line ending with : that's not an import
                    if prev_stripped.endswith(':') and not prev_stripped.startswith(('import ', 'from ')):
                        is_misplaced = True
                    # After an indented line (we're breaking out of a block incorrectly)
                    prev_indent = len(lines[i-1]) - len(lines[i-1].lstrip())
                    if prev_indent > 0 and lines[i-1].strip():
                        # Check if next line is also indented
                        if i + 1 < len(lines) and lines[i+1].strip():
                            next_indent = len(lines[i+1]) - len(lines[i+1].lstrip())
                            if next_indent > 0:
                                is_misplaced = True
        
        if not is_misplaced:
            fixed_lines.append(line)
    
    return '\n'.join(fixed_lines)


def main():
    """Main function to fix all corrupted files."""
    workspace = Path(__file__).parent.parent.parent / "trading_bot"
    
    print("=" * 70)
    print("CORRUPTED IMPORTS FIXER")
    print("=" * 70)
    print(f"\nScanning: {workspace}")
    print(f"Backups will be saved to: {BACKUP_DIR}\n")
    
    # Find all errors
    errors = find_syntax_errors(workspace)
    
    if not errors:
        print("[SUCCESS] No syntax errors found!")
        return
    
    print(f"Found {len(errors)} files with syntax errors\n")
    
    # Fix each file
    fixed = 0
    failed = 0
    
    for file_path, error_msg, line_no in errors:
        rel_path = file_path.relative_to(workspace.parent)
        print(f"\nFixing: {rel_path}")
        print(f"  Error: {error_msg} at line {line_no}")
        
        success, message = fix_corrupted_file(file_path)
        
        if success:
            print(f"  [OK] {message}")
            fixed += 1
        else:
            print(f"  [FAIL] {message}")
            failed += 1
    
    print("\n" + "=" * 70)
    print(f"SUMMARY: Fixed {fixed}/{len(errors)} files, {failed} failed")
    print("=" * 70)
    
    # Verify
    remaining_errors = find_syntax_errors(workspace)
    if remaining_errors:
        print(f"\n[WARNING] {len(remaining_errors)} files still have errors:")
        for fp, msg, line in remaining_errors[:10]:
            print(f"  - {fp.name}: line {line} - {msg}")
        if len(remaining_errors) > 10:
            print(f"  ... and {len(remaining_errors) - 10} more")
    else:
        print("\n[SUCCESS] All files now parse correctly!")


if __name__ == "__main__":
    main()
