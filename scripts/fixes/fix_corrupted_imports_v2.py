#!/usr/bin/env python3
"""
Fix Corrupted Imports Script V2 - More Aggressive
==================================================

This version handles more complex corruption patterns:
1. Imports inserted inside try blocks (before except)
2. Imports inserted with wrong indentation inside functions
3. Multiple consecutive bad imports
"""

import os
import re
import ast
import shutil
from pathlib import Path
from datetime import datetime
from typing import List, Optional, Tuple

BACKUP_DIR = Path(__file__).parent.parent.parent / "syntax_fix_backups" / datetime.now().strftime("%Y%m%d_%H%M%S")


def find_syntax_errors(workspace: Path) -> List[Tuple[Path, str, int]]:
    """Find all Python files with syntax errors."""
    errors = []
    
    for root, dirs, files in os.walk(workspace):
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


def fix_file_v2(file_path: Path) -> Tuple[bool, str]:
    """
    More aggressive fix for corrupted Python files.
    """
    try:
        content = file_path.read_text(encoding='utf-8', errors='ignore')
        original = content
        
        # Try multiple fix strategies
        fixed_content = None
        
        # Strategy 1: Remove standalone imports at wrong indentation
        fixed_content = strategy_remove_wrong_indent_imports(content)
        if is_valid_python(fixed_content):
            return save_if_changed(file_path, original, fixed_content)
        
        # Strategy 2: Fix try-except blocks with imports inside
        fixed_content = strategy_fix_try_except(content)
        if is_valid_python(fixed_content):
            return save_if_changed(file_path, original, fixed_content)
        
        # Strategy 3: Remove all imports that break indentation flow
        fixed_content = strategy_remove_indentation_breakers(content)
        if is_valid_python(fixed_content):
            return save_if_changed(file_path, original, fixed_content)
        
        # Strategy 4: Line-by-line analysis with context
        fixed_content = strategy_context_aware_fix(content)
        if is_valid_python(fixed_content):
            return save_if_changed(file_path, original, fixed_content)
        
        return False, "All strategies failed"
        
    except Exception as e:
        return False, f"Error: {e}"


def is_valid_python(content: str) -> bool:
    """Check if content is valid Python."""
    try:
        ast.parse(content)
        return True
    except SyntaxError:
        return False


def save_if_changed(file_path: Path, original: str, new_content: str) -> Tuple[bool, str]:
    """Save file if content changed."""
    if new_content != original:
        BACKUP_DIR.mkdir(parents=True, exist_ok=True)
        backup_path = BACKUP_DIR / file_path.name
        shutil.copy2(file_path, backup_path)
        file_path.write_text(new_content, encoding='utf-8')
        return True, "Fixed"
    return False, "No changes needed"


def strategy_remove_wrong_indent_imports(content: str) -> str:
    """Remove imports that have wrong indentation relative to surrounding code."""
    lines = content.split('\n')
    result = []
    
    import_patterns = [
        r'^import \w+$',
        r'^from \w+ import \w+$',
    ]
    
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        current_indent = len(line) - len(line.lstrip())
        
        # Check if this is a simple import at column 0
        is_simple_import = any(re.match(p, stripped) for p in import_patterns)
        
        if is_simple_import and current_indent == 0:
            # Check context
            should_remove = False
            
            # Check previous line
            if i > 0 and lines[i-1].strip():
                prev_indent = len(lines[i-1]) - len(lines[i-1].lstrip())
                prev_stripped = lines[i-1].strip()
                
                # If previous line is indented and not a comment
                if prev_indent > 0 and not prev_stripped.startswith('#'):
                    # Check if next line is also indented
                    if i + 1 < len(lines) and lines[i+1].strip():
                        next_indent = len(lines[i+1]) - len(lines[i+1].lstrip())
                        if next_indent > 0:
                            should_remove = True
            
            if not should_remove:
                result.append(line)
        else:
            result.append(line)
        
        i += 1
    
    return '\n'.join(result)


def strategy_fix_try_except(content: str) -> str:
    """Fix imports inserted inside try blocks before except."""
    lines = content.split('\n')
    result = []
    
    in_try_block = False
    try_indent = 0
    
    for i, line in enumerate(lines):
        stripped = line.strip()
        current_indent = len(line) - len(line.lstrip())
        
        # Track try blocks
        if stripped.startswith('try:'):
            in_try_block = True
            try_indent = current_indent
            result.append(line)
            continue
        
        if in_try_block:
            # Check for except/finally
            if stripped.startswith('except') or stripped.startswith('finally'):
                in_try_block = False
                result.append(line)
                continue
            
            # Check if this is an import at wrong indent (column 0 inside try block)
            if current_indent == 0 and (stripped.startswith('import ') or stripped.startswith('from ')):
                # This is a bad import - skip it
                continue
        
        result.append(line)
    
    return '\n'.join(result)


