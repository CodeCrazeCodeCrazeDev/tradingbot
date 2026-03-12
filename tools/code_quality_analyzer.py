"""
Code Quality Analyzer for Trading Bot
Analyzes code quality, identifies issues, and suggests improvements
"""

import ast
import sys
from pathlib import Path
from typing import Dict, List, Set
import re
from collections import defaultdict

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class CodeQualityAnalyzer:
    """Analyzes code quality and identifies issues"""
    
    def __init__(self, source_dir: Path):
        self.source_dir = source_dir
        self.issues = defaultdict(list)
        self.metrics = {}
        
    def analyze_all(self):
        """Run all code quality checks"""
        print(f"\nAnalyzing code in: {self.source_dir}")
        print("="*70)
        
        python_files = list(self.source_dir.rglob("*.py"))
        print(f"Found {len(python_files)} Python files")
        
        for file_path in python_files:
            if '__pycache__' in str(file_path) or 'venv' in str(file_path):
                continue
            
            self.analyze_file(file_path)
        
        self.print_summary()
        
    def analyze_file(self, file_path: Path):
        """Analyze a single file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Parse AST
            try:
                tree = ast.parse(content)
            except SyntaxError as e:
                self.issues['syntax_errors'].append({
                    'file': str(file_path),
                    'line': e.lineno,
                    'message': str(e)
                })
                return
            
            # Run checks
            self.check_function_complexity(file_path, tree)
            self.check_duplicate_code(file_path, content)
            self.check_naming_conventions(file_path, tree)
            self.check_docstrings(file_path, tree)
            self.check_magic_numbers(file_path, tree)
            self.check_long_lines(file_path, content)
            self.check_unused_imports(file_path, tree, content)
            
        except Exception as e:
            self.issues['analysis_errors'].append({
                'file': str(file_path),
                'error': str(e)
            })
    
    def check_function_complexity(self, file_path: Path, tree: ast.AST):
        """Check for overly complex functions"""
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                complexity = self._calculate_complexity(node)
                
                if complexity > 10:
                    self.issues['high_complexity'].append({
                        'file': str(file_path),
                        'function': node.name,
                        'line': node.lineno,
                        'complexity': complexity
                    })
    
    def _calculate_complexity(self, node: ast.FunctionDef) -> int:
        """Calculate cyclomatic complexity"""
        complexity = 1
        
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.ExceptHandler)):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1
        
        return complexity
    
    def check_duplicate_code(self, file_path: Path, content: str):
        """Check for duplicate code blocks"""
        lines = content.split('\n')
        
        # Simple duplicate detection: look for identical blocks of 5+ lines
        block_size = 5
        blocks = {}
        
        for i in range(len(lines) - block_size):
            block = '\n'.join(lines[i:i+block_size])
            block_stripped = block.strip()
            
            if len(block_stripped) > 50:  # Ignore small blocks
                if block_stripped in blocks:
                    blocks[block_stripped].append(i)
                else:
                    blocks[block_stripped] = [i]
        
        for block, line_numbers in blocks.items():
            if len(line_numbers) > 1:
                self.issues['duplicate_code'].append({
                    'file': str(file_path),
                    'lines': line_numbers,
                    'occurrences': len(line_numbers)
                })
    
    def check_naming_conventions(self, file_path: Path, tree: ast.AST):
        """Check naming conventions"""
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                if not self._is_snake_case(node.name) and not node.name.startswith('_'):
                    self.issues['naming_convention'].append({
                        'file': str(file_path),
                        'type': 'function',
                        'name': node.name,
                        'line': node.lineno,
                        'suggestion': self._to_snake_case(node.name)
                    })
            
            elif isinstance(node, ast.ClassDef):
                if not self._is_pascal_case(node.name):
                    self.issues['naming_convention'].append({
                        'file': str(file_path),
                        'type': 'class',
                        'name': node.name,
                        'line': node.lineno,
                        'suggestion': self._to_pascal_case(node.name)
                    })
    
    def _is_snake_case(self, name: str) -> bool:
        """Check if name is in snake_case"""
        return re.match(r'^[a-z_][a-z0-9_]*$', name) is not None
    
    def _is_pascal_case(self, name: str) -> bool:
        """Check if name is in PascalCase"""
        return re.match(r'^[A-Z][a-zA-Z0-9]*$', name) is not None
    
    def _to_snake_case(self, name: str) -> str:
        """Convert name to snake_case"""
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
        return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()
    
    def _to_pascal_case(self, name: str) -> str:
        """Convert name to PascalCase"""
        return ''.join(word.capitalize() for word in name.split('_'))
    
    def check_docstrings(self, file_path: Path, tree: ast.AST):
        """Check for missing docstrings"""
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                if not ast.get_docstring(node):
                    self.issues['missing_docstrings'].append({
                        'file': str(file_path),
                        'type': 'function' if isinstance(node, ast.FunctionDef) else 'class',
                        'name': node.name,
                        'line': node.lineno
                    })
    
    def check_magic_numbers(self, file_path: Path, tree: ast.AST):
        """Check for magic numbers"""
        for node in ast.walk(tree):
            if isinstance(node, ast.Num):
                # Ignore common numbers
                if node.n not in [0, 1, -1, 2, 10, 100, 1000]:
                    self.issues['magic_numbers'].append({
                        'file': str(file_path),
                        'line': node.lineno,
                        'value': node.n
                    })
    
    def check_long_lines(self, file_path: Path, content: str):
        """Check for lines exceeding 120 characters"""
        lines = content.split('\n')
        
        for i, line in enumerate(lines, 1):
            if len(line) > 120:
                self.issues['long_lines'].append({
                    'file': str(file_path),
                    'line': i,
                    'length': len(line)
                })
    
    def check_unused_imports(self, file_path: Path, tree: ast.AST, content: str):
        """Check for unused imports"""
        imports = set()
        used_names = set()
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.add(alias.asname if alias.asname else alias.name)
            elif isinstance(node, ast.ImportFrom):
                for alias in node.names:
                    imports.add(alias.asname if alias.asname else alias.name)
            elif isinstance(node, ast.Name):
                used_names.add(node.id)
        
        unused = imports - used_names
        
        if unused:
            self.issues['unused_imports'].append({
                'file': str(file_path),
                'imports': list(unused)
            })
    
    def print_summary(self):
        """Print analysis summary"""
        print("\n" + "="*70)
        print("CODE QUALITY ANALYSIS SUMMARY")
        print("="*70)
        
        total_issues = sum(len(issues) for issues in self.issues.values())
        
        print(f"\nTotal Issues Found: {total_issues}")
        
        if total_issues == 0:
            print("\n✓ No issues found! Code quality is excellent.")
            return
        
        # Print by category
        categories = {
            'syntax_errors': 'Syntax Errors',
            'high_complexity': 'High Complexity Functions',
            'duplicate_code': 'Duplicate Code Blocks',
            'naming_convention': 'Naming Convention Issues',
            'missing_docstrings': 'Missing Docstrings',
            'magic_numbers': 'Magic Numbers',
            'long_lines': 'Long Lines (>120 chars)',
            'unused_imports': 'Unused Imports'
        }
        
        for key, title in categories.items():
            if key in self.issues and self.issues[key]:
                print(f"\n{title}: {len(self.issues[key])}")
                
                # Show first 5 examples
                for issue in self.issues[key][:5]:
                    if key == 'high_complexity':
                        print(f"  - {issue['file']}:{issue['line']} "
                              f"Function '{issue['function']}' has complexity {issue['complexity']}")
                    elif key == 'naming_convention':
                        print(f"  - {issue['file']}:{issue['line']} "
                              f"{issue['type'].capitalize()} '{issue['name']}' should be '{issue['suggestion']}'")
                    elif key == 'missing_docstrings':
                        print(f"  - {issue['file']}:{issue['line']} "
                              f"{issue['type'].capitalize()} '{issue['name']}' missing docstring")
                    elif key == 'unused_imports':
                        print(f"  - {issue['file']}: {', '.join(issue['imports'])}")
                    else:
                        print(f"  - {issue}")
                
                if len(self.issues[key]) > 5:
                    print(f"  ... and {len(self.issues[key]) - 5} more")
        
        # Recommendations
        print("\n" + "="*70)
        print("RECOMMENDATIONS")
        print("="*70)
        
        if 'high_complexity' in self.issues and self.issues['high_complexity']:
            print("\n1. Reduce Function Complexity:")
            print("   - Break down complex functions into smaller ones")
            print("   - Extract repeated logic into helper functions")
            print("   - Consider using design patterns")
        
        if 'duplicate_code' in self.issues and self.issues['duplicate_code']:
            print("\n2. Remove Duplicate Code:")
            print("   - Extract common code into shared functions")
            print("   - Use inheritance or composition")
            print("   - Create utility modules for common operations")
        
        if 'naming_convention' in self.issues and self.issues['naming_convention']:
            print("\n3. Fix Naming Conventions:")
            print("   - Use snake_case for functions and variables")
            print("   - Use PascalCase for classes")
            print("   - Use UPPER_CASE for constants")
        
        if 'missing_docstrings' in self.issues and self.issues['missing_docstrings']:
            print("\n4. Add Docstrings:")
            print("   - Document all public functions and classes")
            print("   - Include parameters, return values, and examples")
            print("   - Use Google or NumPy docstring format")
        
        if 'magic_numbers' in self.issues and self.issues['magic_numbers']:
            print("\n5. Replace Magic Numbers:")
            print("   - Define constants at module level")
            print("   - Use descriptive names")
            print("   - Group related constants in a config file")
        
        print("\n" + "="*70)


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Analyze code quality')
    parser.add_argument('--dir', default='trading_bot', help='Directory to analyze')
    
    args = parser.parse_args()
    
    source_dir = project_root / args.dir
    
    if not source_dir.exists():
        print(f"Error: Directory {source_dir} does not exist")
        sys.exit(1)
    
    analyzer = CodeQualityAnalyzer(source_dir)
    analyzer.analyze_all()


if __name__ == '__main__':
    main()
