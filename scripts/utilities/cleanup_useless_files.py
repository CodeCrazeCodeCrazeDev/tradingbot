"""
Cleanup Script - Remove Useless Files and Code
Identifies and removes duplicate, obsolete, and unnecessary files
"""

import os
import sys
import io
import shutil
from pathlib import Path
from datetime import datetime
import json

# Set UTF-8 encoding for Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

class CleanupManager:
    """Manages cleanup of useless files"""
    
    def __init__(self, root_dir: str):
        self.root_dir = Path(root_dir)
        self.removed_files = []
        self.removed_dirs = []
        self.space_saved = 0
        
    def cleanup_pycache(self):
        """Remove all __pycache__ directories"""
        print("\n🗑️  Removing __pycache__ directories...")
        
        for pycache in self.root_dir.rglob('__pycache__'):
            if pycache.is_dir():
                size = sum(f.stat().st_size for f in pycache.rglob('*') if f.is_file())
                shutil.rmtree(pycache)
                self.removed_dirs.append(str(pycache))
                self.space_saved += size
                print(f"   ✅ Removed: {pycache}")
        
    def cleanup_pyc_files(self):
        """Remove all .pyc files"""
        print("\n🗑️  Removing .pyc files...")
        
        for pyc in self.root_dir.rglob('*.pyc'):
            if pyc.is_file():
                size = pyc.stat().st_size
                pyc.unlink()
                self.removed_files.append(str(pyc))
                self.space_saved += size
                print(f"   ✅ Removed: {pyc}")
    
    def cleanup_old_backups(self):
        """Remove old backup directories (keep only latest)"""
        print("\n🗑️  Cleaning up old backups...")
        
        backups_dir = self.root_dir / 'backups'
        if backups_dir.exists():
            # Get all backup directories
            backup_dirs = [d for d in backups_dir.iterdir() if d.is_dir()]
            
            if len(backup_dirs) > 1:
                # Sort by modification time, keep only the latest
                backup_dirs.sort(key=lambda x: x.stat().st_mtime, reverse=True)
                
                for old_backup in backup_dirs[1:]:  # Remove all except the latest
                    size = sum(f.stat().st_size for f in old_backup.rglob('*') if f.is_file())
                    shutil.rmtree(old_backup)
                    self.removed_dirs.append(str(old_backup))
                    self.space_saved += size
                    print(f"   ✅ Removed old backup: {old_backup.name}")
        
        # Remove code_backups directory (duplicate)
        code_backups = self.root_dir / 'code_backups'
        if code_backups.exists():
            size = sum(f.stat().st_size for f in code_backups.rglob('*') if f.is_file())
            shutil.rmtree(code_backups)
            self.removed_dirs.append(str(code_backups))
            self.space_saved += size
            print(f"   ✅ Removed: code_backups/")
    
    def cleanup_duplicate_docs(self):
        """Remove duplicate documentation files"""
        print("\n🗑️  Removing duplicate documentation...")
        
        # List of duplicate/obsolete docs to remove
        duplicate_docs = [
            'BATCH_FILES_TEST_REPORT.md',
            'RUN_TESTS.md',
            'SAFE_TESTING_GUIDE.md',
            '100_ITERATION_RESULTS.md',
            'ADVANCED_SYSTEM_STATUS.md',
            'ALPHAALGO_DEPLOYMENT_GUIDE.md',  # Duplicate of main guide
            'AUDIT_SUMMARY.md',  # Covered in comprehensive audit
            'AUTOMATED_DEPLOYMENT_COMPLETE.md',
            'AUTONOMOUS_AI_GUIDE.md',
            'BOT_STARTED_LIVE_TRADING.md',
            'COMPLETE_AUTOMATION_SUMMARY.md',
            'COMPLETE_SYSTEM_SUMMARY.md',
            'CRITICAL_FIXES_ROADMAP.md',
            'DEPLOYMENT_COMPLETE.md',
            'DEPLOYMENT_DECISION.md',
            'DEPLOYMENT_LOG_EXAMPLE.md',
            'DEPLOYMENT_SUMMARY.md',
            'DOCKER_PERFECT_RUN.md',
            'ENHANCED_BOT_SUMMARY.md',
            'FEATURE_ROADMAP.md',
            'FINAL_AUTONOMOUS_SUMMARY.md',
            'FINAL_COMPLETE_GUIDE.md',
            'FINAL_DEPLOYMENT_STATUS.md',
            'FINAL_SUMMARY.md',
            'FIXES_APPLIED_SUMMARY.md',
            'FULL_AUTOMATION_GUIDE.md',
            'INSTALL_AND_RUN.md',
            'MAJOR_ISSUES_FIXED.md',
            'PERFECT_BOT_COMPLETE.md',
            'PRODUCTION_READY.md',
            'RUN_STATUS.md',
            'SURVIVAL_SYSTEM_CHECKLIST.md',
            'SURVIVAL_SYSTEM_COMPLETION_REPORT.md',
            'SURVIVAL_SYSTEM_IMPLEMENTATION.md',
            'THREE_PILLARS_IMPLEMENTATION.md',
            'TRANSFORMATION_COMPLETE_SUMMARY.md',
            'ULTIMATE_BOT_SUCCESS.md',
        ]
        
        for doc in duplicate_docs:
            doc_path = self.root_dir / doc
            if doc_path.exists():
                size = doc_path.stat().st_size
                doc_path.unlink()
                self.removed_files.append(str(doc_path))
                self.space_saved += size
                print(f"   ✅ Removed: {doc}")
    
    def cleanup_duplicate_scripts(self):
        """Remove duplicate/obsolete scripts"""
        print("\n🗑️  Removing duplicate scripts...")
        
        duplicate_scripts = [
            'mvp_bot_fixed.py',  # Keep mvp_bot.py
            'mvp_bot_enhanced.py',  # Keep mvp_bot.py
            'deploy_production_ascii.py',  # Duplicate of deploy_production.py
            'safe_autonomous_tester.py',  # Obsolete
            'test_bot_comprehensive.py',  # Use pytest instead
            'test_run.py',  # Use pytest instead
            'validate_fixes.py',  # Obsolete
            'verify_deployment.py',  # Covered by deployment scripts
            'auto_fix_system.py',  # Obsolete
            'run_bot_now.py',  # Duplicate
            'start_bot.py',  # Duplicate
            'start_trading_now.bat',  # Duplicate
            'test_all_batch_files.bat',  # Obsolete
        ]
        
        for script in duplicate_scripts:
            script_path = self.root_dir / script
            if script_path.exists():
                size = script_path.stat().st_size
                script_path.unlink()
                self.removed_files.append(str(script_path))
                self.space_saved += size
                print(f"   ✅ Removed: {script}")
    
    def cleanup_duplicate_requirements(self):
        """Remove duplicate requirements files"""
        print("\n🗑️  Removing duplicate requirements files...")
        
        # Keep only requirements.txt and requirements-extras.txt
        duplicate_reqs = [
            'requirements_complete.txt',
            'requirements_integrated_system.txt',
            'requirements_mvp.txt',
            'requirements_phase2.txt',
            'requirements_pipeline.txt',
            'requirements_survival_system.txt',
            'requirements_three_pillars.txt',
        ]
        
        for req in duplicate_reqs:
            req_path = self.root_dir / req
            if req_path.exists():
                size = req_path.stat().st_size
                req_path.unlink()
                self.removed_files.append(str(req_path))
                self.space_saved += size
                print(f"   ✅ Removed: {req}")
    
    def cleanup_empty_dirs(self):
        """Remove empty directories"""
        print("\n🗑️  Removing empty directories...")
        
        empty_dirs = [
            '.pytest_cache',
            '.venv',
            'code_backups',
            'dashboard',
            'data',
            'logs',
            'visualizations',
            'deployment_logs',
        ]
        
        for dir_name in empty_dirs:
            dir_path = self.root_dir / dir_name
            if dir_path.exists() and dir_path.is_dir():
                # Check if empty or only has empty subdirs
                if not any(dir_path.rglob('*')):
                    shutil.rmtree(dir_path)
                    self.removed_dirs.append(str(dir_path))
                    print(f"   ✅ Removed empty: {dir_name}/")
    
    def cleanup_log_files(self):
        """Remove old log files"""
        print("\n🗑️  Removing old log files...")
        
        log_files = [
            'deployment_check.log',
            'production_deployment.log',
            'verification.log',
        ]
        
        for log in log_files:
            log_path = self.root_dir / log
            if log_path.exists():
                size = log_path.stat().st_size
                log_path.unlink()
                self.removed_files.append(str(log_path))
                self.space_saved += size
                print(f"   ✅ Removed: {log}")
    
    def cleanup_obsolete_configs(self):
        """Remove obsolete config files"""
        print("\n🗑️  Removing obsolete configs...")
        
        # Keep only essential configs
        obsolete_configs = [
            'elite_config.yaml',  # Duplicate
            'deployment_state.json',  # Temporary
        ]
        
        for config in obsolete_configs:
            config_path = self.root_dir / config
            if config_path.exists():
                size = config_path.stat().st_size
                config_path.unlink()
                self.removed_files.append(str(config_path))
                self.space_saved += size
                print(f"   ✅ Removed: {config}")
    
    def cleanup_duplicate_readmes(self):
        """Remove duplicate README files"""
        print("\n🗑️  Removing duplicate README files...")
        
        # Keep only main README.md
        duplicate_readmes = [
            'README_CLOUD.md',
            'README_ELITE_TRADING_SYSTEM.md',
            'README_FIXES.md',
            'README_INTEGRATED_SYSTEM.md',
            'README_MULTI_SYMBOL.md',
            'README_MVP.md',
            'README_SURVIVAL_SYSTEM.md',
        ]
        
        for readme in duplicate_readmes:
            readme_path = self.root_dir / readme
            if readme_path.exists():
                size = readme_path.stat().st_size
                readme_path.unlink()
                self.removed_files.append(str(readme_path))
                self.space_saved += size
                print(f"   ✅ Removed: {readme}")
    
    def generate_report(self):
        """Generate cleanup report"""
        print("\n" + "="*80)
        print("CLEANUP REPORT")
        print("="*80)
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'files_removed': len(self.removed_files),
            'directories_removed': len(self.removed_dirs),
            'space_saved_bytes': self.space_saved,
            'space_saved_mb': round(self.space_saved / (1024 * 1024), 2),
            'removed_files': self.removed_files,
            'removed_directories': self.removed_dirs
        }
        
        # Save report
        report_path = self.root_dir / 'cleanup_report.json'
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\n📊 Summary:")
        print(f"   Files removed: {report['files_removed']}")
        print(f"   Directories removed: {report['directories_removed']}")
        print(f"   Space saved: {report['space_saved_mb']} MB")
        print(f"\n📁 Report saved to: cleanup_report.json")
        
        return report
    
    def run_full_cleanup(self):
        """Run complete cleanup"""
        print("="*80)
        print("STARTING COMPREHENSIVE CLEANUP")
        print("="*80)
        
        self.cleanup_pycache()
        self.cleanup_pyc_files()
        self.cleanup_old_backups()
        self.cleanup_duplicate_docs()
        self.cleanup_duplicate_scripts()
        self.cleanup_duplicate_requirements()
        self.cleanup_empty_dirs()
        self.cleanup_log_files()
        self.cleanup_obsolete_configs()
        self.cleanup_duplicate_readmes()
        
        report = self.generate_report()
        
        print("\n" + "="*80)
        print("✅ CLEANUP COMPLETE!")
        print("="*80)
        
        return report


def main():
    """Main cleanup function"""
    root_dir = Path(__file__).parent
    
    print("\n🧹 AlphaAlgo Cleanup Tool")
    print("="*80)
    print(f"Root directory: {root_dir}")
    print("="*80)
    
    # Confirm cleanup
    print("\n⚠️  This will remove:")
    print("   • All __pycache__ directories and .pyc files")
    print("   • Old backup directories (keep only latest)")
    print("   • Duplicate documentation files (40+ files)")
    print("   • Duplicate scripts and configs")
    print("   • Obsolete requirements files")
    print("   • Empty directories")
    print("   • Old log files")
    
    # Auto-confirm for automated execution
    print("\n✅ Auto-confirming cleanup...")
    
    cleanup = CleanupManager(root_dir)
    report = cleanup.run_full_cleanup()
    
    print(f"\n🎉 Successfully cleaned up {report['space_saved_mb']} MB!")


if __name__ == '__main__':
    main()
