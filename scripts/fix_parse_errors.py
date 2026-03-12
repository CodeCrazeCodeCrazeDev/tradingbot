"""
Parse Error Fixer for Trading Bot Integration

This script identifies and fixes common syntax errors in Python modules.
It processes modules with parse errors and attempts automatic fixes.

Usage:
    python scripts/fix_parse_errors.py
"""

import ast
import json
import os
import re
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple


class ParseErrorFixer:
    """Identifies and fixes common Python syntax errors."""
    
    def __init__(self, base_path: str):
        self.base_path = Path(base_path)
        self.fixed_count = 0
        self.failed_count = 0
        self.skipped_count = 0
        self.errors: List[Dict] = []
        self.fixes: List[Dict] = []
        
        # Create backup directory
        self.backup_dir = self.base_path / 'syntax_fix_backups' / datetime.now().strftime('%Y%m%d_%H%M%S')
        self.backup_dir.mkdir(parents=True, exist_ok=True)
    
    def scan_for_errors(self) -> List[Dict]:
        """Scan all Python files for syntax errors."""
        errors = []
        
        for root, dirs, files in os.walk(self.base_path):
            # Skip directories that shouldn't be processed
            dirs[:] = [d for d in dirs if d not in (
                '__pycache__', '.git', '.venv', 'venv', 'node_modules',
                'htmlcov', '.pytest_cache', '.hypothesis', 'mlruns',
                'syntax_fix_backups', 'autonomous_backups', 'trading_bot.egg-info'
            )]
            
            for file in files:
                if file.endswith('.py'):
                    file_path = Path(root) / file
                    error = self._check_syntax(file_path)
                    if error:
                        errors.append(error)
        
        return errors
    
    def _check_syntax(self, file_path: Path) -> Optional[Dict]:
        """Check a file for syntax errors."""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            try:
                ast.parse(content)
                return None  # No error
            except SyntaxError as e:
                return {
                    'file_path': str(file_path),
                    'relative_path': str(file_path.relative_to(self.base_path)),
                    'error_type': 'SyntaxError',
                    'message': str(e.msg) if hasattr(e, 'msg') else str(e),
                    'line': e.lineno,
                    'offset': e.offset,
                    'content_preview': self._get_context(content, e.lineno) if e.lineno else None
                }
        except Exception as e:
            return {
                'file_path': str(file_path),
                'relative_path': str(file_path.relative_to(self.base_path)),
                'error_type': type(e).__name__,
                'message': str(e),
                'line': None,
                'offset': None,
                'content_preview': None
            }
    
    def _get_context(self, content: str, line_num: int, context: int = 3) -> str:
        """Get context around an error line."""
        lines = content.splitlines()
        start = max(0, line_num - context - 1)
        end = min(len(lines), line_num + context)
        
        result = []
        for i in range(start, end):
            prefix = '>>> ' if i == line_num - 1 else '    '
            result.append(f"{prefix}{i + 1}: {lines[i]}")
        
        return '\n'.join(result)
    
    def fix_file(self, error: Dict) -> bool:
        """Attempt to fix a file with syntax errors."""
        file_path = Path(error['file_path'])
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            original_content = content
            fixed = False
            fix_description = []
            
            # Try various fixes
            content, was_fixed = self._fix_unexpected_indent(content, error)
            if was_fixed:
                fixed = True
                fix_description.append('Fixed unexpected indent')
            
            content, was_fixed = self._fix_invalid_syntax(content, error)
            if was_fixed:
                fixed = True
                fix_description.append('Fixed invalid syntax')
            
            content, was_fixed = self._fix_unmatched_brackets(content, error)
            if was_fixed:
                fixed = True
                fix_description.append('Fixed unmatched brackets')
            
            content, was_fixed = self._fix_missing_colon(content, error)
            if was_fixed:
                fixed = True
                fix_description.append('Fixed missing colon')
            
            content, was_fixed = self._fix_encoding_issues(content)
            if was_fixed:
                fixed = True
                fix_description.append('Fixed encoding issues')
            
            # Verify the fix worked
            if fixed:
                try:
                    ast.parse(content)
                    
                    # Backup original
                    backup_path = self.backup_dir / error['relative_path']
                    backup_path.parent.mkdir(parents=True, exist_ok=True)
                    with open(backup_path, 'w', encoding='utf-8') as f:
                        f.write(original_content)
                    
                    # Write fixed content
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(content)
                    
                    self.fixes.append({
                        'file': error['relative_path'],
                        'fixes': fix_description,
                        'backup': str(backup_path)
                    })
                    self.fixed_count += 1
                    return True
                    
                except SyntaxError:
                    # Fix didn't work
                    pass
            
            self.failed_count += 1
            self.errors.append(error)
            return False
            
        except Exception as e:
            self.failed_count += 1
            error['fix_error'] = str(e)
            self.errors.append(error)
            return False
    
    def _fix_unexpected_indent(self, content: str, error: Dict) -> Tuple[str, bool]:
        """Fix unexpected indent errors."""
        if 'unexpected indent' not in error.get('message', '').lower():
            return content, False
        
        line_num = error.get('line')
        if not line_num:
            return content, False
        
        lines = content.splitlines()
        if line_num > len(lines):
            return content, False
        
        # Get the problematic line
        problem_line = lines[line_num - 1]
        
        # Find the expected indentation from previous non-empty line
        prev_indent = 0
        for i in range(line_num - 2, -1, -1):
            if lines[i].strip():
                prev_indent = len(lines[i]) - len(lines[i].lstrip())
                # If previous line ends with colon, add one indent level
                if lines[i].rstrip().endswith(':'):
                    prev_indent += 4
                break
        
        # Fix the indentation
        current_indent = len(problem_line) - len(problem_line.lstrip())
        if current_indent > prev_indent:
            fixed_line = ' ' * prev_indent + problem_line.lstrip()
            lines[line_num - 1] = fixed_line
            return '\n'.join(lines), True
        
        return content, False
    
    def _fix_invalid_syntax(self, content: str, error: Dict) -> Tuple[str, bool]:
        """Fix common invalid syntax errors."""
        if 'invalid syntax' not in error.get('message', '').lower():
            return content, False
        
        line_num = error.get('line')
        if not line_num:
            return content, False
        
        lines = content.splitlines()
        if line_num > len(lines):
            return content, False
        
        problem_line = lines[line_num - 1]
        fixed = False
        
        # Fix common issues
        # 1. Missing closing parenthesis on previous line
        if line_num > 1:
            prev_line = lines[line_num - 2]
            open_parens = prev_line.count('(') - prev_line.count(')')
            if open_parens > 0:
                lines[line_num - 2] = prev_line + ')' * open_parens
                fixed = True
        
        # 2. Fix f-string issues
        if 'f"' in problem_line or "f'" in problem_line:
            # Fix unescaped braces
            problem_line = re.sub(r'(?<!\{)\{(?!\{)([^}]*?)(?<!\})\}(?!\})', 
                                  lambda m: '{{' + m.group(1) + '}}' if '{' in m.group(1) or '}' in m.group(1) else m.group(0),
                                  problem_line)
            lines[line_num - 1] = problem_line
            fixed = True
        
        if fixed:
            return '\n'.join(lines), True
        
        return content, False
    
    def _fix_unmatched_brackets(self, content: str, error: Dict) -> Tuple[str, bool]:
        """Fix unmatched brackets/parentheses."""
        if 'unmatched' not in error.get('message', '').lower():
            return content, False
        
        line_num = error.get('line')
        if not line_num:
            return content, False
        
        lines = content.splitlines()
        if line_num > len(lines):
            return content, False
        
        problem_line = lines[line_num - 1]
        
        # Count brackets
        open_parens = problem_line.count('(')
        close_parens = problem_line.count(')')
        open_brackets = problem_line.count('[')
        close_brackets = problem_line.count(']')
        open_braces = problem_line.count('{')
        close_braces = problem_line.count('}')
        
        fixed = False
        
        # Fix extra closing brackets
        if close_parens > open_parens:
            # Remove extra closing parens
            diff = close_parens - open_parens
            for _ in range(diff):
                idx = problem_line.rfind(')')
                if idx >= 0:
                    problem_line = problem_line[:idx] + problem_line[idx+1:]
            fixed = True
        
        if close_brackets > open_brackets:
            diff = close_brackets - open_brackets
            for _ in range(diff):
                idx = problem_line.rfind(']')
                if idx >= 0:
                    problem_line = problem_line[:idx] + problem_line[idx+1:]
            fixed = True
        
        if close_braces > open_braces:
            diff = close_braces - open_braces
            for _ in range(diff):
                idx = problem_line.rfind('}')
                if idx >= 0:
                    problem_line = problem_line[:idx] + problem_line[idx+1:]
            fixed = True
        
        if fixed:
            lines[line_num - 1] = problem_line
            return '\n'.join(lines), True
        
        return content, False
    
    def _fix_missing_colon(self, content: str, error: Dict) -> Tuple[str, bool]:
        """Fix missing colons after def/class/if/etc."""
        line_num = error.get('line')
        if not line_num:
            return content, False
        
        lines = content.splitlines()
        if line_num > len(lines):
            return content, False
        
        # Check previous line for missing colon
        if line_num > 1:
            prev_line = lines[line_num - 2].rstrip()
            keywords = ['def ', 'class ', 'if ', 'elif ', 'else', 'for ', 'while ', 'try', 'except', 'finally', 'with ']
            
            for kw in keywords:
                if prev_line.lstrip().startswith(kw) and not prev_line.endswith(':'):
                    lines[line_num - 2] = prev_line + ':'
                    return '\n'.join(lines), True
        
        return content, False
    
    def _fix_encoding_issues(self, content: str) -> Tuple[str, bool]:
        """Fix encoding-related issues."""
        fixed = False
        
        # Remove null bytes
        if '\x00' in content:
            content = content.replace('\x00', '')
            fixed = True
        
        # Fix Windows line endings issues
        if '\r\n' in content:
            content = content.replace('\r\n', '\n')
            fixed = True
        
        return content, fixed
    
    def generate_report(self) -> Dict:
        """Generate a report of fixes and remaining errors."""
        return {
            'generated_at': datetime.now().isoformat(),
            'summary': {
                'total_errors_found': self.fixed_count + self.failed_count + self.skipped_count,
                'fixed': self.fixed_count,
                'failed': self.failed_count,
                'skipped': self.skipped_count,
            },
            'fixes': self.fixes,
            'remaining_errors': self.errors[:100],  # Limit to first 100
            'backup_directory': str(self.backup_dir)
        }
    
    def save_report(self, output_path: str) -> None:
        """Save the report to a JSON file."""
        report = self.generate_report()
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2)
        
        print(f"Report saved to: {output_path}")


