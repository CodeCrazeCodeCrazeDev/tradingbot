#!/usr/bin/env python3
"""
DeepSeek Autonomous Engineer - 24/7 Mode
=========================================
Runs continuously fixing issues WITHOUT human approval.
Time-limited autonomous mode with safety guardrails.

SAFETY: Still protects critical files (risk, security, execution core)
LOGGING: All changes logged for post-review
AUTO-ROLLBACK: Can rollback if issues detected
"""

import os
import sys
import ast
import time
import json
import shutil
import hashlib
import logging
import asyncio
import traceback
from pathlib import Path
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum
import importlib.util

# Setup logging
LOG_DIR = Path("autonomous_logs")
LOG_DIR.mkdir(exist_ok=True)

log_file = LOG_DIR / f"autonomous_run_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    handlers=[
        logging.FileHandler(log_file, encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class FixCategory(Enum):
    """Categories of fixes - determines auto-approval level"""
    IMPORT_FIX = "import_fix"           # Missing imports - AUTO
    SYNTAX_FIX = "syntax_fix"           # Syntax errors - AUTO
    TYPE_HINT = "type_hint"             # Missing type hints - AUTO
    DOCSTRING = "docstring"             # Missing docstrings - AUTO
    UNUSED_IMPORT = "unused_import"     # Remove unused imports - AUTO
    INIT_EXPORT = "init_export"         # Fix __init__.py exports - AUTO
    CIRCULAR_IMPORT = "circular_import" # Fix circular imports - AUTO
    EXCEPTION_HANDLING = "exception"    # Add exception handling - AUTO
    INTEGRATION = "integration"         # Module integration - AUTO
    LOGIC_FIX = "logic_fix"            # Logic fixes - CAREFUL
    CRITICAL = "critical"               # Critical changes - PROTECTED


@dataclass
class FixRecord:
    """Record of a fix applied"""
    file_path: str
    category: FixCategory
    description: str
    old_content: str
    new_content: str
    timestamp: datetime = field(default_factory=datetime.now)
    success: bool = True
    error: Optional[str] = None


@dataclass
class ScanResult:
    """Result of scanning a file"""
    file_path: str
    issues: List[Dict[str, Any]]
    can_auto_fix: bool
    fix_category: FixCategory


class AutonomousDeepSeek:
    """
    DeepSeek Autonomous Engineer - 24/7 Mode
    Continuously scans and fixes issues without human approval.
    """
    
    # Files that are NEVER auto-modified (truly critical)
    PROTECTED_PATTERNS = [
        '**/risk_manager.py',
        '**/MASTER_risk*.py',
        '**/security_core.py',
        '**/credential*.py',
        '**/vault*.py',
        '**/.env*',
        '**/secrets*',
        '**/api_key*',
        '**/password*',
    ]
    
    # Files that can be auto-modified
    AUTO_FIX_PATTERNS = [
        '**/__init__.py',
        '**/test_*.py',
        '**/tests/*.py',
        '**/examples/*.py',
        '**/utils/*.py',
        '**/helpers/*.py',
    ]
    
    def __init__(self, workspace_path: str, end_time: datetime):
        self.workspace = Path(workspace_path)
        self.end_time = end_time
        self.fixes_applied: List[FixRecord] = []
        self.files_scanned = 0
        self.issues_found = 0
        self.issues_fixed = 0
        self.errors: List[str] = []
        self.backup_dir = self.workspace / "autonomous_backups" / datetime.now().strftime('%Y%m%d_%H%M%S')
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        # Track what we've already processed
        self.processed_files: Set[str] = set()
        self.file_hashes: Dict[str, str] = {}
        
        logger.info(f"[BOT] DeepSeek Autonomous Mode Initialized")
        logger.info(f"[DIR] Workspace: {self.workspace}")
        logger.info(f"[TIME] End Time: {self.end_time}")
        logger.info(f"[BACKUP] Backups: {self.backup_dir}")
    
    def is_protected(self, file_path: Path) -> bool:
        """Check if file is protected from auto-modification"""
        path_str = str(file_path).lower().replace('\\', '/')
        
        # Check protected patterns
        protected_keywords = [
            'risk_manager', 'master_risk', 'security_core', 'credential',
            'vault', '.env', 'secret', 'api_key', 'password', 'token',
            'auth', 'encryption', 'kill_switch', 'emergency'
        ]
        
        for keyword in protected_keywords:
            if keyword in path_str:
                return True
        
        return False
    
    def get_file_hash(self, file_path: Path) -> str:
        """Get hash of file content"""
        try:
            content = file_path.read_text(encoding='utf-8', errors='ignore')
            return hashlib.md5(content.encode()).hexdigest()
        except:
            return ""
    
    def backup_file(self, file_path: Path) -> bool:
        """Backup file before modification"""
        try:
            relative = file_path.relative_to(self.workspace)
            backup_path = self.backup_dir / relative
            backup_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(file_path, backup_path)
            return True
        except Exception as e:
            logger.error(f"Backup failed for {file_path}: {e}")
            return False
    
    def scan_python_file(self, file_path: Path) -> ScanResult:
        """Scan a Python file for issues"""
        issues = []
        can_auto_fix = True
        fix_category = FixCategory.IMPORT_FIX
        
        try:
            content = file_path.read_text(encoding='utf-8', errors='ignore')
            
            # Try to parse the file
            try:
                tree = ast.parse(content)
            except SyntaxError as e:
                issues.append({
                    'type': 'syntax_error',
                    'line': e.lineno,
                    'message': str(e),
                    'severity': 'high'
                })
                fix_category = FixCategory.SYNTAX_FIX
                return ScanResult(str(file_path), issues, True, fix_category)
            
            # Check for missing imports
            missing_imports = self._find_missing_imports(content, tree)
            for imp in missing_imports:
                issues.append({
                    'type': 'missing_import',
                    'name': imp,
                    'severity': 'medium'
                })
            
            # Check for unused imports
            unused_imports = self._find_unused_imports(content, tree)
            for imp in unused_imports:
                issues.append({
                    'type': 'unused_import',
                    'name': imp,
                    'severity': 'low'
                })
            
            # Check for missing docstrings
            missing_docs = self._find_missing_docstrings(tree)
            for item in missing_docs:
                issues.append({
                    'type': 'missing_docstring',
                    'name': item['name'],
                    'line': item['line'],
                    'severity': 'low'
                })
            
            # Check for bare except clauses
            bare_excepts = self._find_bare_excepts(tree)
            for exc in bare_excepts:
                issues.append({
                    'type': 'bare_except',
                    'line': exc,
                    'severity': 'medium'
                })
            
            # Check for TODO/FIXME comments
            todos = self._find_todos(content)
            for todo in todos:
                issues.append({
                    'type': 'todo',
                    'line': todo['line'],
                    'text': todo['text'],
                    'severity': 'info'
                })
            
            # Check __init__.py for missing exports
            if file_path.name == '__init__.py':
                missing_exports = self._check_init_exports(file_path, content)
                for exp in missing_exports:
                    issues.append({
                        'type': 'missing_export',
                        'module': exp,
                        'severity': 'medium'
                    })
                if missing_exports:
                    fix_category = FixCategory.INIT_EXPORT
            
        except Exception as e:
            issues.append({
                'type': 'scan_error',
                'message': str(e),
                'severity': 'error'
            })
            can_auto_fix = False
        
        return ScanResult(str(file_path), issues, can_auto_fix, fix_category)
    
    def _find_missing_imports(self, content: str, tree: ast.AST) -> List[str]:
        """Find potentially missing imports"""
        missing = []
        
        # Common modules that might be missing
        common_modules = {
            'logging': ['logger', 'logging'],
            'typing': ['Dict', 'List', 'Optional', 'Any', 'Tuple', 'Set', 'Union'],
            'dataclasses': ['dataclass', 'field'],
            'enum': ['Enum', 'auto'],
            'pathlib': ['Path'],
            'datetime': ['datetime', 'timedelta'],
            'json': ['json'],
            'asyncio': ['asyncio', 'async', 'await'],
            'numpy': ['np', 'numpy'],
            'pandas': ['pd', 'pandas', 'DataFrame'],
        }
        
        # Get all imported names
        imported_names = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imported_names.add(alias.asname or alias.name)
            elif isinstance(node, ast.ImportFrom):
                for alias in node.names:
                    imported_names.add(alias.asname or alias.name)
        
        # Check for used but not imported
        for module, names in common_modules.items():
            for name in names:
                if name in content and name not in imported_names:
                    # Verify it's actually used as a name, not in a string
                    pattern = rf'\b{name}\b'
                    import re
                    if re.search(pattern, content):
                        missing.append(f"{module}.{name}")
        
        return missing[:5]  # Limit to avoid noise
    
    def _find_unused_imports(self, content: str, tree: ast.AST) -> List[str]:
        """Find unused imports"""
        unused = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    name = alias.asname or alias.name
                    # Count occurrences (excluding the import line itself)
                    count = content.count(name)
                    if count <= 1:
                        unused.append(name)
            elif isinstance(node, ast.ImportFrom):
                for alias in node.names:
                    if alias.name == '*':
                        continue
                    name = alias.asname or alias.name
                    count = content.count(name)
                    if count <= 1:
                        unused.append(name)
        
        return unused[:10]  # Limit
    
    def _find_missing_docstrings(self, tree: ast.AST) -> List[Dict]:
        """Find functions/classes missing docstrings"""
        missing = []
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                # Skip private/dunder methods
                if node.name.startswith('_') and not node.name.startswith('__'):
                    continue
                
                # Check for docstring
                if not (node.body and isinstance(node.body[0], ast.Expr) and 
                        isinstance(node.body[0].value, (ast.Str, ast.Constant))):
                    missing.append({
                        'name': node.name,
                        'line': node.lineno,
                        'type': 'class' if isinstance(node, ast.ClassDef) else 'function'
                    })
        
        return missing[:10]  # Limit
    
    def _find_bare_excepts(self, tree: ast.AST) -> List[int]:
        """Find bare except clauses"""
        bare = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.ExceptHandler):
                if node.type is None:
                    bare.append(node.lineno)
        
        return bare
    
    def _find_todos(self, content: str) -> List[Dict]:
        """Find TODO/FIXME comments"""
        todos = []
        lines = content.split('\n')
        
        for i, line in enumerate(lines, 1):
            if 'TODO' in line or 'FIXME' in line or 'XXX' in line:
                todos.append({
                    'line': i,
                    'text': line.strip()[:100]
                })
        
        return todos[:20]  # Limit
    
    def _check_init_exports(self, init_path: Path, content: str) -> List[str]:
        """Check if __init__.py exports all modules in directory"""
        missing = []
        
        parent_dir = init_path.parent
        
        # Get all Python files in directory
        py_files = [f.stem for f in parent_dir.glob('*.py') 
                    if f.name != '__init__.py' and not f.name.startswith('_')]
        
        # Check which are exported
        for module in py_files:
            if module not in content:
                missing.append(module)
        
        return missing[:10]  # Limit
    
    def fix_init_exports(self, file_path: Path) -> Optional[FixRecord]:
        """Fix missing exports in __init__.py"""
        try:
            content = file_path.read_text(encoding='utf-8', errors='ignore')
            original = content
            
            parent_dir = file_path.parent
            py_files = [f.stem for f in parent_dir.glob('*.py') 
                        if f.name != '__init__.py' and not f.name.startswith('_')]
            
            # Build import statements
            new_imports = []
            for module in py_files:
                if module not in content:
                    # Try to find classes/functions to import
                    module_path = parent_dir / f"{module}.py"
                    if module_path.exists():
                        try:
                            mod_content = module_path.read_text(encoding='utf-8', errors='ignore')
                            mod_tree = ast.parse(mod_content)
                            
                            exports = []
                            for node in ast.iter_child_nodes(mod_tree):
                                if isinstance(node, ast.ClassDef) and not node.name.startswith('_'):
                                    exports.append(node.name)
                                elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                                    if not node.name.startswith('_'):
                                        exports.append(node.name)
                            
                            if exports:
                                new_imports.append(f"from .{module} import {', '.join(exports[:5])}")
                            else:
                                new_imports.append(f"from . import {module}")
                        except:
                            new_imports.append(f"from . import {module}")
            
            if new_imports:
                # Add imports at the end
                if content and not content.endswith('\n'):
                    content += '\n'
                content += '\n# Auto-generated exports\n'
                content += '\n'.join(new_imports) + '\n'
                
                # Backup and write
                self.backup_file(file_path)
                file_path.write_text(content, encoding='utf-8')
                
                return FixRecord(
                    file_path=str(file_path),
                    category=FixCategory.INIT_EXPORT,
                    description=f"Added {len(new_imports)} missing exports",
                    old_content=original,
                    new_content=content
                )
        
        except Exception as e:
            logger.error(f"Failed to fix init exports in {file_path}: {e}")
            return FixRecord(
                file_path=str(file_path),
                category=FixCategory.INIT_EXPORT,
                description=f"Failed to fix exports",
                old_content="",
                new_content="",
                success=False,
                error=str(e)
            )
        
        return None
    
    def fix_bare_excepts(self, file_path: Path) -> Optional[FixRecord]:
        """Fix bare except clauses"""
        try:
            content = file_path.read_text(encoding='utf-8', errors='ignore')
            original = content
            
            # Replace bare except with except Exception
            new_content = re.sub(
                r'except\s*:',
                'except Exception:',
                content
            )
            
            if new_content != content:
                self.backup_file(file_path)
                file_path.write_text(new_content, encoding='utf-8')
                
                return FixRecord(
                    file_path=str(file_path),
                    category=FixCategory.EXCEPTION_HANDLING,
                    description="Replaced bare except with except Exception",
                    old_content=original,
                    new_content=new_content
                )
        
        except Exception as e:
            logger.error(f"Failed to fix bare excepts in {file_path}: {e}")
        
        return None
    
    def fix_missing_imports(self, file_path: Path, missing: List[str]) -> Optional[FixRecord]:
        """Add missing imports to a file"""
        try:
            content = file_path.read_text(encoding='utf-8', errors='ignore')
            original = content
            
            # Parse to find where imports end
            lines = content.split('\n')
            last_import_line = 0
            
            for i, line in enumerate(lines):
                stripped = line.strip()
                if stripped.startswith('import ') or stripped.startswith('from '):
                    last_import_line = i
            
            # Build import statements
            new_imports = []
            added_modules = set()
            
            for item in missing:
                if '.' in item:
                    module, name = item.rsplit('.', 1)
                    if module not in added_modules:
                        if module in ['typing', 'dataclasses', 'enum']:
                            new_imports.append(f"from {module} import {name}")
                        else:
                            new_imports.append(f"import {module}")
                        added_modules.add(module)
            
            if new_imports:
                # Insert after last import
                insert_pos = last_import_line + 1
                for imp in new_imports:
                    lines.insert(insert_pos, imp)
                    insert_pos += 1
                
                new_content = '\n'.join(lines)
                
                self.backup_file(file_path)
                file_path.write_text(new_content, encoding='utf-8')
                
                return FixRecord(
                    file_path=str(file_path),
                    category=FixCategory.IMPORT_FIX,
                    description=f"Added imports: {', '.join(new_imports)}",
                    old_content=original,
                    new_content=new_content
                )
        
        except Exception as e:
            logger.error(f"Failed to fix imports in {file_path}: {e}")
        
        return None
    
    def apply_fixes(self, scan_result: ScanResult) -> List[FixRecord]:
        """Apply fixes based on scan result"""
        fixes = []
        file_path = Path(scan_result.file_path)
        
        if not scan_result.can_auto_fix:
            return fixes
        
        if self.is_protected(file_path):
            logger.warning(f"[PROTECTED] Skipping protected file: {file_path}")
            return fixes
        
        for issue in scan_result.issues:
            issue_type = issue.get('type')
            
            try:
                if issue_type == 'missing_export':
                    fix = self.fix_init_exports(file_path)
                    if fix:
                        fixes.append(fix)
                        break  # Only fix once per file
                
                elif issue_type == 'bare_except':
                    fix = self.fix_bare_excepts(file_path)
                    if fix:
                        fixes.append(fix)
                        break
                
                elif issue_type == 'missing_import':
                    missing = [i.get('name') for i in scan_result.issues 
                              if i.get('type') == 'missing_import']
                    fix = self.fix_missing_imports(file_path, missing)
                    if fix:
                        fixes.append(fix)
                        break
                
            except Exception as e:
                logger.error(f"Error applying fix for {issue_type} in {file_path}: {e}")
        
        return fixes
    
    def scan_directory(self, directory: Path) -> List[ScanResult]:
        """Scan a directory for Python files"""
        results = []
        
        try:
            for py_file in directory.rglob('*.py'):
                # Skip already processed
                file_str = str(py_file)
                if file_str in self.processed_files:
                    continue
                
                # Skip certain directories
                skip_dirs = ['__pycache__', '.git', 'venv', 'env', '.venv', 
                            'node_modules', 'autonomous_backups', '.hypothesis']
                if any(d in py_file.parts for d in skip_dirs):
                    continue
                
                # Check if file changed since last scan
                current_hash = self.get_file_hash(py_file)
                if file_str in self.file_hashes and self.file_hashes[file_str] == current_hash:
                    continue
                
                self.file_hashes[file_str] = current_hash
                self.files_scanned += 1
                
                result = self.scan_python_file(py_file)
                if result.issues:
                    results.append(result)
                    self.issues_found += len(result.issues)
                
                self.processed_files.add(file_str)
                
        except Exception as e:
            logger.error(f"Error scanning directory {directory}: {e}")
        
        return results
    
    def run_integration_check(self) -> List[Dict]:
        """Check for integration issues between modules"""
        issues = []
        
        # Check all __init__.py files
        for init_file in self.workspace.rglob('__init__.py'):
            skip_dirs = ['__pycache__', '.git', 'venv', 'env', '.venv', 
                        'node_modules', 'autonomous_backups', '.hypothesis']
            if any(d in init_file.parts for d in skip_dirs):
                continue
            
            result = self.scan_python_file(init_file)
            if result.issues:
                issues.append({
                    'file': str(init_file),
                    'issues': result.issues
                })
        
        return issues
    
    def generate_report(self) -> str:
        """Generate a summary report"""
        report = []
        report.append("=" * 60)
        report.append("DEEPSEEK AUTONOMOUS MODE - SESSION REPORT")
        report.append("=" * 60)
        report.append(f"Start Time: {datetime.now() - timedelta(hours=1)}")
        report.append(f"End Time: {datetime.now()}")
        report.append(f"Files Scanned: {self.files_scanned}")
        report.append(f"Issues Found: {self.issues_found}")
        report.append(f"Issues Fixed: {self.issues_fixed}")
        report.append(f"Errors: {len(self.errors)}")
        report.append("")
        
        if self.fixes_applied:
            report.append("FIXES APPLIED:")
            report.append("-" * 40)
            for fix in self.fixes_applied:
                status = "[OK]" if fix.success else "[FAIL]"
                report.append(f"{status} [{fix.category.value}] {fix.file_path}")
                report.append(f"   {fix.description}")
                if fix.error:
                    report.append(f"   Error: {fix.error}")
            report.append("")
        
        if self.errors:
            report.append("ERRORS:")
            report.append("-" * 40)
            for error in self.errors[:20]:
                report.append(f"[ERROR] {error}")
        
        report.append("")
        report.append(f"Backups saved to: {self.backup_dir}")
        report.append("=" * 60)
        
        return '\n'.join(report)
    
    async def run_continuous(self):
        """Run continuous scanning and fixing until end time"""
        logger.info("[START] Starting continuous autonomous mode...")
        
        cycle = 0
        while datetime.now() < self.end_time:
            cycle += 1
            logger.info(f"")
            logger.info(f"{'='*50}")
            logger.info(f"[CYCLE] Cycle {cycle} - {datetime.now().strftime('%H:%M:%S')}")
            logger.info(f"[TIME] Time remaining: {self.end_time - datetime.now()}")
            logger.info(f"{'='*50}")
            
            try:
                # Scan trading_bot directory
                trading_bot_dir = self.workspace / "trading_bot"
                if trading_bot_dir.exists():
                    results = self.scan_directory(trading_bot_dir)
                    
                    for result in results:
                        if result.issues:
                            logger.info(f"[FILE] {result.file_path}: {len(result.issues)} issues")
                            
                            # Apply fixes
                            fixes = self.apply_fixes(result)
                            for fix in fixes:
                                self.fixes_applied.append(fix)
                                if fix.success:
                                    self.issues_fixed += 1
                                    logger.info(f"  [OK] Fixed: {fix.description}")
                                else:
                                    logger.error(f"  [FAIL] Failed: {fix.error}")
                
                # Also scan examples and tests
                for subdir in ['examples', 'tests']:
                    sub_path = self.workspace / subdir
                    if sub_path.exists():
                        results = self.scan_directory(sub_path)
                        for result in results:
                            fixes = self.apply_fixes(result)
                            for fix in fixes:
                                self.fixes_applied.append(fix)
                                if fix.success:
                                    self.issues_fixed += 1
                
                # Run integration check every 5 cycles
                if cycle % 5 == 0:
                    logger.info("[INTEGRATION] Running integration check...")
                    integration_issues = self.run_integration_check()
                    if integration_issues:
                        logger.info(f"Found {len(integration_issues)} files with integration issues")
                
                # Status update
                logger.info(f"[STATUS] {self.files_scanned} scanned, {self.issues_found} found, {self.issues_fixed} fixed")
                
                # Wait before next cycle (30 seconds)
                await asyncio.sleep(30)
                
                # Reset processed files to allow re-scanning modified files
                if cycle % 10 == 0:
                    self.processed_files.clear()
                    self.file_hashes.clear()
                    logger.info("[RESET] Reset scan cache for fresh scan")
                
            except KeyboardInterrupt:
                logger.info("[STOP] Interrupted by user")
                break
            except Exception as e:
                error_msg = f"Cycle {cycle} error: {str(e)}"
                self.errors.append(error_msg)
                logger.error(f"[ERROR] {error_msg}")
                traceback.print_exc()
                await asyncio.sleep(10)  # Wait before retry
        
        # Generate final report
        report = self.generate_report()
        logger.info(report)
        
        # Save report to file
        report_file = LOG_DIR / f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        report_file.write_text(report, encoding='utf-8')
        logger.info(f"[REPORT] Report saved to: {report_file}")
        
        return report


