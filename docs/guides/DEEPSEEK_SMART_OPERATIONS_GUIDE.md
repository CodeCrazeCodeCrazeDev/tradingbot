# DeepSeek Smart Operations Guide

## Overview

This guide teaches DeepSeek how to properly perform its functions without corrupting files. The Smart Operations module ensures that DeepSeek:

1. **ALWAYS validates Python syntax** with `ast.parse()` before saving
2. **ALWAYS creates backups** before modifying files
3. **ALWAYS verifies changes** don't break imports
4. **NEVER modifies protected files** without approval
5. **NEVER breaks existing functionality**

## Core Principles

DeepSeek MUST follow these principles:

| Principle | Description |
|-----------|-------------|
| VALIDATE_BEFORE_SAVE | Always validate Python syntax before saving |
| BACKUP_BEFORE_MODIFY | Always create backup before modifying |
| TEST_AFTER_CHANGE | Always run tests after changes |
| PRESERVE_FUNCTIONALITY | Never break existing functionality |
| RESPECT_PROTECTED | Never modify protected files without approval |
| ATOMIC_OPERATIONS | Changes are all-or-nothing |
| ROLLBACK_ON_FAILURE | Automatically rollback if something fails |

## How to Use Smart Operations

### 1. Validate Code Before Writing

```python
from trading_bot.deepseek_ai_engineer import CodeValidator, ValidationResult

# Validate code string
validator = CodeValidator()
result = validator.validate_syntax(code, "my_file.py")

if result.is_valid:
    # Safe to proceed
    print("Code is valid!")
else:
    # DO NOT SAVE - code has errors
    print(f"Errors: {result.errors}")
```

### 2. Safe File Writing

```python
from trading_bot.deepseek_ai_engineer import SafeFileManager
from pathlib import Path

file_manager = SafeFileManager(workspace_path)

# This will:
# 1. Check if file is protected
# 2. Validate Python syntax
# 3. Create backup
# 4. Write file
# 5. Verify write
success, message = file_manager.safe_write(
    Path("my_file.py"),
    new_content,
    validate=True,  # Always True for Python files
    create_backup=True
)

if not success:
    print(f"Write failed: {message}")
```

### 3. Fix Imports Safely

```python
from trading_bot.deepseek_ai_engineer import DeepSeekOperationExecutor
from pathlib import Path

executor = DeepSeekOperationExecutor(workspace_path)

# This will:
# 1. Find safe location for imports
# 2. Avoid multi-line import blocks
# 3. Validate result before saving
success, message = await executor.fix_file_imports(Path("my_file.py"))
```

### 4. Scan and Fix Workspace

```python
from trading_bot.deepseek_ai_engineer import DeepSeekOperationExecutor

executor = DeepSeekOperationExecutor(workspace_path)

# Scan all files and fix issues
results = await executor.scan_and_fix_workspace(
    fix_issues=True,
    max_files=100
)

print(f"Scanned: {results['scanned']}")
print(f"Valid: {results['valid']}")
print(f"Fixed: {results['fixed']}")
print(f"Failed: {results['failed']}")
```

### 5. Pre-Commit Validation

```python
from trading_bot.deepseek_ai_engineer import pre_commit_validate

# Validate files before commit
files = ["file1.py", "file2.py"]
all_valid, errors = pre_commit_validate(files)

if not all_valid:
    print("Cannot commit - files have errors:")
    for error in errors:
        print(f"  - {error}")
```

## Protected Paths

DeepSeek CANNOT modify these paths without human approval:

- `/core/risk/` - Risk management
- `/core/execution/` - Order execution
- `/core/security/` - Authentication
- `/reward_system/` - Rewards
- `*.env*` - Environment files
- `/credentials/` - Credentials
- `/vault/` - Vault files
- `immutable_purpose.py` - Purpose definition
- `guardrails.py` - Safety guardrails

## The Import Fix Bug (What Went Wrong)

### The Problem

The old import fixer had a bug:

```python
# OLD BROKEN CODE
for i, line in enumerate(lines):
    if line.startswith('import ') or line.startswith('from '):
        insert_line = i + 1  # BUG: Doesn't check if inside multi-line import!
```

This caused imports to be inserted inside multi-line blocks:

```python
from .module import (
import logging  # <-- WRONG! Inserted here
import asyncio  # <-- WRONG! Inserted here
    function1,
    function2,
)
```

### The Fix

The new Smart Import Fixer:

1. **Tracks parentheses depth** to know when inside `from x import (...)`
2. **Tracks docstrings** to skip triple-quoted strings
3. **Validates with AST** before applying any change
4. **Rolls back** if validation fails

```python
# NEW CORRECT CODE
def find_safe_import_location(self, content: str) -> int:
    in_multiline_import = False
    paren_depth = 0
    
    for i, line in enumerate(lines):
        # Track multi-line imports
        if in_multiline_import:
            paren_depth += line.count('(') - line.count(')')
            if paren_depth <= 0:
                in_multiline_import = False
                last_import_line = i + 1
            continue  # Don't insert here!
        
        if stripped.startswith('from ') and '(' in line and ')' not in line:
            in_multiline_import = True
            paren_depth = line.count('(') - line.count(')')
```

## Quick Reference

### Validate a File

```python
from trading_bot.deepseek_ai_engineer import quick_validate

is_valid = await quick_validate("path/to/file.py")
```

### Fix a File

```python
from trading_bot.deepseek_ai_engineer import quick_fix

success, message = await quick_fix("path/to/file.py")
```

### Create an Executor

```python
from trading_bot.deepseek_ai_engineer import create_executor

executor = create_executor()  # Uses default workspace
# or
executor = create_executor(Path("/custom/workspace"))
```

## Integration with DeepSeek Orchestrator

The orchestrator now has built-in smart operations:

```python
from trading_bot.deepseek_ai_engineer import DeepSeekOrchestrator

orchestrator = DeepSeekOrchestrator(workspace)

# Validate a file
result = orchestrator.validate_file(Path("my_file.py"))

# Validate code
result = orchestrator.validate_code(code_string, "filename.py")

# Safe write
success, msg = await orchestrator.safe_write_file(path, content)

# Fix imports
success, msg = await orchestrator.fix_file_imports(path)

# Scan workspace
results = await orchestrator.scan_and_fix_workspace()

# Rollback
orchestrator.rollback_last_operation()
orchestrator.rollback_all_operations()
```

## Pre-Commit Hook Setup

Add to `.git/hooks/pre-commit`:

```bash
#!/bin/sh
python trading_bot/deepseek_ai_engineer/pre_commit_hook.py \
    $(git diff --cached --name-only --diff-filter=ACM | grep '\.py$')
```

Or run manually:

```bash
python trading_bot/deepseek_ai_engineer/pre_commit_hook.py file1.py file2.py
```

## Summary

DeepSeek now has:

1. **CodeValidator** - Validates Python syntax with `ast.parse()`
2. **SafeFileManager** - Safe file operations with backup and rollback
3. **SmartImportFixer** - Fixes imports without corrupting files
4. **DeepSeekOperationExecutor** - Main interface for all operations
5. **pre_commit_hook.py** - Validates files before commit

**CRITICAL**: DeepSeek MUST use these tools for ALL file operations. Never write files directly without validation!
