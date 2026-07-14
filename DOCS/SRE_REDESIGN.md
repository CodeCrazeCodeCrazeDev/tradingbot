# Scientific Reasoning Engine (SRE) Redesign Specification

## Overview
The SRE is the central "One Brain" for all cognitive processing in AlphaAlgo. It transforms fragmented "Signals" into rigorous "Institutional Knowledge."

## 1. Unified Hypothesis Structure
All hypotheses (predictions, beliefs, alphas, etc.) must implement the `ScientificHypothesis` interface:

```python
@dataclass
class ScientificHypothesis:
    id: str
    name: str
    state: HypothesisState  # 19 steps
    level: PromotionLevel  # 0 to 5

    # Bayesian Core
    priors: Dict[str, float]
    posterior: float
    uncertainty: float

    # Causal Lineage
    parents: List[str]
    causal_model_ref: str

    # Evidence & History
    evidence_ledger: List[str]
    falsification_attempts: int
```

## 2. The 19-Step Lifecycle
1.  **Observation**: Ingest surprise from the world.
2.  **Anomaly Detection**: Compute VFE (Variational Free Energy).
3.  **Question Generation**: Identify missing causal links.
4.  **Hypothesis Generation**: Propose a falsifiable solution.
5.  **Evidence Collection**: Query HMS and external sources.
6.  **World Model Simulation**: Project outcome in GWM.
7.  **Counterfactual Generation**: Intervene on variables (Do-calculus).
8.  **Adversarial Debate**: Challenge with Verification Swarm.
9.  **Experiment Design**: Define OOS (Out-of-Sample) test.
10. **Execution**: Run the experiment.
11. **Evaluation**: Compute institutional gain metrics.
12. **Bayesian Update**: $P(H|E) = \frac{P(E|H)P(H)}{P(E)}$.
13. **Confidence Calibration**: Adjust for model bias/regime.
14. **Knowledge Integration**: Store in SAGE graph.
15. **Memory Consolidation**: Abstract to general principles.
16. **Policy Improvement**: Update the SkillRouter.
17. **Continuous Monitoring**: Track alpha decay.
18. **Hypothesis Retirement**: Transition to final state.
19. **Automatic Discovery**: Synthesize new observations from results.

## 3. The 10 Authoritative End-States
Every hypothesis must terminate in one of these states:
- **Confirmed**: Validated and ready for production.
- **Rejected**: Falsified by evidence or experiment.
- **Inconclusive**: Insufficient evidence to decide.
- **Merged**: Combined with another hypothesis.
- **Split**: Divided into sub-hypotheses (e.g., regime-specific).
- **Dormant**: Valid but currently inapplicable (e.g., wrong regime).
- **Reactivated**: Dormant hypothesis returned to active testing.
- **Deprecated**: Replaced by a more modern version.
- **Superseded**: Proven wrong by a superior hypothesis.
- **Institutionalized**: Converted into a permanent system rule/invariant.

## 4. Integration Gates
- **Trading Gate**: Only hypotheses at `PromotionLevel.LEVEL_4` (Production) and `HypothesisState.POLICY_IMPROVEMENT` or later can generate trade proposals.
- **Research Gate**: Level 1 and 2 hypotheses are restricted to paper-trading and simulation.
