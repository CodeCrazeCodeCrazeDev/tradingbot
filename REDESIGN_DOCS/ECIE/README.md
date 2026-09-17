# External Capability Intelligence Engine (ECIE): Institutional Engineering Study

This document details the architectural specifications, threat model, and validation plan for the External Capability Intelligence Engine (ECIE). It establishes a safe, governed capability supply chain for AlphaAlgo, converting untrusted external sources (including GitHub, arXiv, Hugging Face, etc.) into verified institutional assets.

---

## 1. Capability Decomposition

ECIE decomposes external repository and capability ingestion into 18 discrete, decoupled services. These services cooperate in a linear, fail-fast refinery pipeline:

1. **Scout Adapter System (e.g., GitHub Scout, arXiv Scout)**: Periodically queries, filters, and identifies candidate capability packages based on relevance profiles (AI agents, quantitative finance, forecasting, RL, orchestration, data engineering).
2. **Repository Classifier**: Analyzes repository structure, files, and metadata to classify the primary domain (e.g., Execution, Risk, Backtesting).
3. **Repository Trust Scorer**: Scores repository maturity and risk using independent multidimensional signals (maintainer history, commit cadence, contributor diversity, issue/release quality, dependency health, OpenSSF scorecard metrics).
4. **Security Scanner**: Inspects code and files for secrets, malware signatures, malicious packages, obfuscated code, and security policy adherence.
5. **License Analyzer**: Checks licenses against compliance lists (Acceptable: MIT, BSD, Apache-2.0; Forbidden: GPL, LGPL, AGPL).
6. **Dependency Analyzer**: Generates a dependency tree and audits package vulnerabilities, bloat, and dependency hygiene.
7. **Static Code Analyzer**: Performs AST parsing of code to detect dangerous calls (`eval`, `exec`, shell command injections, raw filesystem writes).
8. **Behavior Sandbox (Local Restricted Executor)**: Executes untrusted code inside an isolated, disposable subprocess with blocked network access, path restrictions, and restricted resource limits.
9. **Behavior Monitor**: Audits run-time activity during sandboxed execution, flagging illegal disk writes, subprocess spawns, or socket binds.
10. **Capability Extractor**: Isolates specific logic blocks, workflows, or mathematical algorithms, separating pure intellectual value from the untrusted implementation wrapper.
11. **Pattern Distillation Engine**: Formalizes the extracted capabilities into platform-agnostic representations (JSON schemas, abstract workflows, mathematical formulas).
12. **Weakness Inversion Engine**: Audits weaknesses found in the untrusted repo (e.g., lack of validations, missing unit tests, poor error handling) and automatically generates defensive governance rules/controls inside AlphaAlgo.
13. **Skill Compiler**: Packages the distilled and hardened patterns into executable, standard Skill Programs conforming to AlphaAlgo’s One Brain schema.
14. **Pattern Registry**: Manages versioning and local caching of distilled patterns and templates.
15. **Evaluation Engine**: Automatically compiles and executes test suites/benchmarks against the newly compiled Skill Program inside a secure local context.
16. **Governance Gate**: Verifies compliance against Security, License, Architecture, Performance, Validation, and Objective Alignment gates. High-risk promotions are held for explicit Human-in-the-Loop approval.
17. **Rollout Manager**: Transitions approved capabilities through progressive promotion sequences: Sandbox → Shadow Mode → Canary → Limited Production → Full Deployment.
18. **Rollback Manager**: Provides instantaneous reverse capabilities, disabling the capability on any anomaly or performance breach without breaking core One Brain services.

---

## 2. Existing AlphaAlgo Capability Mapping

Several parts of AlphaAlgo touch on ingestion and repository discovery:
- **`trading_bot/sentient_core/institutional_github_scout.py`**: Discovers GitHub repos but is currently decoupled and does not handle sandboxing, pattern distillation, skill compiling, or central lineage persistence.
- **`trading_bot/research/research_os.py`**: Manages hypotheses and model governance but lacks the ability to scan, import, and process external code repositories or other intelligence streams.
- **`trading_bot/core/unified_registry.py`**: Tracks internal registered components but does not govern external capability imports or compile dynamic skill structures.

---

## 3. Redundancy Analysis

To prevent architectural duplication:
- **Scouting**: The existing `InstitutionalGitHubScout` is extendable and will be adapted as the primary `GitHubScoutAdapter` within ECIE, eliminating double implementation of GitHub API queries and basic criteria.
- **Governance**: ECIE will **NOT** create a separate approval registry. Instead, it will submit its promotion proposals and record evidence directly into the existing `ResearchWorkspace` and `PeerReviewBoard` frameworks.
- **Ledger Persistence**: All capability provenance logs, validation reports, and benchmark history will be stored within the core Research OS persistence framework.

---

## 4. Security Threat Model

