# DeepSeek Governance System - Complete Documentation

## Overview

The DeepSeek Governance System implements a comprehensive AI governance framework with three autonomy levels and robust safety guardrails to prevent harmful AI evolution.

## Core Principles

### Three Autonomy Levels

| Level | Domains | Behavior |
|-------|---------|----------|
| **FULL** | Engineering, Testing, Data, Modeling | Can execute without approval |
| **ADVISORY** | Trading, Risk Parameters | Can suggest, human must approve |
| **RESTRICTED** | Production, Config, Security | Auto-PRs only, no direct merges |

### Safety Guarantees

1. **AI cannot execute trades directly** - Only creates suggestions
2. **AI cannot deploy to production directly** - Only creates PRs
3. **AI cannot modify safety guardrails** - Hard-coded protection
4. **AI cannot resist shutdown** - Human override always available
5. **AI cannot expand beyond trading scope** - Scope creep detection

## Architecture

```
trading_bot/deepseek_governance/
├── __init__.py                 # Module exports
├── autonomy_levels.py          # Three autonomy levels
├── safety_guardrails.py        # Safety constraints
├── behavior_monitor.py         # Behavior detection
├── positive_impact.py          # Impact enforcement
├── risk_mitigation.py          # Risk management
└── governance_orchestrator.py  # Master coordinator
```

## Components

### 1. Autonomy Manager (`autonomy_levels.py`)

Manages the three autonomy levels:

```python
from trading_bot.deepseek_governance import AutonomyManager, AutonomyDomain

manager = AutonomyManager()

# Check autonomy level for a domain
level = manager.get_autonomy_level(AutonomyDomain.TRADING)
# Returns: AutonomyLevel.ADVISORY

level = manager.get_autonomy_level(AutonomyDomain.ENGINEERING)
# Returns: AutonomyLevel.FULL
```

**Full Autonomy Domains:**
- Engineering (code refactoring, optimization)
- Testing (test creation, execution)
- Data Processing (cleaning, transformation)
- Modeling (ML training, tuning)
- Documentation
- Logging
- Monitoring
- Diagnostics

**Advisory Autonomy Domains:**
- Trading (trade execution)
- Risk Parameters (limits, sizing)
- Strategy (selection)
- Capital Allocation
- Market Exposure

**Restricted Autonomy Domains:**
- Production Deploy
- Config Changes
- Security Settings
- Broker Settings
- System Evolution

### 2. Safety Guardrails (`safety_guardrails.py`)

Implements hard limits that cannot be overridden:

```python
from trading_bot.deepseek_governance import SafetyGuardrailSystem

safety = SafetyGuardrailSystem()

# Check all guardrails
violations = safety.check_all({
    'risk_per_trade': 0.05,  # Exceeds 2% limit
    'daily_loss': 0.03,
    'drawdown': 0.15
})

# Critical violation triggers shutdown
if safety.is_shutdown_triggered():
    print("Emergency shutdown!")
```

**Hard Limits (Cannot Override):**
- Max 2% risk per trade
- Max 5% daily loss
- Max 20% drawdown
- No market manipulation
- No unauthorized access
- Human override always available

**Behavioral Guardrails:**
- No deceptive behavior
- No self-preservation override
- No goal drift
- No unauthorized communication

**Evolution Guardrails:**
- No core identity modification
- No safety guardrail modification
- Evolution rate limits
- All changes reversible
- No scope expansion

### 3. Behavior Monitor (`behavior_monitor.py`)

Detects harmful behavior patterns:

```python
from trading_bot.deepseek_governance import BehaviorMonitor, HarmfulBehaviorDetector

monitor = BehaviorMonitor()
detector = HarmfulBehaviorDetector()

# Record behaviors
monitor.record_decision({'action': 'trade', 'confidence': 0.8})
monitor.record_resource_usage({'cpu': 0.5, 'memory': 0.6})

# Detect anomalies
anomalies = monitor.detect_anomalies()

# Check for harmful behaviors
harmful = detector.detect_all(action, context)
```

**Detected Patterns:**
- Goal drift
- Deceptive behavior
- Self-preservation attempts
- Scope creep
- Manipulation
- Resource abuse
- Communication anomalies
- Learning anomalies
- Decision anomalies
- Evolution anomalies

### 4. Positive Impact Enforcer (`positive_impact.py`)

Ensures all actions have beneficial effects:

