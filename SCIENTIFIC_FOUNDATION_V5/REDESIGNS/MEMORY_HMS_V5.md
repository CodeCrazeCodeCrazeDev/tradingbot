# HMS V5: Hierarchical Memory System Redesign

The HMS V5 unifies the **Transactional Shared Log** (LogAct) with the **Context-Sensitive Knowledge** (Quantum KG).

## 1. Structure
HMS V5 is organized into 5 Tiers on a unified storage backbone:

*   **Tier 1: Transactional Log (LogAct)**
    *   *Purpose*: Atomic, immutable record of all intents, votes, and executions.
    *   *Source*: LogAct (2026).
    *   *Mechanism*: Write-ahead log for agent actions.
*   **Tier 2: Episodic Buffer (Working Memory)**
    *   *Purpose*: Recent interactions, uncompressed traces.
    *   *Source*: Memory Survey (2026).
    *   *Mechanism*: Ring buffer with TTL.
*   **Tier 3: Quantum Knowledge Graph (Semantic Memory)**
    *   *Purpose*: Verified market facts, causal relationships, institutional SOPs.
    *   *Source*: Quantum KG (2026) + Agents-K1.
    *   *Mechanism*: Triplet store with Context-Validity metadata.
*   **Tier 4: Strategic Artifact Store (Transactive Memory)**
    *   *Purpose*: Population-level reuse of successful agent trajectories and code modules.
    *   *Source*: MATM (2026).
    *   *Mechanism*: Key-Value store (Task, Context) -> (Verified Solution).
*   **Tier 5: Institutional Ledger (Safety & Governance)**
    *   *Purpose*: Immutable safety invariants, formal specifications, risk limits.
    *   *Source*: Reward Hacking Safety (2026).
    *   *Mechanism*: Read-only (at runtime), formally verified state.

## 2. The WMR-V Loop (Write-Manage-Read-Verify)
The V5 memory loop integrates the LogAct Shared Log into the standard memory cycle:

1.  **Write (Pre-Execution)**: Intent is written to Tier 1 (Shared Log).
2.  **Verify**: Verification Swarm (Tier 5) checks intent $\to$ Appends "Vote" to Tier 1.
3.  **Execute & Log**: Once consensus is reached, action is played $\to$ Outcome written to Tier 1.
4.  **Manage (Post-Execution)**:
    *   Background process reads Tier 1 $\to$ Extracts Contextual Triplets.
    *   Appends to Tier 3 (QKG) with regime-validity metadata.
    *   Folds long log segments (HIPIF) into Tier 4 (Artifacts).
5.  **Read**: Agents query Tier 3 (QKG) and Tier 4 (MATM) using their current context.

## 3. Data Schema: Quantum Triplet
```json
{
  "subject": "EURUSD_H1",
  "predicate": "MeanReverting",
  "object": "True",
  "context": {
    "regime": "LowVol_Range",
    "macro": "Post_CPI",
    "volatility_index": "<12",
    "confidence": 0.89,
    "source_trace": "log_idx_9482",
    "expiration": "2026-07-20T00:00:00Z"
  }
}
```
