"""
Auto-Fix Import Issues
Automatically fixes 'from __future__ imports must occur at the beginning' errors
"""

import os
import sys
import io
from pathlib import Path
import re

# Set UTF-8 encoding for Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')


class ImportFixer:
    """Fixes import order issues"""
    
    def __init__(self, root_dir: str):
        self.root_dir = Path(root_dir)
        self.fixed_files = []
        
    def fix_file(self, file_path: Path) -> bool:
        """Fix import order in a single file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # Find __future__ imports
            future_imports = []
            other_lines = []
            docstring_lines = []
            in_docstring = False
            docstring_quote = None
            
            i = 0
            # Handle module docstring first
            if lines and (lines[0].strip().startswith('"""') or lines[0].strip().startswith("'''")):
                quote = '"""' if '"""' in lines[0] else "'''"
                docstring_lines.append(lines[0])
                i = 1
                
                if lines[0].strip().count(quote) == 1:  # Multi-line docstring
                    while i < len(lines):
                        docstring_lines.append(lines[i])
                        if quote in lines[i]:
                            i += 1
                            break
                        i += 1
            
            # Process remaining lines
            for line in lines[i:]:
                if line.strip().startswith('from __future__'):
                    future_imports.append(line)
                else:
                    other_lines.append(line)
            
            # Reconstruct file with correct order
            if future_imports:
                new_content = ''.join(docstring_lines) + ''.join(future_imports) + ''.join(other_lines)
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                
                return True
            
            return False
            
        except Exception as e:
            print(f"Error fixing {file_path}: {e}")
            return False
    
    def fix_duplicate_kwargs(self, file_path: Path) -> bool:
        """Fix duplicate keyword arguments"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Find and fix duplicate source= in function calls
            # This is a simple fix - remove duplicate 'source=' parameters
            pattern = r'(\w+\s*=\s*[^,]+),\s*(\1\s*=\s*[^,]+)'
            
            fixed_content = content
            while re.search(pattern, fixed_content):
                fixed_content = re.sub(pattern, r'\1', fixed_content)
            
            if fixed_content != content:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(fixed_content)
                return True
            
            return False
            
        except Exception as e:
            print(f"Error fixing kwargs in {file_path}: {e}")
            return False
    
    def fix_scanner_interface(self, file_path: Path) -> bool:
        """Fix scanner_interface.py syntax error"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check if it starts with invalid syntax
            if content.strip().startswith('�') or not content.strip():
                # File is corrupted or empty, recreate basic structure
                new_content = '''"""
Scanner Interface - Base class for opportunity scanners
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List
from dataclasses import dataclass
from datetime import datetime


@dataclass
class ScanResult:
    """Result from a scanner"""
    opportunity_type: str
    symbol: str
    confidence: float
    data: Dict[str, Any]
    timestamp: datetime


class ScannerInterface(ABC):
    """Base interface for all scanners"""
    
    @abstractmethod
    async def scan(self, market_data: Dict[str, Any]) -> List[ScanResult]:
        """Scan for opportunities"""
        pass
    
    @abstractmethod
    def get_scanner_name(self) -> str:
        """Get scanner name"""
        pass
'''
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                return True
            
            return False
            
        except Exception as e:
            print(f"Error fixing scanner_interface: {e}")
            return False
    
    def run_fixes(self):
        """Run all fixes"""
        print("="*80)
        print("AUTO-FIX IMPORT ISSUES".center(80))
        print("="*80)
        
        # Get all Python files
        py_files = list(self.root_dir.glob('**/*.py'))
        py_files = [f for f in py_files if '.venv' not in str(f) and 'backups' not in str(f)]
        
        print(f"\nScanning {len(py_files)} Python files...\n")
        
        fixed_count = 0
        
        # Fix __future__ import order
        print("Fixing __future__ import order...")
        for py_file in py_files:
            if self.fix_file(py_file):
                print(f"  [FIXED] {py_file.relative_to(self.root_dir)}")
                self.fixed_files.append(str(py_file.relative_to(self.root_dir)))
                fixed_count += 1
        
        # Fix specific files
        print("\nFixing specific syntax errors...")
        
        # Fix news_analyzer.py duplicate kwargs
        news_analyzer = self.root_dir / 'trading_bot' / 'event_monitoring' / 'news_analyzer.py'
        if news_analyzer.exists() and self.fix_duplicate_kwargs(news_analyzer):
            print(f"  [FIXED] {news_analyzer.relative_to(self.root_dir)}")
            self.fixed_files.append(str(news_analyzer.relative_to(self.root_dir)))
            fixed_count += 1
        
        # Fix scanner_interface.py
        scanner_interface = self.root_dir / 'trading_bot' / 'opportunity_scanner' / 'scanner_interface.py'
        if scanner_interface.exists() and self.fix_scanner_interface(scanner_interface):
            print(f"  [FIXED] {scanner_interface.relative_to(self.root_dir)}")
            self.fixed_files.append(str(scanner_interface.relative_to(self.root_dir)))
            fixed_count += 1
        
        print(f"\n{'='*80}")
        print(f"FIXES APPLIED: {fixed_count} files")
        print(f"{'='*80}")
        
        if self.fixed_files:
            print("\nFixed files:")
            for file in self.fixed_files[:20]:
                print(f"  - {file}")
            if len(self.fixed_files) > 20:
                print(f"  ... and {len(self.fixed_files) - 20} more")
        
        return fixed_count


def main():
    """Main entry point"""
    root_dir = Path(__file__).parent
    
    fixer = ImportFixer(root_dir)
    fixed_count = fixer.run_fixes()
    
    print(f"\n✅ Auto-fix complete! Fixed {fixed_count} files.")
    print(f"\nRun 'py auto_complete_validation.py' to verify fixes.")


if __name__ == '__main__':
    main()
