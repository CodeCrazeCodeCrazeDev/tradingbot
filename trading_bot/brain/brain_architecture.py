"""
Elite Trading Bot - Brain Architecture
Central intelligence system coordinating all advanced capabilities
"""

from typing import Any, Dict, List, Optional
from dataclasses import dataclass
import logging
from datetime import datetime, timedelta
import asyncio
import threading
import queue
from enum import Enum
import time

# Import EliteBrainController from elite_brain module for re-export
try:
    from trading_bot.brain.elite_brain import EliteBrainController
except ImportError:
    # Fallback: create a simple EliteBrainController alias
    EliteBrainController = None

# Core components
from trading_bot.analysis.market_regime_detector import MarketRegimeDetector
from trading_bot.analysis.sentiment_analyzer import UnifiedSentimentAnalyzer
try:
    from trading_bot.analysis.alternative_data import AlternativeDataIntegrator
    ALTERNATIVE_DATA_AVAILABLE = True
except ImportError:
    ALTERNATIVE_DATA_AVAILABLE = False

try:
    from trading_bot.ml.multi_timeframe_rl import MultiTimeframeRL
    RL_AVAILABLE = True
except ImportError:
    RL_AVAILABLE = False
from trading_bot.risk.advanced_risk_manager import AdvancedRiskManager
from trading_bot.execution.market_impact import MarketImpactModel
from trading_bot.dashboard.performance_dashboard import PerformanceDashboard

# Advanced components
from trading_bot.advanced_features.liquidity_holography import LiquidityHolographyEngine
from trading_bot.advanced_features.institutional_footprint_dna import InstitutionalFootprintDNA
from trading_bot.advanced_features.volatility_impulse_vector import VolatilityImpulseVector
from trading_bot.advanced_features.fractal_momentum_divergence import FractalMomentumDivergence
try:
    from trading_bot.advanced_features.multi_agent_rl import MultiAgentRL
    MULTI_AGENT_RL_AVAILABLE = True
except ImportError:
    MULTI_AGENT_RL_AVAILABLE = False
from trading_bot.advanced_features.digital_twin import DigitalTwinSimulator
from trading_bot.advanced_features.quantum_computing import QuantumPortfolioOptimizer
from trading_bot.advanced_features.blockchain_validation import TradingPredictionSystem

# Position management
from trading_bot.position_manager import PositionManager, Position

# Self-improvement
try:
    from trading_bot.self_improvement import SelfImprovementEngine
    SELF_IMPROVEMENT_AVAILABLE = True
except ImportError:
    SELF_IMPROVEMENT_AVAILABLE = False

logger = logging.getLogger(__name__)


class DecisionState(Enum):
    """Decision state for the brain"""
    IDLE = 0
    ANALYZING = 1
    DECIDING = 2
    EXECUTING = 3
    MONITORING = 4
    LEARNING = 5


@dataclass
class BrainDecision:
    """Decision made by the brain"""
    symbol: str
    timestamp: datetime
    action: str  # 'buy', 'sell', 'hold'
    confidence: float
    size: float
    price: Optional[float]
    timeframe: str
    reasoning: List[str]
    components: Dict[str, float]  # Component contributions
    metadata: Dict[str, Any]


