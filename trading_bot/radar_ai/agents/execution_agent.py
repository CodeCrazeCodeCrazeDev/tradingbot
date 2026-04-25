"""
Execution Agent - Order Management & Position Tracking
=======================================================

THE LAST STEP - Execution happens ONLY after all other stages complete.

CRITICAL: Rule 5 - Execution is the LAST step, not the first

Responsibilities:
- Order management
- Position tracking
- Performance attribution
- Retraining signals
- Outcome feedback loop
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
import uuid

logger = logging.getLogger(__name__)


class OrderStatus(Enum):
    """Order status"""
    PENDING = "pending"
    SUBMITTED = "submitted"
    FILLED = "filled"
    PARTIALLY_FILLED = "partially_filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"


@dataclass
class Order:
    """A trade order"""
    order_id: str
    timestamp: datetime
    symbol: str
    action: str  # 'buy' or 'sell'
    quantity: float
    price: float
    order_type: str  # 'market', 'limit', 'stop'
    status: OrderStatus = OrderStatus.PENDING
    filled_quantity: float = 0.0
    filled_price: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'order_id': self.order_id,
            'timestamp': self.timestamp.isoformat(),
            'symbol': self.symbol,
            'action': self.action,
            'quantity': self.quantity,
            'price': self.price,
            'order_type': self.order_type,
            'status': self.status.value,
            'filled_quantity': self.filled_quantity,
            'filled_price': self.filled_price,
        }


@dataclass
class Position:
    """A portfolio position"""
    position_id: str
    symbol: str
    quantity: float
    entry_price: float
    current_price: float
    unrealized_pnl: float
    realized_pnl: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'position_id': self.position_id,
            'symbol': self.symbol,
            'quantity': self.quantity,
            'entry_price': self.entry_price,
            'current_price': self.current_price,
            'unrealized_pnl': self.unrealized_pnl,
            'realized_pnl': self.realized_pnl,
        }


@dataclass
class ExecutionOutcome:
    """Outcome of an execution for feedback loop"""
    outcome_id: str
    timestamp: datetime
    order_id: str
    symbol: str
    action: str
    
    # Performance metrics
    entry_price: float
    exit_price: Optional[float]
    realized_pnl: Optional[float]
    holding_period_days: Optional[int]
    
    # Attribution
    strategy_used: str
    simulation_expected_pnl: float
    actual_vs_expected: Optional[float]
    
    # Retraining signal
    should_retrain: bool
    retrain_reason: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'outcome_id': self.outcome_id,
            'timestamp': self.timestamp.isoformat(),
            'order_id': self.order_id,
            'symbol': self.symbol,
            'action': self.action,
            'entry_price': self.entry_price,
            'exit_price': self.exit_price,
            'realized_pnl': self.realized_pnl,
            'holding_period_days': self.holding_period_days,
            'strategy_used': self.strategy_used,
            'simulation_expected_pnl': self.simulation_expected_pnl,
            'actual_vs_expected': self.actual_vs_expected,
            'should_retrain': self.should_retrain,
            'retrain_reason': self.retrain_reason,
        }


class ExecutionAgent:
    """
    Execution Agent - THE LAST STEP
    
    Handles order management, position tracking, and outcome attribution.
    
    ENFORCES RULE 5: Execution is the LAST step, not the first
    """
    
    def __init__(self, meta_orchestrator: Any):
        self.agent_id = f"EXEC-{uuid.uuid4().hex[:8]}"
        self.meta_orchestrator = meta_orchestrator
        
        # Register with orchestrator
        self.meta_orchestrator.register_agent("ExecutionAgent", self)
        
        # Order book
        self.orders: Dict[str, Order] = {}
        self.order_history: List[Order] = []
        
        # Positions
        self.positions: Dict[str, Position] = {}
        
        # Outcomes for feedback loop
        self.outcomes: List[ExecutionOutcome] = []
        
        # Metrics
        self.total_orders = 0
        self.filled_orders = 0
        self.rejected_orders = 0
        self.total_pnl = 0.0
        
        logger.info(f"ExecutionAgent initialized: {self.agent_id}")
    
    async def execute_trade(
        self,
        workflow_id: str,
        strategy_analysis: Dict[str, Any],
        simulation_result: Dict[str, Any],
        risk_adjudication: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Execute a trade - THE LAST STEP.
        
        This can ONLY be called after:
        1. Data Fusion
        2. Ontology Update
        3. Intelligence Analysis
        4. Strategy Research
        5. Simulation (REQUIRED)
        6. Risk Evaluation
        """
        # Request execution approval from orchestrator
        execution_plan = {
            'workflow_id': workflow_id,
            'symbol': strategy_analysis.get('symbol'),
            'action': strategy_analysis.get('recommended_action'),
            'simulation_verdict': simulation_result.get('simulation_verdict'),
            'risk_verdict': risk_adjudication.get('overall_verdict'),
        }
        
        approval_result = await self.meta_orchestrator.request_execution_approval(
            workflow_id=workflow_id,
            execution_plan=execution_plan,
        )
        
        if approval_result.get('status') != 'pending_approval':
            logger.error(f"Execution blocked: {approval_result.get('message')}")
            return {
                'status': 'blocked',
                'reason': approval_result.get('message'),
                'violations': approval_result.get('violations', []),
            }
        
        # Wait for approval (in production, this would be async)
        # For now, auto-approve if simulation and risk checks passed
        request_id = approval_result.get('request_id')
        
        if (simulation_result.get('proceed_to_execution') and 
            risk_adjudication.get('overall_verdict') in ['approved', 'conditional']):
            await self.meta_orchestrator.approve_request(request_id)
        else:
            await self.meta_orchestrator.reject_request(
                request_id,
                reason="Simulation or risk checks failed"
            )
            self.rejected_orders += 1
            return {
                'status': 'rejected',
                'reason': 'Failed simulation or risk checks',
            }
        
        # Create order
        symbol = strategy_analysis.get('symbol')
        action = strategy_analysis.get('recommended_action')
        
        if action == 'hold':
            return {'status': 'no_action', 'message': 'Strategy recommends hold'}
        
        # Get position size from risk adjudication
        position_size_limit = risk_adjudication.get('position_size_limit', 10000)
        price = strategy_analysis.get('entry_points', [100])[0]
        quantity = position_size_limit / price if price > 0 else 0
        
        order = Order(
            order_id=f"ORD-{uuid.uuid4().hex[:8]}",
            timestamp=datetime.now(timezone.utc),
            symbol=symbol,
            action=action,
            quantity=quantity,
            price=price,
            order_type='limit',
        )
        
        # Submit order (simulated)
        order.status = OrderStatus.SUBMITTED
        self.orders[order.order_id] = order
        self.total_orders += 1
        
        # Simulate fill
        await asyncio.sleep(0.1)
        order.status = OrderStatus.FILLED
        order.filled_quantity = quantity
        order.filled_price = price
        self.filled_orders += 1
        
        # Update positions
        await self._update_position(order)
        
        # Create outcome for feedback loop
        outcome = ExecutionOutcome(
            outcome_id=f"OUT-{uuid.uuid4().hex[:8]}",
            timestamp=datetime.now(timezone.utc),
            order_id=order.order_id,
            symbol=symbol,
            action=action,
            entry_price=price,
            exit_price=None,
            realized_pnl=None,
            holding_period_days=None,
            strategy_used=strategy_analysis.get('strategy_name', 'unknown'),
            simulation_expected_pnl=simulation_result.get('expected_pnl', 0),
            actual_vs_expected=None,
            should_retrain=False,
            retrain_reason="",
        )
        
        self.outcomes.append(outcome)
        
        logger.info(f"Executed trade: {action} {quantity:.2f} {symbol} @ {price:.2f}")
        
        return {
            'status': 'executed',
            'order': order.to_dict(),
            'outcome_id': outcome.outcome_id,
        }
    
    async def _update_position(self, order: Order):
        """Update position based on filled order"""
        symbol = order.symbol
        
        if symbol in self.positions:
            position = self.positions[symbol]
            
            if order.action == 'buy':
                # Add to position
                total_cost = position.quantity * position.entry_price + order.filled_quantity * order.filled_price
                total_quantity = position.quantity + order.filled_quantity
                position.entry_price = total_cost / total_quantity if total_quantity > 0 else 0
                position.quantity = total_quantity
            else:
                # Reduce/close position
                position.quantity -= order.filled_quantity
                
                if position.quantity <= 0:
                    # Position closed
                    del self.positions[symbol]
        else:
            # New position
            if order.action == 'buy':
                position = Position(
                    position_id=f"POS-{uuid.uuid4().hex[:8]}",
                    symbol=symbol,
                    quantity=order.filled_quantity,
                    entry_price=order.filled_price,
                    current_price=order.filled_price,
                    unrealized_pnl=0.0,
                )
                self.positions[symbol] = position
    
    async def update_positions(self, market_picture: Dict[str, Any]):
        """Update positions with current market prices"""
        prices = market_picture.get('prices', {})
        
        for symbol, position in self.positions.items():
            if symbol in prices:
                position.current_price = prices[symbol]
                position.unrealized_pnl = (position.current_price - position.entry_price) * position.quantity
    
    async def close_position(
        self,
        symbol: str,
        reason: str = "manual_close",
    ) -> Dict[str, Any]:
        """Close a position and record outcome"""
        if symbol not in self.positions:
            return {'status': 'error', 'message': 'Position not found'}
        
        position = self.positions[symbol]
        
        # Create close order
        order = Order(
            order_id=f"ORD-{uuid.uuid4().hex[:8]}",
            timestamp=datetime.now(timezone.utc),
            symbol=symbol,
            action='sell' if position.quantity > 0 else 'buy',
            quantity=abs(position.quantity),
            price=position.current_price,
            order_type='market',
            status=OrderStatus.FILLED,
            filled_quantity=abs(position.quantity),
            filled_price=position.current_price,
        )
        
        # Calculate realized PnL
        realized_pnl = position.unrealized_pnl
        self.total_pnl += realized_pnl
        
        # Update outcome
        for outcome in self.outcomes:
            if outcome.symbol == symbol and outcome.exit_price is None:
                outcome.exit_price = position.current_price
                outcome.realized_pnl = realized_pnl
                outcome.actual_vs_expected = realized_pnl - outcome.simulation_expected_pnl
                
                # Determine if retraining needed
                if abs(outcome.actual_vs_expected) > abs(outcome.simulation_expected_pnl) * 0.5:
                    outcome.should_retrain = True
                    outcome.retrain_reason = f"Actual PnL deviated {outcome.actual_vs_expected:.2f} from expected"
                
                break
        
        # Remove position
        del self.positions[symbol]
        
        logger.info(f"Closed position: {symbol}, PnL: {realized_pnl:.2f}")
        
        return {
            'status': 'closed',
            'order': order.to_dict(),
            'realized_pnl': realized_pnl,
        }
    
    def get_retraining_signals(self) -> List[ExecutionOutcome]:
        """Get outcomes that signal need for retraining"""
        return [o for o in self.outcomes if o.should_retrain]
    
    def get_portfolio_summary(self) -> Dict[str, Any]:
        """Get portfolio summary"""
        total_value = sum(p.quantity * p.current_price for p in self.positions.values())
        total_unrealized_pnl = sum(p.unrealized_pnl for p in self.positions.values())
        
        return {
            'total_value': total_value,
            'total_unrealized_pnl': total_unrealized_pnl,
            'total_realized_pnl': self.total_pnl,
            'total_pnl': total_unrealized_pnl + self.total_pnl,
            'num_positions': len(self.positions),
            'positions': [p.to_dict() for p in self.positions.values()],
        }
    
    def get_status(self) -> Dict[str, Any]:
        """Get agent status"""
        return {
            'agent_id': self.agent_id,
            'total_orders': self.total_orders,
            'filled_orders': self.filled_orders,
            'rejected_orders': self.rejected_orders,
            'fill_rate': self.filled_orders / self.total_orders if self.total_orders > 0 else 0,
            'total_pnl': self.total_pnl,
            'active_positions': len(self.positions),
        }
