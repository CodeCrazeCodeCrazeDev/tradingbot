# Autonomous Research Organism

A self-designing, self-innovative, self-programming AI research infrastructure that operates within strict sandbox boundaries.

## Overview

The Autonomous Research Organism enables the AI trading system to continuously improve itself through:
- **Self-Design**: Generates new strategies, indicators, and components
- **Self-Innovation**: Discovers novel patterns and approaches
- **Self-Programming**: Writes and evolves its own code safely

All operations run inside a **sandbox environment** with strict safety controls.

## Components

### 1. SandboxEnvironment
Isolated execution environment for AI-generated code.
- RestrictedPython for AST-level restrictions
- Resource limits (CPU, memory, time)
- Filesystem and network isolation
- Import restrictions (whitelist only)

### 2. ComputeBudgetController
Manages and enforces resource limits.
- CPU time budgets (per operation, hourly, daily)
- Memory limits
- Storage quotas
- API call rate limiting
- Concurrent operation limits

### 3. DataIntegrityFirewall
Protects critical data from unauthorized modification.
- Access control lists
- Integrity verification (checksums)
- Change approval workflow
- Automatic rollback capabilities
- Full audit logging

### 4. CodeSafetyScanner
Analyzes AI-generated code for security vulnerabilities.
- AST analysis for dangerous patterns
- Regex pattern matching
- Semantic analysis
- 30+ built-in threat patterns
- Customizable rules

### 5. ExperimentRegistry
Tracks all autonomous AI experiments.
- Full lifecycle management
- Version control
- Reproducibility tracking
- Performance metrics
- Approval workflow

### 6. SelfProgrammingEngine
Generates and evolves code safely.
- Genetic programming (mutation/crossover)
- Template-based generation
- Fitness evaluation
- Safety-first evolution

### 7. ContinuousResearchOrganism
Main orchestrator for autonomous research.
- Research cycle management
- Directive-based focus
- Multi-phase execution
- Automatic deployment (with limits)

## Safety Principles

1. **All generated code runs in isolated sandbox**
2. **Compute resources are strictly budgeted**
3. **Critical data is protected by firewall**
4. **All code is scanned before execution**
5. **All experiments are registered and auditable**
6. **Human override is ALWAYS available**

## Usage

### Basic Usage

```python
from trading_bot.autonomous_research_organism import (
    ContinuousResearchOrganism,
    ResearchDirective,
    ResearchPriority,
    create_research_organism,
)

# Create the organism
organism = create_research_organism(
    storage_path="./research_data",
    auto_start=False
)

# Add a research directive
organism.create_directive(
    title="Improve Entry Timing",
    description="Research better entry timing for momentum strategies",
    target_area="strategy",
    success_criteria={
        'sharpe_ratio': 1.5,
        'win_rate': 0.55,
    },
    priority=ResearchPriority.HIGH,
)

# Start the organism
organism.start()

# Check status
status = organism.get_status()
print(f"Active: {status['state']['is_active']}")
print(f"Total cycles: {status['state']['total_cycles']}")

# Stop when done
organism.stop()
```

### Using Individual Components

```python
from trading_bot.autonomous_research_organism import (
    SandboxEnvironment,
    SandboxConfig,
    CodeSafetyScanner,
    ComputeBudgetController,
    ResourceType,
)

# Create sandbox
sandbox = SandboxEnvironment(SandboxConfig(
    max_execution_time_seconds=30,
    max_memory_mb=256,
))

# Execute code safely
result = sandbox.execute('''
import math
result = math.sqrt(16) * 2
''')

print(f"Success: {result.success}")
print(f"Result: {result.result}")

# Scan code for safety
scanner = CodeSafetyScanner()
scan_result = scanner.scan('''
import os
os.system("rm -rf /")  # This will be detected!
''')

print(f"Safe: {scan_result.is_safe}")
print(f"Threats: {len(scan_result.findings)}")

# Budget resources
budget = ComputeBudgetController()
with budget.budget_context(ResourceType.CPU_TIME, 10.0, "my_operation"):
    # Do work within budget
    pass
```

## Configuration

### Sandbox Configuration

```python
SandboxConfig(
    max_execution_time_seconds=30.0,
    max_cpu_time_seconds=10.0,
    max_memory_mb=256,
    max_output_size_kb=1024,
    max_recursion_depth=100,
    allow_filesystem=False,
    allow_network=False,
    allowed_imports={'math', 'statistics', 'numpy', 'pandas'},
)
```

### Budget Configuration

```python
# Custom budgets
custom_budgets = {
    ResourceType.CPU_TIME: {
        'max_per_operation': 120.0,
        'max_per_hour': 3600.0,
        'max_per_day': 28800.0,
    },
}
budget = ComputeBudgetController(custom_budgets=custom_budgets)
```

### Evolution Configuration

```python
EvolutionConfig(
    population_size=20,
    elite_size=5,
    mutation_rate=0.3,
    crossover_rate=0.5,
    max_generations=100,
    fitness_threshold=0.8,
)
```

## Rate Limits

The organism enforces strict rate limits:
- **MAX_CYCLES_PER_DAY**: 50 research cycles
- **MAX_EXPERIMENTS_PER_CYCLE**: 10 experiments
- **MAX_CODE_GENERATIONS_PER_CYCLE**: 20 code specimens
- **MAX_DEPLOYMENTS_PER_DAY**: 5 deployments
- **MIN_CYCLE_INTERVAL_MINUTES**: 5 minutes between cycles

## Emergency Stop

```python
# Emergency stop all operations
organism.emergency_stop("Critical issue detected")
```

## Monitoring

```python
# Get comprehensive status
status = organism.get_status()

# Get recent cycles
cycles = organism.get_recent_cycles(limit=10)

# Get component statistics
sandbox_stats = organism.sandbox.get_statistics()
budget_report = organism.budget_controller.get_budget_report()
scanner_stats = organism.scanner.get_statistics()
registry_stats = organism.registry.get_statistics()
```

## Integration with Existing Systems

The organism integrates with existing safety systems:
- `trading_bot.safety.safety_orchestrator`
- `trading_bot.recursive_improvement.harmful_behavior_guard`
- `trading_bot.self_assembly_ai.immutable_safety_core`

## File Structure

```
autonomous_research_organism/
├── __init__.py                    # Package exports
├── sandbox_environment.py         # Isolated code execution
├── compute_budget_controller.py   # Resource management
├── data_integrity_firewall.py     # Data protection
├── code_safety_scanner.py         # Security analysis
├── experiment_registry.py         # Experiment tracking
├── self_programming_engine.py     # Code evolution
├── continuous_research_organism.py # Main orchestrator
└── README.md                      # This file
```

## License

Part of the AlphaAlgo Trading Bot system.
