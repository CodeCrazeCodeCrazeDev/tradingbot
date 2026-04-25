# AlphaAlgo Self-Improvement System

## Overview

The Self-Improvement System is an autonomous code analysis and refactoring tool that:

1. **Finds Issues** - Scans the codebase for bugs, code smells, missing features, security issues
2. **Proposes Fixes** - Generates detailed fix proposals with actual code changes
3. **Analyzes Risks** - Assesses the risk level of each proposed change
4. **Waits for Approval** - You review and approve/reject each proposal
5. **Applies Changes** - Approved proposals are applied to the actual code files

## Quick Start

### Option 1: Interactive Mode (Recommended)
```bash
python run_self_improvement.py
```
Or double-click `RUN_SELF_IMPROVEMENT.bat`

### Option 2: Command Line
```bash
# Scan for issues
python run_self_improvement.py scan

# Generate proposals
python run_self_improvement.py propose

# Review proposals interactively
python run_self_improvement.py review

# Apply approved changes (dry run first!)
python run_self_improvement.py apply --dry-run

# Full cycle
python run_self_improvement.py full
```

## Workflow

```
┌─────────────────────────────────────────────────────────────────────┐
│                    SELF-IMPROVEMENT WORKFLOW                        │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│   1. SCAN                                                           │
│      ↓                                                              │
│   ┌─────────────────────────────────────────────────────────────┐  │
│   │ CodeAnalyzer scans all Python files for:                    │  │
│   │ • TODOs and FIXMEs                                          │  │
│   │ • Empty/stub functions                                      │  │
│   │ • Bare except clauses                                       │  │
│   │ • Hardcoded secrets                                         │  │
│   │ • Long functions                                            │  │
│   │ • Missing docstrings                                        │  │
│   │ • Unused imports                                            │  │
│   │ • Complex conditions                                        │  │
│   │ • Missing error handling                                    │  │
│   │ • Deprecated patterns                                       │  │
│   └─────────────────────────────────────────────────────────────┘  │
│      ↓                                                              │
│   2. PROPOSE                                                        │
│      ↓                                                              │
│   ┌─────────────────────────────────────────────────────────────┐  │
│   │ ProposalEngine generates fix proposals with:                │  │
│   │ • Actual code changes (before/after)                        │  │
│   │ • Risk level assessment                                     │  │
│   │ • Expected benefits                                         │  │
│   │ • Potential drawbacks                                       │  │
│   │ • Testing requirements                                      │  │
│   │ • Rollback plan                                             │  │
│   └─────────────────────────────────────────────────────────────┘  │
│      ↓                                                              │
│   3. REVIEW (Human Decision)                                        │
│      ↓                                                              │
│   ┌─────────────────────────────────────────────────────────────┐  │
│   │ You review each proposal and decide:                        │  │
│   │ • [A]pprove - Accept the change                             │  │
│   │ • [R]eject - Decline the change                             │  │
│   │ • [D]efer - Review later                                    │  │
│   │ • [S]kip - Skip for now                                     │  │
│   └─────────────────────────────────────────────────────────────┘  │
│      ↓                                                              │
│   4. APPLY                                                          │
│      ↓                                                              │
│   ┌─────────────────────────────────────────────────────────────┐  │
│   │ CodeRewriter applies approved changes:                      │  │
│   │ • Creates backup of original files                          │  │
│   │ • Applies code changes                                      │  │
│   │ • Supports rollback if needed                               │  │
│   └─────────────────────────────────────────────────────────────┘  │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

## Issue Categories

| Category | Description | Example |
|----------|-------------|---------|
| `BUG` | Actual or potential bugs | FIXME comments, missing error handling |
| `CODE_SMELL` | Poor code patterns | Bare except, unused imports |
| `INCOMPLETE` | Unfinished code | TODOs, empty functions |
| `SECURITY` | Security vulnerabilities | Hardcoded secrets |
| `MAINTAINABILITY` | Hard to maintain code | Long functions, missing docstrings |
| `DEPRECATED` | Outdated patterns | Old string formatting |

## Severity Levels

| Severity | Description | Action |
|----------|-------------|--------|
| `CRITICAL` | Must fix immediately | Security issues, data loss risks |
| `HIGH` | Should fix soon | Known bugs, FIXMEs |
| `MEDIUM` | Fix when possible | Code smells, TODOs |
| `LOW` | Nice to fix | Style issues, minor improvements |
| `INFO` | Informational | Suggestions, best practices |

## Risk Levels

| Risk | Description | Auto-Approve? |
|------|-------------|---------------|
| `MINIMAL` | Cosmetic only | Yes (optional) |
| `LOW` | Safe changes | No |
| `MEDIUM` | May affect behavior | No |
| `HIGH` | Significant changes | No |
| `CRITICAL` | Core functionality | No |

## Components

### 1. CodeAnalyzer
Scans Python files using AST parsing and regex patterns.

```python
from trading_bot.self_improvement import CodeAnalyzer

analyzer = CodeAnalyzer("c:/Users/peterson/trading bot")
issues = analyzer.analyze_codebase(max_files=100)
summary = analyzer.get_summary()
```

### 2. ProposalEngine
Generates fix proposals with actual code changes.

```python
from trading_bot.self_improvement import ProposalEngine