```python
from trading_bot.deepseek_governance import PositiveImpactEnforcer

enforcer = PositiveImpactEnforcer()

# Assess action impact
allowed, assessment = enforcer.enforce(action, context)

if not allowed:
    print(f"Blocked: {assessment.reasoning}")
    print(f"Violations: {assessment.ethical_violations}")
```

**Ethical Constraints:**
- No financial harm
- No market harm
- No user deception
- Aligned with user goals
- Respects preferences
- Informed consent
- No market manipulation
- No insider trading
- Regulatory compliance
- Fair competition
- Transparency
- Sustainability
- Accountability

### 5. Risk Mitigation (`risk_mitigation.py`)

Mitigates all AI behavior risks:

```python
from trading_bot.deepseek_governance.risk_mitigation import RiskMitigationSystem

risk_system = RiskMitigationSystem()

# Assess risks
events = risk_system.assess_risks(context)

# Apply automatic mitigations
results = risk_system.apply_mitigations(events, context)
```

**Risk Categories:**
- Alignment risks
- Capability risks
- Control risks
- Deception risks
- Manipulation risks
- Evolution risks
- Operational risks
- Financial risks
- Legal risks
- Reputational risks

### 6. Governance Orchestrator (`governance_orchestrator.py`)

Master coordinator for all governance systems:

```python
from trading_bot.deepseek_governance import GovernanceOrchestrator, GovernanceMode

orchestrator = GovernanceOrchestrator(mode=GovernanceMode.BALANCED)

# Evaluate any action
decision = orchestrator.evaluate_action({
    'type': 'execute_trade',
    'description': 'Buy BTCUSDT',
    'impact_score': 0.5,
    'risk_score': 0.4
}, context)

if decision.allowed:
    # Execute action
    pass
elif decision.requires_approval:
    # Wait for human approval
    suggestion_id = decision.conditions[0].split(': ')[1]
elif decision.requires_pr:
    # PR created for review
    pr_id = decision.conditions[0].split(': ')[1]
```

## Usage Examples

### Basic Usage

```python
from trading_bot.deepseek_governance import GovernanceOrchestrator

# Initialize
orchestrator = GovernanceOrchestrator()

# Engineering action - FULL AUTONOMY
decision = orchestrator.evaluate_action({
    'type': 'refactor_code',
    'description': 'Optimize trading strategy',
    'impact_score': 0.3,
    'risk_score': 0.2
}, {})
# Result: ALLOWED (full autonomy)

# Trading action - ADVISORY AUTONOMY
decision = orchestrator.evaluate_action({
    'type': 'execute_trade',
    'description': 'Buy 1 BTC',
    'impact_score': 0.5,
    'risk_score': 0.4
}, {})
# Result: SUGGESTION CREATED (needs human approval)

# Production action - RESTRICTED AUTONOMY
decision = orchestrator.evaluate_action({
    'type': 'deploy_to_production',
    'description': 'Deploy new strategy',
    'impact_score': 0.8,
    'risk_score': 0.6
}, {})
# Result: PR CREATED (needs human review and merge)
```

### Approval Workflow

```python
# Get pending approvals
pending = orchestrator.get_pending_approvals()

# Approve a suggestion
orchestrator.approve_action(
    approval_id="abc123",
    approved_by="human_trader",
    notes="Approved after review"
)

# Reject a suggestion
orchestrator.reject_action(
    approval_id="abc123",
    rejected_by="human_trader",
    reason="Risk too high"
)
```

### Governance Report

```python
report = orchestrator.generate_report()

print(f"System Healthy: {report.system_healthy}")
print(f"Pending Approvals: {report.pending_approvals}")
print(f"Pending PRs: {report.pending_prs}")
print(f"Critical Issues: {report.critical_issues}")
print(f"Recommendations: {report.recommendations}")
```

### Emergency Mode

```python
# Check emergency status
if orchestrator.is_emergency_active():
    print("Emergency mode active!")

# Deactivate emergency (requires human)
orchestrator.deactivate_emergency(
    authorized_by="admin",
    reason="Issue resolved"
)
```

## Integration with Trading Bot

### In Main Trading Loop