def strategy_remove_indentation_breakers(content: str) -> str:
    """Remove any import that breaks the indentation flow."""
    lines = content.split('\n')
    result = []
    
    for i, line in enumerate(lines):
        stripped = line.strip()
        current_indent = len(line) - len(line.lstrip())
        
        # Skip empty lines and comments
        if not stripped or stripped.startswith('#'):
            result.append(line)
            continue
        
        # Check if this is an import
        is_import = stripped.startswith('import ') or (stripped.startswith('from ') and 'import' in stripped)
        
        if is_import and current_indent == 0:
            # Check if this breaks indentation flow
            prev_indent = None
            next_indent = None
            
            # Find previous non-empty line
            for j in range(i - 1, -1, -1):
                if lines[j].strip() and not lines[j].strip().startswith('#'):
                    prev_indent = len(lines[j]) - len(lines[j].lstrip())
                    break
            
            # Find next non-empty line
            for j in range(i + 1, len(lines)):
                if lines[j].strip() and not lines[j].strip().startswith('#'):
                    next_indent = len(lines[j]) - len(lines[j].lstrip())
                    break
            
            # If both prev and next are indented, this import is breaking the flow
            if prev_indent is not None and next_indent is not None:
                if prev_indent > 0 and next_indent > 0:
                    # Skip this import
                    continue
        
        result.append(line)
    
    return '\n'.join(result)


def strategy_context_aware_fix(content: str) -> str:
    """Context-aware fix that understands Python structure."""
    lines = content.split('\n')
    result = []
    
    # Track state
    paren_depth = 0
    bracket_depth = 0
    brace_depth = 0
    in_string = False
    string_char = None
    in_multiline_string = False
    
    for i, line in enumerate(lines):
        stripped = line.strip()
        current_indent = len(line) - len(line.lstrip())
        
        # Update depths (simplified)
        for char in line:
            if char in ('"', "'") and not in_string:
                in_string = True
                string_char = char
            elif char == string_char and in_string:
                in_string = False
            elif not in_string:
                if char == '(':
                    paren_depth += 1
                elif char == ')':
                    paren_depth -= 1
                elif char == '[':
                    bracket_depth += 1
                elif char == ']':
                    bracket_depth -= 1
                elif char == '{':
                    brace_depth += 1
                elif char == '}':
                    brace_depth -= 1
        
        # Check if we're inside a multi-line construct
        in_multiline = paren_depth > 0 or bracket_depth > 0 or brace_depth > 0
        
        # Check if this is a misplaced import
        is_import = stripped.startswith('import ') or (stripped.startswith('from ') and 'import' in stripped)
        
        if is_import and current_indent == 0 and in_multiline:
            # Skip - import inside multi-line construct
            continue
        
        result.append(line)
    
    return '\n'.join(result)


def main():
    """Main function."""
    workspace = Path(__file__).parent.parent.parent / "trading_bot"
    
    print("=" * 70)
    print("CORRUPTED IMPORTS FIXER V2 (Aggressive)")
    print("=" * 70)
    print(f"\nScanning: {workspace}")
    print(f"Backups: {BACKUP_DIR}\n")
    
    errors = find_syntax_errors(workspace)
    
    if not errors:
        print("[SUCCESS] No syntax errors found!")
        return
    
    print(f"Found {len(errors)} files with syntax errors\n")
    
    fixed = 0
    failed = 0
    
    for file_path, error_msg, line_no in errors:
        rel_path = file_path.relative_to(workspace.parent)
        print(f"\nFixing: {rel_path}")
        print(f"  Error: {error_msg} at line {line_no}")
        
        success, message = fix_file_v2(file_path)
        
        if success:
            print(f"  [OK] {message}")
            fixed += 1
        else:
            print(f"  [FAIL] {message}")
            failed += 1
    
    print("\n" + "=" * 70)
    print(f"SUMMARY: Fixed {fixed}/{len(errors)} files, {failed} failed")
    print("=" * 70)
    
    remaining = find_syntax_errors(workspace)
    if remaining:
        print(f"\n[WARNING] {len(remaining)} files still have errors")
    else:
        print("\n[SUCCESS] All files now parse correctly!")


if __name__ == "__main__":
    main()
