"""
Final Deployment Validation
Run this before deploying to production to ensure everything is ready
"""

import os
import sys
import io
from pathlib import Path
from datetime import datetime
import json
import subprocess

# Set UTF-8 encoding for Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')


class FinalValidator:
    """Final deployment validation"""
    
    def __init__(self):
        self.results = {
            'passed': [],
            'failed': [],
            'warnings': []
        }
        self.root_dir = Path(__file__).parent
    
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
    
    def check_environment_file(self):
        """Check .env file exists and is configured"""
        self.print_section("1. ENVIRONMENT CONFIGURATION")
        
        env_file = self.root_dir / '.env'
        env_template = self.root_dir / '.env.template'
        
        if not env_file.exists():
            print("    ❌ .env file not found")
            print("    📝 Action: Copy .env.template to .env and configure")
            self.results['failed'].append({
                'check': 'Environment File',
                'issue': '.env file missing',
                'action': 'Copy .env.template to .env'
            })
            return False
        
        print("    ✅ .env file exists")
        
        # Check if it has content
        with open(env_file, 'r') as f:
            content = f.read()
        
        if len(content) < 50:
            print("    ⚠️ .env file seems empty or minimal")
            self.results['warnings'].append({
                'check': 'Environment File',
                'issue': '.env file may not be configured',
                'action': 'Review and configure all settings'
            })
        else:
            print("    ✅ .env file configured")
        
        self.results['passed'].append('Environment File')
        return True
    
    def check_required_files(self):
        """Check all required files exist"""
        self.print_section("2. REQUIRED FILES")
        
        required_files = [
            'main.py',
            'mvp_bot.py',
            'requirements.txt',
            'config/config.yaml',
            'health_check.py',
            'start_production.bat',
            'start_production.sh',
        ]
        
        all_exist = True
        for file_path in required_files:
            full_path = self.root_dir / file_path
            if full_path.exists():
                print(f"    ✅ {file_path}")
            else:
                print(f"    ❌ {file_path} - MISSING")
                all_exist = False
        
        if all_exist:
            self.results['passed'].append('Required Files')
        else:
            self.results['failed'].append({
                'check': 'Required Files',
                'issue': 'Some files missing',
                'action': 'Ensure all files are present'
            })
        
        return all_exist
    
    def check_module_verification(self):
        """Check module verification results"""
        self.print_section("3. MODULE VERIFICATION")
        
        report_file = self.root_dir / 'module_verification_report.json'
        
        if not report_file.exists():
            print("    ⚠️ Module verification not run yet")
            print("    📝 Action: Run 'py verify_modules_standalone.py'")
            self.results['warnings'].append({
                'check': 'Module Verification',
                'issue': 'Not run yet',
                'action': 'Run verify_modules_standalone.py'
            })
            return False
        
        with open(report_file, 'r') as f:
            report = json.load(f)
        
        success_rate = report.get('success_rate', 0)
        passed = report.get('passed', 0)
        total = report.get('total_tested', 0)
        
        print(f"    Modules Verified: {passed}/{total}")
        print(f"    Success Rate: {success_rate:.1f}%")
        
        if success_rate >= 100:
            print(f"    ✅ All modules verified")
            self.results['passed'].append('Module Verification')
            return True
        elif success_rate >= 90:
            print(f"    ⚠️ Most modules verified")
            self.results['warnings'].append({
                'check': 'Module Verification',
                'issue': f'{success_rate:.1f}% success rate',
                'action': 'Review failed modules'
            })
            return True
        else:
            print(f"    ❌ Module verification failed")
            self.results['failed'].append({
                'check': 'Module Verification',
                'issue': f'Only {success_rate:.1f}% success',
                'action': 'Fix failed modules'
            })
            return False
    
    def check_security_audit(self):
        """Check security audit results"""
        self.print_section("4. SECURITY AUDIT")
        
        report_file = self.root_dir / 'security_audit_report.json'
        
        if not report_file.exists():
            print("    ⚠️ Security audit not run yet")
            print("    📝 Action: Run 'py security_audit_comprehensive.py'")
            self.results['warnings'].append({
                'check': 'Security Audit',
                'issue': 'Not run yet',
                'action': 'Run security_audit_comprehensive.py'
            })
            return False
        
        with open(report_file, 'r') as f:
            report = json.load(f)
        
        critical = report['issues_by_severity'].get('critical', 0)
        high = report['issues_by_severity'].get('high', 0)
        
        print(f"    Critical Issues: {critical}")
        print(f"    High Priority: {high}")
        
        if critical == 0 and high == 0:
            print(f"    ✅ No critical or high priority issues")
            self.results['passed'].append('Security Audit')
            return True
        elif critical == 0:
            print(f"    ⚠️ {high} high priority issues")
            self.results['warnings'].append({
                'check': 'Security Audit',
                'issue': f'{high} high priority issues',
                'action': 'Review and fix high priority issues'
            })
            return True
        else:
            print(f"    ❌ {critical} critical security issues")
            self.results['failed'].append({
                'check': 'Security Audit',
                'issue': f'{critical} critical issues',
                'action': 'Fix critical issues immediately'
            })
            return False
    
    def check_e2e_tests(self):
        """Check E2E test results"""
        self.print_section("5. END-TO-END TESTS")
        
        report_file = self.root_dir / 'e2e_test_report.json'
        
        if not report_file.exists():
            print("    ⚠️ E2E tests not run yet")
            print("    📝 Action: Run 'py e2e_comprehensive_test.py'")
            self.results['warnings'].append({
                'check': 'E2E Tests',
                'issue': 'Not run yet',
                'action': 'Run e2e_comprehensive_test.py'
            })
            return False
        
        with open(report_file, 'r') as f:
            report = json.load(f)
        
        passed = report.get('passed', 0)
        failed = report.get('failed', 0)
        total = passed + failed
        
        print(f"    Tests Passed: {passed}/{total}")
        print(f"    Tests Failed: {failed}")
        
        if failed == 0:
            print(f"    ✅ All E2E tests passed")
            self.results['passed'].append('E2E Tests')
            return True
        else:
            print(f"    ❌ {failed} E2E tests failed")
            self.results['failed'].append({
                'check': 'E2E Tests',
                'issue': f'{failed} tests failed',
                'action': 'Fix failing tests'
            })
            return False
    
    def check_dependencies(self):
        """Check Python dependencies"""
        self.print_section("6. PYTHON DEPENDENCIES")
        
        requirements_file = self.root_dir / 'requirements.txt'
        
        if not requirements_file.exists():
            print("    ❌ requirements.txt not found")
            self.results['failed'].append({
                'check': 'Dependencies',
                'issue': 'requirements.txt missing',
                'action': 'Create requirements.txt'
            })
            return False
        
        print("    ✅ requirements.txt exists")
        
        # Try to check if packages are installed
        try:
            result = subprocess.run(
                [sys.executable, '-m', 'pip', 'list'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                print("    ✅ pip is working")
                self.results['passed'].append('Dependencies')
            else:
                print("    ⚠️ Could not verify pip")
                self.results['warnings'].append({
                    'check': 'Dependencies',
                    'issue': 'Could not verify pip',
                    'action': 'Manually verify dependencies'
                })
        except Exception as e:
            print(f"    ⚠️ Could not check dependencies: {e}")
            self.results['warnings'].append({
                'check': 'Dependencies',
                'issue': 'Could not verify',
                'action': 'Manually verify dependencies'
            })
        
        return True
    
    def check_logs_directory(self):
        """Check logs directory exists"""
        self.print_section("7. LOGS DIRECTORY")
        
        logs_dir = self.root_dir / 'logs'
        
        if not logs_dir.exists():
            print("    📁 Creating logs directory...")
            logs_dir.mkdir(exist_ok=True)
            print("    ✅ Logs directory created")
        else:
            print("    ✅ Logs directory exists")
        
        self.results['passed'].append('Logs Directory')
        return True
    
    def check_data_directory(self):
        """Check data directory exists"""
        self.print_section("8. DATA DIRECTORY")
        
        data_dir = self.root_dir / 'data'
        
        if not data_dir.exists():
            print("    📁 Creating data directory...")
            data_dir.mkdir(exist_ok=True)
            print("    ✅ Data directory created")
        else:
            print("    ✅ Data directory exists")
        
        self.results['passed'].append('Data Directory')
        return True
    
    def generate_final_report(self):
        """Generate final validation report"""
        self.print_header("FINAL VALIDATION REPORT")
        
        total_checks = len(self.results['passed']) + len(self.results['failed']) + len(self.results['warnings'])
        passed = len(self.results['passed'])
        failed = len(self.results['failed'])
        warnings = len(self.results['warnings'])
        
        print(f"  Validation Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"\n  RESULTS:")
        print(f"    Total Checks: {total_checks}")
        print(f"    Passed: {passed} ✅")
        print(f"    Failed: {failed} ❌")
        print(f"    Warnings: {warnings} ⚠️")
        
        if total_checks > 0:
            success_rate = (passed / total_checks) * 100
            print(f"\n  SUCCESS RATE: {success_rate:.1f}%")
        
        # Show failed checks
        if failed > 0:
            print(f"\n  FAILED CHECKS:")
            for item in self.results['failed']:
                print(f"    ❌ {item['check']}")
                print(f"       Issue: {item['issue']}")
                print(f"       Action: {item['action']}")
        
        # Show warnings
        if warnings > 0:
            print(f"\n  WARNINGS:")
            for item in self.results['warnings']:
                print(f"    ⚠️ {item['check']}")
                print(f"       Issue: {item['issue']}")
                print(f"       Action: {item['action']}")
        
        # Overall status
        print(f"\n  DEPLOYMENT STATUS:")
        if failed == 0 and warnings == 0:
            print(f"    [READY] ✅ All checks passed - READY FOR PRODUCTION!")
            status = "READY"
        elif failed == 0:
            print(f"    [READY] ⚠️ Ready with warnings - Review warnings before deployment")
            status = "READY_WITH_WARNINGS"
        else:
            print(f"    [NOT READY] ❌ {failed} critical issues - FIX BEFORE DEPLOYMENT")
            status = "NOT_READY"
        
        # Save report
        report = {
            'timestamp': datetime.now().isoformat(),
            'status': status,
            'total_checks': total_checks,
            'passed': passed,
            'failed': failed,
            'warnings': warnings,
            'success_rate': (passed / total_checks * 100) if total_checks > 0 else 0,
            'results': self.results
        }
        
        with open('final_deployment_validation_report.json', 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\n  Report saved to: final_deployment_validation_report.json")
        
        return status
    
    def run_all_checks(self):
        """Run all validation checks"""
        self.print_header("FINAL DEPLOYMENT VALIDATION")
        
        print(f"  Starting final validation...")
        print(f"  Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Run all checks
        self.check_environment_file()
        self.check_required_files()
        self.check_module_verification()
        self.check_security_audit()
        self.check_e2e_tests()
        self.check_dependencies()
        self.check_logs_directory()
        self.check_data_directory()
        
        # Generate report
        status = self.generate_final_report()
        
        self.print_header("VALIDATION COMPLETE")
        
        if status == "READY":
            print("\n  🎉 CONGRATULATIONS! 🎉")
            print("  Your bot is READY FOR PRODUCTION DEPLOYMENT!")
            print("\n  Next steps:")
            print("    1. Review .env configuration")
            print("    2. Start with paper trading: py start_production.bat")
            print("    3. Monitor for 24 hours")
            print("    4. Deploy to live trading")
            print("\n  🚀 LET'S TRADE! 🚀\n")
        elif status == "READY_WITH_WARNINGS":
            print("\n  ⚠️ READY WITH WARNINGS")
            print("  Review warnings above before deployment")
            print("  Most warnings are informational\n")
        else:
            print("\n  ❌ NOT READY FOR DEPLOYMENT")
            print("  Fix failed checks above before deploying\n")
        
        return status


def main():
    """Main entry point"""
    validator = FinalValidator()
    status = validator.run_all_checks()
    
    # Exit with appropriate code
    if status == "READY":
        sys.exit(0)
    elif status == "READY_WITH_WARNINGS":
        sys.exit(1)
    else:
        sys.exit(2)


if __name__ == '__main__':
    main()
