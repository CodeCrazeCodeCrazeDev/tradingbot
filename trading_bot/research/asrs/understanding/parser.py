import json
import os
from typing import Dict, Any, Optional

class ScientificPaperParser:
    """
    Decodes unstructured literature nodes into highly structured,
    Machine-Actionable Scientific Schemas (MASS) for downstream code generators.
    """
    def __init__(self, schemas_dir: str = "alphaalgo_data/scientific_schemas/"):
        self.schemas_dir = schemas_dir
        os.makedirs(self.schemas_dir, exist_ok=True)

    def parse_paper_to_mass(self, paper_id: str) -> Dict[str, Any]:
        """Convert a paper node into a standardized MASS JSON specification."""
        mass_path = os.path.join(self.schemas_dir, f"{paper_id.replace(':', '_')}.json")
        if os.path.exists(mass_path):
            with open(mass_path, "r") as f:
                return json.load(f)

        # Default fallback extraction specifications for core papers
        if "eksft" in paper_id:
            mass = self._generate_eksft_mass()
        elif "discoloop" in paper_id:
            mass = self._generate_discoloop_mass()
        else:
            mass = self._generate_generic_mass(paper_id)

        with open(mass_path, "w") as f:
            json.dump(mass, f, indent=2)
        return mass

    def _generate_eksft_mass(self) -> Dict[str, Any]:
        return {
            "paper_id": "paper:eksft_2026",
            "title": "EKSFT: Entropy and KL-Divergence Selective Fine-Tuning",
            "mathematical_formulation": {
                "objective_function": "L_EKSFT = L_SFT * Mask(entropy, kl_div)",
                "parameters": [
                    {"symbol": "H_t", "definition": "Entropy threshold boundary", "type": "Float", "default": 1.45},
                    {"symbol": "D_KL", "definition": "KL-Divergence threshold boundary", "type": "Float", "default": 0.05}
                ],
                "constraints": ["H_t > 0", "D_KL >= 0"]
            },
            "algorithmic_definition": {
                "steps": [
                    {"step_num": 1, "description": "Compute token-level entropy and KL from baseline reference model."},
                    {"step_num": 2, "description": "Mask tokens exceeding both H_t and D_KL thresholds."},
                    {"step_num": 3, "description": "Update model weights using masked loss value."}
                ]
            },
            "limitations": {
                "regime_bounds": "Assumes standard market regime, may overfit on extreme trend regime transitions."
            },
            "implementation_roadmap": {
                "isolation_level": 2,
                "target_file": "trading_bot/learning/eksft.py",
                "test_file": "tests/test_eksft_selective_masking.py"
            }
        }

    def _generate_discoloop_mass(self) -> Dict[str, Any]:
        return {
            "paper_id": "paper:discoloop_2026",
            "title": "DiscoLoop: Recurrent Agentic Reasoner Core",
            "mathematical_formulation": {
                "objective_function": "S_k = tanh(W_s * h_k + W_e * e_k)",
                "parameters": [
                    {"symbol": "h_k", "definition": "Discrete reasoning state vector", "type": "Tensor"},
                    {"symbol": "e_k", "definition": "Continuous context state vector", "type": "Tensor"}
                ],
                "constraints": ["dimension(h_k) == dimension(e_k)"]
            },
            "algorithmic_definition": {
                "steps": [
                    {"step_num": 1, "description": "Project discrete channel outputs and continuous inputs into identical state dims."},
                    {"step_num": 2, "description": "Apply recurrent tanh gating transition."},
                    {"step_num": 3, "description": "Route back as persistent memory state S_k for next multi-hop epoch."}
                ]
            },
            "limitations": {
                "latency_cap_ms": 500
            },
            "implementation_roadmap": {
                "isolation_level": 2,
                "target_file": "trading_bot/core/csc/controller.py",
                "test_file": "tests/test_csc_discoloop_recurrence.py"
            }
        }

    def _generate_generic_mass(self, paper_id: str) -> Dict[str, Any]:
        return {
            "paper_id": paper_id,
            "title": f"Scientific extraction of {paper_id}",
            "mathematical_formulation": {
                "objective_function": "Y = f(X)",
                "parameters": [],
                "constraints": []
            },
            "algorithmic_definition": {"steps": []},
            "limitations": {},
            "implementation_roadmap": {
                "isolation_level": 1,
                "target_file": "trading_bot/config/config.yaml",
                "test_file": "tests/test_system_config_validation.py"
            }
        }