| Threat ID | Threat Category | Description | Mitigating Control in ECIE |
|---|---|---|---|
| **T-01** | Malicious Dependency Hijacking | Dependency typosquatting or compromised upstream library executed during analysis. | **Static Analyzer & Sandbox**: Full import graph analysis prior to run, execution only in restricted isolated sandbox with blocked network. |
| **T-02** | Look-ahead / Leakage Attacks | Imported trading strategies containing subtle temporal leaks that simulate high Sharpe. | **Weakness Inversion**: Explicit data-leakage and lookback audits run by the Evaluation Engine; strict Out-of-Sample verification. |
| **T-03** | Shell Command Injection | Repository containing build/setup scripts with malicious obfuscated commands. | **Static Code Analyzer**: AST checks banning string-based `eval`, `exec`, `os.system`, and shell execution patterns. |
| **T-04** | Exfiltration of Proprietary Code | External repository scanning code trying to read environment variables, API keys, or clone parent AlphaAlgo code. | **Disposable Sandbox**: Sandbox executes with fully wiped environment variables, isolated temporary paths, and absolute socket blockage. |

---

## 5. Supply-Chain Risk Assessment

- **Asset Trust Levels**: All external assets begin with a trust level of exactly **zero**.
- **Licensing Compliance**: To prevent legal contamination, ECIE enforces a hard-coded ban on copy-left licenses (`GPL`, `LGPL`, `AGPL`) during the classification and license analysis phases.
- **No Direct Imports**: Under no circumstances does ECIE run Python `import` on raw external repositories. It only imports *distilled, compiled skills* that have been parsed, rewritten into clean AlphaAlgo-native abstractions, and validated in isolation.

---

## 6. Integration Architecture

The following diagram illustrates how ECIE integrates as a research refinery between external intelligence sources and the One Brain architecture:

```
                  +---------------------------------------+
                  |     External Intelligence Sources     |
                  |  (GitHub, arXiv, Hugging Face, etc.)  |
                  +-------------------+-------------------+
                                      |
                                      v
                  +-------------------+-------------------+
                  |      ECIE Source-Agnostic Scouts      |
                  +-------------------+-------------------+
                                      |
                                      v
                  +-------------------+-------------------+
                  |      ECIE Multi-Stage Pipeline        |
                  |  (Trust, Security, License, Sandbox)  |
                  +-------------------+-------------------+
                                      |
                                      v
                  +-------------------+-------------------+
                  |     Distillation & Skill Compiler     |
                  +-------------------+-------------------+
                                      |
                                      v
                  +-------------------+-------------------+
                  |  Research OS / Unified Registry Gate  |
                  |     (Governance & Human Approvals)    |
                  +-------------------+-------------------+
                                      |
                                      v
                  +-------------------+-------------------+
                  |       One Brain Execution Core        |
                  +---------------------------------------+
```

---

## 7. Capability Gap Analysis

| Required Capability | Existing System Status | ECIE Solution |
|---|---|---|
| **Multi-Source Scouting** | GitHub-only (`InstitutionalGitHubScout`) | Refactored Scout Adapter System supporting GitHub, Hugging Face, arXiv. |
| **Isolating Executions** | None (Risk of execution in local env) | Disposable `LocalRestrictedExecutor` with process isolation. |
| **Pattern Distillation** | Manual rewriting | AST-driven pattern extraction and dynamic Skill compilation. |
| **Provenance Logging** | Loose SQLite tables | Comprehensive provenance ledgers persisted directly into Research OS history. |

---

## 8. Architectural Decision Records (ADRs)

### ADR-001: Source-Agnostic Intelligence Pipeline
- **Context**: Relying exclusively on GitHub couples AlphaAlgo to a single code provider.
- **Decision**: Define an extensible adapter structure (`ScoutAdapter`) where any external source can feed the discovery pipeline.
- **Consequences**: Easy expansion to arXiv papers, Hugging Face model cards, and technical blogs without changing pipeline core.

### ADR-002: AST Pattern Distillation over Direct Cloning
- **Context**: Direct code cloning risks licensing lawsuits, formatting clashes, and security compromises.
- **Decision**: Read and analyze untrusted files using Python AST. Extract core mathematical blocks and structural templates, rewriting them into fresh AlphaAlgo-native implementations.
- **Consequences**: Complete protection against malware execution, absolute license sanitization, and clean architectural consistency.

---

## 9. Migration Strategy

1. **Phase 1 (Audit & Align)**: Port and wrap the existing `InstitutionalGitHubScout` into the ECIE adapter interface.
2. **Phase 2 (Pipeline Implementation)**: Deploy the core pipeline modules under `trading_bot/research/ecie/`.
3. **Phase 3 (Core Integration)**: Hook ECIE into `ResearchWorkspace` inside `trading_bot/research/research_os.py`.
4. **Phase 4 (Validation)**: Run comprehensive sandbox stress-tests.

---

## 10. Validation Strategy

- **Static Validation**: Verifies that the AST scanner correctly detects and halts 100% of defined unsafe patterns (e.g., `eval`, `exec`).
- **Sandbox Boundary Validation**: Confirms that execution is successfully blocked/flagged if a repository attempts network communication, file writes outside the temporary directory, or shell commands.
- **Licensing Auditing**: Ensures that copy-left licenses are perfectly filtered and rejected.
- **End-to-End Flow Validation**: Verifies a complete pipeline run: from simulated scouting to pattern distillation, compilation, and successful shadow promotion.
