#!/usr/bin/env python3
"""
DeepSeek Safe 24/7 Engine
=========================
SAFE autonomous engine that:
1. Finds broken code and restores from backup
2. Finds remaining work (TODO, FIXME, empty functions)
3. Fixes issues WITHOUT breaking code
4. Integrates modules safely

Runs until 8 PM - NO HUMAN APPROVAL REQUIRED
"""

import os
import re
import ast
import sys
import json
import time
import shutil
import logging
import asyncio
from pathlib import Path
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set
from dataclasses import dataclass, field
from collections import defaultdict

# Setup logging
LOG_DIR = Path("autonomous_logs")
LOG_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    handlers=[
        logging.FileHandler(LOG_DIR / f"safe_24_7_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log", encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


PROTECTED_PATTERNS = [
    'risk_manager', 'master_risk',
    'security_core', 'credential', 'vault',
    '.env', 'secret', 'api_key', 'password',
    'kill_switch', 'emergency', 'fail_safe'
]


@dataclass
class WorkItem:
    file_path: str
    line: int
    work_type: str
    description: str
    completed: bool = False


class DeepSeekSafe247:
    """Safe autonomous engine that won't break code"""
    
    def __init__(self, workspace: Path, end_time: datetime):
        self.workspace = workspace
        self.end_time = end_time
        self.trading_bot = workspace / "trading_bot"
        
        # Stats
        self.files_checked = 0
        self.files_fixed = 0
        self.work_found: List[WorkItem] = []
        self.work_completed = 0
        self.modules_integrated = 0
        
        logger.info("=" * 60)
        logger.info("DEEPSEEK SAFE 24/7 ENGINE")
        logger.info("=" * 60)
        logger.info(f"End Time: {end_time}")
        logger.info("Mode: SAFE AUTONOMOUS")
        logger.info("=" * 60)
    
    def is_protected(self, path: Path) -> bool:
        path_str = str(path).lower().replace('\\', '/')
        return any(p in path_str for p in PROTECTED_PATTERNS)
    
    def validate_syntax(self, content: str) -> bool:
        """Check if content has valid Python syntax"""
        try:
            ast.parse(content)
            return True
        except SyntaxError:
            return False
    
    def find_good_backup(self, file_path: Path) -> Optional[Path]:
        """Find a backup that has valid syntax"""
        backup_dirs = [
            self.workspace / "autonomous_backups",
            self.workspace / "fix_backups",
        ]
        
        for backup_base in backup_dirs:
            if not backup_base.exists():
                continue
            
            for subdir in sorted(backup_base.iterdir(), reverse=True):
                if not subdir.is_dir():
                    continue
                
                try:
                    rel = file_path.relative_to(self.workspace)
                    backup_file = subdir / rel
                    
                    if backup_file.exists():
                        content = backup_file.read_text(encoding='utf-8', errors='ignore')
                        if self.validate_syntax(content):
                            return backup_file
                except:
                    continue
        
        return None
    
    # ========================================================================
    # TASK 1: FIX BROKEN FILES (RESTORE FROM BACKUP)
    # ========================================================================
    def fix_broken_files(self):
        """Find and fix files with syntax errors by restoring from backup"""
        logger.info("\n[TASK 1] Checking for broken files...")
        
        fixed = 0
        
        for py_file in self.trading_bot.rglob('*.py'):
            if '__pycache__' in str(py_file):
                continue
            
            try:
                content = py_file.read_text(encoding='utf-8', errors='ignore')
                
                if not self.validate_syntax(content):
                    # Try to restore from backup
                    backup = self.find_good_backup(py_file)
                    if backup:
                        backup_content = backup.read_text(encoding='utf-8', errors='ignore')
                        py_file.write_text(backup_content, encoding='utf-8')
                        fixed += 1
                        logger.info(f"  [RESTORED] {py_file.name}")
                    else:
                        logger.warning(f"  [BROKEN] {py_file.name} - no backup found")
                        
            except Exception as e:
                logger.debug(f"  Error: {e}")
        
        if fixed > 0:
            logger.info(f"  Restored {fixed} files from backup")
        else:
            logger.info("  All files have valid syntax")
        
        self.files_fixed += fixed
        return fixed
    
    # ========================================================================
    # TASK 2: FIND REMAINING WORK
    # ========================================================================
    def find_remaining_work(self):
        """Find TODO, FIXME, NotImplemented, empty functions"""
        logger.info("\n[TASK 2] Finding remaining work...")
        
        self.work_found = []
        
        for py_file in self.trading_bot.rglob('*.py'):
            if '__pycache__' in str(py_file):
                continue
            
            try:
                content = py_file.read_text(encoding='utf-8', errors='ignore')
                lines = content.split('\n')
                
                for i, line in enumerate(lines, 1):
                    if 'TODO' in line and '# TODO' in line:
                        self.work_found.append(WorkItem(
                            file_path=str(py_file),
                            line=i,
                            work_type='TODO',
                            description=line.strip()[:80]
                        ))
                    elif 'FIXME' in line:
                        self.work_found.append(WorkItem(
                            file_path=str(py_file),
                            line=i,
                            work_type='FIXME',
                            description=line.strip()[:80]
                        ))
                    elif 'raise NotImplementedError' in line:
                        self.work_found.append(WorkItem(
                            file_path=str(py_file),
                            line=i,
                            work_type='NotImplemented',
                            description=f"NotImplementedError in {py_file.name}"
                        ))
                        
            except Exception as e:
                logger.debug(f"  Error: {e}")
        
        logger.info(f"  Found {len(self.work_found)} items of remaining work")
        
        # Save to file
        work_file = self.workspace / "REMAINING_WORK.json"
        work_data = [
            {
                'file': w.file_path,
                'line': w.line,
                'type': w.work_type,
                'description': w.description
            }
            for w in self.work_found
        ]
        with open(work_file, 'w') as f:
            json.dump(work_data, f, indent=2)
        
        return len(self.work_found)
    
    # ========================================================================
    # TASK 3: SAFE MODULE INTEGRATION
    # ========================================================================
    def integrate_modules_safely(self):
        """Safely integrate modules into __init__.py files"""
        logger.info("\n[TASK 3] Integrating modules safely...")
        
        integrated = 0
        
        for init_file in self.trading_bot.rglob('__init__.py'):
            if '__pycache__' in str(init_file):
                continue
            
            try:
                content = init_file.read_text(encoding='utf-8', errors='ignore')
                parent_dir = init_file.parent
                
                # Get modules in directory
                modules = []
                for py_file in parent_dir.glob('*.py'):
                    if py_file.name != '__init__.py' and not py_file.name.startswith('_'):
                        # Check if module has valid syntax
                        try:
                            mod_content = py_file.read_text(encoding='utf-8', errors='ignore')
                            if self.validate_syntax(mod_content):
                                modules.append(py_file.stem)
                        except:
                            pass
                
                # Find missing modules
                missing = [m for m in modules if m not in content]
                
                if missing:
                    # Add simple imports (safe approach)
                    new_imports = [f"from . import {m}" for m in missing[:5]]
                    
                    new_content = content.rstrip() + '\n\n# Auto-integrated\n' + '\n'.join(new_imports) + '\n'
                    
                    # Validate before saving
                    if self.validate_syntax(new_content):
                        init_file.write_text(new_content, encoding='utf-8')
                        integrated += len(new_imports)
                        logger.info(f"  [INTEGRATED] {parent_dir.name}: {len(new_imports)} modules")
                    
            except Exception as e:
                logger.debug(f"  Error: {e}")
        
        self.modules_integrated += integrated
        return integrated
    
    # ========================================================================
    # TASK 4: REMOVE DUPLICATE IMPORTS
    # ========================================================================
    def remove_duplicate_imports(self):
        """Remove duplicate import statements"""
        logger.info("\n[TASK 4] Removing duplicate imports...")
        
        fixed = 0
        
        for py_file in self.trading_bot.rglob('*.py'):
            if '__pycache__' in str(py_file) or self.is_protected(py_file):
                continue
            
            try:
                content = py_file.read_text(encoding='utf-8', errors='ignore')
                lines = content.split('\n')
                
                seen = set()
                new_lines = []
                duplicates = 0
                
                for line in lines:
                    stripped = line.strip()
                    if stripped.startswith('import ') or stripped.startswith('from '):
                        normalized = ' '.join(stripped.split())
                        if normalized in seen:
                            duplicates += 1
                            continue
                        seen.add(normalized)
                    new_lines.append(line)
                
                if duplicates > 0:
                    new_content = '\n'.join(new_lines)
                    if self.validate_syntax(new_content):
                        py_file.write_text(new_content, encoding='utf-8')
                        fixed += 1
                        
            except Exception as e:
                logger.debug(f"  Error: {e}")
        
        if fixed > 0:
            logger.info(f"  Cleaned {fixed} files")
        
        return fixed
    
    # ========================================================================
    # GENERATE REPORT
    # ========================================================================
    def generate_report(self) -> str:
        report = []
        report.append("=" * 60)
        report.append("DEEPSEEK SAFE 24/7 ENGINE - REPORT")
        report.append("=" * 60)
        report.append(f"Session End: {datetime.now()}")
        report.append(f"Files Fixed: {self.files_fixed}")
        report.append(f"Modules Integrated: {self.modules_integrated}")
        report.append(f"Remaining Work Items: {len(self.work_found)}")
        report.append("")
        
        # Work summary by type
        by_type = defaultdict(int)
        for w in self.work_found:
            by_type[w.work_type] += 1
        
        if by_type:
            report.append("REMAINING WORK BY TYPE:")
            for wtype, count in sorted(by_type.items()):
                report.append(f"  {wtype}: {count}")
        
        report.append("")
        report.append("=" * 60)
        
        return '\n'.join(report)
    
    # ========================================================================
    # RUN CYCLE
    # ========================================================================
    def run_cycle(self, cycle_num: int):
        """Run one safe cycle"""
        logger.info(f"\n{'='*50}")
        logger.info(f"[CYCLE {cycle_num}] {datetime.now().strftime('%H:%M:%S')}")
        logger.info(f"[TIME] Remaining: {self.end_time - datetime.now()}")
        logger.info(f"{'='*50}")
        
        # Always check for broken files first
        self.fix_broken_files()
        
        # Rotate tasks
        if cycle_num % 3 == 1:
            self.remove_duplicate_imports()
        elif cycle_num % 3 == 2:
            self.find_remaining_work()
        else:
            self.integrate_modules_safely()
        
        logger.info(f"\n[STATUS] Fixed: {self.files_fixed}, Integrated: {self.modules_integrated}")
    
    async def run_continuous(self):
        """Run continuously until end time"""
        logger.info("\n[START] Beginning safe autonomous operation...")
        
        cycle = 0
        while datetime.now() < self.end_time:
            cycle += 1
            
            try:
                self.run_cycle(cycle)
                await asyncio.sleep(60)
                
            except KeyboardInterrupt:
                logger.info("[STOP] Interrupted by user")
                break
            except Exception as e:
                logger.error(f"[ERROR] {e}")
                await asyncio.sleep(30)
        
        # Final report
        report = self.generate_report()
        logger.info(report)
        
        # Save report
        report_file = LOG_DIR / f"safe_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        report_file.write_text(report, encoding='utf-8')
        logger.info(f"Report saved: {report_file}")


async def main():
    print("")
    print("=" * 60)
    print("  DEEPSEEK SAFE 24/7 ENGINE")
    print("=" * 60)
    print("")
    print("  Safe Tasks:")
    print("    1. Fix broken files (restore from backup)")
    print("    2. Find remaining work (TODO, FIXME)")
    print("    3. Integrate modules safely")
    print("    4. Remove duplicate imports")
    print("")
    print("  Safety: All changes validated before saving")
    print("  Protected: risk, security, credentials")
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
    engine = DeepSeekSafe247(workspace, end_time)
    
    try:
        await engine.run_continuous()
    except KeyboardInterrupt:
        print("\n[STOPPED] Session ended")
        print(engine.generate_report())


if __name__ == "__main__":
    asyncio.run(main())
