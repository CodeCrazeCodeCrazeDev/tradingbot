# ADR-005: Decoupled Mixture-of-Experts (DMoE)

## Problem Definition
AlphaAlgo currently relies on RAG for injecting domain knowledge (e.g., regulatory rules, specific asset behavior). RAG introduces significant latency (retrieval + re-reading) and often fails on multi-hop reasoning tasks where knowledge is spread across documents.

## Existing Implementation
Flat vector-based RAG using HNSW indexing on various market and research databases.

## Research Evidence
- **Decoupled Mixture-of-Experts for Parametric Knowledge Injection (Yue et al., 2026):** Proposes modular experts attached to FFN layers to bypass RAG bottlenecks.
- **Agents-K1 (Cao et al., 2026):** Demonstrates that agent-native knowledge graphs outperform flat RAG for complex scientific/financial reasoning.

## Selected Decision
Implement **DMoE** as the primary knowledge orchestration mechanism. Financial knowledge is distilled into decoupled expert modules that are dynamically activated by an uncertainty-aware router.

## Competing Alternatives
1. **Post-Training/Fine-tuning:** (Rejected) - Causes catastrophic forgetting of the base model.
2. **GraphRAG:** (Rejected) - High inference-time latency for graph traversal.

## Mathematical Justification
The contribution of the DMoE layer to the hidden representation $h$ is:
$$h_{out} = h_{in} + \sum_{k \in \mathcal{K}} G(x)_k \cdot E_k(h_{in})$$
Where the gating function $G(x)$ is conditioned on the model's epistemic uncertainty $\mathcal{U}_{epi}(s)$:
$$G(x)_k = \begin{cases} \text{Router}(x)_k & \text{if } \mathcal{U}_{epi}(s) > \tau \\ 0 & \text{otherwise} \end{cases}$$
This ensures knowledge is only injected when the base model is calibrated to be uncertain.

## Engineering Justification
- **Inference Speed:** Zero retrieval overhead; experts are part of the forward pass.
- **KV-Cache Preservation:** Decoupled architecture allows for expert updates without recomputing KV-caches for existing prompts.

## Implementation Strategy
1. Build the self-distillation pipeline to convert `knowledge/` documents into experts.
2. Implement the `UncertaintyAwareRouter` in the UCO.

## Validation Strategy
- **Benchmark:** Agents-K1 financial reasoning benchmark.
- **Success Criteria:** >15% improvement in multi-hop question accuracy vs. legacy RAG.

## Risks & Rollback
- **Risk:** Router miscalibration leading to incorrect expert activation.
- **Rollback:** Maintain the RAG pipeline as a high-confidence fallback.

## Confidence Level
**High** (Supported by Tsinghua University and NVIDIA research findings).
