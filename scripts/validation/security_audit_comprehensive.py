"""
Comprehensive Security Audit
Scans for hardcoded secrets, vulnerabilities, and security issues
"""

import os
import sys
import io
import re
from pathlib import Path
from datetime import datetime
import json

# Set UTF-8 encoding for Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')


class SecurityAuditor:
    """Comprehensive security auditor"""
    
    def __init__(self, root_dir: str):
        self.root_dir = Path(root_dir)
        self.issues = {
            'critical': [],
            'high': [],
            'medium': [],
            'low': [],
            'info': []
        }
        
        # Patterns to detect
        self.secret_patterns = [
            (r'password\s*=\s*["\']([^"\']+)["\']', 'Hardcoded password'),
            (r'api_key\s*=\s*["\']([^"\']+)["\']', 'Hardcoded API key'),
            (r'secret\s*=\s*["\']([^"\']+)["\']', 'Hardcoded secret'),
            (r'token\s*=\s*["\']([^"\']+)["\']', 'Hardcoded token'),
            (r'aws_access_key\s*=\s*["\']([^"\']+)["\']', 'AWS access key'),
            (r'private_key\s*=\s*["\']([^"\']+)["\']', 'Private key'),
        ]
        
        # SQL injection patterns
        self.sql_patterns = [
            (r'execute\(["\'].*%s.*["\']\s*%', 'Potential SQL injection'),
            (r'\.format\(.*\).*execute', 'Potential SQL injection'),
            (r'f["\'].*{.*}.*["\'].*execute', 'Potential SQL injection'),
        ]
        
        # Unsafe patterns
        self.unsafe_patterns = [
            (r'eval\(', 'Unsafe eval() usage'),
            (r'exec\(', 'Unsafe exec() usage'),
            (r'__import__\(', 'Dynamic import'),
            (r'pickle\.loads?\(', 'Unsafe pickle usage'),
        ]
    
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
    
    def add_issue(self, severity: str, category: str, description: str, 
                  file: str = None, line: int = None, code: str = None):
        """Add security issue"""
        issue = {
            'category': category,
            'description': description,
            'file': str(file) if file else None,
            'line': line,
            'code': code,
            'timestamp': datetime.now().isoformat()
        }
        self.issues[severity].append(issue)
    
    def scan_file_for_secrets(self, file_path: Path):
        """Scan file for hardcoded secrets"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.split('\n')
            
            for line_num, line in enumerate(lines, 1):
                # Skip comments
                if line.strip().startswith('#'):
                    continue
                
                # Check for secrets
                for pattern, description in self.secret_patterns:
                    matches = re.finditer(pattern, line, re.IGNORECASE)
                    for match in matches:
                        # Check if it's using os.getenv or similar
                        if 'os.getenv' in line or 'os.environ' in line or 'get_env' in line:
                            continue
                        
                        # Check if it's a placeholder
                        value = match.group(1) if match.groups() else match.group(0)
                        if any(placeholder in value.lower() for placeholder in 
                               ['your_', 'placeholder', 'example', 'xxx', 'changeme', 'todo']):
                            continue
                        
                        self.add_issue(
                            'critical',
                            'Hardcoded Secret',
                            description,
                            file_path,
                            line_num,
                            line.strip()
                        )
        
        except Exception as e:
            pass
    
    def scan_file_for_sql_injection(self, file_path: Path):
        """Scan for SQL injection vulnerabilities"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.split('\n')
            
            for line_num, line in enumerate(lines, 1):
                for pattern, description in self.sql_patterns:
                    if re.search(pattern, line):
                        self.add_issue(
                            'high',
                            'SQL Injection',
                            description,
                            file_path,
                            line_num,
                            line.strip()
                        )
        
        except Exception as e:
            pass
    
    def scan_file_for_unsafe_code(self, file_path: Path):
        """Scan for unsafe code patterns"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.split('\n')
            
            for line_num, line in enumerate(lines, 1):
                for pattern, description in self.unsafe_patterns:
                    if re.search(pattern, line):
                        self.add_issue(
                            'medium',
                            'Unsafe Code',
                            description,
                            file_path,
                            line_num,
                            line.strip()
                        )
        
        except Exception as e:
            pass
    
    def check_env_file_security(self):
        """Check .env file security"""
        self.print_section("CHECKING .ENV FILE SECURITY")
        
        env_file = self.root_dir / '.env'
        gitignore = self.root_dir / '.gitignore'
        
        # Check if .env exists
        if env_file.exists():
            print(f"    [FOUND] .env file exists")
            
            # Check if in .gitignore
            if gitignore.exists():
                with open(gitignore, 'r') as f:
                    gitignore_content = f.read()
                
                if '.env' in gitignore_content:
                    print(f"    [OK] .env is in .gitignore")
                else:
                    self.add_issue(
                        'critical',
                        'Git Security',
                        '.env file not in .gitignore - CRITICAL SECURITY RISK!',
                        gitignore
                    )
                    print(f"    [CRITICAL] .env NOT in .gitignore!")
            else:
                self.add_issue(
                    'high',
                    'Git Security',
                    'No .gitignore file found',
                    None
                )
                print(f"    [WARNING] No .gitignore file")
        else:
            print(f"    [INFO] No .env file (using .env.template)")
    
    def check_file_permissions(self):
        """Check file permissions (Unix only)"""
        if sys.platform != 'win32':
            self.print_section("CHECKING FILE PERMISSIONS")
            
            sensitive_files = ['.env', 'config/api_keys.json', 'secrets/']
            
            for file_name in sensitive_files:
                file_path = self.root_dir / file_name
                if file_path.exists():
                    stat_info = file_path.stat()
                    mode = oct(stat_info.st_mode)[-3:]
                    
                    # Should be 600 or 400 (owner only)
                    if mode not in ['600', '400']:
                        self.add_issue(
                            'high',
                            'File Permissions',
                            f'File {file_name} has insecure permissions: {mode}',
                            file_path
                        )
                        print(f"    [WARNING] {file_name}: {mode} (should be 600)")
                    else:
                        print(f"    [OK] {file_name}: {mode}")
    
    def scan_all_files(self):
        """Scan all Python files"""
        self.print_section("SCANNING PYTHON FILES")
        
        py_files = list(self.root_dir.glob('**/*.py'))
        py_files = [f for f in py_files if '.venv' not in str(f) and 'backups' not in str(f)]
        
        print(f"    Scanning {len(py_files)} Python files...\n")
        
        scanned = 0
        for py_file in py_files:
            self.scan_file_for_secrets(py_file)
            self.scan_file_for_sql_injection(py_file)
            self.scan_file_for_unsafe_code(py_file)
            scanned += 1
            
            if scanned % 50 == 0:
                print(f"    Scanned {scanned}/{len(py_files)} files...")
        
        print(f"\n    Scan complete: {scanned} files")
    
    def generate_report(self):
        """Generate security audit report"""
        self.print_header("SECURITY AUDIT REPORT")
        
        # Count issues
        total_issues = sum(len(issues) for issues in self.issues.values())
        critical = len(self.issues['critical'])
        high = len(self.issues['high'])
        medium = len(self.issues['medium'])
        low = len(self.issues['low'])
        
        print(f"  Audit Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"\n  RESULTS:")
        print(f"    Total Issues: {total_issues}")
        print(f"    Critical: {critical} 🔴")
        print(f"    High: {high} ⚠️")
        print(f"    Medium: {medium}")
        print(f"    Low: {low}")
        
        # Show critical issues
        if critical > 0:
            print(f"\n  CRITICAL ISSUES:")
            for issue in self.issues['critical']:
                print(f"    🔴 {issue['description']}")
                if issue['file']:
                    print(f"       File: {issue['file']}")
                if issue['line']:
                    print(f"       Line: {issue['line']}")
                if issue['code']:
                    print(f"       Code: {issue['code'][:80]}")
        
        # Show high priority issues
        if high > 0:
            print(f"\n  HIGH PRIORITY ISSUES:")
            for issue in self.issues['high'][:5]:
                print(f"    ⚠️ {issue['description']}")
                if issue['file']:
                    print(f"       File: {issue['file']}")
        
        # Overall status
        print(f"\n  OVERALL STATUS:")
        if critical == 0 and high == 0:
            print(f"    [SECURE] No critical or high priority issues ✅")
            status = "SECURE"
        elif critical == 0:
            print(f"    [WARNING] {high} high priority issues ⚠️")
            status = "WARNING"
        else:
            print(f"    [CRITICAL] {critical} critical issues - FIX IMMEDIATELY! 🔴")
            status = "CRITICAL"
        
        # Save report
        report = {
            'timestamp': datetime.now().isoformat(),
            'status': status,
            'total_issues': total_issues,
            'issues_by_severity': {
                'critical': critical,
                'high': high,
                'medium': medium,
                'low': low
            },
            'issues': self.issues
        }
        
        with open('security_audit_report.json', 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\n  Report saved to: security_audit_report.json")
        
        return status
    
    def run_full_audit(self):
        """Run complete security audit"""
        self.print_header("COMPREHENSIVE SECURITY AUDIT")
        
        print(f"  Starting security audit...")
        print(f"  Root Directory: {self.root_dir}")
        
        # Run all checks
        self.check_env_file_security()
        self.check_file_permissions()
        self.scan_all_files()
        
        # Generate report
        status = self.generate_report()
        
        self.print_header("AUDIT COMPLETE")
        
        return status


def main():
    """Main entry point"""
    root_dir = Path(__file__).parent
    
    auditor = SecurityAuditor(root_dir)
    status = auditor.run_full_audit()
    
    # Exit with appropriate code
    if status == "SECURE":
        sys.exit(0)
    elif status == "WARNING":
        sys.exit(1)
    else:
        sys.exit(2)


if __name__ == '__main__':
    main()
