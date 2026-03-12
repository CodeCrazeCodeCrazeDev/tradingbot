"""
AlphaAlgo Complete System Runner
=================================

This script orchestrates the complete AlphaAlgo trading system according to
the multi-layer architectural blueprint:

1. Data Layer - Market data ingestion and processing
2. Intelligence Layer - 9-tier brain architecture with ML/AI
3. Decision Layer - Signal fusion and decision generation
4. Execution Layer - Order management and smart routing
5. Risk Management Layer - Position sizing and risk control
6. Portfolio & Performance Layer - Multi-symbol management
7. Interface & Control Layer - Dashboard and monitoring
8. Security & Infrastructure Layer - Health checks and failover

Author: AlphaAlgo Team
Version: 2.0
"""

import asyncio
import logging
import sys
import signal
from pathlib import Path
from typing import Any, Dict, Optional
from datetime import datetime
import yaml
import json

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/alphaalgo_complete.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


class AlphaAlgoSystem:
    """
    Complete AlphaAlgo Trading System
    
    Orchestrates all layers of the trading system according to the
    architectural blueprint.
    """
    
    def __init__(self, config_path: str = "config/alphaalgo_config.yaml"):
        """
        Initialize AlphaAlgo system
        
        Args:
            config_path: Path to configuration file
        """
        self.config_path = config_path
        self.config = self._load_config()
        
        # System components (initialized in order)
        self.data_layer = None
        self.intelligence_layer = None
        self.decision_layer = None
        self.execution_layer = None
        self.risk_layer = None
        self.portfolio_layer = None
        self.interface_layer = None
        self.security_layer = None
        
        # System state
        self.running = False
        self.initialized = False
        
        # Performance tracking
        self.start_time = None
        self.trades_executed = 0
        self.total_pnl = 0.0
        
        logger.info("AlphaAlgo System initialized")
    
    def _load_config(self) -> Dict[str, Any]:
        """Load system configuration"""
        config_file = Path(self.config_path)
        
        if not config_file.exists():
            logger.warning(f"Config file {self.config_path} not found, using defaults")
            return self._get_default_config()
        
        try:
            with open(config_file, 'r') as f:
                config = yaml.safe_load(f)
            logger.info(f"Configuration loaded from {self.config_path}")
            return config
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration"""
        return {
            'system': {
                'name': 'AlphaAlgo',
                'version': '2.0',
                'mode': 'simulation'  # 'simulation' or 'live'
            },
            'data_layer': {
                'symbols': ['EURUSD', 'GBPUSD', 'USDJPY'],
                'timeframes': ['M1', 'M5', 'M15', 'H1', 'H4'],
                'simulate_data': True,
                'use_redis': False,
                'use_plasma': False
            },
            'intelligence_layer': {
                'brain_architecture': 'elite_brain',
                'enable_all_tiers': True,
                'ml_models_enabled': True,
                'multi_agent_enabled': True
            },
            'decision_layer': {
                'signal_fusion_method': 'adaptive_ensemble',
                'min_confidence': 0.7,
                'coherence_threshold': 0.6
            },
            'execution_layer': {
                'broker': 'simulation',
                'execution_algorithm': 'adaptive',
                'slippage_control': True,
                'max_slippage_pips': 2.0
            },
            'risk_layer': {
                'max_risk_per_trade': 0.01,  # 1%
                'max_portfolio_risk': 0.05,  # 5%
                'max_drawdown': 0.15,  # 15%
                'position_sizing_method': 'kelly'
            },
            'portfolio_layer': {
                'max_positions': 5,
                'correlation_limit': 0.7,
                'rebalance_interval': 3600  # seconds
            },
            'interface_layer': {
                'dashboard_enabled': True,
                'dashboard_port': 8050,
                'api_enabled': True,
                'api_port': 8000
            },
            'security_layer': {
                'health_check_interval': 60,
                'auto_healing': True,
                'backup_interval': 3600
            }
        }
    
    async def initialize(self) -> bool:
        """
        Initialize all system layers
        
        Returns:
            True if initialization successful
        """
        if self.initialized:
            logger.warning("System already initialized")
            return True
        
        logger.info("=" * 80)
        logger.info("ALPHAALGO SYSTEM INITIALIZATION")
        logger.info("=" * 80)
        
        try:
            # 1. Initialize Data Layer
            logger.info("Initializing Data Layer...")
            self.data_layer = await self._initialize_data_layer()
            if not self.data_layer:
                raise Exception("Failed to initialize Data Layer")
            logger.info("✓ Data Layer initialized")
            
            # 2. Initialize Intelligence Layer
            logger.info("Initializing Intelligence Layer...")
            self.intelligence_layer = await self._initialize_intelligence_layer()
            if not self.intelligence_layer:
                raise Exception("Failed to initialize Intelligence Layer")
            logger.info("✓ Intelligence Layer initialized")
            
            # 3. Initialize Decision Layer
            logger.info("Initializing Decision Layer...")
            self.decision_layer = await self._initialize_decision_layer()
            if not self.decision_layer:
                raise Exception("Failed to initialize Decision Layer")
            logger.info("✓ Decision Layer initialized")
            
            # 4. Initialize Execution Layer
            logger.info("Initializing Execution Layer...")
            self.execution_layer = await self._initialize_execution_layer()
            if not self.execution_layer:
                raise Exception("Failed to initialize Execution Layer")
            logger.info("✓ Execution Layer initialized")
            
            # 5. Initialize Risk Management Layer
            logger.info("Initializing Risk Management Layer...")
            self.risk_layer = await self._initialize_risk_layer()
            if not self.risk_layer:
                raise Exception("Failed to initialize Risk Management Layer")
            logger.info("✓ Risk Management Layer initialized")
            
            # 6. Initialize Portfolio & Performance Layer
            logger.info("Initializing Portfolio & Performance Layer...")
            self.portfolio_layer = await self._initialize_portfolio_layer()
            if not self.portfolio_layer:
                raise Exception("Failed to initialize Portfolio Layer")
            logger.info("✓ Portfolio & Performance Layer initialized")
            
            # 7. Initialize Interface & Control Layer
            logger.info("Initializing Interface & Control Layer...")
            self.interface_layer = await self._initialize_interface_layer()
            if not self.interface_layer:
                raise Exception("Failed to initialize Interface Layer")
            logger.info("✓ Interface & Control Layer initialized")
            
            # 8. Initialize Security & Infrastructure Layer
            logger.info("Initializing Security & Infrastructure Layer...")
            self.security_layer = await self._initialize_security_layer()
            if not self.security_layer:
                raise Exception("Failed to initialize Security Layer")
            logger.info("✓ Security & Infrastructure Layer initialized")
            
            self.initialized = True
            logger.info("=" * 80)
            logger.info("✓ ALL LAYERS INITIALIZED SUCCESSFULLY")
            logger.info("=" * 80)
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Initialization failed: {e}")
            return False
    
    async def _initialize_data_layer(self) -> Dict[str, Any]:
        """Initialize Data Layer components"""
        from trading_bot.data import (
            MarketDataStream, TimeSeriesDB, 
            RealTimeProcessor, PipelineMonitor
        )
        
        data_config = self.config.get('data_layer', {})
        
        # Market data stream
        market_stream = MarketDataStream(data_config)
        await market_stream.connect()
        
        # Subscribe to symbols
        for symbol in data_config.get('symbols', []):
            await market_stream.subscribe(symbol)
        
        # Time series database
        time_series_db = TimeSeriesDB(data_config)
        
        # Real-time processor
        processor = RealTimeProcessor(data_config)
        await processor.start()
        
        # Pipeline monitor
        monitor = PipelineMonitor(data_config)
        await monitor.start()
        
        return {
            'market_stream': market_stream,
            'time_series_db': time_series_db,
            'processor': processor,
            'monitor': monitor
        }
    
    async def _initialize_intelligence_layer(self) -> Dict[str, Any]:
        """Initialize Intelligence Layer (Brain Architecture)"""
        from trading_bot.brain import EliteBrainController
        from agents.coordinator import MultiAgentCoordinator
        from agents.specialized_agents import (
            TrendFollowingAgent, MeanReversionAgent,
            VolatilityAgent, RiskManagerAgent
        )
        from ml.pipeline import MLPipeline
        
        intel_config = self.config.get('intelligence_layer', {})
        
        # Elite Brain (9-tier architecture)
        brain = EliteBrainController(config_path=None)
        if not brain.initialize():
            raise Exception("Failed to initialize Elite Brain")
        
        # Multi-Agent System
        agents = {
            'trend_follower': TrendFollowingAgent(),
            'mean_reverter': MeanReversionAgent(),
            'volatility_trader': VolatilityAgent(),
            'risk_manager': RiskManagerAgent()
        }
        coordinator = MultiAgentCoordinator(agents)
        
        # ML Pipeline
        feature_config = {
            'price': {'returns': True, 'ma_windows': [10, 20, 50]},
            'volume': {'changes': True},
            'indicators': {'rsi': True, 'macd': True, 'bbands': True}
        }
        model_params = {
            'hidden_dim': 64,
            'num_layers': 2,
            'dropout': 0.2
        }
        ml_pipeline = MLPipeline(feature_config, model_params)
        
        return {
            'brain': brain,
            'coordinator': coordinator,
            'ml_pipeline': ml_pipeline
        }
    
    async def _initialize_decision_layer(self) -> Dict[str, Any]:
        """Initialize Decision Layer"""
        from explainability import ExplainableAI
        
        decision_config = self.config.get('decision_layer', {})
        
        # Explainable AI for decision transparency
        explainable_ai = ExplainableAI()
        
        return {
            'explainable_ai': explainable_ai,
            'config': decision_config
        }
    
    async def _initialize_execution_layer(self) -> Dict[str, Any]:
        """Initialize Execution Layer"""
        from broker.broker_interface import BrokerInterface
        from trading.order_execution import OrderExecutionManager
        
        exec_config = self.config.get('execution_layer', {})
        
        # Broker interface (simulation mode)
        if exec_config.get('broker') == 'simulation':
            broker = None  # Use simulation broker
            logger.info("Using simulation broker")
        else:
            # Initialize real broker
            broker = BrokerInterface(
                api_key="",
                api_secret="",
                base_url="",
                testnet=True
            )
        
        # Order execution manager
        execution_manager = OrderExecutionManager(broker)
        
        return {
            'broker': broker,
            'execution_manager': execution_manager
        }
    
    async def _initialize_risk_layer(self) -> Dict[str, Any]:
        """Initialize Risk Management Layer"""
        from trading_bot.risk import UnifiedRiskManager
        from risk_management import (
            RiskEngine, VaRCalculator, DrawdownMonitor
        )
        
        risk_config = self.config.get('risk_layer', {})
        
        # Unified risk manager
        risk_manager = UnifiedRiskManager(config=risk_config)
        
        # Risk engine
        risk_engine = RiskEngine(risk_config)
        
        # VaR calculator
        var_calculator = VaRCalculator()
        
        # Drawdown monitor
        drawdown_monitor = DrawdownMonitor(risk_config)
        
        return {
            'risk_manager': risk_manager,
            'risk_engine': risk_engine,
            'var_calculator': var_calculator,
            'drawdown_monitor': drawdown_monitor
        }
    
    async def _initialize_portfolio_layer(self) -> Dict[str, Any]:
        """Initialize Portfolio & Performance Layer"""
        from risk_management import PortfolioManager
        from backtesting import AdvancedBacktester
        
        portfolio_config = self.config.get('portfolio_layer', {})
        
        # Portfolio manager
        portfolio_manager = PortfolioManager(portfolio_config)
        
        # Backtester
        backtester = AdvancedBacktester(portfolio_config)
        
        return {
            'portfolio_manager': portfolio_manager,
            'backtester': backtester
        }
    
    async def _initialize_interface_layer(self) -> Dict[str, Any]:
        """Initialize Interface & Control Layer"""
        interface_config = self.config.get('interface_layer', {})
        
        # Dashboard (optional)
        dashboard = None
        if interface_config.get('dashboard_enabled', True):
            try:
                from dashboard import LiveDashboard
                dashboard = LiveDashboard(
                    self,
                    interface_config
                )
                logger.info("Dashboard initialized")
            except ImportError:
                logger.warning("Dashboard not available")
        
        # API Server (optional)
        api_server = None
        if interface_config.get('api_enabled', True):
            try:
                from api.api_server import APIServer
                api_server = APIServer(self, interface_config)
                logger.info("API Server initialized")
            except ImportError:
                logger.warning("API Server not available")
        
        return {
            'dashboard': dashboard,
            'api_server': api_server
        }
    
    async def _initialize_security_layer(self) -> Dict[str, Any]:
        """Initialize Security & Infrastructure Layer"""
        security_config = self.config.get('security_layer', {})
        
        # Health monitoring
        from infrastructure import HealthCheck
        health_check = HealthCheck(security_config)
        
        # Auto-healing (if enabled)
        auto_healing = None
        if security_config.get('auto_healing', True):
            try:
                from infrastructure import SelfHealingSystem
                auto_healing = SelfHealingSystem(security_config)
                logger.info("Auto-healing enabled")
            except ImportError:
                logger.warning("Auto-healing not available")
        
        return {
            'health_check': health_check,
            'auto_healing': auto_healing
        }
    
    async def start(self) -> None:
        """Start the AlphaAlgo system"""
        if not self.initialized:
            logger.error("System not initialized. Call initialize() first.")
            return
        
        if self.running:
            logger.warning("System already running")
            return
        
        logger.info("=" * 80)
        logger.info("STARTING ALPHAALGO SYSTEM")
        logger.info("=" * 80)
        
        self.running = True
        self.start_time = datetime.now()
        
        # Start all layers
        tasks = []
        
        # Start data layer
        if self.data_layer:
            logger.info("Starting Data Layer...")
        
        # Start interface layer
        if self.interface_layer and self.interface_layer.get('dashboard'):
            dashboard_task = asyncio.create_task(
                self.interface_layer['dashboard'].start()
            )
            tasks.append(dashboard_task)
            logger.info("Dashboard started")
        
        if self.interface_layer and self.interface_layer.get('api_server'):
            api_task = asyncio.create_task(
                self.interface_layer['api_server'].start()
            )
            tasks.append(api_task)
            logger.info("API Server started")
        
        # Start main trading loop
        trading_task = asyncio.create_task(self._trading_loop())
        tasks.append(trading_task)
        
        # Start monitoring loop
        monitoring_task = asyncio.create_task(self._monitoring_loop())
        tasks.append(monitoring_task)
        
        logger.info("=" * 80)
        logger.info("✓ ALPHAALGO SYSTEM RUNNING")
        logger.info("=" * 80)
        logger.info(f"Mode: {self.config['system']['mode']}")
        logger.info(f"Symbols: {', '.join(self.config['data_layer']['symbols'])}")
        logger.info(f"Dashboard: http://localhost:{self.config['interface_layer']['dashboard_port']}")
        logger.info("=" * 80)
        
        # Wait for all tasks
        try:
            await asyncio.gather(*tasks)
        except asyncio.CancelledError:
            logger.info("System tasks cancelled")
    
    async def _trading_loop(self) -> None:
        """Main trading loop"""
        logger.info("Trading loop started")
        
        while self.running:
            try:
                # Get market data for all symbols
                for symbol in self.config['data_layer']['symbols']:
                    await self._process_symbol(symbol)
                
                # Sleep before next iteration
                await asyncio.sleep(1)
                
            except asyncio.CancelledError:
                logger.info("Trading loop cancelled")
                break
            except Exception as e:
                logger.error(f"Error in trading loop: {e}")
                await asyncio.sleep(5)
    
    async def _process_symbol(self, symbol: str) -> None:
        """
        Process a single symbol through all layers
        
        Args:
            symbol: Trading symbol
        """
        try:
            # 1. Get market data (Data Layer)
            market_data = await self.data_layer['market_stream'].get_ohlcv(
                symbol, 'M1', limit=100
            )
            
            if market_data is None or market_data.empty:
                return
            
            # 2. Process through Intelligence Layer
            brain_decision = self.intelligence_layer['brain'].process_market_data(
                market_data
            )
            
            if not brain_decision or brain_decision.get('error'):
                return
            
            # 3. Get agent proposals
            agent_proposals = self.intelligence_layer['coordinator'].get_proposals({
                'price': market_data['close'].iloc[-1],
                'sma_20': market_data['close'].rolling(20).mean().iloc[-1],
                'sma_50': market_data['close'].rolling(50).mean().iloc[-1],
                'volatility': market_data['close'].pct_change().std(),
                'symbol': symbol
            })
            
            # 4. Aggregate decisions (Decision Layer)
            if agent_proposals:
                agent_decision = self.intelligence_layer['coordinator'].aggregate_decisions(
                    agent_proposals,
                    method='weighted_vote'
                )
            else:
                agent_decision = {'action': 'HOLD', 'confidence': 0.0}
            
            # 5. Combine brain and agent decisions
            final_decision = self._combine_decisions(brain_decision, agent_decision)
            
            # 6. Risk check (Risk Layer)
            if final_decision['action'] != 'HOLD':
                risk_approved = await self._check_risk(symbol, final_decision)
                
                if not risk_approved:
                    logger.info(f"Trade rejected by risk management for {symbol}")
                    return
            
            # 7. Execute trade (Execution Layer)
            if final_decision['action'] != 'HOLD' and final_decision['confidence'] > 0.7:
                await self._execute_trade(symbol, final_decision)
            
        except Exception as e:
            logger.error(f"Error processing {symbol}: {e}")
    
    def _combine_decisions(self, brain_decision: Dict, agent_decision: Dict) -> Dict:
        """Combine brain and agent decisions"""
        # Simple weighted combination
        brain_weight = 0.6
        agent_weight = 0.4
        
        # Map decisions to numeric values
        decision_map = {'BUY': 1, 'SELL': -1, 'HOLD': 0}
        
        brain_value = decision_map.get(brain_decision.get('decision', 'HOLD'), 0)
        agent_value = decision_map.get(agent_decision.get('action', 'HOLD'), 0)
        
        combined_value = (brain_weight * brain_value + agent_weight * agent_value)
        
        # Determine final action
        if combined_value > 0.3:
            action = 'BUY'
        elif combined_value < -0.3:
            action = 'SELL'
        else:
            action = 'HOLD'
        
        # Combine confidence
        combined_confidence = (
            brain_weight * brain_decision.get('confidence', 0) +
            agent_weight * agent_decision.get('confidence', 0)
        )
        
        return {
            'action': action,
            'confidence': combined_confidence,
            'brain_decision': brain_decision,
            'agent_decision': agent_decision
        }
    
    async def _check_risk(self, symbol: str, decision: Dict) -> bool:
        """Check if trade passes risk management"""
        try:
            # Check drawdown
            if not self.risk_layer['drawdown_monitor'].check_drawdown():
                return False
            
            # Check portfolio risk
            # (Implementation depends on your risk management system)
            
            return True
            
        except Exception as e:
            logger.error(f"Error in risk check: {e}")
            return False
    
    async def _execute_trade(self, symbol: str, decision: Dict) -> None:
        """Execute a trade"""
        try:
            logger.info(f"Executing {decision['action']} for {symbol} (confidence: {decision['confidence']:.2%})")
            
            # Calculate position size
            position_size = self.risk_layer['risk_manager'].calculate_position_size(
                symbol=symbol,
                risk_pct=self.config['risk_layer']['max_risk_per_trade'],
                sl_pips=20.0
            )
            
            # Execute order (simulation mode)
            if self.config['system']['mode'] == 'simulation':
                logger.info(f"SIMULATION: {decision['action']} {position_size} lots of {symbol}")
                self.trades_executed += 1
            else:
                # Execute real order
                if self.execution_layer['execution_manager']:
                    await self.execution_layer['execution_manager'].place_order(
                        symbol=symbol,
                        order_type='market',
                        side=decision['action'].lower(),
                        quantity=position_size
                    )
                    self.trades_executed += 1
            
        except Exception as e:
            logger.error(f"Error executing trade: {e}")
    
    async def _monitoring_loop(self) -> None:
        """System monitoring loop"""
        logger.info("Monitoring loop started")
        
        while self.running:
            try:
                # Health check
                if self.security_layer and self.security_layer['health_check']:
                    health_status = await self.security_layer['health_check'].check()
                    
                    if not health_status.get('healthy', True):
                        logger.warning("System health check failed")
                
                # Log system status
                uptime = (datetime.now() - self.start_time).total_seconds() if self.start_time else 0
                logger.info(
                    f"System Status - Uptime: {uptime:.0f}s, "
                    f"Trades: {self.trades_executed}, "
                    f"PnL: ${self.total_pnl:.2f}"
                )
                
                # Sleep before next check
                await asyncio.sleep(
                    self.config['security_layer']['health_check_interval']
                )
                
            except asyncio.CancelledError:
                logger.info("Monitoring loop cancelled")
                break
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(30)
    
    async def stop(self) -> None:
        """Stop the AlphaAlgo system"""
        if not self.running:
            return
        
        logger.info("=" * 80)
        logger.info("STOPPING ALPHAALGO SYSTEM")
        logger.info("=" * 80)
        
        self.running = False
        
        # Stop all layers in reverse order
        if self.interface_layer:
            if self.interface_layer.get('dashboard'):
                await self.interface_layer['dashboard'].stop()
            if self.interface_layer.get('api_server'):
                await self.interface_layer['api_server'].stop()
        
        if self.data_layer:
            await self.data_layer['processor'].stop()
            await self.data_layer['monitor'].stop()
            await self.data_layer['market_stream'].disconnect()
        
        logger.info("=" * 80)
        logger.info("✓ ALPHAALGO SYSTEM STOPPED")
        logger.info("=" * 80)
        
        # Print final statistics
        if self.start_time:
            uptime = (datetime.now() - self.start_time).total_seconds()
            logger.info(f"Total uptime: {uptime:.0f} seconds")
            logger.info(f"Total trades: {self.trades_executed}")
            logger.info(f"Total PnL: ${self.total_pnl:.2f}")


async def main():
    """Main entry point"""
    # Create necessary directories
    Path('logs').mkdir(exist_ok=True)
    Path('data').mkdir(exist_ok=True)
    Path('config').mkdir(exist_ok=True)
    
    logger.info("=" * 80)
    logger.info("ALPHAALGO COMPLETE TRADING SYSTEM")
    logger.info("Multi-Layer Architecture v2.0")
    logger.info("=" * 80)
    
    # Create system
    system = AlphaAlgoSystem()
    
    # Setup signal handlers for graceful shutdown
    def signal_handler(signum, frame):
        logger.info(f"Received signal {signum}, initiating shutdown...")
        asyncio.create_task(system.stop())
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Initialize system
    if not await system.initialize():
        logger.error("Failed to initialize system")
        sys.exit(1)
    
    # Start system
    try:
        await system.start()
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received")
    except Exception as e:
        logger.error(f"System error: {e}")
        raise
    finally:
        await system.stop()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Shutdown complete")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)
