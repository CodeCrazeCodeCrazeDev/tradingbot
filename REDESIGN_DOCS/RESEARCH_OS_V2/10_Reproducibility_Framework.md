# 10. Provenance and Reproducibility Framework

The Research OS V2 treats reproducibility as a mathematical constraint. If an experiment cannot be replicated exactly, its findings are considered unscientific.

---

## 1. Immutable Provenance Hashing

Every experiment receives a unique, cryptographically signed fingerprint called the `ProvenanceHash`. If even a single parameter, configuration line, or dataset version changes, it represents an entirely different node in the experiment lineage graph.

### 1.1 Computation Formula

$$\text{ProvenanceHash} = \text{SHA-256}\left( \text{dataset\_hash} + \sum \text{feature\_hashes} + \text{git\_commit} + \text{config\_hash} + \text{random\_seed} + \text{env\_fingerprint} \right)$$

*   **dataset_hash:** The SHA-256 hash of the content of the split DataFrame.
*   **feature_hashes:** The ordered combination of feature version tags used in the features dataframe.
*   **git_commit:** The Git commit SHA-1 of the active repository code.
*   **config_hash:** A hash of the hyper-parameters and strategy execution configuration.
*   **random_seed:** The locked integer seed used to initialize random number generators.
*   **env_fingerprint:** A string representing the runtime Python version, dependency locks, and operating system metadata.

---

## 2. Hardened Reproducibility Actions

1.  **Strict Global Seed Locking:** Prior to any calculation (feature computing, ML training, random splits), the Research OS automatically locks the random states of `random`, `numpy`, and any local mathematical libraries to the experiment's declared seed.
2.  **Dataset Hashing:** On dataset registration, the full DataFrame index and content are hashed. Before re-running an experiment, the system compares the active DataFrame's hash against the original `dataset_hash`. If a mismatch is found, execution is blocked immediately.
3.  **Baseline Strategy Library:** Provides deterministic, fixed-seed baseline strategy definitions. This guarantees that baseline comparisons remain perfectly identical across different research machines and parallel executions.
