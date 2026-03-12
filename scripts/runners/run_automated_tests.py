#!/usr/bin/env python3
"""
Automated Test Runner for Trading Bot
Runs comprehensive test suite with reporting and analysis
"""

import argparse
import sys
import time
from pathlib import Path
from datetime import datetime
import subprocess
import json

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


class TestRunner:
    """Automated test runner with comprehensive reporting"""
    
    def __init__(self, config='all', verbose=False, coverage=True):
        self.config = config
        self.verbose = verbose
        self.coverage = coverage
        self.results = {
            'timestamp': datetime.now().isoformat(),
            'config': config,
            'tests': {},
            'summary': {}
        }
        
    def run_unit_tests(self):
        """Run unit tests"""
        print("\n" + "="*70)
        print("RUNNING UNIT TESTS")
        print("="*70)
        
        cmd = ['py', '-m', 'pytest', 'tests/', '-v', '--tb=short']
        
        if self.coverage:
            cmd.extend(['--cov=trading_bot', '--cov-report=term-missing', '--cov-report=html'])
        
        if not self.verbose:
            cmd.append('-q')
            
        start_time = time.time()
        result = subprocess.run(cmd, capture_output=True, text=True)
        duration = time.time() - start_time
        
        self.results['tests']['unit'] = {
            'passed': result.returncode == 0,
            'duration': duration,
            'output': result.stdout + result.stderr
        }
        
        print(result.stdout)
        if result.returncode != 0:
            print(result.stderr)
            
        return result.returncode == 0
    
    def run_integration_tests(self):
        """Run integration tests"""
        print("\n" + "="*70)
        print("RUNNING INTEGRATION TESTS")
        print("="*70)
        
        cmd = ['py', '-m', 'pytest', 'tests/integration/', '-v', '--tb=short']
        
        if not self.verbose:
            cmd.append('-q')
            
        start_time = time.time()
        result = subprocess.run(cmd, capture_output=True, text=True)
        duration = time.time() - start_time
        
        self.results['tests']['integration'] = {
            'passed': result.returncode == 0,
            'duration': duration,
            'output': result.stdout + result.stderr
        }
        
        print(result.stdout)
        if result.returncode != 0:
            print(result.stderr)
            
        return result.returncode == 0
    
    def run_linting(self):
        """Run code quality checks"""
        print("\n" + "="*70)
        print("RUNNING CODE QUALITY CHECKS")
        print("="*70)
        
        checks = {
            'flake8': ['py', '-m', 'flake8', 'trading_bot/', '--count', '--statistics'],
            'pylint': ['py', '-m', 'pylint', 'trading_bot/', '--exit-zero'],
            'mypy': ['py', '-m', 'mypy', 'trading_bot/', '--ignore-missing-imports']
        }
        
        all_passed = True
        
        for name, cmd in checks.items():
            print(f"\n--- Running {name} ---")
            start_time = time.time()
            result = subprocess.run(cmd, capture_output=True, text=True)
            duration = time.time() - start_time
            
            passed = result.returncode == 0
            all_passed = all_passed and passed
            
            self.results['tests'][name] = {
                'passed': passed,
                'duration': duration,
                'output': result.stdout + result.stderr
            }
            
            print(result.stdout)
            if not passed and self.verbose:
                print(result.stderr)
                
        return all_passed
    
    def run_security_scan(self):
        """Run security vulnerability scan"""
        print("\n" + "="*70)
        print("RUNNING SECURITY SCAN")
        print("="*70)
        
        cmd = ['py', '-m', 'bandit', '-r', 'trading_bot/', '-f', 'json']
        
        start_time = time.time()
        result = subprocess.run(cmd, capture_output=True, text=True)
        duration = time.time() - start_time
        
        try:
            scan_results = json.loads(result.stdout)
            high_severity = len([r for r in scan_results.get('results', []) if r['issue_severity'] == 'HIGH'])
            medium_severity = len([r for r in scan_results.get('results', []) if r['issue_severity'] == 'MEDIUM'])
            
            print(f"High severity issues: {high_severity}")
            print(f"Medium severity issues: {medium_severity}")
            
            passed = high_severity == 0
        except:
            passed = result.returncode == 0
            print(result.stdout)
        
        self.results['tests']['security'] = {
            'passed': passed,
            'duration': duration,
            'output': result.stdout
        }
        
        return passed
    
    def generate_report(self):
        """Generate test report"""
        print("\n" + "="*70)
        print("TEST SUMMARY")
        print("="*70)
        
        total_tests = len(self.results['tests'])
        passed_tests = sum(1 for t in self.results['tests'].values() if t['passed'])
        total_duration = sum(t['duration'] for t in self.results['tests'].values())
        
        self.results['summary'] = {
            'total': total_tests,
            'passed': passed_tests,
            'failed': total_tests - passed_tests,
            'duration': total_duration,
            'success_rate': (passed_tests / total_tests * 100) if total_tests > 0 else 0
        }
        
        print(f"\nTotal Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {total_tests - passed_tests}")
        print(f"Success Rate: {self.results['summary']['success_rate']:.1f}%")
        print(f"Total Duration: {total_duration:.2f}s")
        
        # Save report
        report_dir = project_root / 'test_reports'
        report_dir.mkdir(exist_ok=True)
        
        report_file = report_dir / f"test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        print(f"\nDetailed report saved to: {report_file}")
        
        return self.results['summary']['failed'] == 0
    
    def run_all(self):
        """Run all tests"""
        print("\n" + "="*70)
        print("AUTOMATED TEST SUITE")
        print(f"Configuration: {self.config}")
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*70)
        
        # Run test suites
        if self.config in ['all', 'unit']:
            self.run_unit_tests()
        
        if self.config in ['all', 'integration']:
            self.run_integration_tests()
        
        if self.config in ['all', 'quality']:
            self.run_linting()
        
        if self.config in ['all', 'security']:
            self.run_security_scan()
        
        # Generate report
        success = self.generate_report()
        
        return 0 if success else 1


def main():
    parser = argparse.ArgumentParser(description='Run automated tests for trading bot')
    parser.add_argument('--config', choices=['all', 'unit', 'integration', 'quality', 'security'],
                       default='all', help='Test configuration to run')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    parser.add_argument('--no-coverage', action='store_true', help='Disable coverage reporting')
    
    args = parser.parse_args()
    
    runner = TestRunner(
        config=args.config,
        verbose=args.verbose,
        coverage=not args.no_coverage
    )
    
    exit_code = runner.run_all()
    sys.exit(exit_code)


if __name__ == '__main__':
    main()
