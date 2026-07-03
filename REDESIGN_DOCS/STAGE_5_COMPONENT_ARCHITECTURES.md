# Stage 5: Detailed Component Architectures

## 1. Agent Architecture (PCA)
- **Base Class**: `PersistentCognitiveAgent`
- **Identity**: Unique UUID + Persistent State.
- **Cognitive Modules**:
    - `BeliefSystem`: Manages the Epistemic Core (Bayesian).
    - `PlanningEngine`: Implements HIPIF.
    - `MemoryRouter`: Connects to HMS and Transactive Bus.
    - `AdapterManager`: Switches between S2L LoRA adapters.

## 2. World Model Architecture (GWM)
- **Core**: `PredictiveMarketCore` (Mamba + Transformer).
- **Encoders**: `UnifiedCrossAssetEncoder` (FX, Equities, Macro).
- **Heads**:
    - `ScenarioGenerator`: Multi-path sampling.
    - `CausalEngine`: Do-calculus perturbations.
    - `ExecutionModel`: Fill/Slippage prediction.

## 3. Memory Architecture (HMS)
- **Infrastructure**: Hybrid Vector (Chroma/Qdrant) + Graph (NetworkX) + SQL (Postgres).
- **Service**: `HierarchicalMemoryNavigator` using "Organize then Retrieve".
- **Consolidation**: Background task that "folds" episodic memory into semantic facts.

## 4. Planning Architecture (HIPIF)
- **Goal Tree**: Recursive decomposition of high-level objectives.
- **Horizon Manager**: Dynamically scales the planning horizon based on task complexity (Research vs. Execution).
- **Folding Engine**: Semantic summarization of completed sub-trees.

## 5. Decision & Governance Architecture
- **VerdictEngine**: Multi-PCA debate with weighted confidence and disagreement penalties.
- **GovernanceGate**: Final, immutable safety check (OOD Detection, Exposure Limits, Regulatory Compliance).
- **Red-Teaming**: Active simulation of "Adversarial Agent" scenarios to test robustness.

---

## 6. Self-Improvement Architecture (Recursive)

The system improves itself through a **Diagnostic Loop**:
1.  **Failure Analysis (HORIZON)**: Identify "Breaking Points" in long-horizon trajectories.
2.  **Socratic Diagnosis**: Analyze *why* a failure occurred (e.g., Memory retrieval noise vs. World model inaccuracy).
3.  **Hypothesis Generation**: Propose modifications to the Harness (Tools/Prompts) or Weights (LoRA).
4.  **Sandbox Validation**: Test in the GWM-backed simulator or Rigorous Backtest.
5.  **Deployment**: Staged roll-out with rollback capability.

---

## 7. Migration Roadmap

### Phase 1: Foundation (30 Days)
- Implement CSC (Cognitive System Controller).
- Port `WorldModelV2` to GWM (add multi-path simulation).
- Establish the Hierarchical Memory Store.

### Phase 2: Agent Evolution (30 Days)
- Convert specialists into PCAs.
- Implement HIPIF planning.
- Introduce S2L behavioral adapters.

### Phase 3: Platform Independence (30 Days)
- Build Institutional Adapters (FIX/REST).
- Decouple execution from MT5/Windows.
- Containerize the CSC for cloud deployment.

### Phase 4: Self-Evolution (Ongoing)
- Activate the Diagnostic Self-Improvement loop.
- Integrate CL-Bench for continuous "Learning Gain" measurement.