class EliteBrain:
    """
    Elite Trading Bot Brain Architecture
    
    The central intelligence system that coordinates all components
    and makes final trading decisions using a weighted ensemble approach.
    
    Features:
    - Multi-layer decision making
    - Adaptive component weighting
    - Self-optimization
    - Meta-learning
    - Explainable AI
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}

        # Initialize state
        self.state = DecisionState.IDLE
        self.last_decision_time = {}
        self.decision_history = []
        self.component_weights = {}
        self.performance_metrics = {}
        self.learning_rate = self.config.get('learning_rate', 0.01)
        
        # Initialize components
        self._initialize_components()
        
        # Initialize weights
        self._initialize_weights()
        
        # Decision queue
        self.decision_queue = queue.Queue()
        
        # Start monitoring thread
        self.running = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
        
        logger.info("Brain Architecture initialized")
    
    def _initialize_components(self):
        """Initialize all brain components"""
        # Core components
        self.market_regime = MarketRegimeDetector(self.config.get('market_regime_config'))
        self.sentiment = UnifiedSentimentAnalyzer(self.config.get('sentiment_config'))
        self.alternative_data = None
        if ALTERNATIVE_DATA_AVAILABLE:
            self.alternative_data = AlternativeDataIntegrator(self.config.get('alternative_data_config'))
        self.multi_timeframe_rl = None
        if RL_AVAILABLE:
            self.multi_timeframe_rl = MultiTimeframeRL(self.config.get('multi_timeframe_rl_config'))
        self.risk_manager = AdvancedRiskManager(self.config.get('risk_manager_config'))
        self.market_impact = MarketImpactModel(self.config.get('market_impact_config'))
        self.dashboard = PerformanceDashboard(self.config.get('dashboard_config'))
        
        # Advanced components
        self.liquidity_holography = LiquidityHolographyEngine(self.config.get('liquidity_holography_config'))
        self.institutional_dna = InstitutionalFootprintDNA(self.config.get('institutional_dna_config'))
        self.volatility_impulse = VolatilityImpulseVector(self.config.get('volatility_impulse_config'))
        self.fractal_momentum = FractalMomentumDivergence(self.config.get('fractal_momentum_config'))
        self.multi_agent_rl = None
        if MULTI_AGENT_RL_AVAILABLE:
            self.multi_agent_rl = MultiAgentRL(self.config.get('multi_agent_rl_config'))
        self.digital_twin = DigitalTwinSimulator(self.config.get('digital_twin_config'))
        self.quantum_optimizer = QuantumPortfolioOptimizer(self.config.get('quantum_optimizer_config'))
        self.blockchain_validator = TradingPredictionSystem(self.config.get('blockchain_validator_config', {}).get('db_path', 'trading_blockchain.db'))
        
        # Position management
        self.position_manager = PositionManager(self.config.get('position_manager', {
            'max_positions': 5,
            'max_positions_per_symbol': 1,
            'confidence_shift_threshold': 0.6,
            'low_confidence_threshold': 0.3,
            'max_position_age_hours': 24,
            'aged_position_confidence_threshold': 0.5
        }))
        
        # Self-improvement engine
        self.self_improvement = None
        if SELF_IMPROVEMENT_AVAILABLE and self.config.get('self_improvement_enabled', False):
            self.self_improvement = SelfImprovementEngine(self.config.get('self_improvement', {}))
            logger.info("Self-Improvement Engine enabled")
        
        # Store components in dictionary for easier access
        self.components = {
            'market_regime': self.market_regime,
            'sentiment': self.sentiment,
            'alternative_data': self.alternative_data,
            'multi_timeframe_rl': self.multi_timeframe_rl,
            'liquidity_holography': self.liquidity_holography,
            'institutional_dna': self.institutional_dna,
            'volatility_impulse': self.volatility_impulse,
            'fractal_momentum': self.fractal_momentum,
            'multi_agent_rl': self.multi_agent_rl
        }
    
    def _initialize_weights(self):
        """Initialize component weights"""
        # Default weights
        self.component_weights = {
            'market_regime': 0.15,
            'sentiment': 0.10,
            'alternative_data': 0.10,
            'multi_timeframe_rl': 0.15,
            'liquidity_holography': 0.10,
            'institutional_dna': 0.10,
            'volatility_impulse': 0.10,
            'fractal_momentum': 0.10,
            'multi_agent_rl': 0.10
        }
        
        # Override with config if provided
        if 'component_weights' in self.config:
            self.component_weights.update(self.config['component_weights'])
        
        # Normalize weights
        total_weight = sum(self.component_weights.values())
        for component in self.component_weights:
            self.component_weights[component] /= total_weight
    
    async def analyze_market(self, symbol: str, timeframes: List[str]) -> Dict[str, Any]:
        """
        Analyze market using all components
        
        Args:
            symbol: Symbol to analyze
            timeframes: Timeframes to analyze
            
        Returns:
            Dictionary with analysis results
        """
        self.state = DecisionState.ANALYZING
        
        # Collect analysis from all components
        results = {}
        
        # Run analyses in parallel
        tasks = [
            self._analyze_with_component('market_regime', symbol, timeframes),
            self._analyze_with_component('sentiment', symbol, timeframes),
            self._analyze_with_component('alternative_data', symbol, timeframes),
            self._analyze_with_component('multi_timeframe_rl', symbol, timeframes),
            self._analyze_with_component('liquidity_holography', symbol, timeframes),
            self._analyze_with_component('institutional_dna', symbol, timeframes),
            self._analyze_with_component('volatility_impulse', symbol, timeframes),
            self._analyze_with_component('fractal_momentum', symbol, timeframes),
            self._analyze_with_component('multi_agent_rl', symbol, timeframes)
        ]
        
        component_results = await asyncio.gather(*tasks)
        
        # Combine results
        for i, component in enumerate(self.component_weights.keys()):
            results[component] = component_results[i]
        
        return results
    
    async def _analyze_with_component(self, component_name: str, symbol: str, timeframes: List[str]) -> Dict[str, Any]:
        """Analyze market with a specific component"""
        component = self.components.get(component_name)
        if not component:
            return {}
        try:
        
            if component_name == 'market_regime':
                return await self.market_regime.detect_regime(symbol)
            elif component_name == 'sentiment':
                sentiment_results = await self.sentiment.analyze_sentiment([symbol])
                return sentiment_results.get(symbol, {})
            elif component_name == 'alternative_data':
                if self.alternative_data:
                    # Alternative data integrator may have different methods
                    if hasattr(self.alternative_data, 'get_signals'):
                        return await self.alternative_data.get_signals(symbol)
                    elif hasattr(self.alternative_data, 'analyze'):
                        return await self.alternative_data.analyze(symbol)
                return {}
            elif component_name == 'multi_timeframe_rl':
                if self.multi_timeframe_rl:
                    return self.multi_timeframe_rl.predict(symbol)
                return {}
            elif component_name == 'liquidity_holography':
                if hasattr(self.liquidity_holography, 'analyze_liquidity'):
                    return await self.liquidity_holography.analyze_liquidity(symbol, timeframes[0])
                return {}
            elif component_name == 'institutional_dna':
                return await self.institutional_dna.detect_patterns(symbol, timeframes)
            elif component_name == 'volatility_impulse':
                return await self.volatility_impulse.calculate_vector(symbol, timeframes)
            elif component_name == 'fractal_momentum':
                return await self.fractal_momentum.analyze_divergence(symbol, timeframes)
            elif component_name == 'multi_agent_rl':
                if self.multi_agent_rl:
                    return await self.multi_agent_rl.get_consensus(symbol)
                return {}
            else:
                return {}
        except Exception as e:
            logger.error("Error analyzing with %s: %s", component_name, e)
            return {}
    
    async def make_decision(self, symbol: str, timeframes: List[str]) -> BrainDecision:
        """
        Make trading decision using all components
        
        Args:
            symbol: Symbol to trade
            timeframes: Timeframes to analyze
            
        Returns:
            BrainDecision with trading action
        """
        self.state = DecisionState.DECIDING
        
        # Check if we should make a new decision
        if symbol in self.last_decision_time:
            time_since_last = datetime.now() - self.last_decision_time[symbol]
            min_interval = timedelta(minutes=self.config.get('min_decision_interval_minutes', 5))
            if time_since_last < min_interval:
                logger.debug("Skipping decision for %s, too soon after last decision", symbol)
                return None
        
        # Check position limits BEFORE analyzing (save computation)
        can_open, reason = self.position_manager.can_open_new_position(symbol)
        if not can_open:
            logger.info("Cannot open new position for %s: %s", symbol, reason)
            
            # If max positions reached, check if we should close a weak position
            if "Max positions reached" in reason:
                weakest = self.position_manager.get_weakest_position()
                if weakest:
                    logger.info("Found weakest position to potentially close: %s %s (confidence: %.2f)",
                               weakest.symbol, weakest.side, weakest.current_confidence)
                    # Note: Actual closing will happen after we analyze and confirm new signal is strong
        
        # Analyze market
        analysis = await self.analyze_market(symbol, timeframes)
        
        # Extract signals from each component
        signals = {}
        confidences = {}
        
        for component, result in analysis.items():
            signal = self._extract_signal(component, result)
            signals[component] = signal
            confidences[component] = result.get('confidence', 0.5)
        
        # Combine signals using weighted voting
        buy_vote = 0.0
        sell_vote = 0.0
        
        for component, signal in signals.items():
            weight = self.component_weights[component] * confidences[component]
            if signal == 'buy':
                buy_vote += weight
            elif signal == 'sell':
                sell_vote += weight
        
        # Determine action
        if buy_vote > sell_vote and buy_vote > 0.3:
            action = 'buy'
            confidence = buy_vote / (buy_vote + sell_vote) if buy_vote + sell_vote > 0 else 0.5
        elif sell_vote > buy_vote and sell_vote > 0.3:
            action = 'sell'
            confidence = sell_vote / (buy_vote + sell_vote) if buy_vote + sell_vote > 0 else 0.5
        else:
            action = 'hold'
            confidence = 1.0 - (buy_vote + sell_vote)
        
        # Get current price
        price = self._get_current_price(symbol, analysis)
        
        # Calculate position size
        size = self._calculate_position_size(symbol, action, confidence, analysis)
        
        # Create decision reasoning
        reasoning = self._generate_reasoning(action, signals, confidences, analysis)
        
        # Create decision
        decision = BrainDecision(
            symbol=symbol,
            timestamp=datetime.now(),
            action=action,
            confidence=confidence,
            size=size,
            price=price,
            timeframe=timeframes[0],
            reasoning=reasoning,
            components={component: signals[component] for component in signals},
            metadata={
                'analysis': analysis,
                'confidences': confidences,
                'buy_vote': buy_vote,
                'sell_vote': sell_vote
            }
        )
        
        # Store decision
        self.last_decision_time[symbol] = datetime.now()
        self.decision_history.append(decision)
        self.decision_queue.put(decision)
        
        # Validate and record decision with blockchain
        self._validate_decision(decision)
        
        return decision
    
    def _extract_signal(self, component: str, result: Dict[str, Any]) -> str:
        """Extract signal from component result"""
        if not result:
            return 'hold'
        
        if component == 'market_regime':
            regime = result.get('regime', '')
            if 'bull' in regime.lower():
                return 'buy'
            elif 'bear' in regime.lower():
                return 'sell'
            else:
                return 'hold'
        
        elif component == 'sentiment':
            signal_type = result.get('signal_type', '')
            if signal_type == 'bullish':
                return 'buy'
            elif signal_type == 'bearish':
                return 'sell'
            else:
                return 'hold'
        
        elif component == 'alternative_data':
            signal = result.get('signal', '')
            if signal == 'bullish':
                return 'buy'
            elif signal == 'bearish':
                return 'sell'
            else:
                return 'hold'
        
        elif component == 'multi_timeframe_rl':
            position = result.get('position', 0)
            if position > 0.1:
                return 'buy'
            elif position < -0.1:
                return 'sell'
            else:
                return 'hold'
        
        elif component == 'liquidity_holography':
            liquidity_imbalance = result.get('liquidity_imbalance', 0)
            if liquidity_imbalance > 0.2:
                return 'buy'
            elif liquidity_imbalance < -0.2:
                return 'sell'
            else:
                return 'hold'
        
        elif component == 'institutional_dna':
            pattern = result.get('pattern', '')
            if pattern in ['accumulation', 'smart_money_buying']:
                return 'buy'
            elif pattern in ['distribution', 'smart_money_selling']:
                return 'sell'
            else:
                return 'hold'
        
        elif component == 'volatility_impulse':
            vector = result.get('vector', 0)
            if vector > 0.5:
                return 'buy'
            elif vector < -0.5:
                return 'sell'
            else:
                return 'hold'
        
        elif component == 'fractal_momentum':
            divergence = result.get('divergence', '')
            if divergence == 'bullish':
                return 'buy'
            elif divergence == 'bearish':
                return 'sell'
            else:
                return 'hold'
        
        elif component == 'multi_agent_rl':
            consensus = result.get('consensus', '')
            if consensus == 'buy':
                return 'buy'
            elif consensus == 'sell':
                return 'sell'
            else:
                return 'hold'
        
        return 'hold'
    
    def _calculate_position_size(self, symbol: str, action: str, 
                               confidence: float, analysis: Dict[str, Dict[str, Any]]) -> float:
        """Calculate position size based on risk management"""
        if action == 'hold':
            return 0.0
        
        # Get account size
        account_size = self.config.get('account_size', 100000.0)
        
        # Get market regime
        regime = 'normal'
        if 'market_regime' in analysis:
            regime = analysis['market_regime'].get('regime', 'normal')
        
        # Get current price for position sizing
        price = self._get_current_price(symbol, analysis)
        
        # Calculate position size using risk manager
        if hasattr(self.risk_manager, 'calculate_position_size'):
            # Calculate stop loss (simplified - use 2% below entry)
            stop_loss = price * 0.98
            position_result = self.risk_manager.calculate_position_size(
                ticker=symbol,
                entry_price=price,
                stop_loss=stop_loss,
                account_size=account_size
            )
            position_size = position_result.get('position_size', 0.01) * confidence
        else:
            # Fallback: simple position sizing
            risk_amount = account_size * 0.01  # 1% risk
            position_size = risk_amount * confidence
        
        # Adjust for market impact
        price = self._get_current_price(symbol, analysis)
        impact = self.market_impact.estimate_market_impact(
            symbol=symbol,
            order_size=position_size,
            side=action,
            market_data={'price': price}
        )
        
        # Adjust position size if impact is too high
        if impact.get('market_impact_bps', 0) > 50:  # More than 50 bps impact
            position_size *= 0.8  # Reduce by 20%
        
        return position_size
    
    def _generate_reasoning(self, action: str, signals: Dict[str, str], 
                          confidences: Dict[str, float], 
                          analysis: Dict[str, Dict[str, Any]]) -> List[str]:
        """Generate reasoning for decision"""
        reasoning = []
        
        # Add overall decision
        reasoning.append(f"Decision: {action.upper()}")
        
        # Add component signals
        for component, signal in signals.items():
            if signal == action:
                reasoning.append(f"{component}: {signal.upper()} (confidence: {confidences.get(component, 0):.2f})")
        
        # Add supporting evidence
        if action == 'buy':
            if 'market_regime' in analysis and 'regime' in analysis['market_regime']:
                reasoning.append(f"Market regime: {analysis['market_regime']['regime']}")
            
            if 'sentiment' in analysis and 'score' in analysis['sentiment']:
                reasoning.append(f"Sentiment score: {analysis['sentiment']['score']:.2f}")
            
            if 'institutional_dna' in analysis and 'pattern' in analysis['institutional_dna']:
                reasoning.append(f"Institutional pattern: {analysis['institutional_dna']['pattern']}")
        
        elif action == 'sell':
            if 'market_regime' in analysis and 'regime' in analysis['market_regime']:
                reasoning.append(f"Market regime: {analysis['market_regime']['regime']}")
            
            if 'sentiment' in analysis and 'score' in analysis['sentiment']:
                reasoning.append(f"Sentiment score: {analysis['sentiment']['score']:.2f}")
            
            if 'volatility_impulse' in analysis and 'vector' in analysis['volatility_impulse']:
                reasoning.append(f"Volatility impulse: {analysis['volatility_impulse']['vector']:.2f}")
        
        return reasoning
    
    def _validate_decision(self, decision: BrainDecision):
        """Validate and record decision with blockchain"""
        try:
            # Convert decision to dictionary
            decision_dict = {
                'symbol': decision.symbol,
                'timestamp': decision.timestamp.isoformat(),
                'action': decision.action,
                'confidence': decision.confidence,
                'size': decision.size,
                'price': decision.price,
                'timeframe': decision.timeframe,
                'reasoning': decision.reasoning
            }
            
            # Record decision in blockchain
            if hasattr(self.blockchain_validator, 'record_prediction'):
                self.blockchain_validator.record_prediction(
                    symbol=decision.symbol,
                    prediction=decision_dict,
                    confidence=decision.confidence
                )
        except Exception as e:
            logger.error("Error validating decision: %s", e)
    
    def _monitor_loop(self):
        """Monitor loop for processing decisions"""
        while self.running:
            try:
                try:
                    # Check if there's a decision to process
                    decision = self.decision_queue.get(timeout=1)
                except queue.Empty:
                    time.sleep(0.1)
                    continue
                
                # Process decision
                self.state = DecisionState.MONITORING
                
                # Update dashboard
                self._update_dashboard(decision)
                
                # Simulate decision in digital twin
                self._simulate_decision(decision)
                
                # Learn from decision
                self._learn_from_decision(decision)
                
                self.decision_queue.task_done()
            
            except Exception as e:
                logger.error("Error in monitor loop: %s", e)
                time.sleep(1)
    
    def _update_dashboard(self, decision: BrainDecision):
        """Update dashboard with decision"""
        try:
            # Update metrics
            self.dashboard.update_metric('decision_confidence', decision.confidence)
            self.dashboard.update_metric('position_size', decision.size)
            
            # Add decision to dashboard
            self.dashboard.add_trade({
                'symbol': decision.symbol,
                'entry_time': decision.timestamp,
                'signal_type': decision.action,
                'entry_price': decision.price,
                'size': decision.size,
                'confidence': decision.confidence,
                'timeframe': decision.timeframe,
                'source': 'brain',
                'metadata': {
                    'reasoning': decision.reasoning,
                    'components': decision.components
                }
            })
        except Exception as e:
            logger.error("Error updating dashboard: %s", e)
    
    def _simulate_decision(self, decision: BrainDecision):
        """Simulate decision in digital twin"""
        try:
            # Simulate decision
            if hasattr(self.digital_twin, 'simulate_decision'):
                simulation_result = self.digital_twin.simulate_decision(
                    symbol=decision.symbol,
                    action=decision.action,
                    size=decision.size,
                    price=decision.price,
                    timeframe=decision.timeframe
                )
            else:
                simulation_result = {'reward': 0}
            
            # Store simulation result
            if decision.symbol not in self.performance_metrics:
                self.performance_metrics[decision.symbol] = []
            
            self.performance_metrics[decision.symbol].append({
                'timestamp': datetime.now(),
                'decision': decision,
                'simulation': simulation_result
            })
        except Exception as e:
            logger.error("Error simulating decision: %s", e)
    
    def _get_current_price(self, symbol: str, analysis: Dict[str, Any]) -> float:
        """
        Extract current price from analysis data
        
        Args:
            symbol: Symbol to get price for
            analysis: Analysis dictionary
            
        Returns:
            Current price (defaults to 100.0 if not found)
        """
        # Try to get price from various analysis components
        if 'market_data' in analysis and 'price' in analysis['market_data']:
            return float(analysis['market_data']['price'])
        elif 'price' in analysis:
            return float(analysis['price'])
        else:
            # Default fallback price
            logger.warning("Could not find price in analysis for %s, using default 100.0", symbol)
            return 100.0
    
    def _learn_from_decision(self, decision: BrainDecision):
        """Learn from decision and update component weights"""
        self.state = DecisionState.LEARNING
        
        try:
            # Get simulation result
            if decision.symbol in self.performance_metrics:
                simulation_results = self.performance_metrics[decision.symbol]
                if simulation_results:
                    latest_result = simulation_results[-1]
                    simulation = latest_result.get('simulation', {})
                    
                    # Calculate reward
                    reward = simulation.get('reward', 0)
                    
                    # Update component weights based on reward
                    for component, signal in decision.components.items():
                        if signal == decision.action:
                            # Increase weight for components that agreed with decision
                            self.component_weights[component] += self.learning_rate * reward
                        else:
                            # Decrease weight for components that disagreed
                            self.component_weights[component] -= self.learning_rate * reward
                    
                    # Normalize weights
                    total_weight = sum(self.component_weights.values())
                    for component in self.component_weights:
                        self.component_weights[component] /= total_weight
        except Exception as e:
            logger.error("Error learning from decision: %s", e)
    
    def optimize_portfolio(self, symbols: List[str], constraints: Dict[str, Any]) -> Dict[str, float]:
        """
        Optimize portfolio allocation using quantum computing
        
        Args:
            symbols: List of symbols to include in portfolio
            constraints: Optimization constraints
            
        Returns:
            Dictionary of symbol to allocation
        """
        try:
            # Optimize portfolio
            if hasattr(self.quantum_optimizer, 'optimize_portfolio'):
                # Create dummy returns data for optimization
                # In production, this would use actual historical returns
                import pandas as pd
                import numpy as np
                
                # Generate sample returns (would be real data in production)
                returns_data = {}
                for symbol in symbols:
                    returns_data[symbol] = np.random.normal(0.001, 0.02, 100)
                returns_df = pd.DataFrame(returns_data)
                
                # Call optimizer with returns parameter
                portfolio = self.quantum_optimizer.optimize_portfolio(
                    returns=returns_df,
                    constraints=constraints
                )
                
                # Extract weights from result
                if isinstance(portfolio, dict) and 'weights' in portfolio:
                    return portfolio['weights']
                elif hasattr(portfolio, 'weights'):
                    return dict(zip(symbols, portfolio.weights))
                else:
                    return portfolio
            else:
                # Fallback: equal weight
                return {symbol: 1.0 / len(symbols) for symbol in symbols}
        except Exception as e:
            logger.error("Error optimizing portfolio: %s", e)
            return {symbol: 1.0 / len(symbols) for symbol in symbols}
    
    async def update_open_positions(self):
        """
        Update all open positions with current market data and check for auto-close conditions.
        Should be called periodically (e.g., every 60 seconds).
        """
        for ticket_id, position in list(self.position_manager.positions.items()):
            try:
                # Re-analyze the symbol
                decision = await self.make_decision(position.symbol, ['H1'])
                
                if decision:
                    # Update position with current price and confidence
                    self.position_manager.update_position(
                        ticket_id,
                        decision.price,
                        decision.confidence
                    )
                    
                    # Check if position should be auto-closed
                    should_close, close_reason = self.position_manager.should_close_position(
                        position,
                        decision.confidence,
                        decision.action
                    )
                    
                    if should_close:
                        logger.info("Auto-closing position %s: %s", ticket_id, close_reason)
                        # Close position (would integrate with actual broker API)
                        await self._close_position(ticket_id, close_reason)
                        
            except Exception as e:
                logger.error("Error updating position %s: %s", ticket_id, e)
    
    async def _close_position(self, ticket_id: str, reason: str) -> bool:
        """
        Close a position.
        
        Args:
            ticket_id: Position ticket ID
            reason: Reason for closing
            
        Returns:
            True if closed successfully
        """
        try:
            # This would integrate with your actual broker connector
            # For now, just remove from position manager
            logger.info("Closing position %s: %s", ticket_id, reason)
            
            # Record in self-improvement if enabled
            if self.self_improvement and ticket_id in self.position_manager.positions:
                position = self.position_manager.positions[ticket_id]
                if position.unrealized_pnl < 0:  # Losing trade
                    # Trigger self-improvement analysis
                    logger.info("Triggering self-improvement for losing trade %s", ticket_id)
                    # Would call self_improvement.process_losing_trade() here
            
            self.position_manager.remove_position(ticket_id)
            return True
            
        except Exception as e:
            logger.error("Error closing position %s: %s", ticket_id, e)
            return False
    
    def get_system_status(self) -> Dict[str, Any]:
        """
        Get comprehensive system status.
        
        Returns:
            Dictionary with system status
        """
        position_status = self.position_manager.get_status()
        
        status = {
            'brain_state': self.state.name,
            'positions': position_status,
            'component_weights': self.component_weights,
            'decision_history_count': len(self.decision_history),
            'performance_metrics': {
                symbol: len(metrics) 
                for symbol, metrics in self.performance_metrics.items()
            }
        }
        
        # Add self-improvement status if enabled
        if self.self_improvement:
            status['self_improvement'] = self.self_improvement.get_status()
        
        return status
    
    def stop(self):
        """Stop brain architecture"""
        self.running = False
        if self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=5)
        logger.info("Brain Architecture stopped")


# Example usage
if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    # Create brain
    brain = EliteBrain()
    
    # Run async example
    async def main():
        # Make decision
        decision = await brain.make_decision('AAPL', ['1m', '5m', '15m', '1h'])
        
        logger.info(f"Decision: {decision.action}")
        logger.info(f"Confidence: {decision.confidence:.2f}")
        logger.info(f"Size: {decision.size:.2f}")
        logger.info("Reasoning:")
        for reason in decision.reasoning:
            logger.info(f"- {reason}")
        
        # Optimize portfolio
        portfolio = brain.optimize_portfolio(
            symbols=['AAPL', 'MSFT', 'GOOGL'],
            constraints={'risk_level': 'moderate'}
        )
        
        logger.info("\nPortfolio Allocation:")
        for symbol, allocation in portfolio.items():
            logger.info(f"{symbol}: {allocation:.2%}")
        
        # Stop brain
        brain.stop()
    
    asyncio.run(main())
