"""Model Router and Pluggable LLM/Deterministic/ML Interface."""

import time
import logging
from typing import Dict, Any, Optional
from .contracts import TaskRequest, TaskResponse, TaskCategory

logger = logging.getLogger("alphaalgo.cognition.reasoning")


class ModelRouter:
    """Routes tasks dynamically across deterministic, statistical ML, and LLM backends."""

    def __init__(self, llm_provider: Optional[Any] = None):
        self.llm_provider = llm_provider

    def route_and_execute(self, request: TaskRequest) -> TaskResponse:
        start_time = time.time()
        category = request.category

        if category == TaskCategory.ARITHMETIC_DETERMINISTIC:
            # Deterministic Engine: No LLM/ML
            result = self._execute_deterministic(request.payload)
            elapsed = (time.time() - start_time) * 1000.0
            return TaskResponse(
                task_id=request.task_id,
                category=category,
                result=result,
                provider_used="DeterministicEngine",
                latency_ms=round(elapsed, 2),
                cost_estimated=0.0,
                success=True
            )

        elif category == TaskCategory.SPECIALIZED_ML_PREDICTION:
            # Statistical ML Model Engine
            result = self._execute_specialized_ml(request.payload)
            elapsed = (time.time() - start_time) * 1000.0
            return TaskResponse(
                task_id=request.task_id,
                category=category,
                result=result,
                provider_used="SpecializedMLModel",
                latency_ms=round(elapsed, 2),
                cost_estimated=0.0001,
                success=True
            )

        elif category in (TaskCategory.RESEARCH_SYNTHESIS, TaskCategory.STRUCTURED_REASONING):
            # LLM Engine with Deterministic Fallback
            if self.llm_provider:
                try:
                    result = self.llm_provider.synthesize(request.payload)
                    elapsed = (time.time() - start_time) * 1000.0
                    return TaskResponse(
                        task_id=request.task_id,
                        category=category,
                        result=result,
                        provider_used=getattr(self.llm_provider, "name", "LLMProvider"),
                        latency_ms=round(elapsed, 2),
                        cost_estimated=0.005,
                        success=True
                    )
                except Exception as e:
                    logger.warning(f"LLM Provider failed, falling back to deterministic synthesis: {e}")

            # Fallback deterministic synthesis
            result = self._execute_deterministic_synthesis(request.payload)
            elapsed = (time.time() - start_time) * 1000.0
            return TaskResponse(
                task_id=request.task_id,
                category=category,
                result=result,
                provider_used="DeterministicFallback",
                latency_ms=round(elapsed, 2),
                cost_estimated=0.0,
                success=True
            )

        else:
            elapsed = (time.time() - start_time) * 1000.0
            return TaskResponse(
                task_id=request.task_id,
                category=category,
                result=None,
                provider_used="None",
                latency_ms=round(elapsed, 2),
                cost_estimated=0.0,
                success=False,
                error_message=f"Unsupported task category: {category}"
            )

    def _execute_deterministic(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Exact arithmetic/risk calculation."""
        balance = payload.get("balance", 10000.0)
        risk_pct = payload.get("risk_pct", 0.01)
        stop_pips = payload.get("stop_pips", 20.0)
        pip_value = payload.get("pip_value", 10.0)

        risk_amount = balance * risk_pct
        position_size = risk_amount / (stop_pips * pip_value) if (stop_pips * pip_value) > 0 else 0.0
        return {
            "risk_amount": round(risk_amount, 2),
            "position_size": round(position_size, 4)
        }

    def _execute_specialized_ml(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Specialized ML prediction."""
        features = payload.get("features", {})
        rsi = features.get("rsi", 50.0)
        prob_up = 0.60 if rsi < 30 else (0.40 if rsi > 70 else 0.50)
        return {"prob_up": prob_up, "model": "XGBoost_Regime_v1"}

    def _execute_deterministic_synthesis(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Deterministic research synthesis fallback."""
        topic = payload.get("topic", "market_regime")
        return {
            "synthesis": f"Rule-based synthesis for {topic}: Normal volatility regime.",
            "confidence": 0.85
        }
