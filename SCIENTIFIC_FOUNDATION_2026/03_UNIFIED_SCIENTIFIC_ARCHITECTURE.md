# Unified Scientific Architecture (AlphaAlgo 2026)

## Architectural Principle: Single Authoritative Instance
AlphaAlgo eliminates architectural redundancy by enforcing exactly **one** authoritative implementation for every major subsystem:
1. **One Master Orchestrator**: `CognitiveSystemController` (`trading_bot/core/csc/controller.py`)
2. **One Skill & Sub-Agent Router**: `SkillRouter` (`trading_bot/core/router/router.py`)
3. **One Hierarchical Memory System**: `HierarchicalMemorySystem` (`trading_bot/core/hms/memory.py`)
4. **One Multi-Agent Debate Engine**: `MultiAgentDebateSystem` (`trading_bot/agents/multi_agent_debate.py`)
5. **One Policy & Self-Evolution Gatekeeper**: `EvolutionGate` (`trading_bot/core/acpe/evolution_gate.py`)

---

## Architectural Synthesis Diagram

```
                                  [ Market Tick Stream / News / Macro Data ]
                                                      │
                                                      ▼
                            ┌───────────────────────────────────────────────────┐
                            │    LogAct Shared-Log Backbone (UnifiedEventBus)   │
                            └─────────────────────────┬─────────────────────────┘
                                                      │
                                                      ▼
                            ┌───────────────────────────────────────────────────┐
                            │     CognitiveSystemController (Master CSC)        │
                            │  - Free Energy Minimization (CORAL - 2607.01224)   │
                            │  - Explicit Knowledge Bounds (EKSFT - 2605.29303) │
                            └─────────┬───────────────────────┬─────────────────┘
                                      │                       │
           ┌──────────────────────────┘                       └──────────────────────────┐
           ▼                                                                             ▼
┌──────────────────────────────────────┐                               ┌──────────────────────────────────────┐
│     HierarchicalMemorySystem         │                               │              SkillRouter             │
│  - Latent Vector Store (2605.20025)  │                               │  - Bandits / Swarm Router            │
│  - SHA-256 Provenance Hashes         │                               │    (NanoResearch - 2605.10813)       │
└──────────────────┬───────────────────┘                               └──────────────────┬───────────────────┘
                   │                                                                      │
                   └──────────────────────────┐                        ┌──────────────────┘
                                              ▼                        ▼
                                   ┌──────────────────────────────────────────────┐
                                   │           MultiAgentDebateSystem             │
                                   │  - Head AI / MCTS Search (2605.12061)        │
                                   │  - Multimodal Verifiers (2605.21482)          │
                                   │  - Bayesian Decision Engine                  │
                                   └──────────────────────┬───────────────────────┘
                                                          │
                                                          ▼
                                   ┌──────────────────────────────────────────────┐
                                   │       EvolutionGate / Sandboxed ACPE         │
                                   │  - Secure AST Visitor (2605.17734)           │
                                   │  - Risk Sentinel Veto Gate                   │
                                   └──────────────────────┬───────────────────────┘
                                                          │
                                                          ▼
                                            [ Executed Trade / Action ]
```

---

## Subsystem Specifications

### 1. CognitiveSystemController (Master Orchestrator)
* Integrates Variational Free Energy (VFE) computation into state evaluations.
* Evaluates observation divergence ($q_\phi$) against prior beliefs ($p_\theta$).
* Acts as the single entrypoint for perception, state estimation, and action dispatch.

### 2. MultiAgentDebateSystem (Decision Engine)
* Coordinates specialist roles (Analyst, Risk, Execution, Sentiment, Macro, Quant, Microstructure).
* Combines MCTS lookahead reasoning (`Search-R1`) with Quiet-STaR thought scratchpads.
* Enforces multimodal verifiers (`CausalVerifier`, `LiquidityVerifier`, `RegimeVerifier`, `HallucinationDetector`).

### 3. HierarchicalMemorySystem (Memory)
* Manages Working Memory, Episodic Memory, Semantic Memory, and Procedural Memory.
* Encodes structured market states into latent embeddings (`S2L`).
* Verifies SHA-256 state provenance to prevent state corruption.

### 4. SkillRouter (Sub-Agent Dispatch)
* Route incoming prompts and sub-tasks to dynamic micro-agent swarms (`NanoResearch`).
* Uses Thompson Sampling multi-armed bandits to optimize sub-agent selection based on historic accuracy.

### 5. EvolutionGate (Self-Improvement)
* Manages strategy code mutations and self-improvement loops (`AutoResearchClaw`).
* Validates mutated code AST using `SecureASTVisitor` to enforce complete sandboxing.
* Rejects mutations failing out-of-sample backtests or risk metrics.
