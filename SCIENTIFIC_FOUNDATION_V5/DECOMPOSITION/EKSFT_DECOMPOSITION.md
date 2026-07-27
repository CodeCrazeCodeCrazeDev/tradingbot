# Engineering Decomposition: EKSFT (arXiv:2605.29303)

## Core Hypothesis
Supervised Fine-tuning (SFT) in sparse-data regimes (like black-swan market events) causes distribution collapse or catastrophic forgetting. Entropy-KL Selective Fine-Tuning (EKSFT) prevents this by updates only on "informative" tokens that preserve the pre-trained distribution.

## Mathematical Formulation
- **Masking Logic**: Token $x_t$ is masked if it belongs to the high-uncertainty set $\mathcal{M}$.
- **Entropy Mask**: $H(P_{model}(x_t | x_{<t})) > \tau_H$.
- **KL Anchor**: $D_{KL}(P_{ref}(x_t | x_{<t}) || P_{model}(x_t | x_{<t})) > \tau_{KL}$.
- **Loss**: $\mathcal{L}_{EKSFT} = \sum_{t \notin \mathcal{M}} -\log P_{model}(x_t | x_{<t})$.

## Training Methodology
1. Initialize with a frozen Reference Model ($P_{ref}$) and an active Student Model.
2. Calculate token-level entropy and KL-divergence for each sequence in the training set.
3. Apply binary masks $\mathbf{m}$ to the loss function based on thresholds $\tau_H$ and $\tau_{KL}$.
4. Perform gradient updates only on unmasked tokens.

## Learning Algorithm
- **Selective Gradient Filtering**: Direct modification of the SGD/Adam step to ignore high-KL tokens.
- **Monotone-Safe Alignment**: Ensuring the model never moves away from the "safety anchors" of the reference model.

## Memory Architecture
Weight-based parametric memory stabilization. No external memory required.

## Planning Architecture
Improves the reliability of the base model used by the `PlannerAgent`, ensuring it doesn't "hallucinate" novel strategies that conflict with historical risk anchors.

## Agent Architecture
Self-stabilizing reasoning backbone.

## World Model Contribution
Ensures the `WorldModelV3` transition distributions remain calibrated even after fine-tuning on recent volatility.

## Self-improvement Contribution
The "Evolution Gate" utilizes EKSFT to ingest new trade data without strategic drift.

## Failure Modes
- **Anchor Drift**: Reference model itself is misaligned.
- **Under-fitting**: Thresholds too tight, preventing learning of valid new patterns.

## Scalability Limits
Requires 2x memory during training (reference model + active model).

## Computational Complexity
$\mathcal{O}(T \cdot \text{Forward}(P_{ref} + P_{model}))$ per sequence.

## Engineering Tradeoffs
Compute cost (dual model) vs. Alignment stability.

## Financial Applicability
Ingesting rare black-swan events (e.g., flash crashes) without breaking the baseline risk-management policy.

## Production Readiness
High. Implementable as a custom loss layer in PyTorch/XLA.
