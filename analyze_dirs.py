import os, ast

base = r'c:\Users\peterson\trading bot\trading_bot'
results = []

for d in sorted(os.listdir(base)):
    dpath = os.path.join(base, d)
    if not os.path.isdir(dpath) or d.startswith('__') or d.startswith('.'):
        continue
    
    py_files = []
    total_lines = 0
    syntax_errors = 0
    has_init = os.path.exists(os.path.join(dpath, '__init__.py'))
    empty_inits = 0
    no_docstring = 0
    no_logging = 0
    no_error_handling = 0
    stub_files = 0
    
    for root, dirs, files in os.walk(dpath):
        dirs[:] = [dd for dd in dirs if dd != '__pycache__']
        for f in files:
            if f.endswith('.py'):
                fpath = os.path.join(root, f)
                py_files.append(fpath)
                try:
                    content = open(fpath, encoding='utf-8', errors='replace').read()
                    lines = content.count('\n') + 1
                    total_lines += lines
                    
                    if f == '__init__.py' and lines < 3:
                        empty_inits += 1
                    
                    if lines < 20 and 'pass' in content:
                        stub_files += 1
                    
                    try:
                        tree = ast.parse(content)
                    except SyntaxError:
                        syntax_errors += 1
                        continue
                    
                    if not ast.get_docstring(tree):
                        no_docstring += 1
                    
                    has_logging = 'logging' in content or 'logger' in content
                    if not has_logging:
                        no_logging += 1
                    
                    has_try = 'try:' in content
                    if not has_try and lines > 50:
                        no_error_handling += 1
                        
                except Exception:
                    pass
    
    if not py_files:
        continue
    
    score = 0
    issues = []
    
    if not has_init:
        score += 20
        issues.append('missing __init__.py')
    if empty_inits > 0:
        score += 10
        issues.append(str(empty_inits) + ' empty __init__.py')
    if syntax_errors > 0:
        score += 30
        issues.append(str(syntax_errors) + ' syntax errors')
    if stub_files > 0:
        score += 15
        issues.append(str(stub_files) + ' stub/placeholder files')
    if no_docstring > len(py_files) * 0.5:
        score += 10
        issues.append('most files lack docstrings')
    if no_logging > len(py_files) * 0.5:
        score += 10
        issues.append('most files lack logging')
    if no_error_handling > 0:
        score += 10
        issues.append(str(no_error_handling) + ' files lack error handling')
    if total_lines < 100 and len(py_files) > 1:
        score += 15
        issues.append('very thin implementation')
    
    if score > 0:
        results.append({
            'dir': d,
            'files': len(py_files),
            'lines': total_lines,
            'score': score,
            'issues': issues,
        })

results.sort(key=lambda x: x['score'], reverse=True)
print("SCORE | DIRECTORY                                | FILES | LINES  | ISSUES")
print("-" * 120)
for r in results:
    iss = ', '.join(r['issues'])
    print(f"{r['score']:5d} | {r['dir']:40s} | {r['files']:5d} | {r['lines']:6d} | {iss}")
print(f"\nTotal directories needing improvement: {len(results)}")
