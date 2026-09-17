# Capability Extraction Report
### Scientific and System Capabilities Registry

Each first-class architectural capability extracted from AlphaAlgo's specifications.

## Extracted Capabilities Lineage

### [CAP-001] 12-stage Recursive Active Inference Loop
* **Subsystem:** Cognitive System Controller (CSC)
* **Purpose:** Governs strategic decision execution minimizing Variational Free Energy.
* **Priority Level:** Priority 2
* **Mathematical / Algorithm Foundation:** `Active Inference (Friston, 2010), DiscoLoop Recurrence`
* **SLA Interface:** `CSC.process_market_observation()`
* **Governance Constraints:** Dual-gate ImmutableShield confirmation
* **Originating Specification:** `SCIENTIFIC_FOUNDATION_2026/05_UNIFIED_ARCHITECTURE.md`

### [CAP-002] SAGE Self-Evolving Graph Memory
* **Subsystem:** Hierarchical Memory System (HMS)
* **Purpose:** Persists structured causal relationships and triples inside networkx.
* **Priority Level:** Priority 2
* **Mathematical / Algorithm Foundation:** `SAGE Incremental Triplet validity (arXiv:2605.12061)`
* **SLA Interface:** `HMS.retrieve_evidence_chain(), HMS.store_ledger_entry()`
* **Governance Constraints:** SAGE graph growth limits enforced (max 500 nodes)
* **Originating Specification:** `SCIENTIFIC_FOUNDATION_V5/REDESIGNS/MEMORY_HMS_V5.md`

### [CAP-003] AutoMem Meta-memory Versioning
* **Subsystem:** Hierarchical Memory System (HMS)
* **Purpose:** Performs online schema version increment and parameter optimizations based on success.
* **Priority Level:** Priority 2
* **Mathematical / Algorithm Foundation:** `AutoMem Optimization (arXiv:2607.01224)`
* **SLA Interface:** `HMS.optimize_metamemory()`
* **Governance Constraints:** Enforces backward compatibility on database versions
* **Originating Specification:** `SCIENTIFIC_FOUNDATION_V5/DECOMPOSITION/AUTOMEM_DECOMPOSITION.md`

### [CAP-004] HASP Executable Guardrails
* **Subsystem:** SkillRouter
* **Purpose:** Applies hardcoded safety skills and circuit breakers in high-volatility regimes.
* **Priority Level:** Priority 0
* **Mathematical / Algorithm Foundation:** `HASP Guardrail Routing (arXiv:2605.17734)`
* **SLA Interface:** `SkillRouter.route_task()`
* **Governance Constraints:** Requires immediate HOLD override if volatility exceeds 0.3
* **Originating Specification:** `SCIENTIFIC_FOUNDATION_V5/DECOMPOSITION/HASP_DECOMPOSITION.md`

### [CAP-005] Skill-to-LoRA Behavioral Adapters
* **Subsystem:** SkillRouter
* **Purpose:** Binds task parameters to specialized structural and risk-averse model adapters.
* **Priority Level:** Priority 2
* **Mathematical / Algorithm Foundation:** `Skill-to-LoRA Routing (arXiv:2606.16769)`
* **SLA Interface:** `SkillRouter.route_task()`
* **Governance Constraints:** Validates lora_hedging_archetype parameters
* **Originating Specification:** `SCIENTIFIC_FOUNDATION_V5/DECOMPOSITION/S2L_DECOMPOSITION.md`

### [CAP-006] LogAct Shared-Log Backbone
* **Subsystem:** Unified Event Bus
* **Purpose:** Enforces Byzantine transactional ordering, consistency, and auditable votes across validators.
* **Priority Level:** Priority 0
* **Mathematical / Algorithm Foundation:** `LogAct Consensus (arXiv:2604.07988)`
* **SLA Interface:** `UnifiedDecisionBus.propose_action(), LogAction.wait_for_decision()`
* **Governance Constraints:** Veto safety check ensures 100% agreement from voters
* **Originating Specification:** `SCIENTIFIC_FOUNDATION_V5/DECOMPOSITION/LOGACT_DECOMPOSITION.md`

### [CAP-007] Deflated Sharpe Ratio (DSR)
* **Subsystem:** Research OS
* **Purpose:** Corrects Sharpe Ratio for selection bias and multiple testing trials.
* **Priority Level:** Priority 1
* **Mathematical / Algorithm Foundation:** `Bailey and Lopez de Prado DSR formulation (2014)`
* **SLA Interface:** `ResearchKernel.compute_dsr()`
* **Governance Constraints:** Required for strategy promotion to production
* **Originating Specification:** `SCIENTIFIC_FOUNDATION_2026/06_MATHEMATICAL_FOUNDATION.md`

### [CAP-008] Benjamini-Hochberg FDR Control
* **Subsystem:** Research OS / Reality Gates
* **Purpose:** Controls False Discovery Rate given hundreds of research hypotheses.
* **Priority Level:** Priority 1
* **Mathematical / Algorithm Foundation:** `Benjamini-Hochberg P-value rank correction (1995)`
* **SLA Interface:** `MultipleTestingGate.apply_correction()`
* **Governance Constraints:** Blocks strategies that fail multiple testing significance
* **Originating Specification:** `docs/ASRS/12_PROMOTION_GATE.md`

### [CAP-009] Dataset & Feature Lineage Tracking
* **Subsystem:** Research OS
* **Purpose:** Guarantees every derived feature is traceable back to uncleaned base sources via strict hashes.
* **Priority Level:** Priority 1
* **Mathematical / Algorithm Foundation:** `SHA-256 DataFrame hashing and DAG lineage modeling`
* **SLA Interface:** `DataLineageRegistry.register_version()`
* **Governance Constraints:** Strict hash check ensures immutability
* **Originating Specification:** `SCIENTIFIC_FOUNDATION_2026/13_ADDITIONAL_RESEARCH_INTEGRATION.md`

### [CAP-010] Adaptive Control Policy Engine (ACPE)
* **Subsystem:** Cognitive System Controller (CSC)
* **Purpose:** Test-time sub-millisecond retrieval-based parameter adjustment without online LLM loops.
* **Priority Level:** Priority 0
* **Mathematical / Algorithm Foundation:** `Cached SQLite indexed context adaptation`
* **SLA Interface:** `ACPE.parameterize_pipeline()`
* **Governance Constraints:** Strictly blocks test-time online LLM-based diagnosis loops to bound latency
* **Originating Specification:** `SCIENTIFIC_FOUNDATION_2026/17_MEMOHARNESS_INTEGRATION_ANALYSIS.md`
