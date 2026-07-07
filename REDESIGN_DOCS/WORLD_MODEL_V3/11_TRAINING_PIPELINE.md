# 11_TRAINING_PIPELINE.md - Multi-Stage Specialist Training

## Objective
Detail the three-stage training paradigm (WM-AMT, FE-SFT, FC-RL) required to create an institutional-grade World Model.

## Stage 1: World Model Agentic Mid-Training (WM-AMT)
*   **Goal:** Inject "Market Physics" and "Causal Intuition."
*   **Data:** 10+ years of multi-asset high-frequency tick data, L2 order books, and macro news.
*   **Objectives:**
    *   **Self-Supervised Prediction:** Predict $s_{t+1}$ and $s_{t+H}$ from $s_t$.
    *   **Causal Discovery:** Learn the adjacency matrix $\mathcal{A}$ via sparse DAG regularization.
    *   **Regime Identification:** Unsupervised clustering of market states into Volatility/Liquidity regimes.
*   **Loss Function:** $\mathcal{L}_{AMT} = \mathcal{L}_{MSE}(s_{t+H}) + \alpha \cdot \mathcal{L}_{Causal}(\mathcal{A}) + \beta \cdot \mathcal{L}_{Regime}$.

## Stage 2: Format-Eliciting Supervised Fine-Tuning (FE-SFT)
*   **Goal:** Teach the model to generate structured scenarios and reasoning.
*   **Data:** Curated trajectories paired with "Expert Reasoning" traces (generated via high-fidelity backtests and LLM synthesis).
*   **Objectives:**
    *   **Structured Output:** Training the **Reasoning Interface** to output Scenario Trees and Causal Graphs in JSON/DSL format.
    *   **Uncertainty Calibration:** Using temperature scaling and label smoothing to ensure predicted confidence matches historical accuracy.
*   **Loss Function:** $\mathcal{L}_{SFT} = \mathcal{L}_{BCE}(\text{Scenarios}) + \mathcal{L}_{KL}(\text{Confidence})$.

## Stage 3: Foresight-Conditioned Reinforcement Learning (FC-RL)
*   **Goal:** Align the World Model's simulations with institutional utility (PnL + Risk).
*   **Data:** Interaction logs from the `BacktestEngine`.
*   **Mechanism:**
    *   The model generates a plan based on its own simulation.
    *   The plan is executed in the `BacktestEngine`.
    *   Reward is calculated based on the **Realized Outcome** vs. **Predicted Outcome**.
*   **Objectives:**
    *   **Pragmatic Foresight:** Reward the model if its "Scenario A" correctly identified the path that led to profit.
    *   **Risk Aversion:** Heavy penalty for "Confident Hallucinations" (predicting high profit with high confidence when the result was a loss).
*   **Loss Function:** $\mathcal{L}_{RL} = -\mathbb{E}[R \cdot \text{LogProb}(\text{Plan} | \text{Simulation})]$.

## Training Infrastructure
*   **Distributed Compute:** Using PyTorch DistributedDataParallel (DDP) or DeepSpeed.
*   **Curriculum Learning:** Start with simple price prediction on 1 asset $\to$ Multi-asset $\to$ Full SCM $\to$ Multi-horizon simulation.
*   **Replay Buffer:** The HMS Episodic tier acts as the replay buffer for FC-RL, storing "Lessons Learned" from failed simulations.
