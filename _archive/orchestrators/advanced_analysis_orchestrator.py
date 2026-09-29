"""
Advanced Analysis Orchestrator

Master coordinator for all advanced analysis modules:
- Hawkes Process for institutional detection
- Topological Data Analysis (TDA)
- LOB State Transition CNN
- Central Bank Policy Tracker
- Quantum-Enhanced RNG
- Options Hedging Execution
- Liquidity Holography
- Market Microbiome
- Proprietary Indicators
- Multi-Agent RL
- Hypernetwork Adaptation
- Digital Twin Simulation
- Feature Flag Framework

Provides unified interface for all advanced analysis capabilities.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
from collections import deque
import asyncio

logger = logging.getLogger(__name__)


class AnalysisModule(Enum):
    """Available analysis modules"""
    HAWKES_PROCESS = "hawkes_process"
    TOPOLOGICAL_ANALYSIS = "topological_analysis"
    LOB_CNN = "lob_cnn"
    CENTRAL_BANK = "central_bank"
    QUANTUM_RNG = "quantum_rng"
    OPTIONS_HEDGING = "options_hedging"
    LIQUIDITY_HOLOGRAPHY = "liquidity_holography"
    MARKET_MICROBIOME = "market_microbiome"
    PROPRIETARY_INDICATORS = "proprietary_indicators"
    MULTI_AGENT_RL = "multi_agent_rl"
    HYPERNETWORK = "hypernetwork"
    DIGITAL_TWIN = "digital_twin"
    FEATURE_FLAGS = "feature_flags"


@dataclass
class AnalysisResult:
    """Result from analysis module"""
    module: AnalysisModule
    timestamp: datetime
    signal: str  # BUY, SELL, HOLD, CAUTION
    confidence: float
    data: Dict[str, Any]
    reasoning: str
    
    def to_dict(self) -> Dict[str, Any]:
        """
        to_dict function.

    Auto-documented by QwenCodeMender.
        """
        return {
            'module': self.module.value,
            'timestamp': self.timestamp.isoformat(),
            'signal': self.signal,
            'confidence': self.confidence,
            'data': self.data,
            'reasoning': self.reasoning
        }


@dataclass
class UnifiedSignal:
    """Unified signal from all analysis modules"""
    timestamp: datetime
    direction: str  # BUY, SELL, HOLD
    confidence: float
    position_size_multiplier: float
    entry_price: Optional[float]
    stop_loss: Optional[float]
    take_profit: Optional[float]
    contributing_modules: List[str]
    dissenting_modules: List[str]
    risk_score: float
    reasoning: str
    module_results: List[AnalysisResult]
    
    def to_dict(self) -> Dict[str, Any]:
        """
        to_dict function.

    Auto-documented by QwenCodeMender.
        """
        return {
            'timestamp': self.timestamp.isoformat(),
            'direction': self.direction,
            'confidence': self.confidence,
            'position_size_multiplier': self.position_size_multiplier,
            'entry_price': self.entry_price,
            'stop_loss': self.stop_loss,
            'take_profit': self.take_profit,
            'contributing_modules': self.contributing_modules,
            'dissenting_modules': self.dissenting_modules,
            'risk_score': self.risk_score,
            'reasoning': self.reasoning
        }


class AdvancedAnalysisOrchestrator:
    """
    Advanced Analysis Orchestrator
    
    Coordinates all advanced analysis modules and provides
    unified trading signals.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # Module weights for signal aggregation
        self.module_weights = {
            AnalysisModule.HAWKES_PROCESS: 0.15,
            AnalysisModule.TOPOLOGICAL_ANALYSIS: 0.10,
            AnalysisModule.LOB_CNN: 0.12,
            AnalysisModule.CENTRAL_BANK: 0.08,
            AnalysisModule.LIQUIDITY_HOLOGRAPHY: 0.12,
            AnalysisModule.MARKET_MICROBIOME: 0.10,
            AnalysisModule.PROPRIETARY_INDICATORS: 0.13,
            AnalysisModule.MULTI_AGENT_RL: 0.15,
            AnalysisModule.HYPERNETWORK: 0.05,
        }
        
        # Initialize modules lazily
        self._modules: Dict[AnalysisModule, Any] = {}
        self._initialized = False
        
        # Analysis history
        self.analysis_history: deque = deque(maxlen=1000)
        self.signal_history: deque = deque(maxlen=500)
        
        # Feature flags
        self._feature_flags = None
        
        logger.info("AdvancedAnalysisOrchestrator created")
    
    def initialize(self):
        """Initialize all analysis modules"""
        if self._initialized:
            return
        
        logger.info("Initializing advanced analysis modules...")
        
        try:
            # Import and initialize modules
            from .hawkes_process import HawkesProcessDetector
            self._modules[AnalysisModule.HAWKES_PROCESS] = HawkesProcessDetector(self.config)
            logger.info("  - Hawkes Process: OK")
        except Exception as e:
            logger.warning(f"  - Hawkes Process: FAILED ({e})")

        try:
            from .topological_data_analysis import TopologicalAnalyzer
            self._modules[AnalysisModule.TOPOLOGICAL_ANALYSIS] = TopologicalAnalyzer(self.config)
            logger.info("  - Topological Analysis: OK")
        except Exception as e:
            logger.warning(f"  - Topological Analysis: FAILED ({e})")

        try:
            from .lob_cnn import LOBStateCNN
            self._modules[AnalysisModule.LOB_CNN] = LOBStateCNN(self.config)
            logger.info("  - LOB CNN: OK")
        except Exception as e:
            logger.warning(f"  - LOB CNN: FAILED ({e})")

        try:
            from .central_bank_tracker import CentralBankTracker
            self._modules[AnalysisModule.CENTRAL_BANK] = CentralBankTracker(self.config)
            logger.info("  - Central Bank Tracker: OK")
        except Exception as e:
            logger.warning(f"  - Central Bank Tracker: FAILED ({e})")

        try:
            from .quantum_rng import QuantumEnhancedRNG
            self._modules[AnalysisModule.QUANTUM_RNG] = QuantumEnhancedRNG(self.config)
            logger.info("  - Quantum RNG: OK")
        except Exception as e:
            logger.warning(f"  - Quantum RNG: FAILED ({e})")

        try:
            from .options_hedging import OptionsHedgingEngine
            self._modules[AnalysisModule.OPTIONS_HEDGING] = OptionsHedgingEngine(self.config)
            logger.info("  - Options Hedging: OK")
        except Exception as e:
            logger.warning(f"  - Options Hedging: FAILED ({e})")

        try:
            from .liquidity_holography import LiquidityHolography
            self._modules[AnalysisModule.LIQUIDITY_HOLOGRAPHY] = LiquidityHolography(self.config)
            logger.info("  - Liquidity Holography: OK")
        except Exception as e:
            logger.warning(f"  - Liquidity Holography: FAILED ({e})")

        try:
            from .market_microbiome import MarketMicrobiome
            self._modules[AnalysisModule.MARKET_MICROBIOME] = MarketMicrobiome(self.config)
            logger.info("  - Market Microbiome: OK")
        except Exception as e:
            logger.warning(f"  - Market Microbiome: FAILED ({e})")

        try:
            from .proprietary_indicators import ProprietaryIndicators
            self._modules[AnalysisModule.PROPRIETARY_INDICATORS] = ProprietaryIndicators(self.config)
            logger.info("  - Proprietary Indicators: OK")
        except Exception as e:
            logger.warning(f"  - Proprietary Indicators: FAILED ({e})")

        try:
            from .multi_agent_rl import MultiAgentTradingSystem
            self._modules[AnalysisModule.MULTI_AGENT_RL] = MultiAgentTradingSystem(self.config)
            logger.info("  - Multi-Agent RL: OK")
        except Exception as e:
            logger.warning(f"  - Multi-Agent RL: FAILED ({e})")

        try:
            from .hypernetwork_adaptation import HypernetworkAdapter
            self._modules[AnalysisModule.HYPERNETWORK] = HypernetworkAdapter(self.config)
            logger.info("  - Hypernetwork Adapter: OK")
        except Exception as e:
            logger.warning(f"  - Hypernetwork Adapter: FAILED ({e})")

        try:
            from .digital_twin import DigitalTwinSimulator
            self._modules[AnalysisModule.DIGITAL_TWIN] = DigitalTwinSimulator(self.config)
            logger.info("  - Digital Twin: OK")
        except Exception as e:
            logger.warning(f"  - Digital Twin: FAILED ({e})")

        try:
            from .feature_flags import FeatureFlagFramework
            self._feature_flags = FeatureFlagFramework(self.config)
            self._modules[AnalysisModule.FEATURE_FLAGS] = self._feature_flags
            logger.info("  - Feature Flags: OK")
        except Exception as e:
            logger.warning(f"  - Feature Flags: FAILED ({e})")
        
        self._initialized = True
        logger.info(f"Initialized {len(self._modules)} analysis modules")
    
    def get_module(self, module: AnalysisModule) -> Optional[Any]:
        """Get specific analysis module"""
        if not self._initialized:
            self.initialize()
        return self._modules.get(module)
    
    async def analyze(
        self,
        symbol: str,
        market_data: Dict[str, Any],
        enabled_modules: Optional[List[AnalysisModule]] = None
    ) -> UnifiedSignal:
        """
        Run comprehensive analysis using all enabled modules
        
        Args:
            symbol: Trading symbol
            market_data: Market data dictionary
            enabled_modules: List of modules to use (None = all)
        """
        if not self._initialized:
            self.initialize()
        
        results: List[AnalysisResult] = []
        
        # Determine which modules to use
        modules_to_run = enabled_modules or list(self._modules.keys())
        
        # Check feature flags
        if self._feature_flags:
            modules_to_run = [
                m for m in modules_to_run
                if self._feature_flags.is_enabled(f"module_{m.value}", market_data)
                or m not in [AnalysisModule.FEATURE_FLAGS]  # Always run if no flag
            ]
        
        # Run each module
        for module in modules_to_run:
            if module not in self._modules:
                continue
            try:
            
                result = await self._run_module(module, symbol, market_data)
                if result:
                    results.append(result)
            except Exception as e:
                logger.error(f"Module {module.value} error: {e}")
        
        # Aggregate results
        unified = self._aggregate_results(results, market_data)
        
        # Store history
        self.analysis_history.extend(results)
        self.signal_history.append(unified)
        
        return unified
    
    async def _run_module(
        self,
        module: AnalysisModule,
        symbol: str,
        market_data: Dict[str, Any]
    ) -> Optional[AnalysisResult]:
        """Run single analysis module"""
        mod = self._modules.get(module)
        if not mod:
            return None
        try:
        
            if module == AnalysisModule.HAWKES_PROCESS:
                # Process order flow events
                events = market_data.get('events', [])
                signal = None
                for event in events[-10:]:  # Last 10 events
                    from .hawkes_process import MarketEvent, EventType
                    me = MarketEvent(
                        timestamp=datetime.now(),
                        event_type=EventType.TRADE,
                        price=event.get('price', 0),
                        volume=event.get('volume', 0),
                        side=event.get('side', 'BUY')
                    )
                    signal = mod.add_event(me)
                
                if signal:
                    return AnalysisResult(
                        module=module,
                        timestamp=datetime.now(),
                        signal='BUY' if signal.direction == 'ACCUMULATION' else 'SELL' if signal.direction == 'DISTRIBUTION' else 'HOLD',
                        confidence=signal.confidence,
                        data=signal.to_dict(),
                        reasoning=signal.reasoning
                    )
            
            elif module == AnalysisModule.TOPOLOGICAL_ANALYSIS:
                prices = market_data.get('prices', [])
                if len(prices) >= 50:
                    signature = mod.analyze(prices)
                    signal = 'BUY' if signature.pattern.value in ['trending', 'breakout'] else 'SELL' if signature.pattern.value == 'reversal' else 'HOLD'
                    return AnalysisResult(
                        module=module,
                        timestamp=datetime.now(),
                        signal=signal,
                        confidence=signature.confidence,
                        data=signature.to_dict(),
                        reasoning=f"Topological pattern: {signature.pattern.value}"
                    )
            
            elif module == AnalysisModule.LOB_CNN:
                prediction = mod.predict()
                if prediction:
                    signal = 'BUY' if prediction.predicted_move.value in ['up', 'strong_up'] else 'SELL' if prediction.predicted_move.value in ['down', 'strong_down'] else 'HOLD'
                    return AnalysisResult(
                        module=module,
                        timestamp=datetime.now(),
                        signal=signal,
                        confidence=prediction.confidence,
                        data=prediction.to_dict(),
                        reasoning=prediction.reasoning
                    )
            
            elif module == AnalysisModule.CENTRAL_BANK:
                signals = mod.get_trading_signals()
                if signals:
                    top_signal = signals[0]
                    return AnalysisResult(
                        module=module,
                        timestamp=datetime.now(),
                        signal=top_signal['direction'],
                        confidence=top_signal['confidence'],
                        data=top_signal,
                        reasoning=f"Policy divergence: {top_signal['reasoning']}"
                    )
            
            elif module == AnalysisModule.LIQUIDITY_HOLOGRAPHY:
                current_price = market_data.get('price', 0)
                if current_price > 0:
                    mod.update_current_price(current_price)
                    summary = mod.get_gravity_summary()
                    
                    # Determine signal from gravity
                    wells = summary.get('strongest_wells', [])
                    if wells:
                        nearest = wells[0]
                        if nearest['center_price'] > current_price:
                            signal = 'BUY'  # Gravity pulling up
                        else:
                            signal = 'SELL'  # Gravity pulling down
                    else:
                        signal = 'HOLD'
                    
                    return AnalysisResult(
                        module=module,
                        timestamp=datetime.now(),
                        signal=signal,
                        confidence=0.6,
                        data=summary,
                        reasoning=f"Liquidity gravity analysis"
                    )
            
            elif module == AnalysisModule.MARKET_MICROBIOME:
                orders = market_data.get('orders', [])
                if orders:
                    activities = mod.process_order_flow(orders)
                    state = mod.get_ecosystem_state()
                    
                    # Signal based on ecosystem
                    if state.health.value in ['thriving', 'recovering']:
                        signal = 'BUY' if state.dominant_species.value in ['institutional_whale', 'algo_momentum'] else 'HOLD'
                    else:
                        signal = 'CAUTION'
                    
                    return AnalysisResult(
                        module=module,
                        timestamp=datetime.now(),
                        signal=signal,
                        confidence=state.diversity_index,
                        data=state.to_dict(),
                        reasoning=f"Ecosystem health: {state.health.value}"
                    )
            
            elif module == AnalysisModule.PROPRIETARY_INDICATORS:
                prices = market_data.get('prices', np.array([]))
                if len(prices) > 20:
                    price_data = {
                        'high': prices * 1.01,
                        'low': prices * 0.99,
                        'close': prices
                    }
                    volume_data = {
                        'volume': market_data.get('volume', np.ones_like(prices) * 1000)
                    }
                    
                    results_dict = mod.calculate_all(
                        price_data, volume_data, {}, {}, {}
                    )
                    
                    if 'vii' in results_dict:
                        vii = results_dict['vii']
                        return AnalysisResult(
                            module=module,
                            timestamp=datetime.now(),
                            signal=vii.signal,
                            confidence=0.7 if vii.strength.value in ['strong', 'very_strong'] else 0.5,
                            data=vii.to_dict(),
                            reasoning=f"VII: {vii.value:.2f}"
                        )
            
            elif module == AnalysisModule.MULTI_AGENT_RL:
                current_price = market_data.get('price', 100)
                decision = mod.analyze_and_decide(market_data, current_price)
                
                signal = 'BUY' if decision.action.value in ['buy', 'strong_buy'] else 'SELL' if decision.action.value in ['sell', 'strong_sell'] else 'HOLD'
                
                return AnalysisResult(
                    module=module,
                    timestamp=datetime.now(),
                    signal=signal,
                    confidence=decision.confidence,
                    data=decision.to_dict(),
                    reasoning=decision.reasoning
                )
            
            elif module == AnalysisModule.HYPERNETWORK:
                adaptation = mod.adapt_to_market(market_data)
                
                return AnalysisResult(
                    module=module,
                    timestamp=datetime.now(),
                    signal='HOLD',  # Hypernetwork adapts, doesn't signal
                    confidence=adaptation.adaptation_confidence,
                    data=adaptation.to_dict(),
                    reasoning=f"Adapted to {adaptation.regime.value} regime"
                )
        
        except Exception as e:
            logger.error(f"Error in {module.value}: {e}")
        
        return None
    
    def _aggregate_results(
        self,
        results: List[AnalysisResult],
        market_data: Dict[str, Any]
    ) -> UnifiedSignal:
        """Aggregate results from all modules into unified signal"""
        if not results:
            return UnifiedSignal(
                timestamp=datetime.now(),
                direction='HOLD',
                confidence=0,
                position_size_multiplier=0,
                entry_price=None,
                stop_loss=None,
                take_profit=None,
                contributing_modules=[],
                dissenting_modules=[],
                risk_score=0.5,
                reasoning="No analysis results available",
                module_results=[]
            )
        
        # Calculate weighted votes
        buy_score = 0
        sell_score = 0
        hold_score = 0
        total_weight = 0
        
        contributing = []
        dissenting = []
        
        for result in results:
            weight = self.module_weights.get(result.module, 0.1) * result.confidence
            total_weight += weight
            
            if result.signal == 'BUY':
                buy_score += weight
                contributing.append(result.module.value)
            elif result.signal == 'SELL':
                sell_score += weight
                contributing.append(result.module.value)
            elif result.signal == 'CAUTION':
                hold_score += weight * 2  # Caution has extra weight
            else:
                hold_score += weight
        
        # Determine direction
        if total_weight == 0:
            direction = 'HOLD'
            confidence = 0
        elif buy_score > sell_score and buy_score > hold_score:
            direction = 'BUY'
            confidence = buy_score / total_weight
            dissenting = [r.module.value for r in results if r.signal == 'SELL']
        elif sell_score > buy_score and sell_score > hold_score:
            direction = 'SELL'
            confidence = sell_score / total_weight
            dissenting = [r.module.value for r in results if r.signal == 'BUY']
        else:
            direction = 'HOLD'
            confidence = hold_score / total_weight
        
        # Position size multiplier based on confidence
        if confidence > 0.8:
            position_multiplier = 1.5
        elif confidence > 0.6:
            position_multiplier = 1.0
        elif confidence > 0.4:
            position_multiplier = 0.5
        else:
            position_multiplier = 0.25
        
        # Calculate risk score
        caution_modules = sum(1 for r in results if r.signal == 'CAUTION')
        risk_score = min(1.0, 0.3 + caution_modules * 0.2 + (1 - confidence) * 0.3)
        
        # Entry/exit levels
        current_price = market_data.get('price', 0)
        atr = market_data.get('atr', current_price * 0.02)
        
        if direction == 'BUY' and current_price > 0:
            entry_price = current_price
            stop_loss = current_price - atr * 1.5
            take_profit = current_price + atr * 3
        elif direction == 'SELL' and current_price > 0:
            entry_price = current_price
            stop_loss = current_price + atr * 1.5
            take_profit = current_price - atr * 3
        else:
            entry_price = None
            stop_loss = None
            take_profit = None
        
        # Generate reasoning
        reasoning_parts = [f"Direction: {direction} ({confidence:.0%} confidence)"]
        reasoning_parts.append(f"Contributing: {', '.join(contributing[:3])}")
        if dissenting:
            reasoning_parts.append(f"Dissenting: {', '.join(dissenting[:2])}")
        reasoning_parts.append(f"Risk score: {risk_score:.2f}")
        
        return UnifiedSignal(
            timestamp=datetime.now(),
            direction=direction,
            confidence=confidence,
            position_size_multiplier=position_multiplier,
            entry_price=entry_price,
            stop_loss=stop_loss,
            take_profit=take_profit,
            contributing_modules=contributing,
            dissenting_modules=dissenting,
            risk_score=risk_score,
            reasoning=". ".join(reasoning_parts),
            module_results=results
        )
    
    def get_module_status(self) -> Dict[str, Any]:
        """Get status of all modules"""
        return {
            'initialized': self._initialized,
            'modules': {
                m.value: m in self._modules
                for m in AnalysisModule
            },
            'active_modules': len(self._modules),
            'analysis_count': len(self.analysis_history),
            'signal_count': len(self.signal_history)
        }
    
    def get_recent_signals(self, n: int = 10) -> List[Dict[str, Any]]:
        """Get recent unified signals"""
        return [s.to_dict() for s in list(self.signal_history)[-n:]]


# Factory function
def create_advanced_analysis_orchestrator(
    config: Optional[Dict[str, Any]] = None
) -> AdvancedAnalysisOrchestrator:
    """Create advanced analysis orchestrator"""
    orchestrator = AdvancedAnalysisOrchestrator(config)
    orchestrator.initialize()
    return orchestrator


# Quick start function
async def quick_analyze(
    symbol: str,
    market_data: Dict[str, Any],
    config: Optional[Dict[str, Any]] = None
) -> UnifiedSignal:
    """Quick analysis using all modules"""
    orchestrator = create_advanced_analysis_orchestrator(config)
    return await orchestrator.analyze(symbol, market_data)
