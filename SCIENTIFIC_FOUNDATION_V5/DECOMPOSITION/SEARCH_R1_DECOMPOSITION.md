# Engineering Decomposition: Search-R1 (arXiv:2503.09516)

## Core Hypothesis
Training LLMs to autonomously generate multiple search queries during step-by-step reasoning using Reinforcement Learning (RL) improves performance over simple RAG baselines. Interleaving reasoning and searching allows the model to optimally interact with search engines.

## Mathematical Formulation
- **Reward Function**: Outcome-based reward (binary success) for final answer.
- **RL Method**: GRPO or PPO optimized over reasoning trajectories.
- **Interleaved Format**: `<think> ... <search> query </search> ... </think>`

## Training Methodology
- Large-scale RL training on question-answering datasets.
- Uses "retrieved token masking" to stabilize RL training when external search results are injected into the context.

## Learning Algorithm
- RL-based optimization of search calling behavior.
- Multi-turn search interactions within a single reasoning episode.

## Memory Architecture
Episodic context contains interleaved search results.

## Planning Architecture
Step-by-step reasoning with explicit "think-before-search" steps.

## Agent Architecture
Tool-augmented reasoning agent.

## World Model Contribution
Search results act as grounded external world state updates.

## Self-improvement Contribution
The model learns *when* and *what* to search to minimize final error.

## Failure Modes
- Search query collapse: repetitive or irrelevant queries.
- Latency: multiple search turns increase wall-clock time.

## Scalability Limits
Dependent on search engine throughput and cost.

## Computational Complexity
High during training (RL on long trajectories). Standard inference + search overhead.

## Engineering Tradeoffs
Search cost/latency vs. reasoning accuracy.

## Financial Applicability
Real-time news retrieval and data verification during strategy ideation.

## Production Readiness
High. Basis for many "Deep Research" products.
