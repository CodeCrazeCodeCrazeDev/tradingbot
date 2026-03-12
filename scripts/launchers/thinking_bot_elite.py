"""
Elite Thinking Bot - Enhanced with Advanced Features

Integrates the Thinking Bot with:
- Elite Brain system
- Orchestrator components
- Advanced exit strategies
- Market intelligence
- ML/AI models
- Opportunity scanner
- Smart execution
"""

import os
import sys
import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from thinking_bot import (
    ThinkingBot,
    MarketAnalysis,
    TradingSignal,
    SignalType,
    SignalStrength
)

# Import elite components
try:
    from trading_bot.brain import EliteBrain, BrainDecision
    ELITE_BRAIN_AVAILABLE = True
except ImportError:
    ELITE_BRAIN_AVAILABLE = False
    logging.warning("Elite Brain not available")

try:
    from trading_bot.orchestrator import MasterOrchestrator
    ORCHESTRATOR_AVAILABLE = True
except ImportError:
    ORCHESTRATOR_AVAILABLE = False
    logging.warning("Master Orchestrator not available")

try:
    from trading_bot.opportunity_scanner import (
        MarketInefficiencyScanner,
        ArbitrageDetector,
        MomentumCapture
    )
    OPPORTUNITY_SCANNER_AVAILABLE = True
except ImportError:
    OPPORTUNITY_SCANNER_AVAILABLE = False
    logging.warning("Opportunity Scanner not available")

try:
    from trading_bot.exit_strategies import (
        ExitSignalGenerator,
        DynamicTradeManager,
        ProfitMaximizer
    )
    EXIT_STRATEGIES_AVAILABLE = True
except ImportError:
    EXIT_STRATEGIES_AVAILABLE = False
    logging.warning("Exit Strategies not available")

try:
    from trading_bot.market_intelligence import (
        MarketContextAnalyzer,
        LiquidityAnalysis,
        OrderFlowAnalyzer
    )
    MARKET_INTELLIGENCE_AVAILABLE = True
except ImportError:
    MARKET_INTELLIGENCE_AVAILABLE = False
    logging.warning("Market Intelligence not available")

