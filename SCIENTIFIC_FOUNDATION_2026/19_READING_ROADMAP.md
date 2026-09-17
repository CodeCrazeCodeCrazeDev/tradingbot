# 🧭 AI-EOS Scientific Literature Reading Roadmap

This document outlines the ordered learning paths for quant researchers and engineers developing **AI-EOS**. Learnings are structured by seniority level and progressive prerequisites.

## 🗺️ Learning Path Matrix

| Stage | Level | Estimated Effort (Hrs) | Focus Areas | Recommended Order | Objectives |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Stage 1** | **Foundational** | 40-60 | Agent Loops & Tool Use | ReAct → BabyAGI → AutoGPT → ToT | Master basic planning & tool execution. |
| **Stage 2** | **Intermediate** | 60-80 | Verification & Self-Correction | Let's Verify → Math-Shepherd → Self-Refine → Reflexion | Build verifiers to block outcome reward hacking. |
| **Stage 3** | **Advanced** | 80-120 | Self-Rewarding & RSI | Self-Rewarding → RISE → RSA → Introspection Threshold | Transition to autonomous curating and self-play. |
| **Stage 4** | **Expert** | 120+ | Multi-Agent Swarms & Scientists | MetaGPT → MAST → Six Sigma → AI Scientist → PARNESS | Construct fully autonomous open-ended discovery teams. |

## 📘 Detailed Stage Guide

### Stage 1: Foundational (Month 1-2)
Understand the mechanics of interleaved reasoning and acting (ReAct) and basic recursive task execution.
- **Prerequisites:** Python, PyTorch basics.
- **Key Readings:** `ACT-001` (ReAct), `ACT-002` (Tree of Thoughts), `ENG-001` (BabyAGI).
- **Implementation Goal:** Write a single-agent loop that queries trading indicators and formats trade orders without drifting off-track.

### Stage 2: Intermediate (Month 3-6)
Introduce step-wise verification, credit assignment, and failure tracking. Learn why LLMs struggle to verify themselves.
- **Prerequisites:** Stage 1, basic understanding of reinforcement learning.
- **Key Readings:** `V-001` (Let's Verify), `V-002` (Math-Shepherd), `SR-006` (Self-Refine), `SR-007` (Reflexion), `SR-012` (Cannot Self-Correct).
- **Implementation Goal:** Implement a decoupled verifier that audits trade structures and logs verbal reflections upon risk limit hits.

### Stage 3: Advanced (Month 7-12)
Explore self-rewarding policies, population-based reasoning-chain synthesis, and mathematical boundaries of self-evolution.
- **Prerequisites:** Stage 2, probability theory, optimization algorithms.
- **Key Readings:** `RSI-001` (Introspection Threshold), `RSI-004` (RSA), `SR-001` (Self-Rewarding), `SR-002` (Process Self-Rewarding).
- **Implementation Goal:** Develop an active tournament loop where candidate trading parameters play head-to-head on historical out-of-sample data.

### Stage 4: Expert (Year 2+)
Build enterprise-grade, consensus-driven execution networks and fully automated scientific research systems.
- **Prerequisites:** Stage 3, distributed systems, deep RL experience.
- **Key Readings:** `MAS-002` (MAST), `MAS-003` (Coordination Layer), `MAS-004` (Six Sigma), `SCI-001` (The AI Scientist), `SCI-004` (PARNESS).
- **Implementation Goal:** Construct a Virtual Research Team where multiple agents collaborate to write, test, critique, and deploy trading algorithms autonomously.
