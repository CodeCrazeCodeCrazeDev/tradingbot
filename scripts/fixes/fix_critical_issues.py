import logging
#!/usr/bin/env python
"""
Critical Issues Auto-Fixer
Automatically fixes the most critical issues identified in the codebase audit.

Usage:
    py scripts/fixes/fix_critical_issues.py --dry-run  # Preview changes
    py scripts/fixes/fix_critical_issues.py --apply    # Apply changes
"""

import os
import re
import sys
import argparse
import shutil
from datetime import datetime
from pathlib import Path
from typing import List, Tuple, Dict

logger = logging.getLogger(__name__)


# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


class CriticalIssueFixer:
    """Fixes critical issues in the codebase"""
    
    def __init__(self, dry_run: bool = True):
        self.dry_run = dry_run
        self.fixes_applied = 0
        self.files_modified = 0
        self.backup_dir = PROJECT_ROOT / "backup" / f"fix_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
    def run_all_fixes(self):
        """Run all critical fixes"""
        print("=" * 60)
        print("CRITICAL ISSUES AUTO-FIXER")
        print("=" * 60)
        print(f"Mode: {'DRY RUN (preview only)' if self.dry_run else 'APPLY CHANGES'}")
        print(f"Project Root: {PROJECT_ROOT}")
        print("=" * 60)
        
        # Create backup directory
        if not self.dry_run:
            self.backup_dir.mkdir(parents=True, exist_ok=True)
            print(f"\nBackup directory: {self.backup_dir}")
        
        # Run fixes
        self.fix_api_keys_exposure()
        self.fix_silent_exceptions()
        self.fix_print_statements_sample()
        self.add_gitignore_entries()
        
        # Summary
        print("\n" + "=" * 60)
        print("SUMMARY")
        print("=" * 60)
        print(f"Fixes identified: {self.fixes_applied}")
        print(f"Files to modify: {self.files_modified}")
        
        if self.dry_run:
            print("\nRun with --apply to apply these changes")
        else:
            print("\nChanges applied successfully!")
            print(f"Backups saved to: {self.backup_dir}")
    
    def fix_api_keys_exposure(self):
        """Fix exposed API keys in config files"""
        print("\n[1] Fixing API Keys Exposure...")
        
        api_keys_file = PROJECT_ROOT / "config" / "api_keys.json"
        
        if api_keys_file.exists():
            print(f"  Found: {api_keys_file}")
            
            # Create example file
            example_content = '''{
    "fred": {
        "api_key": "YOUR_FRED_API_KEY_HERE"
    },
    "newsapi": {
        "api_key": "YOUR_NEWSAPI_KEY_HERE"
    },
    "alpha_vantage": {
        "api_key": "YOUR_ALPHA_VANTAGE_KEY_HERE"
    }
}
'''
            example_file = PROJECT_ROOT / "config" / "api_keys.json.example"
            
            if not self.dry_run:
                # Backup original
                self._backup_file(api_keys_file)
                
                # Create example file
                with open(example_file, 'w') as f:
                    f.write(example_content)
                print(f"  Created: {example_file}")
                
                # Note: Not deleting original as it may be needed, but adding to gitignore
                self.fixes_applied += 1
                self.files_modified += 1
            else:
                print(f"  Would create: {example_file}")
                print("  Would add config/api_keys.json to .gitignore")
                self.fixes_applied += 1
    
    def fix_silent_exceptions(self):
        """Fix silent exception handling (except: pass)"""
        print("\n[2] Fixing Silent Exception Handling...")
        
        # Files with most silent exceptions
        target_files = [
            "trading_bot/aamis_v3/complete_aamis_system.py",
            "trading_bot/risk/__init__.py",
            "trading_bot/execution/advanced_order_management.py",
            "trading_bot/analytics/__init__.py",
            "trading_bot/connectivity/network_monitor.py",
        ]
        
        pattern = re.compile(r'except\s*(?:Exception)?\s*:\s*\n\s*pass')
        replacement = '''except Exception as e:
            logger.warning(f"Operation failed: {e}")  # TODO: Handle appropriately'''
        
        for rel_path in target_files:
            file_path = PROJECT_ROOT / rel_path
            if file_path.exists():
                self._fix_pattern_in_file(file_path, pattern, replacement, "silent exception")
    
    def fix_print_statements_sample(self):
        """Convert print statements to logging (sample of files)"""
        print("\n[3] Converting Print Statements to Logging (sample)...")
        
        # Just fix a few key files as example
        target_files = [
            "trading_bot/tools/system_check.py",
            "trading_bot/backtesting/rigorous_backtest.py",
        ]
        
        for rel_path in target_files:
            file_path = PROJECT_ROOT / rel_path
            if file_path.exists():
                print(f"  Checking: {rel_path}")
                
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                # Count print statements
                print_count = len(re.findall(r'\bprint\s*\(', content))
                if print_count > 0:
                    print(f"    Found {print_count} print statements")
                    if not self.dry_run:
                        print("    Note: Manual review recommended for print->logger conversion")
                    self.fixes_applied += print_count
    
    def add_gitignore_entries(self):
        """Add missing entries to .gitignore"""
        print("\n[4] Updating .gitignore...")
        
        gitignore_path = PROJECT_ROOT / ".gitignore"
        
        entries_to_add = [
            "\n# Sensitive configuration files",
            "config/api_keys.json",
            "config/encryption.key",
            ".env",
            "*.pem",
            "*.key",
            "\n# Backup directories",
            "backup/fix_backup_*/",
        ]
        
        if gitignore_path.exists():
            with open(gitignore_path, 'r') as f:
                current_content = f.read()
            
            new_entries = []
            for entry in entries_to_add:
                if entry.strip() and entry.strip() not in current_content:
                    new_entries.append(entry)
            
            if new_entries:
                if not self.dry_run:
                    self._backup_file(gitignore_path)
                    with open(gitignore_path, 'a') as f:
                        f.write('\n'.join(new_entries) + '\n')
                    print(f"  Added {len(new_entries)} entries to .gitignore")
                    self.fixes_applied += len(new_entries)
                    self.files_modified += 1
                else:
                    print(f"  Would add {len(new_entries)} entries:")
                    for entry in new_entries:
                        if entry.strip():
                            print(f"    + {entry}")
                    self.fixes_applied += len(new_entries)
            else:
                print("  .gitignore already up to date")
    
    def _fix_pattern_in_file(self, file_path: Path, pattern: re.Pattern, 
                             replacement: str, fix_name: str):
        """Fix a pattern in a file"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            matches = pattern.findall(content)
            if matches:
                print(f"  Found {len(matches)} {fix_name}(s) in {file_path.name}")
                
                if not self.dry_run:
                    self._backup_file(file_path)
                    new_content = pattern.sub(replacement, content)
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(new_content)
                    print(f"    Fixed {len(matches)} instances")
                    self.files_modified += 1
                
                self.fixes_applied += len(matches)
        except Exception as e:
            print(f"  Error processing {file_path}: {e}")
    
    def _backup_file(self, file_path: Path):
        """Backup a file before modifying"""
        if not self.dry_run:
            rel_path = file_path.relative_to(PROJECT_ROOT)
            backup_path = self.backup_dir / rel_path
            backup_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(file_path, backup_path)


def main():
    parser = argparse.ArgumentParser(description="Fix critical issues in codebase")
    parser.add_argument('--dry-run', action='store_true', default=True,
                       help='Preview changes without applying (default)')
    parser.add_argument('--apply', action='store_true',
                       help='Apply changes to files')
    
    args = parser.parse_args()
    
    dry_run = not args.apply
    
    fixer = CriticalIssueFixer(dry_run=dry_run)
    fixer.run_all_fixes()


if __name__ == "__main__":
    main()
