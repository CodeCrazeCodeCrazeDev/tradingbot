"""
Skill #31: Optimal Execution Scheduler
======================================

Schedules order execution to minimize market impact
using Almgren-Chriss framework.
"""

import numpy as np
from dataclasses import dataclass
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


@dataclass
class ExecutionSlice:
    """Single execution slice."""
    time: datetime
    quantity: float
    expected_price: float
    expected_impact: float


@dataclass
class ExecutionSchedule:
    """Complete execution schedule."""
    slices: List[ExecutionSlice]
    total_quantity: float
    expected_cost: float
    expected_impact: float
    risk_adjusted_cost: float


@dataclass
class OptimalExecutionResult:
    """Optimal execution result."""
    schedule: ExecutionSchedule
    urgency_parameter: float
    participation_rate: float
    trading_signal: str
    confidence: float


class OptimalExecutionScheduler:
    """Almgren-Chriss optimal execution scheduler."""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.risk_aversion = self.config.get('risk_aversion', 1e-6)
        self.temporary_impact = self.config.get('temporary_impact', 0.1)
        self.permanent_impact = self.config.get('permanent_impact', 0.01)
        logger.info("OptimalExecutionScheduler initialized")
    
    def schedule(
        self,
        quantity: float,
        duration_minutes: int,
        current_price: float,
        volatility: float,
        avg_volume: float
    ) -> OptimalExecutionResult:
        """Create optimal execution schedule."""
        # Number of slices
        num_slices = max(1, duration_minutes // 5)
        
        # Almgren-Chriss parameters
        kappa = self._calculate_kappa(volatility, avg_volume)
        
        # Optimal trajectory
        slices = self._calculate_trajectory(
            quantity, num_slices, current_price, kappa, volatility
        )
        
        # Calculate costs
        expected_impact = self._calculate_expected_impact(slices, avg_volume)
        expected_cost = sum(s.expected_impact for s in slices)
        risk_cost = self._calculate_risk_cost(slices, volatility)
        
        schedule = ExecutionSchedule(
            slices=slices,
            total_quantity=quantity,
            expected_cost=expected_cost,
            expected_impact=expected_impact,
            risk_adjusted_cost=expected_cost + risk_cost
        )
        
        urgency = self._calculate_urgency(volatility, avg_volume)
        participation = quantity / (avg_volume * duration_minutes / 60)
        
        signal = self._generate_signal(schedule, urgency, participation)
        confidence = self._calculate_confidence(participation, volatility)
        
        return OptimalExecutionResult(
            schedule=schedule,
            urgency_parameter=urgency,
            participation_rate=participation,
            trading_signal=signal,
            confidence=confidence
        )
    
    def _calculate_kappa(self, volatility: float, avg_volume: float) -> float:
        """Calculate urgency parameter kappa."""
        return np.sqrt(self.risk_aversion * volatility**2 / self.temporary_impact)
    
    def _calculate_trajectory(
        self,
        quantity: float,
        num_slices: int,
        price: float,
        kappa: float,
        volatility: float
    ) -> List[ExecutionSlice]:
        """Calculate optimal execution trajectory."""
        slices = []
        remaining = quantity
        now = datetime.now()
        
        for i in range(num_slices):
            # Exponential decay trajectory
            if kappa > 0:
                fraction = (1 - np.exp(-kappa * (i + 1) / num_slices)) / (1 - np.exp(-kappa))
            else:
                fraction = (i + 1) / num_slices
            
            target_executed = quantity * fraction
            slice_qty = target_executed - (quantity - remaining)
            
            # Expected impact
            impact = self.temporary_impact * slice_qty / 1000 + self.permanent_impact * slice_qty / 1000
            expected_price = price * (1 + impact * np.sign(quantity))
            
            slices.append(ExecutionSlice(
                time=now + timedelta(minutes=5 * i),
                quantity=slice_qty,
                expected_price=expected_price,
                expected_impact=impact * abs(slice_qty)
            ))
            
            remaining -= slice_qty
        
        return slices
    
    def _calculate_expected_impact(self, slices: List[ExecutionSlice], avg_volume: float) -> float:
        """Calculate total expected market impact."""
        return sum(s.expected_impact for s in slices)
    
    def _calculate_risk_cost(self, slices: List[ExecutionSlice], volatility: float) -> float:
        """Calculate execution risk cost."""
        remaining_qty = sum(s.quantity for s in slices)
        risk = 0
        for s in slices:
            risk += remaining_qty**2 * volatility**2
            remaining_qty -= s.quantity
        return self.risk_aversion * risk
    
    def _calculate_urgency(self, volatility: float, avg_volume: float) -> float:
        """Calculate urgency parameter."""
        return volatility * 100
    
    def _generate_signal(
        self,
        schedule: ExecutionSchedule,
        urgency: float,
        participation: float
    ) -> str:
        """Generate execution signal."""
        if participation > 0.2:
            return f"HIGH IMPACT: {participation:.0%} participation, split into {len(schedule.slices)} slices"
        elif participation > 0.05:
            return f"MODERATE: {participation:.0%} participation, expected cost {schedule.expected_cost:.4f}"
        return f"LOW IMPACT: {participation:.0%} participation, can execute quickly"
    
    def _calculate_confidence(self, participation: float, volatility: float) -> float:
        """Calculate confidence in schedule."""
        if participation > 0.3 or volatility > 0.05:
            return 0.5
        return 0.8
