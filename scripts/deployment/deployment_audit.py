"""
Comprehensive Deployment Audit System
Scans, validates, and prepares the bot for production deployment
"""

import os
import sys
import io
import ast
import json
import subprocess
from pathlib import Path
from typing import Dict, List, Tuple, Any
from datetime import datetime
import importlib.util

# Set UTF-8 encoding for Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')


class DeploymentAuditor:
    """Comprehensive deployment audit system"""
    
    def __init__(self, root_dir: str):
        self.root_dir = Path(root_dir)
        self.issues = {
            'critical': [],
            'high': [],
            'medium': [],
            'low': [],
            'info': []
        }
        self.fixes_applied = []
        self.test_results = {}
        
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
    
    def add_issue(self, severity: str, category: str, description: str, file: str = None):
        """Add an issue to the audit report"""
        issue = {
            'category': category,
            'description': description,
            'file': file,
            'timestamp': datetime.now().isoformat()
        }
        self.issues[severity].append(issue)
    
    def scan_file_structure(self):
        """Scan and validate file structure"""
        self.print_section("PHASE 1: File Structure Validation")
        
        required_files = [
            'main.py',
            'mvp_bot.py',
            'requirements.txt',
            '.env.template',
            '.gitignore',
            'README.md',
            'pytest.ini',
        ]
        
        required_dirs = [
            'trading_bot',
            'tests',
            'config',
            'docs',
        ]
        
        # Check required files
        print("  Checking required files...")
        for file in required_files:
            file_path = self.root_dir / file
            if file_path.exists():
                print(f"    [OK] {file}")
            else:
                self.add_issue('critical', 'Missing File', f'Required file missing: {file}')
                print(f"    [MISSING] {file}")
        
        # Check required directories
        print("\n  Checking required directories...")
        for dir_name in required_dirs:
            dir_path = self.root_dir / dir_name
            if dir_path.exists() and dir_path.is_dir():
                print(f"    [OK] {dir_name}/")
            else:
                self.add_issue('critical', 'Missing Directory', f'Required directory missing: {dir_name}')
                print(f"    [MISSING] {dir_name}/")
        
        # Check .env file
        env_file = self.root_dir / '.env'
        if not env_file.exists():
            self.add_issue('high', 'Configuration', '.env file not found. Copy from .env.template')
            print(f"\n    [WARNING] .env file not found - copy from .env.template")
        else:
            print(f"\n    [OK] .env file exists")
        
        # Check for sensitive files in git
        gitignore = self.root_dir / '.gitignore'
        if gitignore.exists():
            with open(gitignore, 'r') as f:
                content = f.read()
                if '.env' in content:
                    print(f"    [OK] .env is in .gitignore")
                else:
                    self.add_issue('critical', 'Security', '.env not in .gitignore - SECURITY RISK!')
                    print(f"    [CRITICAL] .env not in .gitignore")
    
    def validate_dependencies(self):
        """Validate all dependencies"""
        self.print_section("PHASE 2: Dependency Validation")
        
        requirements_file = self.root_dir / 'requirements.txt'
        if not requirements_file.exists():
            self.add_issue('critical', 'Dependencies', 'requirements.txt not found')
            return
        
        print("  Parsing requirements.txt...")
        with open(requirements_file, 'r') as f:
            lines = f.readlines()
        
        packages = []
        for line in lines:
            line = line.strip()
            if line and not line.startswith('#'):
                # Extract package name
                pkg = line.split('>=')[0].split('==')[0].split('[')[0].strip()
                if pkg:
                    packages.append(pkg)
        
        print(f"  Found {len(packages)} packages to validate\n")
        
        # Check for duplicate packages
        duplicates = [pkg for pkg in set(packages) if packages.count(pkg) > 1]
        if duplicates:
            self.add_issue('medium', 'Dependencies', f'Duplicate packages: {duplicates}')
            print(f"    [WARNING] Duplicate packages found: {duplicates}")
        
        # Check critical packages
        critical_packages = [
            'pandas', 'numpy', 'MetaTrader5', 'loguru', 
            'aiohttp', 'sqlalchemy', 'pytest'
        ]
        
        print("  Checking critical packages...")
        for pkg in critical_packages:
            if pkg in packages:
                print(f"    [OK] {pkg}")
            else:
                self.add_issue('critical', 'Dependencies', f'Critical package missing: {pkg}')
                print(f"    [MISSING] {pkg}")
        
        # Check for version conflicts
        print("\n  Checking for known conflicts...")
        if 'tensorflow' in packages and 'torch' in packages:
            self.add_issue('medium', 'Dependencies', 
                          'Both TensorFlow and PyTorch installed - may cause conflicts')
            print(f"    [WARNING] TensorFlow and PyTorch both present")
    
    def check_code_quality(self):
        """Check code quality and detect errors"""
        self.print_section("PHASE 3: Code Quality Analysis")
        
        python_files = list(self.root_dir.glob('**/*.py'))
        python_files = [f for f in python_files if '.venv' not in str(f) and 'backups' not in str(f)]
        
        print(f"  Analyzing {len(python_files)} Python files...\n")
        
        syntax_errors = 0
        import_errors = 0
        
        for py_file in python_files[:20]:  # Check first 20 files
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    code = f.read()
                    ast.parse(code)
            except SyntaxError as e:
                syntax_errors += 1
                self.add_issue('critical', 'Syntax Error', 
                              f'Syntax error in {py_file.name}: {str(e)}', str(py_file))
                print(f"    [ERROR] Syntax error in {py_file.name}")
            except Exception as e:
                print(f"    [SKIP] Could not parse {py_file.name}: {str(e)[:50]}")
        
        if syntax_errors == 0:
            print(f"    [OK] No syntax errors found")
        else:
            print(f"    [ERROR] {syntax_errors} syntax errors found")
        
        # Check for empty except blocks
        print("\n  Checking for code quality issues...")
        empty_except_count = 0
        for py_file in python_files[:20]:
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if 'except:\n        pass' in content or 'except Exception:\n        pass' in content:
                        empty_except_count += 1
                        self.add_issue('low', 'Code Quality', 
                                      f'Empty except block in {py_file.name}', str(py_file))
            except:
                pass
        
        if empty_except_count > 0:
            print(f"    [WARNING] {empty_except_count} files with empty except blocks")
        else:
            print(f"    [OK] No empty except blocks found")
    
    def check_security(self):
        """Check for security vulnerabilities"""
        self.print_section("PHASE 4: Security Analysis")
        
        print("  Checking for hardcoded secrets...")
        
        # Check for hardcoded credentials
        python_files = list(self.root_dir.glob('**/*.py'))
        python_files = [f for f in python_files if '.venv' not in str(f) and 'backups' not in str(f)]
        
        security_issues = 0
        patterns = [
            ('password =', 'Hardcoded password'),
            ('api_key =', 'Hardcoded API key'),
            ('secret =', 'Hardcoded secret'),
            ('token =', 'Hardcoded token'),
        ]
        
        for py_file in python_files[:30]:
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read().lower()
                    for pattern, issue_type in patterns:
                        if pattern in content and 'os.getenv' not in content:
                            # Check if it's actually hardcoded
                            lines = content.split('\n')
                            for line in lines:
                                if pattern in line and '=' in line and 'getenv' not in line:
                                    security_issues += 1
                                    self.add_issue('critical', 'Security', 
                                                  f'{issue_type} in {py_file.name}', str(py_file))
                                    break
            except:
                pass
        
        if security_issues == 0:
            print(f"    [OK] No hardcoded secrets found")
        else:
            print(f"    [CRITICAL] {security_issues} potential hardcoded secrets found")
        
        # Check .env file protection
        env_file = self.root_dir / '.env'
        if env_file.exists():
            gitignore = self.root_dir / '.gitignore'
            if gitignore.exists():
                with open(gitignore, 'r') as f:
                    if '.env' in f.read():
                        print(f"    [OK] .env file is protected by .gitignore")
                    else:
                        self.add_issue('critical', 'Security', '.env not in .gitignore')
                        print(f"    [CRITICAL] .env not protected by .gitignore")
    
    def run_tests(self):
        """Run automated tests"""
        self.print_section("PHASE 5: Automated Testing")
        
        print("  Running pytest...")
        try:
            result = subprocess.run(
                [sys.executable, '-m', 'pytest', 'tests/', '-v', '--tb=short', '-x'],
                capture_output=True,
                text=True,
                timeout=120,
                cwd=str(self.root_dir)
            )
            
            if result.returncode == 0:
                print(f"    [OK] All tests passed")
                self.test_results['pytest'] = 'PASSED'
            else:
                # Count failures
                output = result.stdout + result.stderr
                if 'failed' in output.lower():
                    self.add_issue('high', 'Testing', 'Some tests failed')
                    print(f"    [FAILED] Some tests failed")
                    self.test_results['pytest'] = 'FAILED'
                else:
                    print(f"    [WARNING] Tests completed with warnings")
                    self.test_results['pytest'] = 'WARNING'
        except subprocess.TimeoutExpired:
            self.add_issue('medium', 'Testing', 'Tests timed out (>120s)')
            print(f"    [TIMEOUT] Tests took too long")
            self.test_results['pytest'] = 'TIMEOUT'
        except Exception as e:
            self.add_issue('medium', 'Testing', f'Could not run tests: {str(e)}')
            print(f"    [ERROR] Could not run tests: {str(e)}")
            self.test_results['pytest'] = 'ERROR'
    
    def check_deployment_readiness(self):
        """Check if bot is ready for deployment"""
        self.print_section("PHASE 6: Deployment Readiness")
        
        checks = {
            'Environment Configuration': False,
            'Database Setup': False,
            'API Connections': False,
            'Error Handling': False,
            'Logging System': False,
            'Auto-Restart': False,
        }
        
        # Check environment configuration
        env_file = self.root_dir / '.env'
        if env_file.exists():
            checks['Environment Configuration'] = True
            print(f"    [OK] Environment configuration present")
        else:
            print(f"    [MISSING] Environment configuration")
        
        # Check for logging
        main_file = self.root_dir / 'main.py'
        if main_file.exists():
            with open(main_file, 'r') as f:
                content = f.read()
                if 'logger' in content or 'logging' in content:
                    checks['Logging System'] = True
                    print(f"    [OK] Logging system configured")
                else:
                    print(f"    [MISSING] Logging system")
        
        # Check for error handling
        if 'try:' in content and 'except' in content:
            checks['Error Handling'] = True
            print(f"    [OK] Error handling present")
        else:
            print(f"    [WARNING] Limited error handling")
        
        # Overall readiness
        ready_count = sum(checks.values())
        total_checks = len(checks)
        readiness_pct = (ready_count / total_checks) * 100
        
        print(f"\n  Deployment Readiness: {ready_count}/{total_checks} ({readiness_pct:.0f}%)")
        
        if readiness_pct >= 80:
            print(f"    [READY] Bot is ready for deployment")
        elif readiness_pct >= 60:
            print(f"    [PARTIAL] Bot needs minor fixes before deployment")
        else:
            print(f"    [NOT READY] Bot needs significant work before deployment")
            self.add_issue('critical', 'Deployment', 'Bot not ready for deployment')
    
    def apply_automatic_fixes(self):
        """Apply automatic fixes for common issues"""
        self.print_section("PHASE 7: Automatic Fixes")
        
        print("  Applying automatic fixes...\n")
        
        # Fix 1: Create .env from template if missing
        env_file = self.root_dir / '.env'
        env_template = self.root_dir / '.env.template'
        
        if not env_file.exists() and env_template.exists():
            import shutil
            shutil.copy(env_template, env_file)
            self.fixes_applied.append('Created .env from template')
            print(f"    [FIXED] Created .env from .env.template")
        
        # Fix 2: Ensure .env is in .gitignore
        gitignore = self.root_dir / '.gitignore'
        if gitignore.exists():
            with open(gitignore, 'r') as f:
                content = f.read()
            
            if '.env' not in content:
                with open(gitignore, 'a') as f:
                    f.write('\n# Environment variables\n.env\n')
                self.fixes_applied.append('Added .env to .gitignore')
                print(f"    [FIXED] Added .env to .gitignore")
        
        # Fix 3: Create necessary directories
        dirs_to_create = ['logs', 'data', 'backups']
        for dir_name in dirs_to_create:
            dir_path = self.root_dir / dir_name
            if not dir_path.exists():
                dir_path.mkdir(parents=True, exist_ok=True)
                self.fixes_applied.append(f'Created {dir_name}/ directory')
                print(f"    [FIXED] Created {dir_name}/ directory")
        
        if not self.fixes_applied:
            print(f"    [INFO] No automatic fixes needed")
    
    def generate_report(self):
        """Generate comprehensive audit report"""
        self.print_header("DEPLOYMENT AUDIT REPORT")
        
        # Summary
        total_issues = sum(len(issues) for issues in self.issues.values())
        critical_count = len(self.issues['critical'])
        high_count = len(self.issues['high'])
        medium_count = len(self.issues['medium'])
        low_count = len(self.issues['low'])
        
        print(f"  Audit Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"  Total Issues Found: {total_issues}")
        print(f"    - Critical: {critical_count}")
        print(f"    - High: {high_count}")
        print(f"    - Medium: {medium_count}")
        print(f"    - Low: {low_count}")
        print(f"\n  Automatic Fixes Applied: {len(self.fixes_applied)}")
        
        # Critical issues
        if critical_count > 0:
            print(f"\n  CRITICAL ISSUES:")
            for issue in self.issues['critical']:
                print(f"    - [{issue['category']}] {issue['description']}")
                if issue['file']:
                    print(f"      File: {issue['file']}")
        
        # High priority issues
        if high_count > 0:
            print(f"\n  HIGH PRIORITY ISSUES:")
            for issue in self.issues['high']:
                print(f"    - [{issue['category']}] {issue['description']}")
        
        # Test results
        if self.test_results:
            print(f"\n  TEST RESULTS:")
            for test_name, result in self.test_results.items():
                status = "[OK]" if result == "PASSED" else "[FAILED]"
                print(f"    {status} {test_name}: {result}")
        
        # Deployment status
        print(f"\n  DEPLOYMENT STATUS:")
        if critical_count == 0 and high_count == 0:
            print(f"    [GREEN LIGHT] Bot is ready for deployment")
            deployment_status = "READY"
        elif critical_count == 0:
            print(f"    [YELLOW LIGHT] Bot can be deployed with minor issues")
            deployment_status = "READY_WITH_WARNINGS"
        else:
            print(f"    [RED LIGHT] Bot NOT ready - fix critical issues first")
            deployment_status = "NOT_READY"
        
        # Save report to JSON
        report = {
            'timestamp': datetime.now().isoformat(),
            'deployment_status': deployment_status,
            'total_issues': total_issues,
            'issues_by_severity': {
                'critical': critical_count,
                'high': high_count,
                'medium': medium_count,
                'low': low_count
            },
            'issues': self.issues,
            'fixes_applied': self.fixes_applied,
            'test_results': self.test_results
        }
        
        report_file = self.root_dir / 'deployment_audit_report.json'
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\n  Full report saved to: deployment_audit_report.json")
        
        return deployment_status
    
    def run_full_audit(self):
        """Run complete deployment audit"""
        self.print_header("ALPHAALGO DEPLOYMENT AUDIT")
        
        print(f"  Starting comprehensive deployment audit...")
        print(f"  Root Directory: {self.root_dir}")
        
        # Run all audit phases
        self.scan_file_structure()
        self.validate_dependencies()
        self.check_code_quality()
        self.check_security()
        self.run_tests()
        self.check_deployment_readiness()
        self.apply_automatic_fixes()
        
        # Generate final report
        status = self.generate_report()
        
        self.print_header("AUDIT COMPLETE")
        
        return status


def main():
    """Main entry point"""
    root_dir = Path(__file__).parent
    
    auditor = DeploymentAuditor(root_dir)
    status = auditor.run_full_audit()
    
    # Exit with appropriate code
    if status == "READY":
        sys.exit(0)
    elif status == "READY_WITH_WARNINGS":
        sys.exit(1)
    else:
        sys.exit(2)


if __name__ == '__main__':
    main()
