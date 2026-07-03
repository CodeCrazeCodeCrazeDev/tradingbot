# Stage 2: Capability Matrix

## 1. Governance & Risk (MSOS)
| Capability | Description | Technical Implementation |
|---|---|---|
| Capital Preservation | Hierarchy-based constraint enforcement. | `orchestrator.py` |
| Market Tradability | Evaluating liquidity, spread, volatility structure before entry. | `market_tradability.py` |
| Loss Shape Monitoring | Analysis of drawdown acceleration and loss clustering. | `loss_monitor.py` |
| Assumption Engine | Tracking and validating signal assumptions over time. | `assumption_engine.py` |
| Learning Firewall | Preventing toxic data/regimes from corrupting models. | `learning_firewall.py` |
| Data Adversarial Defense | Protection against market manipulation/fake signals. | `data_adversarial.py` |

## 2. Intelligence & World Modeling
| Capability | Description | Technical Implementation |
|---|---|---|
| Latent Dynamics | Abstract state prediction using JEPA/DreamerV3. | `world_model/latent_dynamics.py` |
| Causal Reasoning | do-calculus for counterfactual market interventions. | `aads/core/causal_world_model.py` |
| Multi-Horizon Forecast | Predictive intelligence across multiple timeframes. | `superpowerful_ai/predictive_intelligence.py` |
| Multimodal Fusion | Combining price, text, and alternative data. | `aamis_v3/core/multimodal_fusion.py` |
| Uncertainty Estimation | Measuring "Ignorance Score" for model grounding. | `world_model/ignorance_score.py` |

## 3. Autonomous Research & Discovery
| Capability | Description | Technical Implementation |
|---|---|---|
| Alpha Discovery | Evolutionary search for new trading indicators. | `aads/core/alpha_discovery_loop.py` |
| Scientific Research | Generator-Verifier-Reviser loop for hypotheses. | `aletheia_autonomous/aletheia_orchestrator.py` |
| Self-Modification | Autonomous code/parameter mutation engine. | `autonomous_superintelligence/self_modifier.py` |
| Strategy Evolution | Sakana-style evolution for strategy genomes. | `aads/core/sakana_engine.py` |
| Knowledge Synthesis | Distilling cross-domain insights into policy. | `autonomous_superintelligence/knowledge_synthesizer.py` |

## 4. Continuous Learning (Student-Teacher)
| Capability | Description | Technical Implementation |
|---|---|---|
| Market Feedback Loop | Learning from trade outcomes (rewards/punishments). | `market_student/learning_cycle.py` |
| Policy Distillation | Distilling complex teacher knowledge into simple student agents. | `market_teacher/strategy_evolution.py` |
| Curiosity Engine | Driving exploration of unknown market regimes. | `market_teacher/curiosity_engine.py` |
| Meta-Learning | Optimizing the learning process itself (MAML). | `meta_learning/maml.py` |

## 5. Institutional & Information Pipeline
| Capability | Description | Technical Implementation |
|---|---|---|
| Information Pipeline | Acquire → Verify → Filter → Rank pipeline for web data. | `internet_access/alphaalgo_orchestrator.py` |
| Order Flow Analysis | Institutional footprint and liquidity modeling. | `institutional/bloomberg_bridge.py` |
| Market Microstructure | TCA and execution quality monitoring. | `msos/execution_reality.py` |
| Behavioral Defense | Detecting predatory institutional behavior. | `aamis_v3/critical_systems/behavioral_defense_network.py` |

## 6. Execution & Infrastructure (MOSEFS)
| Capability | Description | Technical Implementation |
|---|---|---|
| Multi-Layer Execution | Decoupled execution from intelligence. | `mosefs/layer2_execution.py` |
| Self-Evolving Infra | Infrastructure that adapts to load/compute needs. | `mosefs/layer1_infrastructure.py` |
| Consciousness Layer | High-level meta-awareness of system goals. | `mosefs/layer7_consciousness.py` |
| Swarm Coordination | Managing MicroFish-style agent swarms. | `aads/core/microfish_swarm.py` |
