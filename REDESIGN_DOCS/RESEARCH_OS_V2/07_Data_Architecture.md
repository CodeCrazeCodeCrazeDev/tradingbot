# 07. Data Architecture and Registries

To eliminate data leakage, feature redundancy, and lookahead bias, the Research OS V2 structures all inputs, features, models, and strategies into formal registries mapped to Directed Acyclic Graphs (DAGs) using `networkx`.

---

## 1. Registry Specifications

The platform manages six structural registries backed by the SQLite database `research.db`:

```text
                               +--------------------+
                               | HypothesisRegistry |
                               +---------+----------+
                                         |
                                         ▼
                               +--------------------+
                               |  DatasetRegistry   |
                               +---------+----------+
                                         |
                                         ▼
                               +--------------------+
                               |  FeatureRegistry   |
                               +---------+----------+
                                         |
                                         ▼
                               +--------------------+
                               |   ModelRegistry    |
                               +---------+----------+
                                         |
                                         ▼
                               +--------------------+
                               |  StrategyRegistry  |
                               +---------+----------+
                                         |
                                         ▼
                               +--------------------+
                               |  BacktestRegistry  |
                               +--------------------+
```

### 1.1 Dataset Registry
*   Tracks raw and cleaned dataset files, partition histories, and data splits.
*   **Fields:** `dataset_id`, `name`, `source`, `version_tag`, `start_time`, `end_time`, `row_count`, `sha256_hash`, `regime_tag`.

### 1.2 Feature Registry
*   Tracks individual feature definition parameters to avoid duplicate feature calculations.
*   **Fields:** `feature_id`, `name`, `expression`, `lookback_bars`, `creator_id`, `mutual_information_score`, `drift_psi`.

### 1.3 Model Registry
*   Stores model architectures, trained weights references, training hyper-parameters, and performance profiles.
*   **Fields:** `model_id`, `experiment_id`, `model_type`, `parameter_count`, `weights_path`, `training_time`.

### 1.4 Strategy Registry
*   Manages rule-based or model-based signal generators mapped to trading constraints.
*   **Fields:** `strategy_id`, `name`, `model_id`, `direction_bias`, `stop_loss_pips`, `take_profit_rr`, `status`.

---

## 2. Lineage Graphs via NetworkX DAGs

Lineage is managed through independent Directed Acyclic Graphs (DAGs) constructed via the `networkx` library:

### 2.1 Dataset Lineage Graph
*   Nodes represent raw files or cleaned partitions.
*   Edges trace data splits or cleaning transformations.
*   **Cycle Detection:** On adding any node, the system runs `nx.is_directed_acyclic_graph` to guarantee no circular dependencies.

### 2.2 Feature Lineage Graph
*   Nodes represent features (`FeatureVersion`).
*   Edges represent dependent transformations (e.g. `LogReturns` -> `RealizedVolatility` -> `NormalizedZScore`).
*   **Impact Analysis:** If a base feature's formula changes, the system traverses descendants (`nx.descendants`) to mark downstream dependent features as `STALE`.

```python
import networkx as nx

class FeatureLineageGraph:
    def __init__(self):
        self.graph = nx.DiGraph()

    def add_feature(self, feature_id: str, parent_ids: list):
        self.graph.add_node(feature_id)
        for parent in parent_ids:
            self.graph.add_edge(parent, feature_id)

        # Verify DAG structure
        if not nx.is_directed_acyclic_graph(self.graph):
            self.graph.remove_node(feature_id)
            raise ValueError("Circular dependency detected in feature lineage.")
```
