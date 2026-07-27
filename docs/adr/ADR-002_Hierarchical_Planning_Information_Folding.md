# ADR-002: Hierarchical Planning with Information Folding (HIPIF)

## Problem Definition
AlphaAlgo's long-horizon autonomous missions (spanning weeks/months) frequently fail due to "Context Saturation." As the execution trace grows, the agent loses track of initial strategic constraints and begins to prioritize local noise over global goals.

## Existing Implementation
Flat ReAct loops with a fixed 10-20 step history. Older history is truncated or retrieved via noisy RAG.

## Research Evidence
- **HIPIF: Hierarchical Planning and Information Folding (arXiv:2606.10507):** Introduces end-to-end training for explicit subgoals and "folding" completed traces.
- **The Long-Horizon Task Mirage (arXiv:2604.11978):** Taxonomizes memory limitation failures in agents.

## Selected Decision
Implement a 3-layer planning hierarchy (Mission -> Task -> Action) with **Information Folding**. When a task is completed, its 50+ step trace is summarized into a `FoldedState` and the raw trace is moved to long-term storage.

## Competing Alternatives
1. **Infinite Context Models:** (Rejected) - High cost and "Lost in the Middle" retrieval issues.
2. **Pure RAG Memory:** (Rejected) - Retrieval noise interferes with sequential logic.

## Mathematical Justification
Information Folding is a mapping $\phi: \mathcal{T} \to \mathcal{S}$ that maximizes the Mutual Information between the folded summary $\mathcal{S}$ and the future optimal action $a_{t+1}$:
$$\phi^* = \arg\max_\phi I(\phi(\tau_{0:t}); a^*_{t+1})$$
subject to $|\phi(\tau)| \ll |\tau|$. This ensures that critical decision-making context is preserved while noise is discarded.

## Engineering Justification
- **Context Efficiency:** Maintains <2000 token working memory regardless of mission length.
- **Observability:** Provides human-readable summaries of high-level progress.

## Implementation Strategy
1. Implement `TraceFoldingModule` using a specialized summarization prompt/model.
2. Update `UnifiedCognitiveOrchestrator` to accept `FoldedState` objects.

## Validation Strategy
- **Benchmark:** Compare success rate on 100-step tasks with and without folding.
- **Success Criteria:** >90% information retention of critical variables (e.g., Entry Price, Stop Loss, Initial Goal).

## Risks & Rollback
- **Risk:** Lossy compression might discard "black swan" indicators.
- **Rollback:** Disable folding and revert to simple truncation if failure rates spike.

## Confidence Level
**Medium-High** (Well-supported by theoretical work and Snowflake AI Research benchmarks).
