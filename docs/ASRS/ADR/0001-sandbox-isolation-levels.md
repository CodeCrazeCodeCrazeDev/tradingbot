# ADR 0001: Sandbox Isolation Levels
## Status: Approved

### Context
Allowing an autonomous system to self-modify its own codebase presents severe operational, structural, and capital risks. If mutated code containing syntax errors, infinite loops, or malicious calls (e.g. data exfiltration) is directly introduced to the trading thread, it could cause catastrophic financial loss and system crashes.

### Decision
We will enforce three distinct isolation levels (L1, L2, L3) for all experiments, preventing any direct or un-sandboxed modifications to the production environment:

1. **Level 1 (Configuration & Prompt Sandbox)**: Operates purely in-memory. Evolved prompts, templates, or model configurations are injected into local RAM contexts of targeted agent threads. File-system mutations are prohibited.
2. **Level 2 (Virtual Workspace Sandbox)**: Operates in temporary folders (e.g. `/tmp/asrs-L2/`). Python code is mutated (via Abstract Syntax Trees) and compiled inside clean, isolated virtual environments with OS-level subprocess constraints and disabled network access.
3. **Level 3 (Version Control & Container Sandbox)**: Operates inside programmatic git worktrees on dedicated research branches. Full multi-dimensional stress testing and backtests are executed inside isolated Docker containers with capped hardware resource allocations.

### Consequences
* **Security**: Eliminates the risk of arbitrary code execution impacting live operations.
* **Reliability**: Any crash or unhandled exception during evolution is safely contained within the sandbox.
* **Speed**: L1 mutations can be evaluated and rolled back instantly (sub-millisecond overhead), while L3 mutations support complex, multi-system evolutionary overhauls with a standardized git-commit trail.
* **Complexity**: Managing multi-level workspaces, symlinks, and virtual environments requires robust directory-management modules.
