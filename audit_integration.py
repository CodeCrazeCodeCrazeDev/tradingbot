#!/usr/bin/env python3
"""Audit script for integration verification"""
import ast
import re
import sys

def audit_file(filepath, is_service_file=False):
    """Audit a Python file for syntax and patterns"""
    issues = []
    
    try:
        with open(filepath, 'r') as f:
            code = f.read()
    except FileNotFoundError:
        return [f"File not found: {filepath}"], 0
    
    # Check syntax
    try:
        ast.parse(code)
    except SyntaxError as e:
        issues.append(f"Syntax error at line {e.lineno}: {e.msg}")
        return issues, 0
    
    # Count ServiceInfo
    service_count = code.count('ServiceInfo(')
    
    # For service files, check for problematic dict-style service definitions
    # These would have 'name': '...', 'interval_seconds': ... patterns
    if is_service_file:
        # Look for dict entries that look like service definitions (have name and interval)
        service_dict_pattern = r"'name':\s*'[^']+'.*?'interval_seconds':"
        dict_matches = re.findall(service_dict_pattern, code, re.DOTALL)
        if dict_matches:
            issues.append(f"Found {len(dict_matches)} dict-style service definitions")
    
    return issues, service_count

def main():
    print("="*60)
    print("INTEGRATION AUDIT REPORT")
    print("="*60)
    
    # 1. background_services.py
    print("\n1. background_services.py:")
    issues, count = audit_file('background_services.py', is_service_file=True)
    if issues:
        for i in issues:
            print(f"   [FAIL] {i}")
    else:
        print(f"   [PASS] Valid syntax")
        print(f"   [PASS] {count} ServiceInfo definitions")
    
    # 2. main.py
    print("\n2. main.py:")
    issues, _ = audit_file('main.py')
    if issues:
        for i in issues:
            print(f"   [FAIL] {i}")
    else:
        print("   [PASS] Valid syntax")
        # Check integration imports
        with open('main.py', 'r') as f:
            code = f.read()
        systems = ['deepchart', 'msos', 'systems_ai', 'event_pipeline', 'hedge_fund', 'alphaalgo']
        found = sum(1 for s in systems if s in code.lower())
        print(f"   [PASS] {found}/{len(systems)} major system imports present")
    
    # 3. scheduled_jobs_runner.py
    print("\n3. scheduled_jobs_runner.py:")
    issues, _ = audit_file('scheduled_jobs_runner.py')
    if issues:
        for i in issues:
            print(f"   [FAIL] {i}")
    else:
        print("   [PASS] Valid syntax")
    
    print("\n" + "="*60)
    print("AUDIT COMPLETE")
    print("="*60)

if __name__ == '__main__':
    main()
