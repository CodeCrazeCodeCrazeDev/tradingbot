# DeepSeek Corruption Fix Report

## Executive Summary

The DeepSeek AI Engineer system was corrupting Python files by incorrectly inserting import statements in invalid locations. This report documents the root cause, fixes applied, and remaining work.

## Root Cause Analysis

### The Bug
The `fix_missing_imports()` method in `trading_bot/deepseek_engineer/autonomous_fixer.py` had a critical flaw:

1. It scanned for lines starting with `import` or `from` to find the import section
2. It inserted new imports after the last import line found
3. **BUG**: It did NOT check if it was inside:
   - Multi-line imports with parentheses: `from x import (\n    a,\n    b,\n)`
   - Try-except blocks
   - Function/method bodies
   - Docstrings

### The Result
The auto-fixer inserted imports like this:
```python
from .immutable_purpose import (
import logging        # <-- WRONG! Inserted here
import asyncio        # <-- WRONG! Inserted here
    get_purpose_guard,
    verify_purpose_integrity,
)
```

This broke 325+ Python files across the codebase.

## Fixes Applied

### 1. Root Cause Fix (autonomous_fixer.py)
Fixed the `fix_missing_imports()` method to:
- Track multi-line imports (parentheses depth)
- Track docstrings
- Track try-except blocks
- **Validate with AST before applying** - if the result doesn't parse, don't apply it

### 2. Corrupted Files Fixed
- **DeepSeek modules fixed manually**: 8 files
- **Automated fix v1**: 57 files
- **Automated fix v2**: 169 files
- **Manual fixes**: 2 files
- **Total fixed**: ~228 files

### 3. Remaining Corrupted Files
~97 files still have syntax errors. These have more complex corruption patterns that require manual review.

## Files Fixed

### DeepSeek Core Modules (Manually Fixed)
1. `deepseek_ai_engineer/daily_maintenance.py`
2. `deepseek_ai_engineer/chief_ai_engineer.py`
3. `deepseek_ai_engineer/self_evolution_engine.py`
4. `deepseek_engineer/__init__.py`
5. `deepseek_engineer/autonomous_fixer.py`
6. `deepseek_engineer/codebase_analyzer.py`
7. `deepseek_engineer/proposal_system.py`
8. `deepseek_engineer/protected_registry.py`

### Fix Scripts Created
1. `scripts/fixes/fix_corrupted_imports.py` - Basic fixer
2. `scripts/fixes/fix_corrupted_imports_v2.py` - Aggressive fixer

## How to Fix Remaining Files

### Option 1: Run the Fixer Again
```bash
py scripts/fixes/fix_corrupted_imports_v2.py
```

### Option 2: Manual Fix Pattern
For each file with "unexpected indent" or "expected 'except'" errors:

1. Open the file at the error line
2. Look for imports at column 0 that should be indented
3. Remove the incorrectly inserted imports:
   - `import logging`
   - `import asyncio`
   - `import numpy`
   - `import pandas`
   - `from enum import auto`
   - `from typing import Any`

### Option 3: Restore from Backup
If you have a git commit before the corruption:
```bash
git checkout <commit-hash> -- <file-path>
```

## Prevention

The root cause has been fixed in `autonomous_fixer.py`. The fix includes:

1. **Multi-line import tracking**: Counts parentheses to know when inside `from x import (...)`
2. **Docstring tracking**: Skips triple-quoted strings
3. **Try-except awareness**: Doesn't insert inside try blocks
4. **AST validation**: Tests the result before applying

```python
# Safety check: validate the file will still parse after insertion
try:
    ast.parse(test_content)
except SyntaxError as e:
    logger.warning(f"Import insertion would cause syntax error: {e}")
    return None  # Don't apply the fix
```

## Recommendations

1. **Run tests before deploying** - The DeepSeek system should run `ast.parse()` on any file it modifies
2. **Add pre-commit hooks** - Validate Python syntax before commits
3. **Limit auto-fix scope** - Don't auto-fix files in critical paths
4. **Human review** - Require human approval for any code modifications

## Statistics

| Metric | Value |
|--------|-------|
| Files originally corrupted | 325 |
| Files fixed automatically | 228 |
| Files remaining | 97 |
| Fix success rate | 70% |

## Next Steps

1. Run `py scripts/fixes/fix_corrupted_imports_v2.py` again after manual fixes
2. Review and manually fix the 97 remaining files
3. Run full test suite to verify functionality
4. Consider restoring from git backup for complex files
