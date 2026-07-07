# Paper Synthesis: FIRE Benchmark

## Paper Information
* **Title**: FIRE: A Comprehensive Benchmark for Financial Intelligence and Reasoning Evaluation
* **Authors**: Xiyuan Zhang, et al.
* **Publication**: arXiv:2602.22273
* **Year**: 2026
* **Link**: https://arxiv.org/abs/2602.22273

## Core Scientific Contribution
Introduces **FIRE**, a comprehensive benchmark for both theoretical financial knowledge and practical business scenarios. Includes 3,000 questions across complex financial domains.

## Reusable Algorithms & Engineering Principles
* **Systematic Evaluation Matrix**: Categorizing financial intelligence into subdomains (macro, risk, portfolio, etc.).
* **Open-Ended Evaluation Rubrics**: Using rubrics for complex, non-deterministic financial tasks.

## Architectural Patterns
* **Multi-Domain Benchmarking**: Evaluating models across different financial "specialties".

## Mathematical Foundations
* **Metric Formulation**: Success rates across varied financial scenario distributions.

## Failure Modes & Complexity
* **Failure Modes**: Data leakage (if training data contains the benchmark); rubric subjectivity.
* **Computational Complexity**: Low (evaluation-time only).
* **Scalability Limits**: Fixed set of 3,000 questions.

## Comparison against AlphaAlgo (UCA-2026)
* **Status**: AlphaAlgo uses `CL-Bench` (Continual Learning).
* **Improvement**: FIRE provides *domain-specific* financial grounding that `CL-Bench` lacks.

## Decision: ADOPT
* **Justification**: We need an institutional "IQ Test" for the bot. FIRE is that test.
* **Implementation**: Integrate FIRE into the `ValidationFramework` as the primary "Domain Intelligence" metric.

---

# Paper Synthesis: Grow, Don't Overwrite

## Paper Information
* **Title**: Grow, Don't Overwrite: Fine-tuning Without Forgetting
* **Authors**: Dyah Adila, et al.
* **Publication**: arXiv:2603.08647
* **Year**: 2026
* **Link**: https://arxiv.org/abs/2603.08647

## Core Scientific Contribution
Introduces a **function-preserving expansion method** for fine-tuning. Replicates pre-trained parameters and applies a scaling correction so the model is identical to the original at initialization. Prevents catastrophic forgetting.

## Reusable Algorithms & Engineering Principles
* **Function-Preserving Expansion**: Expanding model capacity without changing behavior at initialization.
* **Scaling Correction**: Mathematical guarantee of identity.
* **Selective Layer Expansion**: Modularity to reduce computational cost.

## Architectural Patterns
* **Growing Neural Networks**: Dynamic expansion of specialized submodules.

## Mathematical Foundations
* **Parameter Replication Logic**: $W_{new} = [W_{orig}, W_{orig}] \cdot \text{scale}$.

## Failure Modes & Complexity
* **Failure Modes**: Parameter explosion (if not selective); complexity in initialization logic.
* **Computational Complexity**: Low during training (compared to full fine-tuning).
* **Scalability Limits**: GPU memory (if expanding too many layers).

## Comparison against AlphaAlgo (UCA-2026)
* **Status**: AlphaAlgo uses "Skill-to-LoRA" (S2L).
* **Improvement**: S2L is an adapter. "Grow" is a *native capacity expansion*.
* **Synergy**: Use "Grow" for the core World Model and S2L for transient skills.

## Decision: ADOPT
* **Justification**: Essential for "Continual Learning" without losing foundational knowledge.
* **Implementation**: Include in the "Future Training Architecture" for World Model V5.
