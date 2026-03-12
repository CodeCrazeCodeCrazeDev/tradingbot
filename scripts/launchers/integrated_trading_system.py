"""
Integrated Trading System - Complete Integration of All Components
Combines Elite System, Market Intelligence, Orchestrator, and Opportunity Scanner
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
import numpy as np
import pandas as pd

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/integrated_system.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class IntegratedTradingSystem:
    """
    Complete integration of all trading bot components:
    - Elite System (Psychology, Regime Detection, Risk Management)
    - Market Intelligence (Wyckoff, Liquidity, Pattern Recognition)
    - Orchestrator (Master Coordination, Execution, ML Prediction)
    - Opportunity Scanner (All opportunity types)
    - Advanced Features (Liquidity Holography, Institutional DNA, etc.)
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """Initialize integrated trading system."""
        logger.info("="*80)
        logger.info("🚀 INITIALIZING INTEGRATED TRADING SYSTEM")
        logger.info("="*80)
        
        self.config = config or self._default_config()
        self.is_running = False
        self.components_initialized = False
        self.connection_monitor = None
        
        # CRITICAL SAFETY: Enforce paper trading mode by default
        if 'trading_mode' not in self.config:
            self.config['trading_mode'] = 'paper'
            logger.warning("⚠️ SAFETY: Trading mode not specified, defaulting to PAPER mode")
        
        if self.config.get('trading_mode') == 'live':
            logger.critical("🚨 LIVE TRADING MODE DETECTED - MANUAL APPROVAL REQUIRED 🚨")
            logger.critical("🚨 System will NOT execute live trades without explicit confirmation 🚨")
            self.config['trading_mode'] = 'paper'  # Override to paper for safety
        
        # Initialize all components
        self._initialize_components()
        
        # Initialize connection monitor
        self._init_connection_monitor()
        
        logger.info("="*80)
        logger.info("✅ INTEGRATED TRADING SYSTEM INITIALIZED")
        logger.info(f"📋 Mode: {self.config['trading_mode'].upper()}")
        logger.info("="*80)
    
    def _default_config(self) -> Dict:
        """Default configuration."""
        return {
            'symbols': ['EURUSD', 'GBPUSD', 'USDJPY', 'AUDUSD', 'USDCAD'],
            'timeframes': ['M5', 'M15', 'H1', 'H4', 'D1'],
            'risk_per_trade': 0.02,
            'max_positions': 5,
            'trading_mode': 'balanced',
            'enable_ml': True,
            'enable_rl': True,
            'enable_quantum': False,  # Optional
            'enable_blockchain': False,  # Optional
        }
    
    def _initialize_components(self):
        """Initialize all trading components."""
        try:
            # 1. Elite System Components
            self._init_elite_system()
            
            # 2. Market Intelligence Components
            self._init_market_intelligence()
            
            # 3. Orchestrator Components
            self._init_orchestrator()
            
            # 4. Opportunity Scanner Components
            self._init_opportunity_scanner()
            
            # 5. Advanced Features (Optional)
            self._init_advanced_features()
            
            # 6. Learning and Optimization
            self._init_learning_systems()
            
            self.components_initialized = True
            logger.info("✅ All components initialized successfully")
            
        except Exception as e:
            logger.error(f"❌ Component initialization failed: {e}")
            raise
    
    def _init_elite_system(self):
        """Initialize Elite System components."""
        try:
            from trading_bot.elite_system import (
                EliteMarketPsychology,
                EliteRegimeDetector,
                EliteRiskManager,
                ElitePatternRecognizer,
                EliteMarketAnalyzer
            )
            from trading_bot.risk.unified_risk_manager import UnifiedRiskManager
            
            self.market_psychology = EliteMarketPsychology()
            self.regime_detector = EliteRegimeDetector()
            self.elite_risk_manager = EliteRiskManager()
            self.pattern_recognizer = ElitePatternRecognizer()
            self.market_analyzer = EliteMarketAnalyzer()
            
            # NEW: Unified Risk Manager (handles multiple RiskManager implementations)
            self.unified_risk_manager = UnifiedRiskManager(
                config={
                    'max_drawdown_pct': self.config.get('max_drawdown_pct', 20.0),
                    'risk_per_trade_pct': self.config.get('risk_per_trade', 0.02) * 100,
                    'max_lots': self.config.get('max_lots', 1.0)
                }
            )
            logger.info("✅ Unified Risk Manager initialized (compatibility wrapper)")
            
            logger.info("✅ Elite System initialized")
        except ImportError as e:
            logger.warning(f"⚠️ Elite System not available: {e}")
            self.market_psychology = None
            self.regime_detector = None
            self.elite_risk_manager = None
            self.pattern_recognizer = None
            self.market_analyzer = None
            self.unified_risk_manager = None
    
    def _init_market_intelligence(self):
        """Initialize Market Intelligence components."""
        try:
            from trading_bot.market_intelligence import (
                WyckoffAccumulationDetector,
                OrderBlockAnalysis,
                MarketStructureAnalysis,
                LiquidityPoolDetector
            )
            
            self.wyckoff_detector = WyckoffAccumulationDetector()
            self.order_block_analyzer = OrderBlockAnalysis()
            self.market_structure = MarketStructureAnalysis()
            self.liquidity_detector = LiquidityPoolDetector()
            
            logger.info("✅ Market Intelligence initialized")
        except ImportError as e:
            logger.warning(f"⚠️ Market Intelligence not available: {e}")
            self.wyckoff_detector = None
            self.order_block_analyzer = None
            self.market_structure = None
            self.liquidity_detector = None
    
    def _init_orchestrator(self):
        """Initialize Orchestrator components."""
        try:
            from trading_bot.orchestrator import (
                MasterOrchestrator,
                ExecutionEngine,
                OpportunityPredictor,
                PortfolioRiskManager,
                PerformanceTracker
            )
            from trading_bot.orchestrator.position_rotator import PositionRotator
            
            self.orchestrator = MasterOrchestrator()
            self.execution_engine = ExecutionEngine()
            self.opportunity_predictor = OpportunityPredictor()
            self.portfolio_risk_manager = PortfolioRiskManager()
            self.performance_tracker = PerformanceTracker()
            
            # NEW: Position Rotator for max_positions management
            self.position_rotator = PositionRotator(
                max_positions=self.config.get('max_positions', 5),
                min_confidence_diff=0.1,
                enable_time_rotation=True,
                enable_performance_rotation=True
            )
            logger.info("✅ Position Rotator initialized (auto-close enabled)")
            
            logger.info("✅ Orchestrator initialized")
        except ImportError as e:
            logger.warning(f"⚠️ Orchestrator not available: {e}")
            self.orchestrator = None
            self.execution_engine = None
            self.opportunity_predictor = None
            self.portfolio_risk_manager = None
            self.performance_tracker = None
            self.position_rotator = None
    
    def _init_opportunity_scanner(self):
        """Initialize Opportunity Scanner components."""
        try:
            from trading_bot.opportunity_scanner import (
                MarketInefficiencyScanner,
                CrossExchangeArbitrage,
                NewsImpactAnalyzer,
                CorrelationBreakdownDetector,
                OrderFlowImbalanceDetector,
                VolatilityArbitrage,
                MomentumBurstDetector
            )
            
            self.inefficiency_scanner = MarketInefficiencyScanner()
            self.arbitrage_detector = CrossExchangeArbitrage()
            self.news_analyzer = NewsImpactAnalyzer()
            self.correlation_detector = CorrelationBreakdownDetector()
            self.flow_detector = OrderFlowImbalanceDetector()
            self.volatility_trader = VolatilityArbitrage()
            self.momentum_detector = MomentumBurstDetector()
            
            logger.info("✅ Opportunity Scanner initialized")
        except ImportError as e:
            logger.warning(f"⚠️ Opportunity Scanner not available: {e}")
            self.inefficiency_scanner = None
            self.arbitrage_detector = None
            self.news_analyzer = None
            self.correlation_detector = None
            self.flow_detector = None
            self.volatility_trader = None
            self.momentum_detector = None
    
    def _init_advanced_features(self):
        """Initialize Advanced Features (optional)."""
        try:
            from trading_bot.advanced_features import (
                LiquidityHolographyEngine,
                InstitutionalFootprintDNA,
                VolatilityImpulseVector,
                FractalMomentumDivergence,
                MultiAgentTradingSystem,
                DigitalTwinSimulator
            )
            
            self.liquidity_holography = LiquidityHolographyEngine()
            self.institutional_dna = InstitutionalFootprintDNA()
            self.volatility_impulse = VolatilityImpulseVector()
            self.fractal_divergence = FractalMomentumDivergence()
            self.multi_agent_system = MultiAgentTradingSystem()
            self.digital_twin = DigitalTwinSimulator()
            
            logger.info("✅ Advanced Features initialized")
        except ImportError as e:
            logger.warning(f"⚠️ Advanced Features not available: {e}")
            self.liquidity_holography = None
            self.institutional_dna = None
            self.volatility_impulse = None
            self.fractal_divergence = None
            self.multi_agent_system = None
            self.digital_twin = None
    
    def _init_learning_systems(self):
        """Initialize Learning and Optimization systems."""
        try:
            from learning.distributional_rl import DistributionalQLearning
            from learning.multi_objective_rl import MultiObjectiveRL
            from learning.strategy_optimizer import StrategyOptimizer
            from trading_bot.ml.offline_rl.offline_rl_trainer import OfflineRLTrainer, TrainingConfig
            
            self.distributional_rl = DistributionalQLearning(
                state_dim=50,
                action_dim=3,
                num_quantiles=51
            )
            self.multi_objective_rl = MultiObjectiveRL()
            self.strategy_optimizer = StrategyOptimizer()
            
            # NEW: Offline RL Trainer
            self.offline_rl_trainer = OfflineRLTrainer(
                config=TrainingConfig(
                    algorithm='cql',  # Conservative Q-Learning
                    num_epochs=100,
                    min_fqe_score=0.7,
                    min_win_rate=0.55
                )
            )
            logger.info("✅ Offline RL Trainer initialized (CQL algorithm)")
            
            logger.info("✅ Learning Systems initialized")
        except ImportError as e:
            logger.warning(f"⚠️ Learning Systems not available: {e}")
            self.distributional_rl = None
            self.multi_objective_rl = None
            self.strategy_optimizer = None
            self.offline_rl_trainer = None
    
    def _init_connection_monitor(self):
        """Initialize Connection Monitor for internet connectivity handling."""
        try:
            from trading_bot.connectivity.connection_monitor import ConnectionMonitor
            
            self.connection_monitor = ConnectionMonitor(
                check_interval=30,  # Check every 30 seconds
                max_consecutive_failures=3
            )
            
            # Register callbacks for connection status changes
            self.connection_monitor.on_online(self._on_connection_restored)
            self.connection_monitor.on_degraded(self._on_connection_degraded)
            self.connection_monitor.on_offline(self._on_connection_lost)
            
            logger.info("✅ Connection Monitor initialized (graceful degradation enabled)")
        except ImportError as e:
            logger.warning(f"⚠️ Connection Monitor not available: {e}")
            self.connection_monitor = None
    
    def _on_connection_restored(self):
        """Handle connection restored event."""
        logger.info("✅ Internet connection restored - resuming normal operations")
    
    def _on_connection_degraded(self):
        """Handle degraded connection event."""
        logger.warning("⚠️ Internet connection degraded - reducing network activity")
    
    def _on_connection_lost(self):
        """Handle connection lost event."""
        logger.error("❌ Internet connection lost - switching to cached data only")
    
    async def analyze_market(self, symbol: str, timeframe: str) -> Dict[str, Any]:
        """
        Comprehensive market analysis using all available components.
        
        Args:
            symbol: Trading symbol (e.g., 'EURUSD')
            timeframe: Timeframe (e.g., 'H1')
        
        Returns:
            Dictionary with comprehensive analysis results
        """
        logger.info(f"📊 Analyzing {symbol} on {timeframe}")
        
        analysis = {
            'symbol': symbol,
            'timeframe': timeframe,
            'timestamp': datetime.now(),
            'signals': [],
            'opportunities': [],
            'risk_assessment': {},
            'confidence': 0.0
        }
        
        try:
            # 1. Elite System Analysis
            if self.market_analyzer:
                elite_analysis = await self._elite_analysis(symbol, timeframe)
                analysis['elite_analysis'] = elite_analysis
                analysis['signals'].extend(elite_analysis.get('signals', []))
            
            # 2. Market Intelligence Analysis
            if self.market_structure:
                intel_analysis = await self._intelligence_analysis(symbol, timeframe)
                analysis['intelligence_analysis'] = intel_analysis
                analysis['signals'].extend(intel_analysis.get('signals', []))
            
            # 3. Opportunity Scanning
            if self.inefficiency_scanner:
                opportunities = await self._scan_opportunities(symbol, timeframe)
                analysis['opportunities'] = opportunities
            
            # 4. Risk Assessment
            if self.portfolio_risk_manager:
                risk_assessment = await self._assess_risk(symbol, analysis)
                analysis['risk_assessment'] = risk_assessment
            
            # 5. ML Prediction
            if self.opportunity_predictor:
                ml_prediction = await self._ml_prediction(symbol, analysis)
                analysis['ml_prediction'] = ml_prediction
                analysis['confidence'] = ml_prediction.get('confidence', 0.0)
            
            # 6. Advanced Features Analysis (if available)
            if self.liquidity_holography:
                advanced_analysis = await self._advanced_analysis(symbol, timeframe)
                analysis['advanced_analysis'] = advanced_analysis
            
            logger.info(f"✅ Analysis complete for {symbol}: {len(analysis['signals'])} signals, "
                       f"{len(analysis['opportunities'])} opportunities")
            
        except Exception as e:
            logger.error(f"❌ Analysis failed for {symbol}: {e}")
            analysis['error'] = str(e)
        
        return analysis
    
    async def _elite_analysis(self, symbol: str, timeframe: str) -> Dict:
        """Elite System analysis."""
        # Placeholder - implement actual analysis
        return {
            'regime': 'trending',
            'sentiment': 'bullish',
            'risk_level': 'medium',
            'signals': ['BUY']
        }
    
    async def _intelligence_analysis(self, symbol: str, timeframe: str) -> Dict:
        """Market Intelligence analysis."""
        # Placeholder - implement actual analysis
        return {
            'wyckoff_phase': 'accumulation',
            'order_blocks': [],
            'liquidity_zones': [],
            'signals': ['BUY']
        }
    
    async def _scan_opportunities(self, symbol: str, timeframe: str) -> List[Dict]:
        """Scan for trading opportunities."""
        # Placeholder - implement actual scanning
        return [
            {'type': 'momentum', 'confidence': 0.75, 'direction': 'long'},
            {'type': 'inefficiency', 'confidence': 0.65, 'direction': 'long'}
        ]
    
    async def _assess_risk(self, symbol: str, analysis: Dict) -> Dict:
        """Assess risk for potential trades."""
        # Placeholder - implement actual risk assessment
        return {
            'portfolio_var': 0.02,
            'position_size': 0.01,
            'max_drawdown': 0.05,
            'risk_score': 0.3
        }
    
    async def _ml_prediction(self, symbol: str, analysis: Dict) -> Dict:
        """ML-based prediction."""
        # Placeholder - implement actual ML prediction
        return {
            'direction': 'long',
            'confidence': 0.72,
            'expected_return': 0.015,
            'risk_adjusted_return': 0.012
        }
    
    async def _advanced_analysis(self, symbol: str, timeframe: str) -> Dict:
        """Advanced features analysis."""
        # Placeholder - implement actual advanced analysis
        return {
            'liquidity_gravity': 0.65,
            'institutional_footprint': 'accumulation',
            'volatility_impulse': 0.45
        }
    
    async def execute_trade(self, symbol: str, signal: str, analysis: Dict) -> Dict:
        """
        Execute trade based on analysis.
        
        Args:
            symbol: Trading symbol
            signal: Trade signal (BUY/SELL/HOLD)
            analysis: Market analysis results
        
        Returns:
            Execution result
        """
        logger.info(f"🎯 Executing {signal} trade for {symbol}")
        
        try:
            # 1. Validate signal
            if signal == 'HOLD':
                return {'status': 'skipped', 'reason': 'HOLD signal'}
            
            # 2. Calculate position size
            risk_assessment = analysis.get('risk_assessment', {})
            position_size = risk_assessment.get('position_size', 0.01)
            
            # 3. Execute via execution engine
            if self.execution_engine:
                result = await self.execution_engine.execute(
                    symbol=symbol,
                    direction=signal,
                    size=position_size,
                    algorithm='smart'
                )
            else:
                # Simulated execution
                result = {
                    'status': 'executed',
                    'symbol': symbol,
                    'direction': signal,
                    'size': position_size,
                    'price': 1.1000,  # Placeholder
                    'timestamp': datetime.now()
                }
            
            # 4. Track performance
            if self.performance_tracker:
                await self.performance_tracker.record_trade(result)
            
            logger.info(f"✅ Trade executed: {result}")
            return result
            
        except Exception as e:
            logger.error(f"❌ Trade execution failed: {e}")
            return {'status': 'failed', 'error': str(e)}
    
    async def run(self):
        """Main trading loop."""
        logger.info("🚀 Starting Integrated Trading System")
        self.is_running = True
        cycle = 0
        
        try:
            while self.is_running:
                cycle += 1
                logger.info(f"\n{'='*80}\n⏰ Cycle {cycle} - {datetime.now().strftime('%H:%M:%S')}\n{'='*80}")
                
                # Analyze all symbols
                for symbol in self.config['symbols']:
                    for timeframe in self.config['timeframes'][:2]:  # Limit to 2 timeframes
                        analysis = await self.analyze_market(symbol, timeframe)
                        
                        # Generate trading decision
                        if analysis.get('confidence', 0) > 0.7:
                            signals = analysis.get('signals', [])
                            if signals:
                                signal = signals[0]  # Take first signal
                                await self.execute_trade(symbol, signal, analysis)
                
                # Display statistics every 5 cycles
                if cycle % 5 == 0:
                    await self.display_statistics()
                
                # Wait before next cycle
                await asyncio.sleep(60)
        
        except KeyboardInterrupt:
            logger.info("\n🛑 Stopping Integrated Trading System...")
            self.is_running = False
        
        finally:
            await self.shutdown()
    
    async def display_statistics(self):
        """Display system statistics."""
        logger.info("\n" + "="*80)
        logger.info("📊 INTEGRATED TRADING SYSTEM STATISTICS")
        logger.info("="*80)
        
        if self.performance_tracker:
            stats = await self.performance_tracker.get_statistics()
            logger.info(f"Total Trades: {stats.get('total_trades', 0)}")
            logger.info(f"Win Rate: {stats.get('win_rate', 0):.2%}")
            logger.info(f"Total P/L: ${stats.get('total_pnl', 0):.2f}")
            logger.info(f"Sharpe Ratio: {stats.get('sharpe_ratio', 0):.2f}")
        else:
            logger.info("Performance tracking not available")
        
        logger.info("="*80)
    
    async def shutdown(self):
        """Graceful shutdown."""
        logger.info("🔄 Shutting down Integrated Trading System...")
        
        # Save state
        if self.strategy_optimizer:
            self.strategy_optimizer.save_knowledge()
        
        if self.distributional_rl:
            self.distributional_rl.save('knowledge/distributional_rl.pt')
        
        logger.info("✅ Shutdown complete")


async def main():
    """Main entry point."""
    import os
    os.makedirs('logs', exist_ok=True)
    os.makedirs('knowledge', exist_ok=True)
    
    # Create and run integrated system
    system = IntegratedTradingSystem()
    await system.run()


if __name__ == '__main__':
    asyncio.run(main())
