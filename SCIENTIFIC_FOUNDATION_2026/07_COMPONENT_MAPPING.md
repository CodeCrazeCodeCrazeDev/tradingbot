# Phase 6 (Part 1): Component Mapping

This document maps the scientific principles and implementation roadmap to the actual target files in the AlphaAlgo codebase.

---

## 1. Subsystem Implementation Map

| UCA Component | Target Path (New Stack) | Scientific Principle |
| :--- | :--- | :--- |
| **CSC (Brain)** | `trading_bot/core/csc/controller.py` | Unified Brain / Active Inference |
| **Folding Buffer** | `trading_bot/core/csc/folding.py` | HIPIF (Information Folding) |
| **S2L Router** | `trading_bot/core/csc/router.py` | Skill-to-LoRA |
| **SCM (World Model)** | `trading_bot/world_model/causal/scm.py` | CWMI / Do-Calculus |
| **Evidence Graph** | `trading_bot/knowledge/graph/evidence.py` | Agents-K1 (Graph Orchestration) |
| **Evolution Gate** | `trading_bot/governance/evolution_gate.py` | RSEA (Monotone-Safe Gate) |
| **Safety Gate** | `trading_bot/governance/immutable_shield.py` | Reward Hacking Safety |
| **HMS (Memory)** | `trading_bot/persistence/hms/` | Hierarchical WMR Loop |

---

## 2. Agent Mapping (PCAs)

| Agent Role | Logic Implementation | state Management |
| :--- | :--- | :--- |
| **Macro PCA** | Bayesian Epistemic Core | Transactive Memory |
| **Risk PCA** | Bayesian EV-Optimizer | Immutable Safety Gate |
| **Alpha PCA** | SocraticPO Loop | Research Evidence Graph |

---

## 3. Tool Mapping

| New Tool | Functionality | Source Paper |
| :--- | :--- | :--- |
| **FoldingOperator** | Compresses subgoal logs | HIPIF |
| **CausalSandbox** | Predicts intervention impact | CWMI |
| **SocraticVerifier** | Diagnoses reasoning errors | SocraticPO |
| **GainValidator** | Measures online learning gain | CL-Bench |
