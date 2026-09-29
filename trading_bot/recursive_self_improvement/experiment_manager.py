import hashlib
import inspect
import logging
import uuid
from typing import Any, Dict, List, Optional
from datetime import datetime
from .memory import ImprovementMemory
from .evaluation import EvaluationEngine

logger = logging.getLogger(__name__)

class ExperimentManager:
    """
    Handles the execution and monitoring of improvement experiments.
    Interfaces with backtesting and simulation environments.
    """

    def __init__(
        self,
        memory: ImprovementMemory,
        evaluation: EvaluationEngine,
        config: Optional[Dict[str, Any]] = None,
        simulation_runner: Any = None,
    ):
        self.memory = memory
        self.evaluation = evaluation
        self.config = config or {}
        self.simulation_runner = simulation_runner
        self.allow_synthetic_fallback = bool(self.config.get("allow_synthetic_fallback", False))
        self.active_experiments: Dict[str, Dict[str, Any]] = {}

    async def run_experiment(self, domain: str, hypothesis: str, parameters: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Setup and run an experiment.
        """
        experiment_id = f"EXP-{domain.upper()}-{uuid.uuid4().hex[:8]}"
        logger.info(f"Starting experiment {experiment_id} in domain {domain}")

        # 1. Record start
        self.memory.record_experiment(experiment_id, domain, hypothesis, parameters, context)

        self.active_experiments[experiment_id] = {
            "start_time": datetime.utcnow(),
            "domain": domain,
            "status": "running"
        }

        try:
            # 2. Run Backtest/Simulation (Mock for now, integrate with backtester later)
            results = await self._execute_simulation(domain, parameters)

            # 3. Evaluate results
            baseline = context.get("baseline_metrics", {}) if context else {}
            eval_report = self.evaluation.evaluate_improvement(baseline, results)
            # Promotion eligibility requires both a real improvement and a
            # deterministic evidence source: the injected replay runner is the
            # only promotable origin; synthetic/unmarked output stays diagnostic.
            if results.get("evidence_source") == "injected_replay_runner":
                eval_report["is_improved"] = bool(
                    eval_report.get("overall_score", 0.0) > self.evaluation.min_improvement_threshold
                    and not eval_report.get("regressions")
                )
                eval_report["promotion_eligible"] = eval_report["is_improved"]
            else:
                eval_report["promotion_eligible"] = False
            if results.get("evidence_source") == "synthetic_fallback":
                eval_report["is_improved"] = False
                eval_report["recommendation"] = "research_only_synthetic"
                eval_report["promotion_eligible"] = False

            # 4. Record results
            status = "completed" if eval_report["is_improved"] else "failed"
            score = eval_report["overall_score"]
            self.memory.update_experiment_result(experiment_id, status, score, {
                "metrics": results,
                "evaluation": eval_report
            })

            logger.info(f"Experiment {experiment_id} {status} with score {score:.4f}")
            return {
                "experiment_id": experiment_id,
                "status": status,
                "score": score,
                "evaluation": eval_report
            }

        except Exception as e:
            logger.error(f"Experiment {experiment_id} failed with error: {e}")
            self.memory.update_experiment_result(experiment_id, "error", 0.0, {"error": str(e)})
            return {"experiment_id": experiment_id, "status": "error", "error": str(e)}
        finally:
            if experiment_id in self.active_experiments:
                del self.active_experiments[experiment_id]

    async def _execute_simulation(self, domain: str, parameters: Dict[str, Any]) -> Dict[str, float]:
        """
        Internal dispatcher for different types of simulations.
        Integrates with the system's actual backtesting and validation engines.
        """
        logger.info(f"Executing simulation for {domain}")

        if self.simulation_runner is not None:
            result = self.simulation_runner(domain, parameters)
            if inspect.isawaitable(result):
                result = await result
            if not isinstance(result, dict):
                raise TypeError("simulation_runner must return a metrics dictionary")
            if not result.get("evidence_source"):
                result["evidence_source"] = "injected_replay_runner"
            result["promotion_eligible"] = False
            return result

        if not self.allow_synthetic_fallback:
            raise RuntimeError(
                "No deterministic simulation_runner configured; refusing to create "
                "promotion evidence from synthetic metrics."
            )

        # Explicitly labeled fallback for development smoke tests only. Its
        # stable hash makes tests reproducible, but it remains non-promotable.
        digest = hashlib.sha256(
            f"{domain}:{sorted(parameters.items())}".encode("utf-8")
        ).digest()
        offset = digest[0] / 2550.0
        return {
            "sharpe_ratio": 1.8 + offset,
            "total_return": 0.15 + offset / 10.0,
            "max_drawdown": 0.05 - offset / 20.0,
            "win_rate": 0.62 + offset / 10.0,
            "evidence_source": "synthetic_fallback",
            "promotion_eligible": False,
        }
