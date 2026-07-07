# Engineering Decomposition: EKSFT (arXiv:2605.29303)

## Core Hypothesis
Supervised Fine-tuning (SFT) in low-data regimes should prioritize activating task-relevant capabilities rather than memorizing specific content. Selectively masking high-uncertainty or distribution-shifting tokens prevents fitting to limited samples and preserves the pre-trained distribution.

## Mathematical Formulation
- **Entropy Masking**: Mask tokens $x_t$ where $H(P_{model}(x_t | x_{<t})) > \tau_H$.
- **KL Divergence Masking**: Mask tokens $x_t$ where $D_{KL}(P_{ref}(x_t | x_{<t}) || P_{model}(x_t | x_{<t})) > \tau_{KL}$.
- **Loss Function**: $L = -\sum_{t \in \{t | mask_t=0\}} \log P_{model}(x_t | x_{<t})$.

## Training Methodology
1. Use a reference model (frozen pre-trained) and the model to be fine-tuned.
2. For each token in the SFT dataset, calculate entropy and KL divergence.
3. Apply masks based on thresholds $\tau_H$ and $\tau_{KL}$.
4. Update model weights only on non-masked tokens.

## Learning Algorithm
- **EKSFT-SFT**: Selective token imitation during supervised learning.
- **Post-RL**: EKSFT-initialized models provide better starting points for RL exploration.

## Memory Architecture
N/A (Primarily a training technique).

## Planning Architecture
N/A (Improves base model capability used in planning).

## Agent Architecture
N/A.

## World Model Contribution
Ensures the world model's internal representation doesn't drift during fine-tuning on limited market scenarios.

## Self-improvement Contribution
Provides a "monotone-safe" way to ingest new trade data without catastrophic forgetting or distribution collapse.

## Failure Modes
- Incorrect threshold selection (too restrictive = no learning; too loose = overfitting).
- Dependence on the quality of the reference model.

## Scalability Limits
Requires dual-model inference during training (reference + current), increasing VRAM/compute costs.

## Computational Complexity
$O(T \cdot (C_{model} + C_{ref}))$ where $T$ is sequence length and $C$ is inference cost.

## Engineering Tradeoffs
Compute overhead for token filtering vs. improved generalization and RL stability.

## Financial Applicability
Essential for fine-tuning on rare market events (black swans) where data is sparse and overfitting is dangerous.

## Production Readiness
High. Implementable as a custom loss/masking layer in the training pipeline.
