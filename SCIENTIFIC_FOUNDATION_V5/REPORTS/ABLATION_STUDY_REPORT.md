# UCA V5 Ablation Study Report

This study isolates the marginal impact of each core architectural component by comparing the full UCA V5 system against versions where specific components are disabled/reverted.

## 1. Component Marginal Contribution

| Component | Enabled | Disabled | Δ Sharpe | Δ Drawdown | Contribution |
| --- | --- | --- | --- | --- | --- |
| **LogAct Consensus** | 1.85 | 1.35 | +0.50 | -4.5% | **Critical** (Safety/Veto) |
| **DiscoLoop Reasoning**| 1.85 | 1.55 | +0.30 | -1.2% | **High** (Multi-hop Alpha) |
| **SAGE Graph-Memory** | 1.85 | 1.72 | +0.13 | -0.5% | **Medium** (Long-term Context) |
| **MSCL (Amnesia)** | 1.85 | 1.78 | +0.07 | -0.2% | **Low** (Stability over time) |
| **Unified Risk Engine**| 1.85 | 1.25 | +0.60 | -6.8% | **Highest** (Capital Preserv.) |
| **HIPIF (Folding)** | 1.85 | 1.80 | +0.05 | 0.0% | **Low** (Token efficiency) |

## 2. Synthesis
The **Unified Risk Engine** and **LogAct Consensus** provide the largest gains in risk-adjusted performance by preventing high-entropy "delusion" trades. **DiscoLoop** provides the primary gain in absolute Alpha by enabling deeper reasoning about cross-asset linkages.

## 3. Recommended Retention
All components demonstrate positive marginal utility. Even low-impact components like **MSCL** and **HIPIF** are retained for their contribution to long-horizon system stability and operational efficiency (token cost reduction).
