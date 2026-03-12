"""
AlphaAlgo Weekly Test Framework
Automated testing for weekly curriculum progress
"""

import sys
import os
import io
import subprocess
import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple
import importlib.util
from typing import Set
import asyncio
import numpy
import pandas

# Set UTF-8 encoding for Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Color codes for terminal output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def print_header(text: str):
    """Print formatted header"""
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*80}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}{text.center(80)}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'='*80}{Colors.RESET}\n")

def print_success(text: str):
    """Print success message"""
    print(f"{Colors.GREEN}✅ {text}{Colors.RESET}")

def print_error(text: str):
    """Print error message"""
    print(f"{Colors.RED}❌ {text}{Colors.RESET}")

def print_warning(text: str):
    """Print warning message"""
    print(f"{Colors.YELLOW}⚠️  {text}{Colors.RESET}")

def print_info(text: str):
    """Print info message"""
    print(f"{Colors.BLUE}ℹ️  {text}{Colors.RESET}")


class WeeklyTestRunner:
    """Automated weekly test runner"""
    
    def __init__(self):
        self.root_dir = Path(__file__).parent
        self.test_dir = self.root_dir / 'tests'
        self.learning_dir = self.root_dir / 'learning_path'
        self.results = {
            'timestamp': datetime.now().isoformat(),
            'tests_run': 0,
            'tests_passed': 0,
            'tests_failed': 0,
            'details': []
        }
    
    def run_pytest(self, test_file: str = None) -> Tuple[bool, str]:
        """Run pytest on specific file or all tests"""
        try:
            if test_file:
                cmd = [sys.executable, '-m', 'pytest', str(test_file), '-v', '--tb=short']
            else:
                cmd = [sys.executable, '-m', 'pytest', str(self.test_dir), '-v', '--tb=short']
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            return result.returncode == 0, result.stdout + result.stderr
        except Exception as e:
            return False, str(e)
    
    def run_learning_script(self, script_path: Path) -> Tuple[bool, str]:
        """Run a learning path script"""
        try:
            result = subprocess.run(
                [sys.executable, str(script_path)],
                capture_output=True,
                text=True,
                timeout=60
            )
            return result.returncode == 0, result.stdout + result.stderr
        except subprocess.TimeoutExpired:
            return False, "Script timeout (>60s)"
        except Exception as e:
            return False, str(e)
    
    def check_imports(self, module_path: str) -> Tuple[bool, str]:
        """Check if module imports successfully"""
        try:
            spec = importlib.util.spec_from_file_location("test_module", module_path)
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                return True, "Imports successful"
            return False, "Module spec not found"
        except Exception as e:
            return False, str(e)
    
    def test_week_1(self) -> Dict:
        """Test Week 1: Python Mastery & Async Programming"""
        print_header("WEEK 1: Python Mastery & Async Programming")
        
        results = {
            'week': 1,
            'tests': []
        }
        
        # Test 1: Async data fetcher
        print_info("Testing async data fetcher...")
        script = self.learning_dir / 'week1_async_data_fetcher.py'
        if script.exists():
            success, output = self.check_imports(str(script))
            results['tests'].append({
                'name': 'Async Data Fetcher Import',
                'passed': success,
                'output': output
            })
            if success:
                print_success("Async data fetcher imports OK")
            else:
                print_error(f"Async data fetcher failed: {output[:100]}")
        else:
            print_warning(f"Script not found: {script}")
        
        # Test 2: Numpy/Pandas mastery
        print_info("Testing numpy/pandas mastery...")
        script = self.learning_dir / 'week1_numpy_pandas_mastery.py'
        if script.exists():
            success, output = self.check_imports(str(script))
            results['tests'].append({
                'name': 'Numpy/Pandas Mastery Import',
                'passed': success,
                'output': output
            })
            if success:
                print_success("Numpy/Pandas mastery imports OK")
            else:
                print_error(f"Numpy/Pandas mastery failed: {output[:100]}")
        else:
            print_warning(f"Script not found: {script}")
        
        # Test 3: Check dependencies
        print_info("Checking Week 1 dependencies...")
        deps = ['pandas', 'numpy', 'aiohttp', 'asyncio']
        for dep in deps:
            try:
                __import__(dep)
                results['tests'].append({
                    'name': f'Dependency: {dep}',
                    'passed': True,
                    'output': 'Installed'
                })
                print_success(f"Dependency {dep} installed")
            except ImportError:
                results['tests'].append({
                    'name': f'Dependency: {dep}',
                    'passed': False,
                    'output': 'Not installed'
                })
                print_error(f"Dependency {dep} missing")
        
        return results
    
    def test_week_2(self) -> Dict:
        """Test Week 2: Live Data Integration & Backtesting"""
        print_header("WEEK 2: Live Data Integration & Backtesting")
        
        results = {
            'week': 2,
            'tests': []
        }
        
        # Test 1: Data integration
        print_info("Testing data integration...")
        script = self.learning_dir / 'week2_data_integration.py'
        if script.exists():
            success, output = self.check_imports(str(script))
            results['tests'].append({
                'name': 'Data Integration Import',
                'passed': success,
                'output': output
            })
            if success:
                print_success("Data integration imports OK")
            else:
                print_error(f"Data integration failed: {output[:100]}")
        
        # Test 2: Backtesting engine
        print_info("Testing backtesting engine...")
        script = self.learning_dir / 'week2_backtesting_engine.py'
        if script.exists():
            success, output = self.check_imports(str(script))
            results['tests'].append({
                'name': 'Backtesting Engine Import',
                'passed': success,
                'output': output
            })
            if success:
                print_success("Backtesting engine imports OK")
            else:
                print_error(f"Backtesting engine failed: {output[:100]}")
        
        return results
    
    def test_week_3(self) -> Dict:
        """Test Week 3: Feature Engineering & ML Foundations"""
        print_header("WEEK 3: Feature Engineering & ML Foundations")
        
        results = {
            'week': 3,
            'tests': []
        }
        
        # Test 1: First ML model
        print_info("Testing first ML model...")
        script = self.learning_dir / 'week3_first_ml_model.py'
        if script.exists():
            success, output = self.check_imports(str(script))
            results['tests'].append({
                'name': 'First ML Model Import',
                'passed': success,
                'output': output
            })
            if success:
                print_success("First ML model imports OK")
            else:
                print_error(f"First ML model failed: {output[:100]}")
        
        # Test 2: ML dependencies
        print_info("Checking ML dependencies...")
        deps = ['sklearn', 'scipy', 'joblib']
        for dep in deps:
            try:
                __import__(dep)
                results['tests'].append({
                    'name': f'ML Dependency: {dep}',
                    'passed': True,
                    'output': 'Installed'
                })
                print_success(f"ML dependency {dep} installed")
            except ImportError:
                results['tests'].append({
                    'name': f'ML Dependency: {dep}',
                    'passed': False,
                    'output': 'Not installed'
                })
                print_error(f"ML dependency {dep} missing")
        
        return results
    
    def test_phase_1(self) -> Dict:
        """Test complete Phase 1 integration"""
        print_header("PHASE 1: Complete Integration Test")
        
        results = {
            'phase': 1,
            'tests': []
        }
        
        # Run all week tests
        week1 = self.test_week_1()
        week2 = self.test_week_2()
        week3 = self.test_week_3()
        
        results['weeks'] = [week1, week2, week3]
        
        # Calculate overall success
        total_tests = sum(len(w['tests']) for w in results['weeks'])
        passed_tests = sum(
            sum(1 for t in w['tests'] if t['passed']) 
            for w in results['weeks']
        )
        
        results['total_tests'] = total_tests
        results['passed_tests'] = passed_tests
        results['success_rate'] = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        return results
    
    def run_all_unit_tests(self) -> Dict:
        """Run all unit tests in tests/ directory"""
        print_header("RUNNING ALL UNIT TESTS")
        
        results = {
            'category': 'unit_tests',
            'tests': []
        }
        
        # Find all test files
        test_files = list(self.test_dir.glob('test_*.py'))
        
        print_info(f"Found {len(test_files)} test files")
        
        for test_file in test_files:
            print_info(f"Running {test_file.name}...")
            success, output = self.run_pytest(test_file)
            
            results['tests'].append({
                'file': test_file.name,
                'passed': success,
                'output': output[:500]  # Truncate output
            })
            
            if success:
                print_success(f"{test_file.name} passed")
            else:
                print_error(f"{test_file.name} failed")
        
        return results
    
    def generate_report(self, results: Dict):
        """Generate test report"""
        print_header("TEST REPORT")
        
        # Save to JSON
        report_file = self.root_dir / f'test_reports/weekly_test_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        report_file.parent.mkdir(exist_ok=True)
        
        with open(report_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        print_success(f"Report saved to: {report_file}")
        
        # Print summary
        if 'weeks' in results:
            for week in results['weeks']:
                passed = sum(1 for t in week['tests'] if t['passed'])
                total = len(week['tests'])
                print(f"\n{Colors.BOLD}Week {week['week']}:{Colors.RESET} {passed}/{total} tests passed")
        
        if 'total_tests' in results:
            print(f"\n{Colors.BOLD}Overall:{Colors.RESET} {results['passed_tests']}/{results['total_tests']} tests passed")
            print(f"{Colors.BOLD}Success Rate:{Colors.RESET} {results['success_rate']:.1f}%")
            
            if results['success_rate'] >= 80:
                print_success("EXCELLENT! Phase 1 ready ✨")
            elif results['success_rate'] >= 60:
                print_warning("GOOD! Some improvements needed")
            else:
                print_error("NEEDS WORK! Focus on failing tests")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='AlphaAlgo Weekly Test Framework')
    parser.add_argument('--week', type=int, help='Test specific week (1-60)')
    parser.add_argument('--phase', type=int, help='Test specific phase (1-5)')
    parser.add_argument('--all', action='store_true', help='Run all tests')
    parser.add_argument('--report', action='store_true', help='Generate report only')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be tested')
    
    args = parser.parse_args()
    
    runner = WeeklyTestRunner()
    
    print_header("ALPHAALGO WEEKLY TEST FRAMEWORK")
    print(f"{Colors.BOLD}Test Directory:{Colors.RESET} {runner.test_dir}")
    print(f"{Colors.BOLD}Learning Directory:{Colors.RESET} {runner.learning_dir}")
    
    if args.dry_run:
        print_info("DRY RUN MODE - No tests will be executed")
        print_info(f"Available test files: {len(list(runner.test_dir.glob('test_*.py')))}")
        print_info(f"Available learning scripts: {len(list(runner.learning_dir.glob('week*.py')))}")
        return
    
    results = {}
    
    if args.week == 1:
        results = runner.test_week_1()
    elif args.week == 2:
        results = runner.test_week_2()
    elif args.week == 3:
        results = runner.test_week_3()
    elif args.phase == 1:
        results = runner.test_phase_1()
        runner.generate_report(results)
    elif args.all:
        results = runner.run_all_unit_tests()
        runner.generate_report(results)
    else:
        # Default: Run Phase 1 tests
        print_info("No specific test selected, running Phase 1 tests...")
        results = runner.test_phase_1()
        runner.generate_report(results)


if __name__ == '__main__':
    main()