def main():
    """Main entry point."""
    script_dir = Path(__file__).parent
    base_path = script_dir.parent / 'trading_bot'
    
    print(f"Scanning for parse errors in: {base_path}")
    print("=" * 60)
    
    fixer = ParseErrorFixer(str(base_path))
    
    # Scan for errors
    print("Scanning for syntax errors...")
    errors = fixer.scan_for_errors()
    print(f"Found {len(errors)} files with syntax errors")
    
    # Attempt to fix each error
    print("\nAttempting automatic fixes...")
    for i, error in enumerate(errors):
        if (i + 1) % 50 == 0:
            print(f"  Processed {i + 1}/{len(errors)} files...")
        fixer.fix_file(error)
    
    # Generate report
    report_path = script_dir.parent / 'docs' / 'integration' / f'parse_error_fixes_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
    fixer.save_report(str(report_path))
    
    # Print summary
    print("\n" + "=" * 60)
    print("PARSE ERROR FIX SUMMARY")
    print("=" * 60)
    print(f"Total errors found: {len(errors)}")
    print(f"Successfully fixed: {fixer.fixed_count}")
    print(f"Failed to fix: {fixer.failed_count}")
    print(f"Backups saved to: {fixer.backup_dir}")
    
    if fixer.errors:
        print(f"\nRemaining errors require manual review:")
        for err in fixer.errors[:10]:
            print(f"  - {err['relative_path']}: {err['message']}")
        if len(fixer.errors) > 10:
            print(f"  ... and {len(fixer.errors) - 10} more")


if __name__ == '__main__':
    main()
