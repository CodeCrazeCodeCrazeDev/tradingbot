# 03. RESEARCH UNDERSTANDING
## Research Understanding Division & Machine-Actionable Scientific Schemas

### 1. Architectural Mission
The **Research Understanding Division (RUD)** bridges the gap between raw academic literature and algorithmic implementation. It is responsible for parsing unstructured scientific papers (once ingested by the Discovery Division) and mapping them into standardized, **Machine-Actionable Scientific Schemas (MASS)**.

Academic text is often dense, ambiguous, or lacks explicit parameter definitions. The RUD extracts mathematical formulations, algorithmic state changes, network topologies, datasets, baseline metrics, and precise implementation roadmaps.

---

### 2. Machine-Actionable Scientific Schema (MASS)
The extracted data is compiled into a highly structured JSON-LD format. This ensures that downstream compilers, code generators, and experiment evaluators can parse the paper's contents directly to construct pipelines, constraints, and objective functions.

#### Unified JSON-LD Schema Specification
```json
{
  "@context": "https://alphaalgo.org/contexts/scientific_research.jsonld",
  "@type": "ScientificPaper",
  "paper_id": "paper:eksft_2026",
  "title": "EKSFT: Entropy and KL-Divergence Selective Fine-Tuning",
  "mathematical_formulation": {
    "objective_function": "L_EKSFT = L_SFT * M(s)",
    "parameters": [
      {
        "symbol": "M(s)",
        "definition": "Token mask matrix based on thresholds",
        "type": "Tensor"
      },
      {
        "symbol": "H_t",
        "definition": "Entropy threshold boundary",
        "type": "Float",
        "default": 1.45
      },
      {
        "symbol": "D_KL",
        "definition": "KL Divergence threshold boundary",
        "type": "Float",
        "default": 0.05
      }
    ],
    "constraints": [
      "H_t > 0",
      "D_KL >= 0"
    ]
  },
  "architecture_specification": {
    "input_dimensions": "Variable",
    "layer_sequence": [
      {
        "layer_id": "tok_emb",
        "layer_type": "Embedding",
        "output_shape": [null, null, 4096]
      },
      {
        "layer_id": "mask_filter",
        "layer_type": "SelectiveMaskingLayer",
        "parameters": {
          "entropy_source": "logits",
          "kl_divergence_source": "ref_model"
        }
      }
    ]
  },
  "algorithmic_definition": {
    "steps": [
      {
        "step_num": 1,
        "description": "Forward pass to compute logits over reference model and target model.",
        "preconditions": ["valid_token_sequence"],
        "postconditions": ["logits_computed"]
      },
      {
        "step_num": 2,
        "description": "Calculate localized per-token entropy and Kullback-Leibler Divergence.",
        "preconditions": ["logits_computed"],
        "postconditions": ["entropy_and_kl_computed"]
      },
      {
        "step_num": 3,
        "description": "Apply binary mask where token entropy exceeds H_t or KL-div exceeds D_KL.",
        "preconditions": ["entropy_and_kl_computed"],
        "postconditions": ["mask_applied"]
      }
    ]
  },
  "evaluation_baselines": {
    "benchmark_dataset": "DeepWeb-Bench",
    "metrics": {
      "accuracy": 0.824,
      "latency_ms": 12.4
    }
  },
  "implementation_roadmap": {
    "isolation_level": "Level2",
    "target_files": [
      "trading_bot/learning/eksft.py"
    ],
    "verification_test": "tests/test_eksft_selective_masking.py"
  }
}
```

---

### 3. Pipeline Extraction Logic
The RUD runs a highly structured, multi-agent parse-and-validate process:

```
+--------------------+      +--------------------+      +--------------------+
|  PDF/Text Ingest   | ---> | Math Parse Agent   | ---> | Algo Validation    |
|  (Raw paper data)  |      | (Sympy extraction) |      | (Type-checks MASS) |
+--------------------+      +--------------------+      +--------------------+
                                      |                            |
                                      v                            v
                            +--------------------+      +--------------------+
                            | Architecture Agent | ---> | Output Validation  |
                            | (Sequence mapper)  |      | (Saves JSON-LD)    |
                            +--------------------+      +--------------------+
```

1. **Structured Ingestion**: Raw text is normalized, stripping math formatting irregularities (e.g. converting multi-line LaTeX equations to explicit SymPy expressions).
2. **SymPy Formulation Check**: The Math Parse Agent tries to parse equations into symbolic algebraic definitions (using SymPy packages). If an equation is mathematically inconsistent or contains undefined variables, the paper is flagged for manual verification or prompt re-evaluation.
3. **Architecture Extraction**: Maps structural diagrams and text descriptions of layers, parameter counts, memory caching mechanisms, and routing depths.
4. **Implementation Path Generation**: Based on the dependencies of existing AlphaAlgo modules, the RUD dynamically determines which Python classes or modules are eligible to implement this paper's algorithms.

---

### 4. Machine-Readable Limitation Map
The RUD explicitly parses academic "Limitations" sections to build a safety envelope:
* **Volatility Constraints**: Does the algorithm assume stationarity of market regimes?
* **Liquidity Limits**: Does the strategy assume infinite depth of market order books?
* **Computation Restrictions**: Does the algorithm require continuous O(N^2) multi-hop reasoning over deep layers that violates institutional real-time latency SLAs?
* **Safety Boundaries**: Saves these limits directly inside the MASS metadata, triggering runtime warnings or simulation exclusions in the Opportunity and Experiment divisions.
