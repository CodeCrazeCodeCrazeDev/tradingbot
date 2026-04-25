# Autonomous Improvement Agent

## Overview

The Autonomous Improvement Agent is a self-directed AI system that systematically analyzes, improves, and evolves your trading bot codebase. It reads every line of code, identifies weaknesses, proposes improvements, generates tests, and applies approved changes.

## Core Mission

Transform the existing codebase into a world-class trading system by:
1. **Reading** and understanding every line of code
2. **Identifying** weaknesses, gaps, and improvement opportunities
3. **Proposing** concrete improvements with full implementation
4. **Generating** comprehensive tests
5. **Creating** change proposals for human review
6. **Learning** from feedback to improve future proposals

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    IMPROVEMENT AGENT                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────┐    ┌─────────────────┐                    │
│  │ DeepCodebase    │───▶│ Weakness        │                    │
│  │ Analyzer        │    │ Detector        │                    │
│  └─────────────────┘    └────────┬────────┘                    │
│                                  │                              │
│                                  ▼                              │
│  ┌─────────────────┐    ┌─────────────────┐                    │
│  │ Test            │◀───│ Improvement     │                    │
│  │ Generator       │    │ Proposer        │                    │
│  └────────┬────────┘    └────────┬────────┘                    │
│           │                      │                              │
│           ▼                      ▼                              │
│  ┌─────────────────────────────────────────┐                   │
│  │           Change Manager                 │                   │
│  │  (Tracks, Approves, Applies Changes)    │                   │
│  └─────────────────────────────────────────┘                   │
│                         │                                       │
│                         ▼                                       │
│  ┌─────────────────────────────────────────┐                   │
│  │           Agent Interface                │◀── YOU (Human)   │
│  │  (Observe, Direct, Review, Approve)     │                   │
│  └─────────────────────────────────────────┘                   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## Components

### 1. DeepCodebaseAnalyzer (`deep_analyzer.py`)
- Reads every file in the codebase
- Parses Python files using AST
- Builds dependency graphs
- Calculates complexity metrics
- Identifies architecture patterns

### 2. WeaknessDetector (`weakness_detector.py`)
- Detects code smells and anti-patterns
- Finds security vulnerabilities
- Identifies performance bottlenecks
- Spots architectural issues
- Finds testing gaps
- Detects trading-specific risks

### 3. ImprovementProposer (`improvement_proposer.py`)
- Generates concrete fixes for weaknesses
- Creates new feature implementations
- Proposes refactoring changes
- Produces complete code diffs

### 4. TestGenerator (`test_generator.py`)
- Creates unit tests for functions
- Generates integration tests
- Produces edge case tests
- Creates regression tests

### 5. ChangeManager (`change_manager.py`)
- Tracks all proposed changes
- Manages approval workflow
- Creates backups before changes
- Applies approved changes
- Supports rollback

### 6. ImprovementAgent (`agent_orchestrator.py`)
- Coordinates all components
- Manages the improvement cycle
- Handles directives from humans
- Maintains state and history

### 7. AgentInterface (`agent_interface.py`)
- Provides human control interface
- Supports interactive review
- Generates reports
- Executes commands

## Quick Start

### Option 1: Run from Command Line

```bash
# Navigate to trading bot directory
cd "c:\Users\peterson\trading bot"

# Run in observe mode (analysis only)
python -m trading_bot.improvement_agent.run_agent --mode observe

# Run with interactive review
python -m trading_bot.improvement_agent.run_agent --interactive

# Focus on specific area
python -m trading_bot.improvement_agent.run_agent --focus risk --focus security

# Generate report only
python -m trading_bot.improvement_agent.run_agent --report-only
```

### Option 2: Use in Python

```python
from trading_bot.improvement_agent import (
    ImprovementAgent,
    AgentConfig,
    AgentMode,
    AgentInterface,
)

# Create agent
config = AgentConfig(mode=AgentMode.SUPERVISED)
agent = ImprovementAgent("c:/Users/peterson/trading bot/trading_bot", config)

# Create interface for control
interface = AgentInterface(agent)

# Run analysis
agent.analyze_codebase()
agent.detect_weaknesses()

# Generate improvements
agent.generate_improvements()

# Review pending changes
pending = interface.get_pending_for_review()
for change in pending:
    print(f"Change: {change['id']} - {change['file']}")
    print(f"  {change['description']}")

# Approve a change
interface.execute_command("approve", {"id": "CHG_20240101_001"})

# Apply approved changes
agent.apply_approved_changes()
```

## Operating Modes

| Mode | Description | Use Case |
|------|-------------|----------|
| `observe` | Only analyze, no proposals | Understanding codebase |
| `propose` | Analyze and propose | Getting improvement ideas |
| `supervised` | Apply only approved changes | **Default - Recommended** |
| `autonomous` | Auto-apply safe changes | Trusted automation |

## Workflow

### 1. Analysis Phase
```
Agent reads every file → Builds dependency graph → Calculates metrics
```

### 2. Detection Phase
```
Scans for code smells → Finds security issues → Identifies gaps
```

### 3. Proposal Phase
```
Generates fixes → Creates diffs → Estimates effort
```

### 4. Review Phase
```
YOU review proposals → Approve or reject → Add feedback
```

### 5. Application Phase
```
Creates backups → Applies changes → Generates tests
```

## Commands Reference