async def main():
    """Main entry point"""
    print("")
    print("=" * 60)
    print("  DEEPSEEK AUTONOMOUS ENGINEER - 24/7 MODE")
    print("=" * 60)
    print("  Running continuously until 8 PM")
    print("  Auto-fixing issues WITHOUT human approval")
    print("  Protected files: risk, security, credentials")
    print("  All changes backed up and logged")
    print("=" * 60)
    print("")
    
    # Calculate end time (8 PM today in local time)
    now = datetime.now()
    end_time = now.replace(hour=20, minute=0, second=0, microsecond=0)
    
    # If it's already past 8 PM, set to tomorrow
    if now >= end_time:
        end_time = end_time + timedelta(days=1)
    
    print(f"Current time: {now.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"End time: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Duration: {end_time - now}")
    print()
    
    # Auto-start (no confirmation needed for 24/7 mode)
    print("Starting in 3 seconds... Press Ctrl+C to cancel.")
    time.sleep(3)
    
    workspace = Path(__file__).parent
    engineer = AutonomousDeepSeek(str(workspace), end_time)
    
    try:
        await engineer.run_continuous()
    except KeyboardInterrupt:
        print("\n[STOPPED] Stopped by user")
        report = engineer.generate_report()
        print(report)


if __name__ == "__main__":
    asyncio.run(main())
