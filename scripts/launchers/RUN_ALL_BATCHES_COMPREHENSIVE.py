"""
Comprehensive Batch File Runner
Runs all batch files and tracks success/failure
"""

import os
import subprocess
import json
from datetime import datetime
from pathlib import Path

# Batch files to skip (require user interaction or long-running)
SKIP_LIST = [
    'install_as_windows_service.bat',
    'deploy_to_production.bat',
    'START_DEMO_TRADING.bat',
    'start_production.bat',
    'start_trading_bot.bat',
    'START_OPERATIONAL_BOT.bat',
    'START_BOT_WITH_WATCHDOG.bat',
    'start_full_automation.bat',
    'start_autonomous_ai.bat',
    'START_ALPHAALGO.bat',
    'START_ALPHAALGO_OFFLINE_RL.bat',
    'START_DEEPSEEK_ENGINEER.bat',
    'RUN_BOT.bat',
    'RUN_SAFE_BOT.bat',
    'MASTER_CONTROL.bat',
    'STOP_LOOP.bat',
    'CREATE_DESKTOP_SHORTCUT.bat',
]

# Batch files that are safe to auto-run
AUTO_RUN_LIST = [
    'CHECK_BOT_STATUS.bat',
    'CHECK_DEEPSEEK_STATUS.bat',
    'apply_all_fixes.bat',
]

def run_batch(filepath, timeout=60):
    """Run a batch file with timeout"""
    try:
        # Use echo to simulate pressing Enter for prompts
        result = subprocess.run(
            ['cmd', '/c', f'echo. | "{filepath}"'],
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=os.path.dirname(filepath) or '.'
        )
        
        return {
            'status': 'PASSED' if result.returncode == 0 else 'FAILED',
            'exit_code': result.returncode,
            'stdout': result.stdout[:500] if result.stdout else '',
            'stderr': result.stderr[:500] if result.stderr else ''
        }
    except subprocess.TimeoutExpired:
        return {
            'status': 'TIMEOUT',
            'exit_code': -1,
            'stdout': '',
            'stderr': f'Timeout after {timeout} seconds'
        }
    except Exception as e:
        return {
            'status': 'ERROR',
            'exit_code': -1,
            'stdout': '',
            'stderr': str(e)
        }

def main():
    """Run all batch files"""
    print("=" * 80)
    print("COMPREHENSIVE BATCH FILE EXECUTION")
    print("=" * 80)
    print()
    
    # Find all batch files
    batch_files = []
    for root, dirs, files in os.walk('.'):
        if '.venv' in root or 'site-packages' in root:
            continue
        
        for file in files:
            if file.endswith('.bat'):
                batch_files.append(os.path.join(root, file))
    
    batch_files = sorted(batch_files)
    
    print(f"Found {len(batch_files)} batch files")
    print(f"Auto-run: {len([f for f in batch_files if os.path.basename(f) in AUTO_RUN_LIST])}")
    print(f"Skipped: {len([f for f in batch_files if os.path.basename(f) in SKIP_LIST])}")
    print()
    
    results = []
    stats = {
        'total': 0,
        'passed': 0,
        'failed': 0,
        'skipped': 0,
        'timeout': 0,
        'error': 0
    }
    
    for i, filepath in enumerate(batch_files, 1):
        filename = os.path.basename(filepath)
        stats['total'] += 1
        
        print(f"[{i}/{len(batch_files)}] {filename}...", end=' ')
        
        # Check if should skip
        if filename in SKIP_LIST:
            print("[SKIPPED] - Requires user interaction or long-running")
            stats['skipped'] += 1
            results.append({
                'file': filename,
                'path': filepath,
                'status': 'SKIPPED',
                'reason': 'Requires user interaction or long-running'
            })
            continue
        
        # Check if safe to auto-run
        if filename in AUTO_RUN_LIST:
            result = run_batch(filepath, timeout=30)
            status = result['status']
            
            if status == 'PASSED':
                print(f"[PASSED]")
                stats['passed'] += 1
            elif status == 'FAILED':
                print(f"[FAILED] Exit code: {result['exit_code']}")
                stats['failed'] += 1
            elif status == 'TIMEOUT':
                print(f"[TIMEOUT]")
                stats['timeout'] += 1
            else:
                print(f"[ERROR] {result['stderr'][:50]}")
                stats['error'] += 1
            
            results.append({
                'file': filename,
                'path': filepath,
                **result
            })
        else:
            print("[SKIPPED] - Not in auto-run list")
            stats['skipped'] += 1
            results.append({
                'file': filename,
                'path': filepath,
                'status': 'SKIPPED',
                'reason': 'Not in auto-run list'
            })
    
    # Generate report
    print()
    print("=" * 80)
    print("EXECUTION SUMMARY")
    print("=" * 80)
    print(f"Total batch files: {stats['total']}")
    print(f"Passed: {stats['passed']}")
    print(f"Failed: {stats['failed']}")
    print(f"Skipped: {stats['skipped']}")
    print(f"Timeout: {stats['timeout']}")
    print(f"Error: {stats['error']}")
    
    if stats['total'] > 0:
        executed = stats['passed'] + stats['failed'] + stats['timeout'] + stats['error']
        if executed > 0:
            success_rate = (stats['passed'] / executed) * 100
            print(f"Success Rate: {success_rate:.1f}% ({stats['passed']}/{executed} executed)")
    
    # Save detailed report
    report = {
        'timestamp': datetime.now().isoformat(),
        'stats': stats,
        'results': results
    }
    
    report_file = f"batch_execution_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2)
    
    print()
    print(f"Detailed report saved to: {report_file}")
    print("=" * 80)
    
    # Show failed/error files
    failed_files = [r for r in results if r['status'] in ['FAILED', 'ERROR', 'TIMEOUT']]
    if failed_files:
        print()
        print("FAILED/ERROR FILES:")
        for r in failed_files:
            print(f"  - {r['file']}: {r['status']}")
            if 'stderr' in r and r['stderr']:
                print(f"    Error: {r['stderr'][:100]}")

if __name__ == "__main__":
    main()
