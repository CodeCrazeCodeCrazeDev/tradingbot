"""
File Organization Script
========================

This script organizes the 78+ Python files in the root directory into a proper structure.

Run this to clean up the project structure.
"""

import os
import shutil
from pathlib import Path
from typing import Dict, List

# Define organization rules
ORGANIZATION_RULES = {
    # Scripts to archive (old/deprecated)
    'archive/scripts': [
        'alphaalgo_2_0.py',
        'alphaalgo_autonomous_operator.py',
        'alphaalgo_offline_rl_integration.py',
        'alphaalgo_offline_rl_master.py',
        'alpha_deployment_manager.py',
        'adaptive_restart.py',
        'autonomous_operator.py',
        'autonomous_ai_manager.py',
    ],
    
    # Deployment scripts
    'scripts/deployment': [
        'deploy.py',
        'deploy_production.py',
        'deploy_5star_production.py',
        'auto_deploy.py',
        'deployment_audit.py',
        'final_deployment_check.py',
        'final_deployment_validation.py',
        'ci_cd_pipeline.py',
        'docker_test_runner.py',
    ],
    
    # Fix/patch scripts
    'scripts/fixes': [
        'fix_all_issues.py',
        'fix_all_issues_safe.py',
        'fix_indent.py',
        'fix_position_check.py',
        'fix_position_sizing.py',
        'fix_position_sizing_correct.py',
        'apply_critical_fixes.py',
        'auto_fix_critical_issues.py',
        'auto_fix_critical_issues_v2.py',
        'auto_fix_imports.py',
        'auto_patch_manager.py',
    ],
    
    # Validation/testing scripts
    'scripts/validation': [
        'comprehensive_validation.py',
        'comprehensive_qa_validation.py',
        'auto_complete_validation.py',
        'e2e_comprehensive_test.py',
        'integration_test.py',
        'INTEGRATION_VERIFICATION.py',
        'quick_validation.py',
        'run_all_tests.py',
        'run_comprehensive_tests.py',
        'run_tests.py',
        'test_runner.py',
    ],
    
    # Monitoring/checking scripts
    'scripts/monitoring': [
        'check_alphaalgo_status.py',
        'check_memory.py',
        'check_real_prices.py',
        'file_integrity_monitor.py',
        'health_check.py',
        'monitor_system.py',
        'system_health_check.py',
    ],
    
    # Utility scripts
    'scripts/utils': [
        'audit_tuple_imports.py',
        'calculate_correct_tick_value.py',
        'cleanup_useless_files.py',
        'config_tuner.py',
        'credential_rotation.py',
        'data_manager.py',
        'dynamic_resource_scaling.py',
        'graceful_degradation.py',
        'setup.py',
        'setup_environment.py',
        'setup_production.py',
    ],
    
    # Demo/example scripts
    'examples': [
        'demo_trading_simulator.py',
        'fully_automated_system.py',
        'ALPHAALGO_5STAR_IMPLEMENTATION_GUIDE.py',
    ],
    
    # CLI tools
    'scripts/cli': [
        'bot_cli.py',
        'bot_help.py',
    ],
}

# Files to keep in root
KEEP_IN_ROOT = [
    'main.py',  # Primary entry point
    'setup.py',  # Python package setup (if it's the package setup)
    'ORGANIZE_FILES.py',  # This script
]

def create_directories():
    """Create all necessary directories."""
    dirs = set()
    for target_dir in ORGANIZATION_RULES.keys():
        dirs.add(target_dir)
    
    for dir_path in dirs:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
        print(f"✅ Created directory: {dir_path}")

def organize_files(dry_run=True):
    """Organize files according to rules."""
    moved_count = 0
    
    for target_dir, files in ORGANIZATION_RULES.items():
        for filename in files:
            source = Path(filename)
            if source.exists():
                destination = Path(target_dir) / filename
                
                if dry_run:
                    print(f"📋 Would move: {source} → {destination}")
                else:
                    try:
                        shutil.move(str(source), str(destination))
                        print(f"✅ Moved: {source} → {destination}")
                        moved_count += 1
                    except Exception as e:
                        print(f"❌ Error moving {source}: {e}")
            else:
                print(f"⚠️  Not found: {source}")
    
    return moved_count

def create_readme_files():
    """Create README files in each directory."""
    readmes = {
        'archive/scripts': """# Archived Scripts

These are old/deprecated scripts that have been superseded by newer implementations.

Kept for reference only.
""",
        'scripts/deployment': """# Deployment Scripts

Scripts for deploying the trading bot to various environments.

**Main Scripts**:
- `deploy_production.py` - Production deployment
- `ci_cd_pipeline.py` - CI/CD automation
""",
        'scripts/fixes': """# Fix Scripts

Scripts for applying fixes and patches to the codebase.

**Note**: Most fixes have been applied. These are kept for reference.
""",
        'scripts/validation': """# Validation Scripts

Scripts for testing and validating the trading bot.

**Main Scripts**:
- `comprehensive_validation.py` - Full system validation
- `e2e_comprehensive_test.py` - End-to-end tests
""",
        'scripts/monitoring': """# Monitoring Scripts

Scripts for monitoring system health and performance.

**Main Scripts**:
- `system_health_check.py` - System health monitoring
- `file_integrity_monitor.py` - File integrity checks
""",
        'scripts/utils': """# Utility Scripts

Various utility scripts for system maintenance and configuration.
""",
        'scripts/cli': """# CLI Tools

Command-line interface tools for interacting with the trading bot.

**Usage**:
```bash
python bot_cli.py --help
```
""",
    }
    
    for dir_path, content in readmes.items():
        readme_path = Path(dir_path) / 'README.md'
        if not readme_path.exists():
            readme_path.write_text(content)
            print(f"✅ Created README: {readme_path}")

def main():
    """Main organization function."""
    print("=" * 80)
    print("FILE ORGANIZATION SCRIPT")
    print("=" * 80)
    print()
    
    # Dry run first
    print("🔍 DRY RUN - Showing what would be moved...")
    print()
    create_directories()
    print()
    organize_files(dry_run=True)
    print()
    
    # Ask for confirmation
    response = input("\n❓ Proceed with actual file moves? (yes/no): ").strip().lower()
    
    if response == 'yes':
        print("\n✅ Proceeding with file organization...")
        moved = organize_files(dry_run=False)
        print(f"\n✅ Moved {moved} files")
        
        print("\n📝 Creating README files...")
        create_readme_files()
        
        print("\n✅ Organization complete!")
        print("\n📊 Summary:")
        print(f"   - Files organized: {moved}")
        print(f"   - Directories created: {len(ORGANIZATION_RULES)}")
        print(f"   - Files kept in root: {len(KEEP_IN_ROOT)}")
    else:
        print("\n❌ Organization cancelled")

if __name__ == '__main__':
    main()
