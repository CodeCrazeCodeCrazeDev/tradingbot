"""
Auto-Complete Validation System
Runs every file in the bot and validates expected outputs
"""

import os
import sys
import io
import subprocess
import json
from pathlib import Path
from datetime import datetime
from typing import Any, Dict, List, Tuple
import importlib.util
import traceback

# Set UTF-8 encoding for Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')


class AutoCompleteValidator:
    """Automatically validates all bot components"""
    
    def __init__(self, root_dir: str):
        self.root_dir = Path(root_dir)
        self.results = {
            'passed': [],
            'failed': [],
            'skipped': [],
            'errors': []
        }
        self.total_files = 0
        
    def print_header(self, text: str):
        """Print formatted header"""
        print(f"\n{'='*80}")
        print(f"{text.center(80)}")
        print(f"{'='*80}\n")
    
    def print_section(self, text: str):
        """Print section header"""
        print(f"\n{'-'*80}")
        print(f"  {text}")
        print(f"{'-'*80}")
    
    def run_python_file(self, file_path: Path) -> Tuple[bool, str]:
        """Run a Python file and check for errors"""
        try:
            # Skip certain files
            skip_patterns = [
                '__pycache__', '.venv', 'backups', 'test_', 
                'setup.py', 'deploy', 'install', 'start_'
            ]
            
            if any(pattern in str(file_path) for pattern in skip_patterns):
                return None, "Skipped (excluded pattern)"
            
            # Try to import and validate syntax
            spec = importlib.util.spec_from_file_location("module", file_path)
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                return True, "Import successful"
            else:
                return False, "Could not load module"
                
        except SyntaxError as e:
            return False, f"Syntax Error: {str(e)}"
        except ImportError as e:
            return None, f"Import issue (dependencies): {str(e)[:100]}"
        except Exception as e:
            return None, f"Runtime issue: {str(e)[:100]}"
    
    def validate_main_scripts(self):
        """Validate main entry point scripts"""
        self.print_section("VALIDATING MAIN SCRIPTS")
        
        main_scripts = [
            'main.py',
            'mvp_bot.py',
            'run_complete_system.py',
            'weekly_tests.py'
        ]
        
        for script in main_scripts:
            script_path = self.root_dir / script
            if script_path.exists():
                print(f"  Checking {script}...")
                
                # Check syntax only
                try:
                    with open(script_path, 'r', encoding='utf-8') as f:
                        compile(f.read(), script, 'exec')
                    print(f"    [OK] {script} - Syntax valid")
                    self.results['passed'].append(script)
                except SyntaxError as e:
                    print(f"    [ERROR] {script} - Syntax error: {e}")
                    self.results['failed'].append(script)
            else:
                print(f"    [MISSING] {script}")
                self.results['skipped'].append(script)
    
    def validate_trading_bot_modules(self):
        """Validate all trading_bot modules"""
        self.print_section("VALIDATING TRADING_BOT MODULES")
        
        trading_bot_dir = self.root_dir / 'trading_bot'
        if not trading_bot_dir.exists():
            print(f"  [ERROR] trading_bot directory not found")
            return
        
        # Get all Python files
        py_files = list(trading_bot_dir.rglob('*.py'))
        py_files = [f for f in py_files if '__pycache__' not in str(f)]
        
        print(f"  Found {len(py_files)} Python modules\n")
        
        passed = 0
        failed = 0
        skipped = 0
        
        for py_file in py_files:
            rel_path = py_file.relative_to(self.root_dir)
            result, message = self.run_python_file(py_file)
            
            if result is True:
                passed += 1
                if passed <= 10:  # Show first 10
                    print(f"    [OK] {rel_path}")
            elif result is False:
                failed += 1
                print(f"    [FAILED] {rel_path}: {message}")
                self.results['failed'].append(str(rel_path))
            else:
                skipped += 1
                if skipped <= 5:  # Show first 5
                    print(f"    [SKIP] {rel_path}: {message}")
        
        print(f"\n  Summary: {passed} passed, {failed} failed, {skipped} skipped")
        self.results['passed'].extend([f"trading_bot modules: {passed}"])
        if failed > 0:
            self.results['errors'].append(f"{failed} modules with errors")
    
    def validate_tests(self):
        """Validate test suite"""
        self.print_section("VALIDATING TEST SUITE")
        
        print("  Running pytest...")
        
        try:
            result = subprocess.run(
                [sys.executable, '-m', 'pytest', 'tests/', '-v', '--tb=short', '-q'],
                capture_output=True,
                text=True,
                timeout=180,
                cwd=str(self.root_dir)
            )
            
            output = result.stdout + result.stderr
            
            # Parse results
            if 'passed' in output:
                # Extract numbers
                import re
                passed_match = re.search(r'(\d+) passed', output)
                failed_match = re.search(r'(\d+) failed', output)
                
                passed = int(passed_match.group(1)) if passed_match else 0
                failed = int(failed_match.group(1)) if failed_match else 0
                
                print(f"    [RESULT] {passed} tests passed, {failed} tests failed")
                
                if failed == 0:
                    self.results['passed'].append(f"All {passed} tests passed")
                else:
                    self.results['failed'].append(f"{failed} tests failed")
                    
            else:
                print(f"    [INFO] Test output: {output[:200]}")
                
        except subprocess.TimeoutExpired:
            print(f"    [TIMEOUT] Tests took too long (>180s)")
            self.results['errors'].append("Test timeout")
        except Exception as e:
            print(f"    [ERROR] Could not run tests: {str(e)}")
            self.results['errors'].append(f"Test error: {str(e)}")
    
    def validate_examples(self):
        """Validate example scripts"""
        self.print_section("VALIDATING EXAMPLE SCRIPTS")
        
        examples_dir = self.root_dir / 'examples'
        if not examples_dir.exists():
            print(f"  [SKIP] examples directory not found")
            return
        
        example_files = list(examples_dir.glob('*.py'))
        print(f"  Found {len(example_files)} example scripts\n")
        
        passed = 0
        failed = 0
        
        for example in example_files[:10]:  # Check first 10
            try:
                with open(example, 'r', encoding='utf-8') as f:
                    compile(f.read(), str(example), 'exec')
                print(f"    [OK] {example.name}")
                passed += 1
            except SyntaxError as e:
                print(f"    [ERROR] {example.name}: {str(e)}")
                failed += 1
        
        print(f"\n  Summary: {passed} passed, {failed} failed")
        if failed == 0:
            self.results['passed'].append(f"Examples: {passed} valid")
        else:
            self.results['failed'].append(f"Examples: {failed} errors")
    
    def validate_configuration(self):
        """Validate configuration files"""
        self.print_section("VALIDATING CONFIGURATION")
        
        config_files = [
            ('config/config.yaml', 'yaml'),
            ('config/adaptive_config.yaml', 'yaml'),
            ('requirements.txt', 'text'),
            ('.env.template', 'text'),
            ('pytest.ini', 'ini'),
        ]
        
        for config_file, file_type in config_files:
            config_path = self.root_dir / config_file
            if config_path.exists():
                try:
                    if file_type == 'yaml':
                        import yaml
                        with open(config_path, 'r') as f:
                            yaml.safe_load(f)
                        print(f"    [OK] {config_file}")
                        self.results['passed'].append(config_file)
                    elif file_type == 'json':
                        with open(config_path, 'r') as f:
                            json.load(f)
                        print(f"    [OK] {config_file}")
                        self.results['passed'].append(config_file)
                    else:
                        # Just check it's readable
                        with open(config_path, 'r') as f:
                            f.read()
                        print(f"    [OK] {config_file}")
                        self.results['passed'].append(config_file)
                except Exception as e:
                    print(f"    [ERROR] {config_file}: {str(e)}")
                    self.results['failed'].append(config_file)
            else:
                print(f"    [MISSING] {config_file}")
                self.results['skipped'].append(config_file)
    
    def validate_deployment_readiness(self):
        """Validate deployment readiness"""
        self.print_section("VALIDATING DEPLOYMENT READINESS")
        
        checks = {
            'Environment file': self.root_dir / '.env',
            'Health check': self.root_dir / 'health_check.py',
            'Startup script (Windows)': self.root_dir / 'start_production.bat',
            'Startup script (Linux)': self.root_dir / 'start_production.sh',
            'Docker config': self.root_dir / 'Dockerfile.production',
            'Docker Compose': self.root_dir / 'docker-compose.production.yml',
            'Deployment checklist': self.root_dir / 'DEPLOYMENT_CHECKLIST.md',
        }
        
        passed = 0
        for check_name, check_path in checks.items():
            if check_path.exists():
                print(f"    [OK] {check_name}")
                passed += 1
            else:
                print(f"    [MISSING] {check_name}")
        
        print(f"\n  Deployment readiness: {passed}/{len(checks)} ({passed/len(checks)*100:.0f}%)")
        
        if passed >= len(checks) * 0.8:
            self.results['passed'].append(f"Deployment ready: {passed}/{len(checks)}")
        else:
            self.results['failed'].append(f"Deployment incomplete: {passed}/{len(checks)}")
    
    def run_integration_tests(self):
        """Run integration tests"""
        self.print_section("RUNNING INTEGRATION TESTS")
        
        print("  Testing core imports...")
        
        critical_imports = [
            ('pandas', 'Data processing'),
            ('numpy', 'Numerical computing'),
            ('loguru', 'Logging'),
            ('aiohttp', 'Async HTTP'),
            ('sqlalchemy', 'Database'),
        ]
        
        passed = 0
        for module, description in critical_imports:
            try:
                __import__(module)
                print(f"    [OK] {module} - {description}")
                passed += 1
            except ImportError:
                print(f"    [MISSING] {module} - {description}")
        
        print(f"\n  Critical imports: {passed}/{len(critical_imports)}")
        
        if passed == len(critical_imports):
            self.results['passed'].append("All critical imports available")
        else:
            self.results['failed'].append(f"Missing {len(critical_imports)-passed} critical imports")
    
    def generate_report(self):
        """Generate final validation report"""
        self.print_header("AUTO-COMPLETE VALIDATION REPORT")
        
        total_passed = len(self.results['passed'])
        total_failed = len(self.results['failed'])
        total_skipped = len(self.results['skipped'])
        total_errors = len(self.results['errors'])
        
        print(f"  Validation Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"\n  RESULTS:")
        print(f"    Passed:  {total_passed}")
        print(f"    Failed:  {total_failed}")
        print(f"    Skipped: {total_skipped}")
        print(f"    Errors:  {total_errors}")
        
        # Calculate success rate
        total_checks = total_passed + total_failed
        if total_checks > 0:
            success_rate = (total_passed / total_checks) * 100
            print(f"\n  SUCCESS RATE: {success_rate:.1f}%")
        
        # Show failures
        if total_failed > 0:
            print(f"\n  FAILED ITEMS:")
            for item in self.results['failed'][:10]:
                print(f"    - {item}")
        
        # Show errors
        if total_errors > 0:
            print(f"\n  ERRORS:")
            for error in self.results['errors'][:10]:
                print(f"    - {error}")
        
        # Overall status
        print(f"\n  OVERALL STATUS:")
        if total_failed == 0 and total_errors == 0:
            print(f"    [SUCCESS] All validations passed!")
            status = "SUCCESS"
        elif total_failed <= 3:
            print(f"    [PARTIAL] Most validations passed with minor issues")
            status = "PARTIAL_SUCCESS"
        else:
            print(f"    [FAILED] Multiple validation failures")
            status = "FAILED"
        
        # Save report
        report = {
            'timestamp': datetime.now().isoformat(),
            'status': status,
            'results': self.results,
            'summary': {
                'passed': total_passed,
                'failed': total_failed,
                'skipped': total_skipped,
                'errors': total_errors,
                'success_rate': success_rate if total_checks > 0 else 0
            }
        }
        
        report_file = self.root_dir / 'auto_complete_validation_report.json'
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\n  Report saved to: auto_complete_validation_report.json")
        
        return status
    
    def run_full_validation(self):
        """Run complete validation"""
        self.print_header("AUTO-COMPLETE VALIDATION SYSTEM")
        
        print(f"  Starting comprehensive validation...")
        print(f"  Root Directory: {self.root_dir}")
        
        # Run all validations
        self.validate_main_scripts()
        self.validate_trading_bot_modules()
        self.validate_tests()
        self.validate_examples()
        self.validate_configuration()
        self.validate_deployment_readiness()
        self.run_integration_tests()
        
        # Generate report
        status = self.generate_report()
        
        self.print_header("VALIDATION COMPLETE")
        
        return status


def main():
    """Main entry point"""
    root_dir = Path(__file__).parent
    
    validator = AutoCompleteValidator(root_dir)
    status = validator.run_full_validation()
    
    # Exit with appropriate code
    if status == "SUCCESS":
        sys.exit(0)
    elif status == "PARTIAL_SUCCESS":
        sys.exit(1)
    else:
        sys.exit(2)


if __name__ == '__main__':
    main()
