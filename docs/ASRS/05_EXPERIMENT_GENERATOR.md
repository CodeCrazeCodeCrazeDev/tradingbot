# 05. EXPERIMENT GENERATOR
## Experiment Generator, Isolation Levels, Resource Scheduler & Registry

### 1. Architectural Mission
The **Experiment Generator (EG)** converts validated research hypotheses into physical, executable experiments. It guarantees that no experiment or self-improvement process interferes with the trading bot's live operations.

The EG implements strict isolation boundaries, handles concurrent computational requests through a dedicated hardware resource scheduler, and registers all active runs in an auditable experiment registry.

---

### 2. The Three Isolation Levels
To manage implementation complexity and maintain absolute safety, ASRS categorizes all experiments into three distinct isolation levels:

```
                  +----------------------------------------------+
                  |             THREE ISOLATION LEVELS           |
                  +----------------------------------------------+
                  |                                              |
                  | [Level 1: Configuration & Prompt Sandbox]    |
                  | - Prompt templates, JSON config files        |
                  | - In-memory routing / planning parameters    |
                  | - Zero filesystem mutation / Zero git branches|
                  |                                              |
                  | [Level 2: Virtual Workspace Sandbox]         |
                  | - Local virtual environment (temp folder)    |
                  | - AST mutation / python file compilation     |
                  | - Isolated local testing & local backtests   |
                  |                                              |
                  | [Level 3: Version Control Sandbox]           |
                  | - Programmatic Git worktree (isolated branch)|
                  | - Independent dependency graph resolution    |
                  | - Comprehensive performance / benchmark suite|
                  |                                              |
                  +----------------------------------------------+
```

#### Level 1: Configuration & Prompt Sandbox
* **Scope**: Prompts, templates, model selection, routing depths, JSON/YAML configurations.
* **Mechanism**: Changes are loaded as localized objects in the live memory structure of the designated target agent without modifying any persistent files.
* **Rollback Time**: $< 10 \text{ ms}$ (simply revert the memory reference).

#### Level 2: Virtual Workspace Sandbox
* **Scope**: Algorithmic adjustments, AST modifications, file compilations, local performance profiling.
* **Mechanism**: The EG creates a temporary workspace directory (e.g. `/tmp/asrs-sandbox-UUID/`) with symbolic links to AlphaAlgo packages. It uses `ast` mutations to inject or swap out classes (e.g. replacing a planner class) and executes test suits inside a clean, isolated virtual environment.
* **Rollback Time**: $< 500 \text{ ms}$ (destroys the temporary workspace).

#### Level 3: Version Control Sandbox
* **Scope**: Subsystem overhauls, database migrations, neural model transitions, multi-agent coordination architectures.
* **Mechanism**: The EG leverages Git worktrees to checkout an isolated local research branch (e.g., `research/improve-planning-UUID`). It builds a full isolated container or virtual environment, runs comprehensive stress/backtest datasets, and generates promotion candidates.
* **Rollback Time**: Instant Git rollback to main branch HEAD SHA.

---

### 3. Compute Resource Scheduler
To prevent background research loops from consuming hardware resources needed by the live trading platform, ASRS implements a **Compute Resource Scheduler (CRS)**. The CRS is a prioritized queue manager governed by strict resource allocation invariants:

* **Real-time Priority**: The trading engine and live execution modules always occupy Thread/Process Priority Class **High / Real-time**.
* **Cooperative Scheduling**: Level 2 and Level 3 experiments are scheduled on isolated CPU affinity cores (e.g., core 4-15 on a 16-core system) and limited to process priority **Idle / Low**.
* **Resource Quota Enforcement**:
  * **GPU Allocation**: GPU VRAM is strictly partitioned. No experiment can request more than 30% of total VRAM, leaving 70% reserved for live LLMs and predictive World Models.
  * **Memory Limits**: The CRS continuously monitors system memory. If system RAM utilization exceeds 85%, the CRS automatically pauses queued or active Level 2/3 experiments in descending order of EROI.

---

### 4. Experiment Registry Schema
Every scheduled experiment is assigned a cryptographically random UUIDv4 and tracked in an sqlite3-backed database (`research_experiments.db`).

```sql
CREATE TABLE experiment_registry (
    experiment_id VARCHAR(36) PRIMARY KEY,
    hypothesis_id VARCHAR(36) NOT NULL,
    isolation_level INT NOT NULL, -- 1, 2, or 3
    state VARCHAR(20) NOT NULL,    -- QUEUED, RUNNING, COMPLETED, FAILED, VERIFYING, AUDITING, PROMOTED, REJECTED
    git_sha VARCHAR(40) NOT NULL,
    resources_allocated TEXT NOT NULL, -- JSON config of CPU cores, VRAM allocation
    creation_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_update_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    error_log TEXT,
    rollback_instructions TEXT NOT NULL
);
```
