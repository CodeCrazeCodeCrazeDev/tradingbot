# 07. HARNESS EVOLUTION
## Harness Evolution System, Prompt Engineering & Scaffolding Optimization

### 1. Architectural Mission
The **Harness Evolution System (HES)** optimizes the logical and linguistic scaffolding of AlphaAlgo's agent systems. While traditional ML research focuses on model weights, the HES assumes the model weights are fixed (or optimized independently) and focuses exclusively on improving the **execution environment, instructions, routing structures, and tool interfaces**.

---

### 2. Execution Harness Components
The HES optimizes five core execution dimensions:

```text
                  +----------------------------------------------+
                  |         HARNESS OPTIMIZATION DOMAINS         |
                  +----------------------------------------------+
                  |                                              |
                  | [Prompt Templates]                           |
                  | - System instructions, task framing          |
                  | - Zero-shot vs. Few-shot example libraries   |
                  |                                              |
                  | [Tool Registries]                            |
                  | - Tool parameter structures, tool descriptions|
                  | - Function execution order & schema design   |
                  |                                              |
                  | [Routing Polices]                            |
                  | - Routing algorithms (S2L behavioral router) |
                  | - Fast-path fallback channels                |
                  |                                              |
                  | [Planning Depth & Logic]                     |
                  | - Number of multi-hop reasoning iterations   |
                  | - Consensus-synchronized audit structures     |
                  |                                              |
                  | [Retrieval Policies]                         |
                  | - Vector search parameters (top-K, threshold)|
                  | - SAGE graph pruning and traversal rules     |
                  |                                              |
                  +----------------------------------------------+
```

---

### 3. TextGrad & Linguistic Evolution (L1 Isolation)
To optimize prompt instructions, the HES implements an automated **TextGrad** loop. TextGrad treats language as a differentiable medium, performing "textual gradients" to optimize prompts based on evaluation feedback:

1. **Forward Pass**: Execute the agent with Prompt $P_0$ on a benchmark set $D$ (e.g., historical market scenarios). Collect outputs and feedback $F$.
2. **Linguistic Feedback**: Feed the execution traces, final answers, and target standards to a Critic Agent. The Critic produces a structured, detailed critique (the "textual gradient") explaining *why* the prompt failed or how it can be improved.
3. **Prompt Update**: Feed prompt $P_0$ and the critique gradient to an Optimizer Agent. The Optimizer mutates $P_0$ along the direction of the critique to produce Prompt $P_1$.
4. **Validation**: Evaluate $P_1$ on the next cross-validation batch. Keep changes that improve statistical accuracy and reduce processing latency.

$$\text{Prompt}_{t+1} = \text{Prompt}_t + \eta \cdot \text{Critique}(\text{Trace}_t)$$

---

### 4. Workflow Evolution (Level 2/3 Isolation)
For structural agent-scaffolding changes (such as changing the order of validation steps in a consensus loop), the HES uses a tree-based mutation approach:

```mermaid
graph TD
    %% Workflow Mutation
    subgraph Original Workflow
        A1[Receive Observation] --> B1[Synthesize Evidence]
        B1 --> C1[Execute Action]
    end

    subgraph Mutated Workflow
        A2[Receive Observation] --> B2[Detect Anomaly]
        B2 --> C2[Synthesize Evidence]
        C2 --> D2[Adversarial Debate]
        D2 --> E2[Execute Action]
    end

    classDef orig fill:#eceff1,stroke:#607d8b,stroke-width:1.5px;
    classDef mut fill:#e0f2f1,stroke:#009688,stroke-width:2px;
    class A1,B1,C1 orig;
    class A2,B2,C2,D2,E2 mut;
```

* **Workflow AST Parsing**: The system parses execution routines (e.g. `process_market_observation`) into discrete processing blocks.
* **Structural Mutation**: The mutation engine can:
  * **Insert**: Add validation nodes (e.g. adding an explicit `Adversarial Debate` step before trading execution).
  * **Delete**: Prune slow steps if the latency penalty outweighs accuracy benefits.
  * **Swap**: Reorder steps (e.g. moving `Confidence Calibration` before `World Model Simulation`).
* **Harness Integrity Enforcement**: Every mutated harness is validated against structural invariant rules. For example, any pipeline proposed for live execution *must* contain an active, un-bypassable `RiskSentinel` veto check before a trade is dispatched.
