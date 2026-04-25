# Autonomous Code Fixer

## Overview

The Autonomous Code Fixer is a comprehensive tool that scans your entire codebase, identifies all issues line-by-line, and automatically fixes them.

## Quick Start

```batch
# Run the fixer
FIX_ALL_ISSUES.bat
```

Or run directly with Python:
```bash
py scripts/fixes/autonomous_code_fixer.py --path "c:\Users\peterson\trading bot"
```

## Features

### Issue Detection
The fixer detects the following types of issues:

| Category | Issues Detected |
|----------|-----------------|
| **Syntax Errors** | Missing colons, unclosed brackets, unclosed strings, indentation errors |
| **Missing Imports** | 100+ common imports (numpy, pandas, typing, dataclasses, etc.) |
| **Typos** | 80+ common typos (imoprt→import, retrun→return, slef→self, etc.) |
| **Code Smells** | Bare except, mutable defaults, None comparison, mixed indentation |
| **Security** | eval/exec usage, hardcoded passwords/API keys/secrets |
| **Style** | Trailing whitespace, mixed tabs/spaces |

### Auto-Fix Capabilities
The fixer can automatically fix:
- ✅ Syntax errors (missing colons, unclosed brackets)
- ✅ Missing imports (adds at top of file)
- ✅ Typos (replaces with correct spelling)
- ✅ Bare except → except Exception
- ✅ == None → is None
- ✅ != None → is not None
- ✅ Mixed tabs/spaces → spaces only
- ✅ Trailing whitespace → removed

### Safety Features
- **Automatic Backups**: All modified files are backed up before changes
- **Validation**: Changes are validated with AST before saving
- **Rollback**: If validation fails, original file is restored
- **Dry Run Mode**: Preview changes without modifying files

## Usage Modes

### 1. Full Fix (Default)
c:
```bash
py scripts/fixes/autonomous_code_fixer.py --path .
```

### 2. Dry Run
Scan only, show issues but don't modify files:
```bash
py scripts/fixes/autonomous_code_fixer.py --path . --dry-run
```

### 3. Verbose Mode
Full fix with detailed output:
```bash
py scripts/fixes/autonomous_code_fixer.py --path . --verbose
```

## Output

### Console Output
```
======================================================================
AUTONOMOUS CODE FIXER - STARTING
======================================================================

[INFO] Root directory: c:\Users\peterson\trading bot
[INFO] Found 1500 Python files to scan
[INFO] Backup directory: autonomous_backups\20241209_165700

[1/1500] Scanning: trading_bot/trading_engine.py -> 3 issues found
         -> 2 fixes applied
[2/1500] Scanning: trading_bot/master_orchestrator.py -> OK
...

======================================================================
AUTONOMOUS CODE FIXER - REPORT
======================================================================

Files Scanned:    1500
Issues Found:     245
Issues Fixed:     198
Files Modified:   87

Issues by Severity:
  🔴 CRITICAL: 5
  🟠 HIGH: 45
  🟡 MEDIUM: 120
  🟢 LOW: 75

Issues by Type (top 15):
  - MISSING_IMPORT: 89
  - TYPO: 45
  - BARE_EXCEPT: 23
  - NONE_COMPARISON: 18
  ...
```

### Report Files
Reports are saved to `autonomous_logs/`:
- `fix_report_YYYYMMDD_HHMMSS.txt` - Human-readable report
- `fix_report_YYYYMMDD_HHMMSS.json` - Machine-readable report

### Backup Files
All modified files are backed up to `autonomous_backups/YYYYMMDD_HHMMSS/`

## Issue Types

### Severity Levels
| Level | Description |
|-------|-------------|
| CRITICAL | Breaks execution (syntax errors) |
| HIGH | Major bug or security issue |
| MEDIUM | Code smell or potential bug |
| LOW | Style or minor issue |
| INFO | Informational |

### Common Typos Fixed
```
imoprt → import      retrun → return      slef → self
funciton → function  defualt → default    clss → class
asnyc → async        awiat → await        pritn → print
ture → True          flase → False        noen → None
lenght → length      widht → width        heigth → height
```

### Import Auto-Detection
The fixer automatically detects and adds missing imports for:
- **Standard Library**: os, sys, re, json, logging, datetime, pathlib, asyncio, etc.
- **Typing**: Dict, List, Optional, Tuple, Any, Union, Set, Callable, etc.
- **Collections**: defaultdict, deque, Counter, OrderedDict, namedtuple
- **Dataclasses**: dataclass, field, asdict
- **Enum**: Enum, auto, IntEnum
- **Third-party**: numpy (np), pandas (pd), torch, tensorflow (tf), requests, etc.

## Directories Skipped
The fixer automatically skips:
- `__pycache__`
- `.git`
- `.pytest_cache`
- `venv`, `env`, `.venv`
- `node_modules`
- `.hypothesis`
- `htmlcov`
- `autonomous_backups`
- `.mypy_cache`
- `mlruns`
- `models`
- `backup`
- `archive`

## Extending the Fixer

### Adding New Typos
Edit `scripts/fixes/autonomous_code_fixer.py` and add to `TypoFixer.TYPOS`:
```python
TYPOS = {
    'mytypo': 'correct_spelling',
    ...
}
```

### Adding New Imports
Edit `ImportFixer.IMPORT_MAP`:
```python
IMPORT_MAP = {
    'MyClass': 'from mymodule import MyClass',
    ...
}
```

## Troubleshooting

### "No module named 'scripts.fixes.autonomous_code_fixer'"
Run from the project root directory:
```bash
cd "c:\Users\peterson\trading bot"
py scripts\fixes\autonomous_code_fixer.py --path .
```

### Files not being fixed
1. Check if the file is in a skipped directory
2. Run with `--verbose` to see detailed output
3. Check `autonomous_logs/` for the detailed report

### Backup restoration
If something went wrong, restore from backup:
```bash
xcopy /E /Y autonomous_backups\YYYYMMDD_HHMMSS\* .
```

## Integration with CI/CD

Add to your CI pipeline:
```yaml
- name: Run Code Fixer (Dry Run)
  run: python scripts/fixes/autonomous_code_fixer.py --path . --dry-run
  
- name: Check for issues
  run: |
    if [ -f autonomous_logs/fix_report_*.json ]; then
      issues=$(python -c "import json; print(json.load(open('autonomous_logs/fix_report_*.json'))['total_issues_found'])")
      if [ "$issues" -gt 0 ]; then
        echo "Found $issues issues!"
        exit 1
      fi
    fi
```

## License

Part of the AlphaAlgo Trading Bot project.
