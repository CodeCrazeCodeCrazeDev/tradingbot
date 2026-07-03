# ADR-004: Skill-to-LoRA (S2L) Behavioral Modules

## Problem Definition
AlphaAlgo relies on textual skill injection (concatenating `SKILL.md` to prompts). This causes significant token overhead, increases inference latency, and introduces "context interference" where the procedural instructions distract the model from the actual market data.

## Existing Implementation
A `ToolRegistry` and `AgentCapability` system where natural language descriptions of skills are injected into the agent's system prompt at runtime.

## Research Evidence
- **Skill-to-LoRA: From Using Skills to Learning Behaviors (arXiv:2606.16769):** Demonstrates that parameterized skill representations reduce context overhead and improve pass rates.
- **SocraticPO (arXiv:2606.09887):** Provides the interactive guidance framework to refine these behaviors.

## Selected Decision
Transition to **Skill-to-LoRA (S2L)** behavioral modules. Specialized skills (e.g., "Order Block Detection", "Risk Sensitivity Tuning") will be distilled into lightweight LoRA adapters (rank-16) and dynamically loaded by the Unified Cognitive Orchestrator.

## Competing Alternatives
1. **Full-Text Prompting:** (Rejected) - Inefficient and leads to "lost in the middle" failures.
2. **Hard-coded Logic:** (Rejected) - Lacks the nuanced reasoning of LLM-based behavioral execution.

## Mathematical Justification
S2L optimizes the "Cost-Normalized Gain" (CNG):
$$CNG = \frac{\Delta \text{Success Rate}}{\Delta \text{Token Cost}}$$
Textual injection has negative CNG in many SWE-Skills-Bench tasks. S2L achieves positive CNG by keeping $\Delta \text{Token Cost}$ near zero (parameters vs. tokens) while increasing performance through behavioral alignment.

## Engineering Justification
- **Low Latency:** Eliminates the need to process 1000+ tokens of skill instructions per step.
- **Modularity:** Skills can be updated by swapping a 50MB `.bin` file instead of rewriting system prompts.

## Implementation Strategy
1. Establish the `SkillDistillationPipeline` (Skill.md -> Synthetic Demos -> LoRA training).
2. Integrate a dynamic LoRA loader into the UCO inference path.

## Validation Strategy
- **Benchmark:** SWE-Skills-Bench (adapted for financial tasks).
- **Success Criteria:** >0.5 CNG on AlphaAlgo internal skills.

## Risks & Rollback
- **Risk:** Adapter interference if multiple LoRAs are loaded simultaneously.
- **Rollback:** Revert to textual prompting if LoRA behavioral fidelity is low.

## Confidence Level
**Medium-High** (Strong empirical evidence from 2026 benchmarks, requires robust infrastructure).
