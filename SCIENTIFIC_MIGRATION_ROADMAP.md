# Scientific Migration Roadmap - UCA 2026 Redesign

This roadmap outlines the transition from the fragmented hypothesis ecosystem to the Unified Scientific Reasoning Engine (SRE).

## Phase 1: Foundation & Data Normalization (Current)
- **Centralize Data Model**: Enforce `ScientificHypothesis` in `trading_bot/core_agent_system/scientific_reasoning/core.py` as the primary entity.
- **Bridge Legacy Components**: Map existing signals from CSC, PHCE-D, and Alpha Mining to the SRE registry via internal adapters.
- **Baseline Metrics**: Activate `ScientificMetrics` to track current system performance and identify bottleneck baselines.

## Phase 2: Pipeline Hardening (Weeks 1-4)
- **Concrete Lifecycle Implementation**: Replace SRE stubs (Steps 2, 7, 19) with full production-grade logic.
  - Integrate GWM for `detect_anomalies`.
  - Wire `AdversarialAnalyzer` for `generate_counterfactuals`.
- **Epistemic Calibration**: Force all Level 3+ hypotheses through the `EpistemologyEngine` for adversarial evaluation before promotion.

## Phase 3: SAGE & Memory Integration (Weeks 5-8)
- **Institutional Memory**: Connect Step 15 (`Memory Consolidation`) to the SAGE Graph memory in HMS.
- **Scientific Replay**: Implement surprise-driven replay to prevent "Scientific Amnesia" and refine historical hypothesis failures.

## Phase 4: Full Autonomy & Meta-Discovery (Weeks 9+)
- **Active Inference**: Enable full VFE-driven reasoning where the system autonomously generates research questions based on surprise.
- **Alpha Evolution**: Connect SRE Meta-Discovery (Step 19) to the `GeneticAlphaSearch` search priors.
- **Legacy Decommissioning**: Gradual removal of redundant registries once SRE parity is verified in live trading.
