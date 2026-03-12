#!/usr/bin/env python3
"""
DeepSeek Comprehensive Autonomous Engineer
===========================================
Runs 24/7 until 8 PM, performing:
1. Module Integration - Connect disconnected modules
2. Gap Analysis - Find and fix missing functionality
3. Code Improvement - Refactor and optimize
4. Idea Generation - Suggest enhancements
5. Quality Assurance - Fix bugs and issues

NO HUMAN APPROVAL REQUIRED (except for protected files)
"""

import os
import re
import ast
import sys
import json
import time
import shutil
import hashlib
import logging
import asyncio
import traceback
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict

# Setup logging
LOG_DIR = Path("autonomous_logs")
LOG_DIR.mkdir(exist_ok=True)

log_file = LOG_DIR / f"comprehensive_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    handlers=[
        logging.FileHandler(log_file, encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


# ============================================================================
# PROTECTED FILES - NEVER AUTO-MODIFY
# ============================================================================
PROTECTED_PATTERNS = [
    'risk_manager', 'master_risk', 'MASTER_risk',
    'security_core', 'credential', 'vault', 
    '.env', 'secret', 'api_key', 'password', 'token',
    'auth', 'encryption', 'kill_switch', 'emergency',
    'fail_safe', 'circuit_breaker'
]


class TaskType(Enum):
    """Types of autonomous tasks"""
    INTEGRATE_MODULES = "integrate_modules"
    FIX_IMPORTS = "fix_imports"
    FIX_INIT_FILES = "fix_init_files"
    REMOVE_DUPLICATES = "remove_duplicates"
    FIX_SYNTAX = "fix_syntax"
    ADD_DOCSTRINGS = "add_docstrings"
    GENERATE_IDEAS = "generate_ideas"
    CREATE_TESTS = "create_tests"
    FIX_CIRCULAR_IMPORTS = "fix_circular_imports"


@dataclass
class TaskResult:
    """Result of a task execution"""
    task_type: TaskType
    file_path: str
    success: bool
    description: str
    changes_made: List[str] = field(default_factory=list)
    error: Optional[str] = None


@dataclass
class ImprovementIdea:
    """An idea for improving the codebase"""
    category: str
    title: str
    description: str
    priority: str  # 'critical', 'high', 'medium', 'low'
    affected_files: List[str]
    estimated_effort: str  # 'small', 'medium', 'large'


class DeepSeekComprehensiveEngineer:
    """
    Comprehensive autonomous engineer that:
    1. Integrates disconnected modules
    2. Fixes gaps and issues
    3. Generates improvement ideas
    4. Runs continuously until 8 PM
    """
    
    def __init__(self, workspace: Path, end_time: datetime):
        self.workspace = workspace
        self.end_time = end_time
        self.trading_bot_dir = workspace / "trading_bot"
        
        # Statistics
        self.files_processed = 0
        self.issues_fixed = 0
        self.modules_integrated = 0
        self.ideas_generated: List[ImprovementIdea] = []
        self.task_results: List[TaskResult] = []
        self.errors: List[str] = []
        
        # Tracking
        self.processed_files: Set[str] = set()
        self.file_hashes: Dict[str, str] = {}
        self.module_map: Dict[str, List[str]] = {}  # module -> exports
        
        # Backup
        self.backup_dir = workspace / "autonomous_backups" / datetime.now().strftime('%Y%m%d_%H%M%S')
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info("=" * 60)
        logger.info("DeepSeek Comprehensive Engineer Initialized")
        logger.info(f"Workspace: {self.workspace}")
        logger.info(f"End Time: {self.end_time}")
        logger.info(f"Backups: {self.backup_dir}")
        logger.info("=" * 60)
    
    def is_protected(self, file_path: Path) -> bool:
        """Check if file is protected"""
        path_str = str(file_path).lower().replace('\\', '/')
        return any(pattern in path_str for pattern in PROTECTED_PATTERNS)
    
    def backup_file(self, file_path: Path) -> bool:
        """Backup file before modification"""
        try:
            if not file_path.exists():
                return True
            relative = file_path.relative_to(self.workspace)
            backup_path = self.backup_dir / relative
            backup_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(file_path, backup_path)
            return True
        except Exception as e:
            logger.error(f"Backup failed: {e}")
            return False
    
    def get_file_hash(self, file_path: Path) -> str:
        """Get MD5 hash of file"""
        try:
            return hashlib.md5(file_path.read_bytes()).hexdigest()
        except:
            return ""
    
    # ========================================================================
    # TASK 1: FIX DUPLICATE IMPORTS
    # ========================================================================
    def fix_duplicate_imports(self, file_path: Path) -> Optional[TaskResult]:
        """Remove duplicate import statements"""
        try:
            content = file_path.read_text(encoding='utf-8', errors='ignore')
            lines = content.split('\n')
            
            seen_imports = set()
            new_lines = []
            duplicates_removed = 0
            
            for line in lines:
                stripped = line.strip()
                
                # Check if it's an import line
                if stripped.startswith('import ') or stripped.startswith('from '):
                    if stripped in seen_imports:
                        duplicates_removed += 1
                        continue
                    seen_imports.add(stripped)
                
                new_lines.append(line)
            
            if duplicates_removed > 0:
                new_content = '\n'.join(new_lines)
                self.backup_file(file_path)
                file_path.write_text(new_content, encoding='utf-8')
                
                return TaskResult(
                    task_type=TaskType.REMOVE_DUPLICATES,
                    file_path=str(file_path),
                    success=True,
                    description=f"Removed {duplicates_removed} duplicate imports",
                    changes_made=[f"Removed {duplicates_removed} duplicates"]
                )
        except Exception as e:
            return TaskResult(
                task_type=TaskType.REMOVE_DUPLICATES,
                file_path=str(file_path),
                success=False,
                description="Failed to remove duplicates",
                error=str(e)
            )
        return None
    
    # ========================================================================
    # TASK 2: FIX MISSING IMPORTS (SMART - NO DUPLICATES)
    # ========================================================================
    def fix_missing_imports_smart(self, file_path: Path) -> Optional[TaskResult]:
        """Add missing imports without creating duplicates"""
        try:
            content = file_path.read_text(encoding='utf-8', errors='ignore')
            
            # Parse to check syntax first
            try:
                tree = ast.parse(content)
            except SyntaxError:
                return None  # Skip files with syntax errors
            
            # Get existing imports
            existing_imports = set()
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        existing_imports.add(alias.name.split('.')[0])
                        if alias.asname:
                            existing_imports.add(alias.asname)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        existing_imports.add(node.module.split('.')[0])
                    for alias in node.names:
                        existing_imports.add(alias.name)
                        if alias.asname:
                            existing_imports.add(alias.asname)
            
            # Common imports needed
            needed_imports = {
                'logging': 'import logging',
                'asyncio': 'import asyncio',
                'json': 'import json',
                'os': 'import os',
                'sys': 'import sys',
                'Path': 'from pathlib import Path',
                'datetime': 'from datetime import datetime',
                'timedelta': 'from datetime import timedelta',
                'dataclass': 'from dataclasses import dataclass',
                'field': 'from dataclasses import field',
                'Enum': 'from enum import Enum',
                'Dict': 'from typing import Dict',
                'List': 'from typing import List',
                'Optional': 'from typing import Optional',
                'Any': 'from typing import Any',
                'Tuple': 'from typing import Tuple',
                'Set': 'from typing import Set',
            }
            
            # Find what's used but not imported
            imports_to_add = []
            for name, import_stmt in needed_imports.items():
                # Check if name is used in content but not imported
                if name in content and name not in existing_imports:
                    # Verify it's used as a name (not in string)
                    pattern = rf'\b{name}\b'
                    if re.search(pattern, content):
                        # Don't add if already have similar import
                        if import_stmt not in content:
                            imports_to_add.append(import_stmt)
                            existing_imports.add(name)
            
            if imports_to_add:
                # Find insertion point (after existing imports)
                lines = content.split('\n')
                insert_idx = 0
                for i, line in enumerate(lines):
                    stripped = line.strip()
                    if stripped.startswith('import ') or stripped.startswith('from '):
                        insert_idx = i + 1
                    elif stripped and not stripped.startswith('#') and not stripped.startswith('"""') and not stripped.startswith("'''"):
                        if insert_idx == 0:
                            insert_idx = i
                        break
                
                # Insert imports
                for imp in imports_to_add:
                    lines.insert(insert_idx, imp)
                    insert_idx += 1
                
                new_content = '\n'.join(lines)
                self.backup_file(file_path)
                file_path.write_text(new_content, encoding='utf-8')
                
                return TaskResult(
                    task_type=TaskType.FIX_IMPORTS,
                    file_path=str(file_path),
                    success=True,
                    description=f"Added {len(imports_to_add)} missing imports",
                    changes_made=imports_to_add
                )
        except Exception as e:
            logger.debug(f"Import fix error in {file_path}: {e}")
        return None
    
    # ========================================================================
    # TASK 3: FIX __init__.py FILES
    # ========================================================================
    def fix_init_file(self, init_path: Path) -> Optional[TaskResult]:
        """Fix __init__.py to export all modules"""
        try:
            content = init_path.read_text(encoding='utf-8', errors='ignore')
            parent_dir = init_path.parent
            
            # Get Python modules in directory
            modules = []
            for py_file in parent_dir.glob('*.py'):
                if py_file.name != '__init__.py' and not py_file.name.startswith('_'):
                    modules.append(py_file.stem)
            
            # Check which are missing
            missing = [m for m in modules if m not in content]
            
            if not missing:
                return None
            
            # Build new imports
            new_imports = []
            for module in missing[:10]:  # Limit to 10 at a time
                module_path = parent_dir / f"{module}.py"
                try:
                    mod_content = module_path.read_text(encoding='utf-8', errors='ignore')
                    mod_tree = ast.parse(mod_content)
                    
                    # Get exportable names
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
                # Add to file
                if content.strip():
                    new_content = content.rstrip() + '\n\n# Auto-integrated modules\n' + '\n'.join(new_imports) + '\n'
                else:
                    new_content = '"""Auto-generated module exports"""\n\n' + '\n'.join(new_imports) + '\n'
                
                self.backup_file(init_path)
                init_path.write_text(new_content, encoding='utf-8')
                
                return TaskResult(
                    task_type=TaskType.FIX_INIT_FILES,
                    file_path=str(init_path),
                    success=True,
                    description=f"Added {len(new_imports)} module exports",
                    changes_made=new_imports
                )
        except Exception as e:
            logger.debug(f"Init fix error: {e}")
        return None
    
    # ========================================================================
    # TASK 4: INTEGRATE DISCONNECTED MODULES
    # ========================================================================
    def find_disconnected_modules(self) -> List[Path]:
        """Find modules that aren't imported anywhere"""
        disconnected = []
        
        if not self.trading_bot_dir.exists():
            return disconnected
        
        # Build import graph
        all_modules = set()
        imported_modules = set()
        
        for py_file in self.trading_bot_dir.rglob('*.py'):
            if '__pycache__' in str(py_file):
                continue
            
            module_name = py_file.stem
            all_modules.add(module_name)
            
            try:
                content = py_file.read_text(encoding='utf-8', errors='ignore')
                # Find imports
                for match in re.finditer(r'from\s+\.(\w+)\s+import|from\s+trading_bot\.(\w+)', content):
                    imported = match.group(1) or match.group(2)
                    if imported:
                        imported_modules.add(imported)
            except:
                pass
        
        # Find disconnected
        for py_file in self.trading_bot_dir.rglob('*.py'):
            if '__pycache__' in str(py_file) or py_file.name == '__init__.py':
                continue
            if py_file.stem not in imported_modules:
                disconnected.append(py_file)
        
        return disconnected[:20]  # Limit
    
    def integrate_module(self, module_path: Path) -> Optional[TaskResult]:
        """Integrate a disconnected module into the system"""
        try:
            # Find the parent __init__.py
            init_path = module_path.parent / '__init__.py'
            
            if not init_path.exists():
                # Create __init__.py
                init_content = f'"""Auto-generated module exports"""\n\nfrom . import {module_path.stem}\n'
                init_path.write_text(init_content, encoding='utf-8')
                
                return TaskResult(
                    task_type=TaskType.INTEGRATE_MODULES,
                    file_path=str(init_path),
                    success=True,
                    description=f"Created __init__.py and integrated {module_path.stem}",
                    changes_made=[f"Created {init_path}", f"Added import for {module_path.stem}"]
                )
            else:
                # Add to existing __init__.py
                return self.fix_init_file(init_path)
        except Exception as e:
            return TaskResult(
                task_type=TaskType.INTEGRATE_MODULES,
                file_path=str(module_path),
                success=False,
                description="Failed to integrate module",
                error=str(e)
            )
    
    # ========================================================================
    # TASK 5: GENERATE IMPROVEMENT IDEAS
    # ========================================================================
    def analyze_for_ideas(self) -> List[ImprovementIdea]:
        """Analyze codebase and generate improvement ideas"""
        ideas = []
        
        if not self.trading_bot_dir.exists():
            return ideas
        
        # Analyze patterns
        todo_count = 0
        fixme_count = 0
        large_files = []
        missing_tests = []
        
        for py_file in self.trading_bot_dir.rglob('*.py'):
            if '__pycache__' in str(py_file):
                continue
            
            try:
                content = py_file.read_text(encoding='utf-8', errors='ignore')
                lines = content.split('\n')
                
                # Count TODOs
                todo_count += content.count('TODO')
                fixme_count += content.count('FIXME')
                
                # Large files
                if len(lines) > 500:
                    large_files.append(str(py_file))
                
                # Missing tests
                if py_file.parent.name != 'tests' and not py_file.name.startswith('test_'):
                    test_file = self.workspace / 'tests' / f'test_{py_file.name}'
                    if not test_file.exists():
                        missing_tests.append(str(py_file))
            except:
                pass
        
        # Generate ideas
        if todo_count > 10:
            ideas.append(ImprovementIdea(
                category="Technical Debt",
                title=f"Resolve {todo_count} TODO comments",
                description="Many TODO comments indicate incomplete features",
                priority="medium",
                affected_files=["Multiple files"],
                estimated_effort="large"
            ))
        
        if large_files:
            ideas.append(ImprovementIdea(
                category="Code Quality",
                title=f"Refactor {len(large_files)} large files",
                description="Files over 500 lines should be split",
                priority="medium",
                affected_files=large_files[:5],
                estimated_effort="large"
            ))
        
        if len(missing_tests) > 20:
            ideas.append(ImprovementIdea(
                category="Testing",
                title=f"Add tests for {len(missing_tests)} modules",
                description="Many modules lack unit tests",
                priority="high",
                affected_files=missing_tests[:10],
                estimated_effort="large"
            ))
        
        return ideas
    
    # ========================================================================
    # TASK 6: FIX BARE EXCEPTS
    # ========================================================================
    def fix_bare_excepts(self, file_path: Path) -> Optional[TaskResult]:
        """Replace bare except with except Exception"""
        try:
            content = file_path.read_text(encoding='utf-8', errors='ignore')
            
            # Replace bare except
            new_content = re.sub(r'except\s*:', 'except Exception:', content)
            
            if new_content != content:
                self.backup_file(file_path)
                file_path.write_text(new_content, encoding='utf-8')
                
                count = content.count('except:') - new_content.count('except:')
                return TaskResult(
                    task_type=TaskType.FIX_SYNTAX,
                    file_path=str(file_path),
                    success=True,
                    description=f"Fixed {count} bare except clauses",
                    changes_made=[f"Replaced {count} bare excepts"]
                )
        except Exception as e:
            logger.debug(f"Bare except fix error: {e}")
        return None
    
    # ========================================================================
    # MAIN PROCESSING
    # ========================================================================
    def process_file(self, file_path: Path) -> List[TaskResult]:
        """Process a single file with all tasks"""
        results = []
        
        if self.is_protected(file_path):
            logger.debug(f"[PROTECTED] Skipping: {file_path.name}")
            return results
        
        # Task 1: Remove duplicate imports
        result = self.fix_duplicate_imports(file_path)
        if result:
            results.append(result)
            self.issues_fixed += 1
        
        # Task 2: Fix missing imports (smart)
        result = self.fix_missing_imports_smart(file_path)
        if result:
            results.append(result)
            self.issues_fixed += 1
        
        # Task 3: Fix __init__.py
        if file_path.name == '__init__.py':
            result = self.fix_init_file(file_path)
            if result:
                results.append(result)
                self.modules_integrated += 1
        
        # Task 4: Fix bare excepts
        result = self.fix_bare_excepts(file_path)
        if result:
            results.append(result)
            self.issues_fixed += 1
        
        return results
    
    def run_cycle(self, cycle_num: int) -> Dict[str, Any]:
        """Run one processing cycle"""
        cycle_results = {
            'cycle': cycle_num,
            'files_processed': 0,
            'issues_fixed': 0,
            'modules_integrated': 0
        }
        
        # Process trading_bot directory
        if self.trading_bot_dir.exists():
            for py_file in self.trading_bot_dir.rglob('*.py'):
                if '__pycache__' in str(py_file) or '.hypothesis' in str(py_file):
                    continue
                
                # Check if file changed
                file_str = str(py_file)
                current_hash = self.get_file_hash(py_file)
                
                if file_str in self.file_hashes and self.file_hashes[file_str] == current_hash:
                    continue
                
                self.file_hashes[file_str] = current_hash
                
                # Process file
                results = self.process_file(py_file)
                if results:
                    for r in results:
                        self.task_results.append(r)
                        if r.success:
                            logger.info(f"[OK] {r.task_type.value}: {py_file.name} - {r.description}")
                            cycle_results['issues_fixed'] += 1
                
                cycle_results['files_processed'] += 1
                self.files_processed += 1
        
        # Process examples
        examples_dir = self.workspace / 'examples'
        if examples_dir.exists():
            for py_file in examples_dir.rglob('*.py'):
                results = self.process_file(py_file)
                for r in results:
                    if r.success:
                        self.task_results.append(r)
        
        # Process tests
        tests_dir = self.workspace / 'tests'
        if tests_dir.exists():
            for py_file in tests_dir.rglob('*.py'):
                if self.is_protected(py_file):
                    continue
                results = self.process_file(py_file)
                for r in results:
                    if r.success:
                        self.task_results.append(r)
        
        return cycle_results
    
    def generate_report(self) -> str:
        """Generate final report"""
        report = []
        report.append("=" * 70)
        report.append("DEEPSEEK COMPREHENSIVE ENGINEER - SESSION REPORT")
        report.append("=" * 70)
        report.append(f"Session End: {datetime.now()}")
        report.append(f"Files Processed: {self.files_processed}")
        report.append(f"Issues Fixed: {self.issues_fixed}")
        report.append(f"Modules Integrated: {self.modules_integrated}")
        report.append(f"Ideas Generated: {len(self.ideas_generated)}")
        report.append("")
        
        # Task summary
        task_counts = defaultdict(int)
        for result in self.task_results:
            if result.success:
                task_counts[result.task_type.value] += 1
        
        if task_counts:
            report.append("TASKS COMPLETED:")
            report.append("-" * 40)
            for task, count in sorted(task_counts.items()):
                report.append(f"  {task}: {count}")
            report.append("")
        
        # Ideas
        if self.ideas_generated:
            report.append("IMPROVEMENT IDEAS:")
            report.append("-" * 40)
            for idea in self.ideas_generated[:10]:
                report.append(f"  [{idea.priority.upper()}] {idea.title}")
                report.append(f"    Category: {idea.category}")
                report.append(f"    Effort: {idea.estimated_effort}")
            report.append("")
        
        report.append(f"Backups saved to: {self.backup_dir}")
        report.append("=" * 70)
        
        return '\n'.join(report)
    
    async def run_continuous(self):
        """Run continuously until end time"""
        logger.info("[START] Beginning continuous operation...")
        
        cycle = 0
        while datetime.now() < self.end_time:
            cycle += 1
            
            logger.info("")
            logger.info("=" * 50)
            logger.info(f"[CYCLE {cycle}] {datetime.now().strftime('%H:%M:%S')}")
            logger.info(f"[TIME] Remaining: {self.end_time - datetime.now()}")
            logger.info("=" * 50)
            
            try:
                # Run processing cycle
                results = self.run_cycle(cycle)
                
                logger.info(f"[STATUS] Processed: {results['files_processed']}, Fixed: {results['issues_fixed']}")
                
                # Every 5 cycles, find disconnected modules
                if cycle % 5 == 0:
                    logger.info("[INTEGRATION] Finding disconnected modules...")
                    disconnected = self.find_disconnected_modules()
                    for module in disconnected[:5]:
                        result = self.integrate_module(module)
                        if result and result.success:
                            logger.info(f"[INTEGRATED] {module.name}")
                            self.modules_integrated += 1
                
                # Every 10 cycles, generate ideas
                if cycle % 10 == 0:
                    logger.info("[IDEAS] Analyzing for improvements...")
                    ideas = self.analyze_for_ideas()
                    self.ideas_generated.extend(ideas)
                    for idea in ideas:
                        logger.info(f"[IDEA] {idea.title}")
                
                # Every 20 cycles, reset cache for fresh scan
                if cycle % 20 == 0:
                    self.file_hashes.clear()
                    logger.info("[RESET] Cache cleared for fresh scan")
                
                # Wait before next cycle
                await asyncio.sleep(30)
                
            except KeyboardInterrupt:
                logger.info("[STOP] Interrupted by user")
                break
            except Exception as e:
                self.errors.append(str(e))
                logger.error(f"[ERROR] Cycle {cycle}: {e}")
                traceback.print_exc()
                await asyncio.sleep(10)
        
        # Final report
        report = self.generate_report()
        logger.info(report)
        
        # Save report
        report_file = LOG_DIR / f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        report_file.write_text(report, encoding='utf-8')
        logger.info(f"[SAVED] Report: {report_file}")
        
        return report


async def main():
    print("")
    print("=" * 60)
    print("  DEEPSEEK COMPREHENSIVE AUTONOMOUS ENGINEER")
    print("=" * 60)
    print("  Tasks:")
    print("    1. Integrate disconnected modules")
    print("    2. Fix missing imports (no duplicates)")
    print("    3. Fix __init__.py exports")
    print("    4. Fix bare except clauses")
    print("    5. Generate improvement ideas")
    print("  ")
    print("  Protected: risk, security, credentials, auth")
    print("  All changes backed up")
    print("=" * 60)
    print("")
    
    # Calculate end time (8 PM)
    now = datetime.now()
    end_time = now.replace(hour=20, minute=0, second=0, microsecond=0)
    if now >= end_time:
        end_time += timedelta(days=1)
    
    print(f"Current: {now.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"End:     {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Duration: {end_time - now}")
    print("")
    print("Starting in 3 seconds...")
    time.sleep(3)
    
    workspace = Path(__file__).parent
    engineer = DeepSeekComprehensiveEngineer(workspace, end_time)
    
    try:
        await engineer.run_continuous()
    except KeyboardInterrupt:
        print("\n[STOPPED] Session ended by user")
        report = engineer.generate_report()
        print(report)


if __name__ == "__main__":
    asyncio.run(main())