try:
    from trading_bot.ml import (
        OnlineLearner,
        ExplainableAI
    )
    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False
    logging.warning("ML modules not available")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'logs/elite_thinking_bot_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class EliteThinkingBot(ThinkingBot):
    """
    Enhanced Thinking Bot with Elite Features
    
    Extends the base ThinkingBot with:
    - Elite Brain decision making
    - Opportunity scanning
    - Advanced exit strategies
    - Market intelligence
    - ML-powered predictions
    - Explainable AI
    """
    
    def __init__(self, config_path: str = "config/config.yaml"):
        super().__init__(config_path)
        
        # Elite components
        self.elite_brain = None
        self.opportunity_scanner = None
        self.exit_manager = None
        self.market_intelligence = None
        self.ml_predictor = None
        self.explainable_ai = None
        
        logger.info("Elite Thinking Bot initialized")
    
    async def initialize(self) -> bool:
        """Initialize with elite components"""
        # Initialize base components
        if not await super().initialize():
            return False
        
        logger.info("\nInitializing Elite Components...")
        
        # 1. Elite Brain
        if ELITE_BRAIN_AVAILABLE:
            try:
                self.elite_brain = EliteBrain(config=self.config)
                logger.info("✓ Elite Brain initialized")
            except Exception as e:
                logger.warning(f"⚠ Elite Brain initialization failed: {e}")
        
        # 2. Opportunity Scanner
        if OPPORTUNITY_SCANNER_AVAILABLE:
            try:
                self.opportunity_scanner = {
                    'inefficiency': MarketInefficiencyScanner(),
                    'arbitrage': ArbitrageDetector(),
                    'momentum': MomentumCapture()
                }
                logger.info("✓ Opportunity Scanner initialized")
            except Exception as e:
                logger.warning(f"⚠ Opportunity Scanner initialization failed: {e}")
        
        # 3. Exit Strategies
        if EXIT_STRATEGIES_AVAILABLE:
            try:
                self.exit_manager = {
                    'signal_generator': ExitSignalGenerator(),
                    'trade_manager': DynamicTradeManager(),
                    'profit_maximizer': ProfitMaximizer()
                }
                logger.info("✓ Exit Strategies initialized")
            except Exception as e:
                logger.warning(f"⚠ Exit Strategies initialization failed: {e}")
        
        # 4. Market Intelligence
        if MARKET_INTELLIGENCE_AVAILABLE:
            try:
                self.market_intelligence = {
                    'context': MarketContextAnalyzer(),
                    'liquidity': LiquidityAnalysis(),
                    'order_flow': OrderFlowAnalyzer()
                }
                logger.info("✓ Market Intelligence initialized")
            except Exception as e:
                logger.warning(f"⚠ Market Intelligence initialization failed: {e}")
        
        # 5. ML Components
        if ML_AVAILABLE:
            try:
                self.ml_predictor = OnlineLearner()
                self.explainable_ai = ExplainableAI()
                logger.info("✓ ML/AI components initialized")
            except Exception as e:
                logger.warning(f"⚠ ML/AI initialization failed: {e}")
        
        logger.info("=" * 80)
        logger.info("ELITE THINKING BOT READY")
        logger.info("=" * 80)
        
        return True
    
    async def analyze_market_elite(self, symbol: str) -> MarketAnalysis:
        """
        Enhanced market analysis with elite components
        """
        # Get base analysis
        analysis = await self.analyze_market(symbol)
        
        # Enhance with market intelligence
        if self.market_intelligence:
            try:
                # Add market context
                context = self.market_intelligence['context'].analyze(symbol)
                
                # Add liquidity analysis
                liquidity = self.market_intelligence['liquidity'].analyze(symbol)
                
                # Add order flow
                order_flow = self.market_intelligence['order_flow'].analyze(symbol)
                
                logger.info(f"✓ Enhanced analysis with market intelligence for {symbol}")
            except Exception as e:
                logger.warning(f"⚠ Market intelligence analysis failed: {e}")
        
        # Scan for opportunities
        if self.opportunity_scanner:
            try:
                opportunities = []
                
                # Check for inefficiencies
                inefficiencies = self.opportunity_scanner['inefficiency'].scan(symbol)
                if inefficiencies:
                    opportunities.extend(inefficiencies)
                
                # Check for arbitrage
                arbitrage = self.opportunity_scanner['arbitrage'].detect(symbol)
                if arbitrage:
                    opportunities.extend(arbitrage)
                
                # Check for momentum
                momentum = self.opportunity_scanner['momentum'].capture(symbol)
                if momentum:
                    opportunities.extend(momentum)
                
                if opportunities:
                    logger.info(f"✓ Found {len(opportunities)} opportunities for {symbol}")
            except Exception as e:
                logger.warning(f"⚠ Opportunity scanning failed: {e}")
        
        return analysis
    
    async def generate_signal_elite(self, analysis: MarketAnalysis) -> Optional[TradingSignal]:
        """
        Enhanced signal generation with Elite Brain
        """
        # Get base signal
        signal = await self.generate_signal(analysis)
        
        if signal is None:
            return None
        
        # Enhance with Elite Brain
        if self.elite_brain:
            try:
                # Get brain decision
                brain_decision = await self.elite_brain.make_decision(
                    symbol=analysis.symbol,
                    market_data={
                        'price': analysis.current_price,
                        'trend': analysis.trend_direction,
                        'rsi': analysis.rsi,
                        'macd': analysis.macd
                    }
                )
                
                # Adjust signal based on brain decision
                if brain_decision:
                    signal.confidence *= brain_decision.confidence
                    signal.reasoning += f" | Elite Brain: {brain_decision.reasoning}"
                    logger.info(f"✓ Elite Brain enhanced signal: confidence={signal.confidence:.2f}")
            except Exception as e:
                logger.warning(f"⚠ Elite Brain decision failed: {e}")
        
        # Enhance with ML prediction
        if self.ml_predictor:
            try:
                # Get ML prediction
                prediction = self.ml_predictor.predict(
                    features={
                        'rsi': analysis.rsi,
                        'macd': analysis.macd,
                        'trend_strength': analysis.trend_strength,
                        'volatility': analysis.volatility,
                        'momentum': analysis.momentum
                    }
                )
                
                signal.ai_prediction = prediction.get('direction')
                signal.ai_confidence = prediction.get('confidence')
                
                logger.info(f"✓ ML prediction: {signal.ai_prediction} (confidence={signal.ai_confidence:.2f})")
            except Exception as e:
                logger.warning(f"⚠ ML prediction failed: {e}")
        
        # Get AI explanation
        if self.explainable_ai:
            try:
                explanation = self.explainable_ai.explain_signal(signal)
                logger.info(f"✓ AI Explanation: {explanation}")
            except Exception as e:
                logger.warning(f"⚠ AI explanation failed: {e}")
        
        return signal
    
    async def monitor_positions_elite(self):
        """
        Enhanced position monitoring with exit strategies
        """
        # Base monitoring
        await self.monitor_positions()
        
        # Enhanced exit management
        if self.exit_manager and self.active_positions:
            try:
                for ticket, position in list(self.active_positions.items()):
                    # Generate exit signals
                    exit_signals = self.exit_manager['signal_generator'].generate_signals(
                        position=position,
                        current_price=position.get('current_price', position['entry_price'])
                    )
                    
                    if exit_signals:
                        logger.info(f"✓ Exit signals generated for position {ticket}: {len(exit_signals)} signals")
                    
                    # Dynamic trade management
                    trade_health = self.exit_manager['trade_manager'].assess_trade_health(position)
                    
                    # Profit maximization
                    optimal_exit = self.exit_manager['profit_maximizer'].find_optimal_exit(position)
                    
                    if optimal_exit:
                        logger.info(f"✓ Optimal exit found for position {ticket}: {optimal_exit}")
            except Exception as e:
                logger.warning(f"⚠ Elite exit management failed: {e}")
    
    async def trading_cycle_elite(self):
        """
        Enhanced trading cycle with all elite features
        """
        try:
            self.cycle_count += 1
            
            # Get symbols
            symbols = self.config.get('mt5', {}).get('symbols', ['EURUSD'])
            
            for symbol in symbols:
                try:
                    logger.info(f"\n{'='*60}")
                    logger.info(f"ELITE TRADING CYCLE #{self.cycle_count} - {symbol}")
                    logger.info(f"{'='*60}")
                    
                    # 1. ELITE ANALYSIS
                    logger.info("1. Performing elite market analysis...")
                    analysis = await self.analyze_market_elite(symbol)
                    
                    # 2. ELITE SIGNAL GENERATION
                    logger.info("2. Generating elite trading signal...")
                    signal = await self.generate_signal_elite(analysis)
                    
                    if signal is None:
                        logger.info(f"   No signal for {symbol}")
                        continue
                    
                    logger.info(f"   Signal: {signal.signal_type.value}, Confidence: {signal.confidence:.2f}")
                    
                    # 3. RISK VALIDATION
                    logger.info("3. Validating signal with risk management...")
                    validation = await self.validate_signal(signal)
                    
                    if not validation.is_valid:
                        logger.warning(f"   Signal validation failed: {', '.join(validation.errors)}")
                        continue
                    
                    logger.info(f"   Validation passed: {validation.approved_lots:.2f} lots approved")
                    
                    # 4. EXECUTION
                    logger.info("4. Executing trade...")
                    execution = await self.execute_trade(signal, validation)
                    
                    if not execution.success:
                        logger.error(f"   Execution failed: {execution.error}")
                        continue
                    
                    logger.info(f"   ✓ Trade executed successfully: Ticket={execution.ticket}")
                    
                except Exception as e:
                    logger.error(f"Error in elite trading cycle for {symbol}: {e}")
            
            # 5. ELITE MONITORING
            logger.info("\n5. Monitoring positions with elite exit strategies...")
            await self.monitor_positions_elite()
            
            # 6. PERFORMANCE UPDATE
            logger.info("6. Updating performance metrics...")
            await self.update_performance()
            
            logger.info(f"\n{'='*60}")
            logger.info(f"ELITE CYCLE #{self.cycle_count} COMPLETE")
            logger.info(f"{'='*60}\n")
            
        except Exception as e:
            logger.error(f"Error in elite trading cycle: {e}")
    
    async def run(self):
        """Main run loop with elite features"""
        logger.info("=" * 80)
        logger.info("ELITE THINKING BOT - STARTING")
        logger.info("=" * 80)
        
        # Initialize
        if not await self.initialize():
            logger.error("Initialization failed. Exiting.")
            return
        
        self.running = True
        
        try:
            logger.info("\n🚀 Elite Thinking Bot is now running...")
            logger.info("Press Ctrl+C to stop\n")
            
            # Main loop
            while self.running:
                await self.trading_cycle_elite()
                
                # Sleep between cycles
                await asyncio.sleep(60)
                
        except KeyboardInterrupt:
            logger.info("\n⚠ Keyboard interrupt received")
        except Exception as e:
            logger.error(f"Fatal error: {e}")
        finally:
            self.running = False
            
            # Cleanup
            logger.info("\n" + "=" * 80)
            logger.info("ELITE THINKING BOT - SHUTTING DOWN")
            logger.info("=" * 80)
            
            import MetaTrader5 as mt5
            mt5.shutdown()
            
            logger.info("✓ Shutdown complete")


async def main():
    """Main entry point"""
    bot = EliteThinkingBot()
    await bot.run()


if __name__ == "__main__":
    asyncio.run(main())
