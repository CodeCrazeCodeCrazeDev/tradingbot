"""
AlphaAlgo Intelligence Hierarchy - Tier Structure
Multi-layer architecture for the AlphaAlgo trading system
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np
import pandas as pd
import logging

logger = logging.getLogger(__name__)


@dataclass
class SignalOutput:
    """Base class for tier signal outputs"""
    timestamp: pd.Timestamp
    signal_value: float  # -1.0 to 1.0 (sell to buy)
    confidence: float    # 0.0 to 1.0
    metadata: Dict[str, Any]


@dataclass
class MarketStateVector(SignalOutput):
    """Output from Tier 1: Technical Analysis"""
    trend_direction: float
    trend_strength: float
    volatility_state: str
    momentum: float
    fractal_dimension: float
    overbought_oversold: float


@dataclass
class OrderFlowIntelligence(SignalOutput):
    """Output from Tier 2: Order Flow Analysis"""
    buying_pressure: float
    selling_pressure: float
    institutional_activity: float
    volume_imbalance: float
    absorption_score: float
    iceberg_detected: bool


@dataclass
class MarketGeometryModel(SignalOutput):
    """Output from Tier 3: Market Structure"""
    key_levels: Dict[str, float]
    liquidity_zones: Dict[str, Tuple[float, float]]
    mean_reversion_probability: float
    statistical_edge: float
    market_efficiency: float


@dataclass
class RegimeContextVector(SignalOutput):
    """Output from Tier 4: Regime Detection"""
    regime_type: str
    regime_probability: float
    market_phase: str
    phase_probability: float
    optimal_policy: str
    shap_values: Dict[str, float]


@dataclass
class SentimentVector(SignalOutput):
    """Output from Tier 5: Sentiment Analysis"""
    market_sentiment: float
    fear_greed_index: float
    order_book_bias: float
    news_impact: float
    social_sentiment: float
    narrative_strength: float


@dataclass
class MacroContext(SignalOutput):
    """Output from Tier 6: Macro Analysis"""
    interest_rate_differential: float
    yield_curve_slope: float
    correlation_strength: Dict[str, float]
    risk_sentiment: str
    capital_flow_direction: str


@dataclass
class RiskParameters(SignalOutput):
    """Output from Tier 7: Risk Management"""
    position_size: float
    stop_loss_level: float
    take_profit_level: float
    max_drawdown_limit: float
    portfolio_var: float
    risk_reward_ratio: float


@dataclass
class ExecutionIntelligence(SignalOutput):
    """Output from Tier 8: Execution"""
    optimal_venue: str
    execution_algorithm: str
    expected_slippage: float
    execution_cost: float
    fill_probability: float
    performance_metrics: Dict[str, float]


@dataclass
class EliteBrainSignal(SignalOutput):
    """Output from Tier 9: Meta-Learning & Ensemble"""
    final_decision: str
    position_type: str
    ensemble_weights: Dict[str, float]
    uncertainty: float
    coherence_score: float
    explanation: Dict[str, Any]


class TierBase(ABC):
    """Base class for all tiers in the AlphaAlgo intelligence hierarchy"""
    
    def __init__(self, name: str, config: Optional[Dict[str, Any]] = None):
        self.name = name
        self.config = config or {}
        self.last_output = None
        self.is_initialized = False
        logger.info(f"Initializing {self.name}")
    
    @abstractmethod
    def process(self, market_data: pd.DataFrame, 
               previous_tier_output: Optional[SignalOutput] = None, 
               additional_inputs: Optional[Dict[str, Any]] = None) -> SignalOutput:
        """Process inputs and generate tier output"""
        pass
    
    def initialize(self) -> bool:
        """Initialize the tier components"""
        try:
            self._initialize_components()
            self.is_initialized = True
            logger.info(f"[OK] {self.name} initialized successfully")
            return True
        except Exception as e:
            logger.error(f"[ERROR] Failed to initialize {self.name}: {str(e)}")
            return False
    
    @abstractmethod
    def _initialize_components(self) -> None:
        """Initialize tier-specific components"""
        pass
    
    def validate_input(self, market_data: pd.DataFrame) -> bool:
        """Validate input data"""
        if market_data is None or market_data.empty:
            logger.warning(f"Empty market data provided to {self.name}")
            return False
        
        required_columns = self.get_required_columns()
        missing_columns = [col for col in required_columns if col not in market_data.columns]
        
        if missing_columns:
            logger.warning(f"Missing required columns in {self.name}: {missing_columns}")
            return False
        
        return True
    
    def get_required_columns(self) -> List[str]:
        """Get required columns for this tier"""
        return ['open', 'high', 'low', 'close', 'volume']
    
    def __str__(self) -> str:
        return f"{self.name} (initialized: {self.is_initialized})"


class AlphaBrain:
    """
    AlphaAlgo's Elite Brain
    Manages the full intelligence hierarchy and decision flow
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.tiers = {}
        self.last_decision = None
        self.performance_history = []
        logger.info("Initializing AlphaBrain")
    
    def initialize_tiers(self) -> bool:
        """Initialize all tiers in the hierarchy"""
        try:
            # Import tier implementations
            from trading_bot.brain.tier1_technical import Tier1TechnicalAnalysis
            from trading_bot.brain.tier2_orderflow import Tier2OrderFlowIntelligence
            from trading_bot.brain.tier3_structure import Tier3MarketStructure
            from trading_bot.brain.tier4_regime import Tier4RegimeDetection
            from trading_bot.brain.tier5_sentiment import Tier5SentimentAnalysis
            from trading_bot.brain.tier6_macro import Tier6MacroContext
            from trading_bot.brain.tier7_risk import Tier7RiskManagement
            from trading_bot.brain.tier8_execution import Tier8ExecutionIntelligence
            from trading_bot.brain.tier9_metalearning import Tier9MetaLearning
            
            # Create tier instances
            self.tiers = {
                1: Tier1TechnicalAnalysis(config=self.config.get('tier1', {})),
                2: Tier2OrderFlowIntelligence(config=self.config.get('tier2', {})),
                3: Tier3MarketStructure(config=self.config.get('tier3', {})),
                4: Tier4RegimeDetection(config=self.config.get('tier4', {})),
                5: Tier5SentimentAnalysis(config=self.config.get('tier5', {})),
                6: Tier6MacroContext(config=self.config.get('tier6', {})),
                7: Tier7RiskManagement(config=self.config.get('tier7', {})),
                8: Tier8ExecutionIntelligence(config=self.config.get('tier8', {})),
                9: Tier9MetaLearning(config=self.config.get('tier9', {}))
            }
            
            # Initialize each tier
            for tier_num, tier in self.tiers.items():
                if not tier.initialize():
                    logger.error(f"Failed to initialize Tier {tier_num}")
                    return False
            
            logger.info("[OK] All tiers initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"[ERROR] Failed to initialize tiers: {str(e)}")
            return False
    
    def process_market_data(self, market_data: pd.DataFrame, 
                           additional_inputs: Optional[Dict[str, Any]] = None) -> EliteBrainSignal:
        """
        Process market data through all tiers and generate a trading decision
        
        Args:
            market_data: DataFrame with OHLCV data
            additional_inputs: Additional inputs like news, sentiment, etc.
            
        Returns:
            EliteBrainSignal with the final trading decision
        """
        if not self.tiers:
            logger.error("Tiers not initialized. Call initialize_tiers() first.")
            return None
        try:
        
            # Process through each tier sequentially
            tier_outputs = {}
            previous_output = None
            
            for tier_num in range(1, 10):
                tier = self.tiers.get(tier_num)
                if not tier:
                    logger.error(f"Tier {tier_num} not found")
                    continue
                
                logger.debug(f"Processing Tier {tier_num}: {tier.name}")
                tier_output = tier.process(
                    market_data=market_data,
                    previous_tier_output=previous_output,
                    additional_inputs=additional_inputs
                )
                
                tier_outputs[tier_num] = tier_output
                previous_output = tier_output
            
            # Final output is from Tier 9
            final_output = tier_outputs.get(9)
            self.last_decision = final_output
            
            logger.info(f"Decision: {final_output.final_decision} | "
                       f"Confidence: {final_output.confidence:.2%} | "
                       f"Regime: {tier_outputs.get(4).regime_type}")
            
            return final_output
            
        except Exception as e:
            logger.error(f"❌ Error processing market data: {str(e)}")
            return None
    
    def update_performance(self, trade_result: Dict[str, Any]) -> None:
        """
        Update performance metrics after a trade
        
        Args:
            trade_result: Dictionary with trade outcome information
        """
        self.performance_history.append(trade_result)
        
        # Update Tier 9 (Meta-Learning) with performance feedback
        if 9 in self.tiers:
            meta_learning_tier = self.tiers[9]
            meta_learning_tier.update_from_feedback(trade_result)
    
    def get_explanation(self) -> Dict[str, Any]:
        """
        Get explanation for the last decision
        
        Returns:
            Dictionary with SHAP values and other explanatory information
        """
        if not self.last_decision:
            return {"error": "No decision has been made yet"}
        
        return {
            "decision": self.last_decision.final_decision,
            "confidence": self.last_decision.confidence,
            "explanation": self.last_decision.explanation,
            "shap_values": self.last_decision.explanation.get("shap_values", {})
        }
    
    def __str__(self) -> str:
        return f"AlphaBrain with {len(self.tiers)} tiers"


# Example usage
if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.INFO, 
                      format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # Create sample data
    dates = pd.date_range('2024-01-01', periods=100, freq='1H')
    df = pd.DataFrame({
        'open': np.random.randn(100).cumsum() + 100,
        'high': np.random.randn(100).cumsum() + 102,
        'low': np.random.randn(100).cumsum() + 98,
        'close': np.random.randn(100).cumsum() + 100,
        'volume': np.random.randint(1000, 10000, 100)
    }, index=dates)
    
    # Initialize AlphaBrain
    brain = AlphaBrain()
    brain.initialize_tiers()
    
    # Process market data
    decision = brain.process_market_data(df)
    
    # Get explanation
    explanation = brain.get_explanation()
    logger.info(f"\nDecision: {explanation['decision']}")
    logger.info(f"Confidence: {explanation['confidence']:.2%}")
    logger.info("\nTop factors:")
    for factor, value in sorted(explanation['shap_values'].items(), 
                              key=lambda x: abs(x[1]), reverse=True)[:5]:
        logger.info(f"- {factor}: {value:.4f}")