### Lifecycle Commands
| Command | Description |
|---------|-------------|
| `start` | Run full improvement cycle |
| `stop` | Stop the agent |
| `pause` | Pause the agent |
| `resume` | Resume paused agent |

### Analysis Commands
| Command | Description |
|---------|-------------|
| `analyze` | Analyze codebase |
| `detect` | Detect weaknesses |
| `propose` | Generate improvements |

### Review Commands
| Command | Args | Description |
|---------|------|-------------|
| `approve` | `id=X` | Approve specific change |
| `approve` | `all=True` | Approve all pending |
| `reject` | `id=X reason=Y` | Reject with reason |

### Application Commands
| Command | Args | Description |
|---------|------|-------------|
| `apply` | `id=X` | Apply specific change |
| `apply` | (none) | Apply all approved |
| `rollback` | `id=X` | Rollback a change |

### Direction Commands
| Command | Args | Description |
|---------|------|-------------|
| `focus` | `target=X` | Focus on area |
| `skip` | `target=X` | Skip area |

### Reporting Commands
| Command | Args | Description |
|---------|------|-------------|
| `status` | (none) | Show status |
| `report` | `type=summary` | Summary report |
| `report` | `type=pending` | Pending changes |

## Weakness Categories

The agent detects these types of weaknesses:

| Category | Examples |
|----------|----------|
| **Security** | Hardcoded secrets, SQL injection, eval usage |
| **Performance** | Blocking calls, inefficient loops, N+1 queries |
| **Code Quality** | Long functions, deep nesting, code duplication |
| **Error Handling** | Bare except, silent failures, missing validation |
| **Architecture** | Circular dependencies, tight coupling, god classes |
| **Testing** | Missing tests, low coverage, no edge cases |
| **Documentation** | Missing docstrings, outdated comments |
| **Trading Safety** | Hardcoded limits, missing stop-loss, no validation |

## Protected Paths

These paths require extra confirmation before changes:
- `core/risk/` - Risk management
- `core/execution/` - Order execution
- `core/security/` - Security systems
- `trading/` - Trading logic
- `broker/` - Broker connections
- `.env` - Environment files
- `credentials` - Credential files

## Best Practices

### 1. Start with Observe Mode
```bash
python -m trading_bot.improvement_agent.run_agent --mode observe --report-only
```
Review the report before making any changes.

### 2. Focus on Critical Areas First
```bash
python -m trading_bot.improvement_agent.run_agent --focus security --focus risk
```

### 3. Review Changes Carefully
Use interactive mode to review each change:
```bash
python -m trading_bot.improvement_agent.run_agent --interactive
```

### 4. Apply Incrementally
Approve and apply changes in small batches, testing after each.

### 5. Keep Backups
The agent creates backups automatically, but consider version control.

## Example Session

```
$ python -m trading_bot.improvement_agent.run_agent --interactive

╔══════════════════════════════════════════════════════════════════╗
║            IMPROVEMENT AGENT - Making Your Code Better           ║
╚══════════════════════════════════════════════════════════════════╝

Analyzing: c:\Users\peterson\trading bot\trading_bot
Mode: supervised
Depth: deep

Entering interactive mode. Type 'help' for commands, 'quit' to exit.

agent> analyze
✓ Analyzed 150 files, 45000 lines

agent> detect
✓ Found 87 weaknesses

agent> status
========================================
AGENT STATUS
========================================
State: awaiting_review
Mode: supervised
Total Runs: 1
Pending Changes: 23
Active Directives: 0
========================================

agent> focus risk
✓ Agent will focus on: risk

agent> propose
✓ Generated 15 improvements

agent> review
--- Change 1/15 ---
ID: CHG_20240101_0001
File: trading_bot/risk/risk_manager.py
Type: modify
Description: Fix bare except clause

[A]pprove / [R]eject / [S]kip / [V]iew full / [Q]uit: a
✓ Approved

agent> apply
✓ Applied 1 changes, 0 failed

agent> quit
Goodbye!
```

## Troubleshooting

### Agent Not Finding Files
Ensure the path is correct and accessible:
```python
agent = ImprovementAgent("c:/Users/peterson/trading bot/trading_bot")
```

### Changes Not Applying
Check if changes are approved:
```python
pending = interface.get_pending_for_review()
print(f"Pending: {len(pending)}")
```

### Rollback a Bad Change
```python
interface.execute_command("rollback", {"id": "CHG_20240101_001"})
```

## Files Created

| File | Purpose |
|------|---------|
| `improvement_agent/__init__.py` | Module exports |
| `improvement_agent/deep_analyzer.py` | Codebase analysis |
| `improvement_agent/weakness_detector.py` | Weakness detection |
| `improvement_agent/improvement_proposer.py` | Improvement generation |
| `improvement_agent/test_generator.py` | Test generation |
| `improvement_agent/change_manager.py` | Change management |
| `improvement_agent/agent_orchestrator.py` | Main orchestrator |
| `improvement_agent/agent_interface.py` | Human interface |
| `improvement_agent/run_agent.py` | CLI runner |

## Human Oversight Principles

1. **All changes require approval** - Nothing is applied without your consent
2. **Protected files have extra safeguards** - Critical files flagged for attention
3. **Full transparency** - See exactly what will change before it happens
4. **Rollback capability** - Undo any change if needed
5. **Direction control** - Focus or skip areas as needed
6. **Stop anytime** - Pause or stop the agent at any point

---

*The Autonomous Improvement Agent - Your AI pair programmer for continuous codebase improvement.*