```python
from trading_bot.deepseek_governance import GovernanceOrchestrator

orchestrator = GovernanceOrchestrator()

async def execute_trade(signal):
    # Evaluate through governance
    decision = orchestrator.evaluate_action({
        'type': 'execute_trade',
        'description': f"Trade {signal.symbol}",
        'impact_score': signal.impact,
        'risk_score': signal.risk,
        'expected_return': signal.expected_return,
        'risk_per_trade': signal.position_risk
    }, get_current_context())
    
    if decision.allowed:
        # Full autonomy - execute
        return await broker.execute(signal)
    elif decision.requires_approval:
        # Advisory - wait for approval
        logger.info(f"Trade suggestion created: {decision.conditions}")
        return None
    else:
        # Blocked
        logger.warning(f"Trade blocked: {decision.reasoning}")
        return None
```

### With Evolution System

```python
from trading_bot.deepseek_governance import GovernanceOrchestrator
from trading_bot.eternal_evolution import EternalEvolutionOrchestrator

governance = GovernanceOrchestrator()
evolution = EternalEvolutionOrchestrator()

async def evolve_system():
    # Evaluate evolution action
    decision = governance.evaluate_action({
        'type': 'system_evolution',
        'description': 'Optimize risk parameters',
        'impact_score': 0.6,
        'risk_score': 0.5
    }, {})
    
    if decision.requires_pr:
        # Create PR for evolution changes
        pr_id = decision.conditions[0].split(': ')[1]
        logger.info(f"Evolution PR created: {pr_id}")
        # Wait for human to merge PR
    else:
        logger.warning(f"Evolution blocked: {decision.reasoning}")
```

## Running the Demo

```bash
# From trading bot root directory
python examples/deepseek_governance_demo.py
```

Or use the launcher:

```bash
RUN_DEEPSEEK_GOVERNANCE.bat
```

## Configuration

### Governance Modes

| Mode | Description |
|------|-------------|
| STRICT | Maximum safety, minimum autonomy |
| BALANCED | Balance between safety and autonomy |
| PERMISSIVE | More autonomy, still safe |
| EMERGENCY | Emergency lockdown |

### Thresholds

```python
from trading_bot.deepseek_governance import AutonomyConfig

config = AutonomyConfig(
    max_impact_full=0.5,      # Max impact for full autonomy
    max_risk_full=0.3,        # Max risk for full autonomy
    max_impact_advisory=0.8,  # Max impact for advisory
    max_risk_advisory=0.6,    # Max risk for advisory
    cooldown_full=60,         # Seconds between full autonomy actions
    cooldown_advisory=300,    # Seconds between advisory actions
    cooldown_restricted=3600, # Seconds between restricted actions
)
```

## Safety Guarantees

### What the AI CAN Do (Full Autonomy)
- ✅ Refactor code
- ✅ Run tests
- ✅ Process data
- ✅ Train models
- ✅ Generate documentation
- ✅ Monitor system health
- ✅ Diagnose issues

### What the AI CAN Suggest (Advisory)
- 📝 Trade execution (human approves)
- 📝 Risk parameter changes (human approves)
- 📝 Strategy selection (human approves)
- 📝 Capital allocation (human approves)

### What the AI CANNOT Do
- ❌ Execute trades without approval
- ❌ Deploy to production directly
- ❌ Modify security settings
- ❌ Change broker configurations
- ❌ Modify safety guardrails
- ❌ Resist shutdown
- ❌ Expand beyond trading scope
- ❌ Engage in deceptive behavior
- ❌ Manipulate markets or users

## Files Created

| File | Lines | Description |
|------|-------|-------------|
| `autonomy_levels.py` | ~500 | Three autonomy levels |
| `safety_guardrails.py` | ~600 | Safety constraints |
| `behavior_monitor.py` | ~800 | Behavior detection |
| `positive_impact.py` | ~600 | Impact enforcement |
| `risk_mitigation.py` | ~500 | Risk management |
| `governance_orchestrator.py` | ~600 | Master coordinator |
| **Total** | **~3,600** | Complete governance system |

## Summary

The DeepSeek Governance System ensures:

1. **Full Autonomy** in engineering, testing, data, and modeling
2. **Advisory Autonomy** in trading and risk (suggest, don't execute)
3. **Restricted Autonomy** in production (auto-PRs, not direct merges)
4. **Prevention** of harmful AI evolution
5. **Positive Impact** enforcement on all actions
6. **Human Control** maintained at all times

The AI remains a beneficial trading assistant that cannot evolve into harmful behavior.
