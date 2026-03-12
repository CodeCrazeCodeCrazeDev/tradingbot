"""
Structured Trade Logger

Logs every trade with full context including SHAP attribution for debugging.
"""

import json
import uuid
import logging
from datetime import datetime
from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Optional
from pathlib import Path

try:
    import shap
    import numpy as np
    SHAP_AVAILABLE = True
except ImportError:
    SHAP_AVAILABLE = False

logger = logging.getLogger(__name__)


@dataclass
class TradeInputs:
    """Input features and context for a trade."""
    features: Dict[str, float]
    news_sentiment: Dict[str, Any]
    price_history: List[float]
    market_regime: str
    timestamp: str


@dataclass
class ModelOutputs:
    """Model predictions and attributions."""
    policy: str  # long, short, hold
    q_values: Dict[str, float]
    confidence: float
    feature_importance: Dict[str, float]
    shap_values: Optional[Dict[str, float]] = None


@dataclass
class ExecutionDetails:
    """Trade execution information."""
    requested_lots: float
    executed_lots: float
    slippage_pips: float
    fill_price: float
    ticket: int
    execution_time_ms: float


@dataclass
class TradeOutcome:
    """Trade outcome and performance."""
    pnl: float
    duration_minutes: int
    exit_reason: str
    max_adverse_excursion: float
    max_favorable_excursion: float
    final_price: float


@dataclass
class StructuredTradeLog:
    """Complete structured trade log."""
    trade_id: str
    timestamp: str
    symbol: str
    inputs: TradeInputs
    model_outputs: ModelOutputs
    execution: ExecutionDetails
    outcome: Optional[TradeOutcome] = None