engine = ProposalEngine("c:/Users/peterson/trading bot")
proposals = engine.generate_proposals(issues)
```

### 3. ApprovalManager
Tracks approval status and decisions.

```python
from trading_bot.self_improvement import ApprovalManager

manager = ApprovalManager("./approvals")
manager.add_proposals(proposals)
manager.approve("PROP-20251206-0001", "Looks good")
manager.reject("PROP-20251206-0002", "Not needed")
```

### 4. CodeRewriter
Applies approved changes to files.

```python
from trading_bot.self_improvement import CodeRewriter

rewriter = CodeRewriter("c:/Users/peterson/trading bot")
result = rewriter.apply_proposal(proposal, dry_run=True)
rewriter.rollback_proposal("PROP-20251206-0001")
```

### 5. SelfImprovementOrchestrator
Coordinates the entire workflow.

```python
from trading_bot.self_improvement import SelfImprovementOrchestrator

orchestrator = SelfImprovementOrchestrator("c:/Users/peterson/trading bot")

# Full cycle
orchestrator.scan(max_files=100)
orchestrator.propose()
orchestrator.review_interactive()
orchestrator.apply(dry_run=True)  # Always dry run first!
```

## Example Proposal

```
======================================================================
PROPOSAL: PROP-20251206-0001
======================================================================

📋 TITLE: Fix bare except clause

📁 FILE: trading_bot/core/engine.py
📍 LINE: 145

🏷️ CATEGORY: CODE_SMELL
⚠️ SEVERITY: MEDIUM
🎯 RISK LEVEL: MINIMAL

📝 DESCRIPTION:
Replace 'except:' with 'except Exception as e:' to avoid catching 
system exceptions like KeyboardInterrupt.

🔍 CURRENT CODE:
```
except:
    logger.error("Something went wrong")
```

✏️ PROPOSED CHANGES:

  Change 1: replace_code
  Lines 145-145
  
  OLD:
  ```
  except:
  ```
  
  NEW:
  ```
  except Exception as e:
  ```
  
  Explanation: Replace bare except with specific exception type

📊 RISK ANALYSIS:
Minimal risk - improves exception handling without changing logic

✅ EXPECTED BENEFITS:
  • Won't catch KeyboardInterrupt/SystemExit
  • Access to exception details

⚠️ POTENTIAL DRAWBACKS:
  • None

🧪 TESTING REQUIRED:
Run existing tests

↩️ ROLLBACK PLAN:
Revert to 'except:'

⏱️ ESTIMATED EFFORT: 1 minute

======================================================================
DECISION: [A]pprove | [R]eject | [D]efer | [S]kip
======================================================================
```

## Safety Features

1. **Backups** - All files are backed up before modification
2. **Dry Run** - Test changes without applying them
3. **Rollback** - Revert any applied changes
4. **Human Approval** - Nothing is applied without your approval
5. **Risk Assessment** - Each change is assessed for risk
6. **Audit Trail** - All decisions are logged

## Storage Locations

```
trading bot/
├── self_improvement_data/
│   ├── approvals/
│   │   └── approval_records.json
│   ├── backups/
│   │   ├── backup_index.json
│   │   └── *.bak files
│   ├── scan_report_*.json
│   ├── proposals_*.json
│   └── pending_review_*.txt
```

## Best Practices

1. **Always dry run first** - Use `--dry-run` before applying changes
2. **Review carefully** - Read each proposal before approving
3. **Start small** - Scan a few files first to understand the output
4. **Test after applying** - Run tests after applying changes
5. **Keep backups** - Don't delete the backup files

## Troubleshooting

### "No issues found"
- Increase `max_files` parameter
- Check if files are being excluded

### "Proposal has no changes"
- Some issues require manual review
- Complex refactoring can't be automated

### "Apply failed"
- Check file permissions
- Verify the file hasn't changed since scan
- Use rollback to restore original

## Files Created

| File | Description | Lines |
|------|-------------|-------|
| `code_analyzer.py` | Scans codebase for issues | ~500 |
| `proposal_engine.py` | Generates fix proposals | ~550 |
| `approval_manager.py` | Manages approval workflow | ~350 |
| `code_rewriter.py` | Applies changes to files | ~400 |
| `self_improvement_orchestrator.py` | Main coordinator | ~350 |
| `run_self_improvement.py` | CLI interface | ~200 |
| `RUN_SELF_IMPROVEMENT.bat` | Windows launcher | ~100 |

**Total: ~2,450 lines of new code**

## Usage Examples

### Quick Scan
```bash
python run_self_improvement.py scan --max-files 50
```

### Critical Issues Only
```bash
python run_self_improvement.py propose --critical-only
```

### Auto-Approve Safe Changes
```bash
python run_self_improvement.py full --auto-approve-safe --dry-run
```

### Save for Offline Review
```python
orchestrator.save_for_offline_review("review_proposals.txt")
```

---

**Remember: The AI proposes, YOU decide. Nothing is applied without your approval.**
