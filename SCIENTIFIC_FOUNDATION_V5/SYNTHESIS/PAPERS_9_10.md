# Paper Synthesis: Learning to Self-Evolve (LSE)

## Paper Information
* **Title**: Learning to Self-Evolve
* **Authors**: Xiaoyin Chen, et al.
* **Publication**: arXiv:2603.18620
* **Year**: 2026
* **Link**: https://arxiv.org/abs/2603.18620

## Core Scientific Contribution
Introduces **Learning to Self-Evolve (LSE)**, a reinforcement learning framework that trains LLMs to improve their own contexts/prompts at test time. Reduces multi-step evolution to a single-step RL objective.

## Reusable Algorithms & Engineering Principles
* **Single-Step RL for Evolution**: Reward = Improvement in downstream task.
* **Tree-Guided Evolution Loop**: Using tree search to find optimal context edits.
* **Skill Internalization**: Treating self-evolution as a learnable model skill.

## Architectural Patterns
* **Test-Time Adaptation**: Real-time context refinement.
* **Self-Evolving Policy**: The model is trained specifically to be an "Evolver".

## Mathematical Foundations
* **Reward Formulation**: $\mathcal{R} = \Delta \text{Perf}(\tau)$.

## Failure Modes & Complexity
* **Failure Modes**: Overfitting the context to a single problem instance; unstable RL trajectories.
* **Computational Complexity**: Moderate (test-time optimization).
* **Scalability Limits**: Quality of the reward signal.

## Comparison against AlphaAlgo (UCA-2026)
* **Status**: AlphaAlgo has `AutonomousLearner` (passive).
* **Improvement**: LSE makes evolution an *active, trained skill*.

## Decision: ADOPT
* **Justification**: Enhances the "Recursive Diagnostic Self-Improvement" loop with a trained evolution policy.
* **Implementation**: Include LSE as the "Future RL" recipe for fine-tuning AlphaAlgo's core models.

---

# Paper Synthesis: ReTool

## Paper Information
* **Title**: ReTool: Reinforcement Learning for Strategic Tool Use in LLMs
* **Authors**: Jiazhan Feng, et al.
* **Publication**: arXiv:2504.11536
* **Year**: 2025
* **Link**: https://arxiv.org/abs/2504.11536

## Core Scientific Contribution
Introduces **ReTool**, which enhances long-form reasoning with strategic, tool-integrated learning. Uses RL to teach the model **when and how** to invoke tools (like code interpreters) based on outcome feedback.

## Reusable Algorithms & Engineering Principles
* **Strategic Tool Interleaving**: Dynamic switching between text reasoning and code execution.
* **Automated RL Paradigm for Tools**: Rollouts with multi-turn tool use.
* **Code Self-Correction**: Emergent "aha moments" where the model fixes its own tool calls.

## Architectural Patterns
* **Neuro-Symbolic Hybrid**: LLM reasoning + Deterministic tool execution.
* **Outcome-Driven Policy**: Rewards based on the final success of the tool-integrated chain.

## Mathematical Foundations
* **Sequential Decision Process**: Tool use as a set of actions in an RL trajectory.

## Failure Modes & Complexity
* **Failure Modes**: Tool-use loops; reliance on "cheating" tools; execution environment failures.
* **Computational Complexity**: Moderate (interleaving latency).
* **Scalability Limits**: Diversity of the toolset.

## Comparison against AlphaAlgo (UCA-2026)
* **Status**: AlphaAlgo has a `ToolRegistry` and `SkillRouter`.
* **Improvement**: ReTool provides a way to *train* the strategy for tool usage, rather than just providing the tools.

## Decision: EXTEND
* **Justification**: Trading involves many "tools" (calculators, backtesters). Strategic use is critical.
* **Implementation**: Integrate ReTool's "Strategic Tool Interleaving" into the `SkillRouter` logic.