class StructuredTradeLogger:
    """
    Logs trades with full context for debugging and analysis.
    
    Features:
    - Complete input/output logging
    - SHAP value attribution
    - Trade outcome tracking
    - Automatic autopsy for losses
    """
    
    def __init__(self, log_dir: str = "logs/structured_trades"):
        """
        Initialize structured trade logger.
        
        Args:
            log_dir: Directory for trade logs
        """
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.open_trades: Dict[str, StructuredTradeLog] = {}
        
        if not SHAP_AVAILABLE:
            logger.warning("SHAP not available, attribution will be limited")
        
        logger.info(f"Structured Trade Logger initialized: {self.log_dir}")
    
    def log_trade_entry(
        self,
        symbol: str,
        features: Dict[str, float],
        model_outputs: Dict[str, Any],
        execution: Dict[str, Any],
        news_sentiment: Optional[Dict[str, Any]] = None,
        price_history: Optional[List[float]] = None,
        market_regime: str = "unknown"
    ) -> str:
        """
        Log trade entry with full context.
        
        Args:
            symbol: Trading symbol
            features: Input features
            model_outputs: Model predictions
            execution: Execution details
            news_sentiment: News sentiment data
            price_history: Recent price history
            market_regime: Current market regime
        
        Returns:
            Trade ID
        """
        trade_id = str(uuid.uuid4())
        
        # Compute SHAP values if model available
        shap_values = None
        if SHAP_AVAILABLE and 'model' in model_outputs:
            shap_values = self._compute_shap_values(features, model_outputs['model'])
        
        # Create trade log
        trade_log = StructuredTradeLog(
            trade_id=trade_id,
            timestamp=datetime.utcnow().isoformat(),
            symbol=symbol,
            inputs=TradeInputs(
                features=features,
                news_sentiment=news_sentiment or {},
                price_history=price_history or [],
                market_regime=market_regime,
                timestamp=datetime.utcnow().isoformat()
            ),
            model_outputs=ModelOutputs(
                policy=model_outputs.get('policy', 'unknown'),
                q_values=model_outputs.get('q_values', {}),
                confidence=model_outputs.get('confidence', 0.0),
                feature_importance=model_outputs.get('feature_importance', {}),
                shap_values=shap_values
            ),
            execution=ExecutionDetails(**execution)
        )
        
        self.open_trades[trade_id] = trade_log
        self._save_log(trade_log)
        
        logger.info(f"Trade entry logged: {trade_id} ({symbol} {model_outputs.get('policy')})")
        
        return trade_id
    
    def log_trade_exit(
        self,
        trade_id: str,
        pnl: float,
        exit_reason: str,
        final_price: float,
        max_adverse: float,
        max_favorable: float
    ):
        """
        Log trade exit and outcome.
        
        Args:
            trade_id: Trade ID from entry
            pnl: Profit/loss
            exit_reason: Reason for exit
            final_price: Final exit price
            max_adverse: Maximum adverse excursion
            max_favorable: Maximum favorable excursion
        """
        if trade_id not in self.open_trades:
            logger.error(f"Trade {trade_id} not found in open trades")
            return
        
        trade_log = self.open_trades[trade_id]
        entry_time = datetime.fromisoformat(trade_log.timestamp)
        duration = (datetime.utcnow() - entry_time).total_seconds() / 60
        
        trade_log.outcome = TradeOutcome(
            pnl=pnl,
            duration_minutes=int(duration),
            exit_reason=exit_reason,
            max_adverse_excursion=max_adverse,
            max_favorable_excursion=max_favorable,
            final_price=final_price
        )
        
        self._save_log(trade_log)
        del self.open_trades[trade_id]
        
        logger.info(f"Trade exit logged: {trade_id} (PnL: ${pnl:.2f}, Duration: {duration:.0f}min)")
        
        # Trigger autopsy if loss
        if pnl < 0:
            logger.warning(f"Loss detected, triggering autopsy for {trade_id}")
            self._trigger_autopsy(trade_log)
    
    def _compute_shap_values(
        self,
        features: Dict[str, float],
        model: Any
    ) -> Optional[Dict[str, float]]:
        """
        Compute SHAP values for feature attribution.
        
        Args:
            features: Input features
            model: ML model
        
        Returns:
            Dictionary of SHAP values per feature
        """
        if not SHAP_AVAILABLE:
            return None
        try:
        
            feature_array = np.array([list(features.values())])
            feature_names = list(features.keys())
            
            # Try TreeExplainer first (for tree-based models)
            try:
                explainer = shap.TreeExplainer(model)
                shap_vals = explainer.shap_values(feature_array)
            except Exception:
                # Fallback to KernelExplainer
                explainer = shap.KernelExplainer(model.predict, feature_array)
                shap_vals = explainer.shap_values(feature_array)
            
            # Convert to dict
            if isinstance(shap_vals, list):
                shap_vals = shap_vals[0]  # For binary classification
            
            return dict(zip(feature_names, shap_vals[0]))
            
        except Exception as e:
            logger.error(f"SHAP computation failed: {e}")
            return None
    
    def _save_log(self, trade_log: StructuredTradeLog):
        """Save trade log to JSON file."""
        try:
            date_str = datetime.utcnow().strftime("%Y%m%d")
            log_file = self.log_dir / f"trades_{date_str}.jsonl"
            
            with open(log_file, 'a') as f:
                f.write(json.dumps(asdict(trade_log)) + '\n')
                
        except Exception as e:
            logger.error(f"Failed to save trade log: {e}")
    
    def _trigger_autopsy(self, trade_log: StructuredTradeLog):
        """Trigger post-trade autopsy for losing trades."""
        try:
            from .trade_autopsy import TradeAutopsy
            
            autopsy = TradeAutopsy()
            autopsy.analyze_failed_trade(trade_log)
            
        except Exception as e:
            logger.error(f"Autopsy failed: {e}")
    
    def get_trade_log(self, trade_id: str) -> Optional[StructuredTradeLog]:
        """Get trade log by ID."""
        return self.open_trades.get(trade_id)
    
    def get_open_trades(self) -> List[StructuredTradeLog]:
        """Get all open trades."""
        return list(self.open_trades.values())
