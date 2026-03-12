"""
Self-Checklist Core System - Comprehensive Self-Assessment Framework

This module provides self-assessment capabilities for the trading bot.
Covers: State Reflection, Context Recognition, Confidence Estimation,
Explainability, Mood Index, Memory System, Budgeting, Benchmarking.

Author: Trading Bot Team
Date: 2025-10-23
"""

import logging
import asyncio
from typing import Any, Dict, List
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from collections import deque

logger = logging.getLogger(__name__)


class SelfChecklistStatus(Enum):
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"


@dataclass
class SelfChecklistItem:
    name: str
    status: SelfChecklistStatus
    score: float
    timestamp: datetime = field(default_factory=datetime.now)
    details: Dict[str, Any] = field(default_factory=dict)
    recommendations: List[str] = field(default_factory=list)


class SelfStateReflection:
    """Bot reflects on its current operational state"""
    def __init__(self):
        try:
            self.state_history = deque(maxlen=100)
            self.state_changes = []
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    async def reflect_on_state(self) -> SelfChecklistItem:
        try:
            state_changes = len(self.state_changes)
            stability = 100 - min(100, state_changes * 10)
            return SelfChecklistItem(
                name="State Reflection",
                status=SelfChecklistStatus.HEALTHY if stability > 70 else SelfChecklistStatus.WARNING,
                score=stability,
                details={"state_changes": state_changes, "stability": stability}
            )
        except Exception as e:
            logger.error(f"Error in reflect_on_state: {e}")
            raise


class SelfContextRecognition:
    """Bot understands its operational context"""
    def __init__(self):
        try:
            self.context_history = deque(maxlen=100)
            self.market_regimes = []
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    async def recognize_context(self) -> SelfChecklistItem:
        try:
            context_clarity = 85 if self.market_regimes else 50
            return SelfChecklistItem(
                name="Context Recognition",
                status=SelfChecklistStatus.HEALTHY if context_clarity > 70 else SelfChecklistStatus.WARNING,
                score=context_clarity,
                details={"market_regimes": len(self.market_regimes)}
            )
        except Exception as e:
            logger.error(f"Error in recognize_context: {e}")
            raise


class SelfConfidenceEstimation:
    """Bot estimates confidence in its decisions"""
    def __init__(self):
        try:
            self.confidence_scores = deque(maxlen=1000)
            self.decision_outcomes = deque(maxlen=1000)
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    async def estimate_confidence(self) -> SelfChecklistItem:
        try:
            avg_confidence = sum(self.confidence_scores) / len(self.confidence_scores) if self.confidence_scores else 0
            return SelfChecklistItem(
                name="Confidence Estimation",
                status=SelfChecklistStatus.HEALTHY if avg_confidence > 0.7 else SelfChecklistStatus.WARNING,
                score=avg_confidence * 100,
                details={"avg_confidence": avg_confidence, "decisions": len(self.confidence_scores)}
            )
        except Exception as e:
            logger.error(f"Error in estimate_confidence: {e}")
            raise


class SelfExplainability:
    """Bot explains its own decisions"""
    def __init__(self):
        try:
            self.decision_explanations = deque(maxlen=1000)
            self.explanation_quality = deque(maxlen=100)
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    async def check_explainability(self) -> SelfChecklistItem:
        try:
            avg_quality = sum(self.explanation_quality) / len(self.explanation_quality) if self.explanation_quality else 0
            return SelfChecklistItem(
                name="Explainability",
                status=SelfChecklistStatus.HEALTHY if avg_quality > 0.7 else SelfChecklistStatus.WARNING,
                score=avg_quality * 100,
                details={"explanations": len(self.decision_explanations), "quality": avg_quality}
            )
        except Exception as e:
            logger.error(f"Error in check_explainability: {e}")
            raise


class SelfMoodIndex:
    """Bot tracks its operational mood/sentiment"""
    def __init__(self):
        try:
            self.mood_history = deque(maxlen=1000)
            self.mood_factors = {}
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    async def calculate_mood(self) -> SelfChecklistItem:
        try:
            current_mood = self.mood_history[-1] if self.mood_history else 0.5
            mood_score = current_mood * 100
            return SelfChecklistItem(
                name="Mood Index",
                status=SelfChecklistStatus.HEALTHY if mood_score > 60 else SelfChecklistStatus.WARNING,
                score=mood_score,
                details={"mood": current_mood, "factors": len(self.mood_factors)}
            )
        except Exception as e:
            logger.error(f"Error in calculate_mood: {e}")
            raise


class SelfMemorySystem:
    """Bot manages its own memory and learning history"""
    def __init__(self):
        try:
            self.short_term_memory = deque(maxlen=100)
            self.long_term_memory = {}
            self.memory_efficiency = 0.8
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    async def check_memory(self) -> SelfChecklistItem:
        try:
            efficiency = self.memory_efficiency * 100
            return SelfChecklistItem(
                name="Memory System",
                status=SelfChecklistStatus.HEALTHY if efficiency > 70 else SelfChecklistStatus.WARNING,
                score=efficiency,
                details={"st_memory": len(self.short_term_memory), "lt_memory": len(self.long_term_memory)}
            )
        except Exception as e:
            logger.error(f"Error in check_memory: {e}")
            raise


class SelfBudgeting:
    """Bot manages its own capital and risk budget"""
    def __init__(self):
        try:
            self.capital_allocated = 0
            self.capital_available = 10000
            self.risk_budget_used = 0
            self.risk_budget_total = 100
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    async def check_budget(self) -> SelfChecklistItem:
        try:
            capital_util = (self.capital_allocated / self.capital_available * 100) if self.capital_available > 0 else 0
            budget_health = 100 - abs(capital_util - 50) / 50 * 50
            return SelfChecklistItem(
                name="Budgeting",
                status=SelfChecklistStatus.HEALTHY if budget_health > 70 else SelfChecklistStatus.WARNING,
                score=budget_health,
                details={"capital_util": capital_util, "risk_util": self.risk_budget_used / self.risk_budget_total * 100}
            )
        except Exception as e:
            logger.error(f"Error in check_budget: {e}")
            raise


class SelfBenchmarking:
    """Bot compares itself against benchmarks"""
    def __init__(self):
        try:
            self.performance_history = deque(maxlen=1000)
            self.benchmark_returns = 0.05
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    async def benchmark_performance(self) -> SelfChecklistItem:
        try:
            if self.performance_history:
                avg_return = sum(self.performance_history) / len(self.performance_history)
                outperf = (avg_return - self.benchmark_returns) / self.benchmark_returns * 100 if self.benchmark_returns > 0 else 0
            else:
                outperf = 0
            benchmark_score = min(100, max(0, 50 + outperf))
            return SelfChecklistItem(
                name="Benchmarking",
                status=SelfChecklistStatus.HEALTHY if benchmark_score > 60 else SelfChecklistStatus.WARNING,
                score=benchmark_score,
                details={"outperformance": outperf}
            )
        except Exception as e:
            logger.error(f"Error in benchmark_performance: {e}")
            raise
