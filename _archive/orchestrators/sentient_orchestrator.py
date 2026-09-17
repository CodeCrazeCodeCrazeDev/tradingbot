"""
Sentient Orchestrator - Master Controller for Autonomous Self-Evolving Trading Bot

Coordinates all sentient systems:
- Network monitoring and auto-activation
- Knowledge harvesting from the internet
- Learning from other AI systems
- Self-protection and security
- Self-analysis and improvement
- Code evolution and integration
- Profit maximization
"""

import asyncio
import json
import threading
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Set
from pathlib import Path
import logging
import os

from .network_sentinel import NetworkSentinel, ConnectionState, TradingMode, get_network_sentinel
from .knowledge_harvester import KnowledgeHarvester, KnowledgeType
from .ai_learner import AILearner, LearningSource
from .self_defender import SelfDefender, ThreatLevel
from .introspector import Introspector, FlawType, FlawSeverity
from .code_evolver import CodeEvolver, EvolutionType
from .profit_maximizer import ProfitMaximizer, TradeResult

logger = logging.getLogger(__name__)


class SystemState(Enum):
    """Overall system state"""
    OFFLINE = auto()
    INITIALIZING = auto()
    CONNECTING = auto()
    LEARNING = auto()
    TRADING = auto()
    EVOLVING = auto()
    DEFENDING = auto()
    SHUTTING_DOWN = auto()


@dataclass
class SystemStatus:
    """Complete system status"""
    state: SystemState
    is_connected: bool
    trading_mode: TradingMode
    threat_level: ThreatLevel
    knowledge_items: int
    techniques_learned: int
    flaws_detected: int
    changes_applied: int
    total_pnl: float
    uptime_seconds: float
    last_evolution: Optional[datetime]
    active_systems: List[str]


class SentientOrchestrator:
    """
    Master orchestrator for the autonomous self-evolving trading bot.
    
    This is the brain that coordinates:
    1. Network connectivity monitoring
    2. Automatic system activation on WiFi/internet connection
    3. Continuous knowledge gathering from the internet
    4. Learning from other AI trading systems
    5. Self-protection from hackers and threats
    6. Self-analysis and flaw detection
    7. Code evolution and self-improvement
    8. Profit maximization
    
    The system automatically:
    - Activates when internet is detected
    - Switches between live and paper trading based on connection quality
    - Gathers market sentiment and trading knowledge
    - Learns from successful trading systems
    - Protects itself from security threats
    - Identifies and fixes its own flaws
    - Evolves its code to improve performance
    - Maximizes trading profits
    """
    
    def __init__(
        self,
        config: Dict[str, Any] = None,
        data_path: str = "sentient_data/",
    ):
        self.config = config or {}
        self.data_path = Path(data_path)
        self.data_path.mkdir(parents=True, exist_ok=True)
        
        # Initialize all subsystems
        self.network_sentinel = get_network_sentinel()
        self.knowledge_harvester = KnowledgeHarvester(
            db_path=str(self.data_path / "knowledge.db"),
            harvest_interval=self.config.get('harvest_interval', 300),
        )
        self.ai_learner = AILearner(
            db_path=str(self.data_path / "ai_learning.db"),
            learning_interval=self.config.get('learning_interval', 3600),
        )
        self.self_defender = SelfDefender(
            secrets_path=str(self.data_path / "secrets"),
            log_path=str(self.data_path / "security_logs"),
        )
        self.introspector = Introspector(
            project_root="trading_bot",
            analysis_interval=self.config.get('analysis_interval', 3600),
            report_path=str(self.data_path / "introspection_reports"),
        )
        self.code_evolver = CodeEvolver(
            project_root="trading_bot",
            backup_path=str(self.data_path / "code_backups"),
        )
        self.profit_maximizer = ProfitMaximizer(
            initial_capital=self.config.get('initial_capital', 10000.0),
            risk_per_trade=self.config.get('risk_per_trade', 0.02),
            data_path=str(self.data_path / "performance"),
        )
        
        # State
        self.state = SystemState.OFFLINE
        self.is_running = False
        self._main_task: Optional[asyncio.Task] = None
        self._lock = threading.Lock()
        self.start_time: Optional[datetime] = None
        self.last_evolution: Optional[datetime] = None
        
        # Register callbacks
        self._setup_callbacks()
        
        # Statistics
        self.stats = {
            'total_uptime_seconds': 0,
            'connection_events': 0,
            'evolution_cycles': 0,
            'threats_handled': 0,
            'knowledge_applied': 0,
        }
        
        logger.info("SentientOrchestrator initialized")
    
    def _setup_callbacks(self) -> None:
        """Setup callbacks between subsystems"""
        # Network callbacks
        self.network_sentinel.on_connect(self._on_network_connect)
        self.network_sentinel.on_disconnect(self._on_network_disconnect)
        self.network_sentinel.on_mode_change(self._on_mode_change)
        
        # Security callbacks
        self.self_defender.on_threat(self._on_threat_detected)
    
    def _on_network_connect(self, event) -> None:
        """Handle network connection"""
        logger.info("Network connected - activating systems")
        self.stats['connection_events'] += 1
        
        # Start all subsystems
        asyncio.create_task(self._activate_all_systems())
    
    def _on_network_disconnect(self, event) -> None:
        """Handle network disconnection"""
        logger.warning("Network disconnected - entering safe mode")
        
        # Stop non-essential systems
        asyncio.create_task(self._enter_safe_mode())
    
    def _on_mode_change(self, old_mode: TradingMode, new_mode: TradingMode) -> None:
        """Handle trading mode change"""
        logger.info(f"Trading mode changed: {old_mode.name} -> {new_mode.name}")
        
        # Update profit maximizer
        is_live = new_mode == TradingMode.LIVE
        self.profit_maximizer.set_live_mode(is_live)
    
    def _on_threat_detected(self, event) -> None:
        """Handle security threat"""
        logger.warning(f"Threat detected: {event.description}")
        self.stats['threats_handled'] += 1
        
        if event.threat_level.value >= ThreatLevel.HIGH.value:
            # Enter defensive mode
            asyncio.create_task(self._enter_defensive_mode())
    
    async def start(self) -> None:
        """Start the sentient orchestrator"""
        if self.is_running:
            return
        
        logger.info("Starting SentientOrchestrator...")
        self.is_running = True
        self.start_time = datetime.now()
        self.state = SystemState.INITIALIZING
        
        # Start network monitoring first
        self.network_sentinel.start()
        
        # Start security monitoring
        self.self_defender.start()
        
        # Wait for network connection
        self.state = SystemState.CONNECTING
        logger.info("Waiting for network connection...")
        
        connected = await self.network_sentinel.wait_for_connection(timeout=60)
        
        if connected:
            await self._activate_all_systems()
        else:
            logger.warning("No network connection - running in offline mode")
            self.state = SystemState.OFFLINE
        
        # Start main loop
        self._main_task = asyncio.create_task(self._main_loop())
        
        logger.info("SentientOrchestrator started")
    
    async def stop(self) -> None:
        """Stop the sentient orchestrator"""
        logger.info("Stopping SentientOrchestrator...")
        self.is_running = False
        self.state = SystemState.SHUTTING_DOWN
        
        # Stop all subsystems
        await self._stop_all_systems()
        
        if self._main_task:
            self._main_task.cancel()
            try:
                await self._main_task
            except asyncio.CancelledError:
                pass
        
        # Update uptime
        if self.start_time:
            self.stats['total_uptime_seconds'] += (
                datetime.now() - self.start_time
            ).total_seconds()
        
        logger.info("SentientOrchestrator stopped")
    
    async def _activate_all_systems(self) -> None:
        """Activate all subsystems"""
        logger.info("Activating all systems...")
        
        try:
            # Start knowledge harvesting
            await self.knowledge_harvester.start()
            
            # Start AI learning
            await self.ai_learner.start()
            
            # Start introspection
            await self.introspector.start()
            
            # Start profit maximization
            await self.profit_maximizer.start()
            
            self.state = SystemState.TRADING
            logger.info("All systems activated")
            
        except Exception as e:
            logger.error(f"Failed to activate systems: {e}")
    
    async def _stop_all_systems(self) -> None:
        """Stop all subsystems"""
        logger.info("Stopping all systems...")
        
        try:
            await self.knowledge_harvester.stop()
            await self.ai_learner.stop()
            await self.introspector.stop()
            await self.profit_maximizer.stop()
            self.self_defender.stop()
            self.network_sentinel.stop()
        except Exception as e:
            logger.error(f"Error stopping systems: {e}")
    
    async def _enter_safe_mode(self) -> None:
        """Enter safe mode when network is lost"""
        logger.warning("Entering safe mode...")
        
        # Stop internet-dependent systems
        await self.knowledge_harvester.stop()
        await self.ai_learner.stop()
        
        # Keep security and introspection running
        self.state = SystemState.OFFLINE
    
    async def _enter_defensive_mode(self) -> None:
        """Enter defensive mode when threat detected"""
        logger.warning("Entering defensive mode...")
        self.state = SystemState.DEFENDING
        
        # Reduce trading activity
        self.profit_maximizer.trading_mode = TradingMode.DEFENSIVE
    
    async def _main_loop(self) -> None:
        """Main orchestration loop"""
        while self.is_running:
            try:
                await self._orchestration_cycle()
            except Exception as e:
                logger.error(f"Orchestration error: {e}")
            
            await asyncio.sleep(60)  # Run every minute
    
    async def _orchestration_cycle(self) -> None:
        """Run one orchestration cycle"""
        # Check system health
        await self._check_system_health()
        
        # Apply learned knowledge
        await self._apply_knowledge()
        
        # Run evolution if conditions are right
        await self._maybe_evolve()
        
        # Save state
        self._save_state()
    
    async def _check_system_health(self) -> None:
        """Check health of all systems"""
        # Check network
        if not self.network_sentinel.is_ready_for_trading():
            if self.state == SystemState.TRADING:
                logger.warning("Network quality degraded")
        
        # Check security
        threat_level = self.self_defender.get_threat_level()
        if threat_level.value >= ThreatLevel.HIGH.value:
            await self._enter_defensive_mode()
        
        # Check for critical flaws
        critical_flaws = self.introspector.get_flaws(min_severity=FlawSeverity.CRITICAL)
        if critical_flaws:
            logger.warning(f"Critical flaws detected: {len(critical_flaws)}")
    
    async def _apply_knowledge(self) -> None:
        """Apply harvested knowledge to improve trading"""
        # Get actionable insights
        insights = self.knowledge_harvester.get_actionable_insights()
        
        for insight in insights[:5]:  # Process top 5
            try:
                if insight['type'] == 'STRATEGY':
                    # Consider adding new strategy
                    logger.info(f"New strategy insight: {insight['title']}")
                
                elif insight['type'] == 'AI_RESEARCH':
                    # Consider new ML techniques
                    logger.info(f"AI research insight: {insight['title']}")
                
                # Mark as applied
                self.knowledge_harvester.mark_applied(insight['id'])
                self.stats['knowledge_applied'] += 1
                
            except Exception as e:
                logger.debug(f"Error applying insight: {e}")
        
        # Get recommended techniques from AI learner
        techniques = self.ai_learner.get_recommended_techniques(limit=3)
        
        for technique in techniques:
            try:
                if technique.category == 'strategy' and technique.confidence > 0.7:
                    # Consider integrating strategy
                    logger.info(f"Recommended technique: {technique.name}")
                    
            except Exception as e:
                logger.debug(f"Error processing technique: {e}")
    
    async def _maybe_evolve(self) -> None:
        """Run evolution cycle if conditions are right"""
        # Check if enough time has passed
        if self.last_evolution:
            hours_since = (datetime.now() - self.last_evolution).total_seconds() / 3600
            if hours_since < 24:  # Evolve at most once per day
                return
        
        # Check if we have enough data
        metrics = self.profit_maximizer.get_performance_metrics()
        if metrics.total_trades < 50:
            return
        
        # Check if performance needs improvement
        if metrics.profit_factor < 1.5 or metrics.win_rate < 0.5:
            logger.info("Starting evolution cycle...")
            self.state = SystemState.EVOLVING
            
            try:
                await self._run_evolution_cycle()
                self.last_evolution = datetime.now()
                self.stats['evolution_cycles'] += 1
            except Exception as e:
                logger.error(f"Evolution error: {e}")
            
            self.state = SystemState.TRADING
    
    async def _run_evolution_cycle(self) -> None:
        """Run a complete evolution cycle"""
        # Get improvement suggestions from introspector
        suggestions = self.introspector.get_improvement_suggestions()
        
        for suggestion in suggestions[:3]:
            logger.info(f"Improvement suggestion: {suggestion['issue']}")
        
        # Get strategy rankings
        rankings = self.profit_maximizer.get_strategy_ranking()
        
        if rankings:
            best_strategy = rankings[0][0]
            worst_strategy = rankings[-1][0] if len(rankings) > 1 else None
            
            logger.info(f"Best performing strategy: {best_strategy}")
            if worst_strategy:
                logger.info(f"Worst performing strategy: {worst_strategy}")
        
        # Get learned techniques that could help
        techniques = self.ai_learner.get_techniques_by_category('strategy')
        
        for technique in techniques[:2]:
            if technique.confidence > 0.8 and not technique.integrated:
                # Consider adding this technique
                logger.info(f"High-confidence technique available: {technique.name}")
    
    def _save_state(self) -> None:
        """Save current state to disk"""
        state = {
            'state': self.state.name,
            'is_running': self.is_running,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'last_evolution': self.last_evolution.isoformat() if self.last_evolution else None,
            'stats': self.stats,
            'network_status': self.network_sentinel.get_status(),
            'security_status': self.self_defender.get_security_status(),
            'profit_status': self.profit_maximizer.get_status(),
            'timestamp': datetime.now().isoformat(),
        }
        
        state_file = self.data_path / "orchestrator_state.json"
        with open(state_file, 'w') as f:
            json.dump(state, f, indent=2, default=str)
    
    # Public API
    
    def get_status(self) -> SystemStatus:
        """Get complete system status"""
        uptime = 0
        if self.start_time:
            uptime = (datetime.now() - self.start_time).total_seconds()
        
        return SystemStatus(
            state=self.state,
            is_connected=self.network_sentinel.is_ready_for_trading(),
            trading_mode=self.network_sentinel.current_mode,
            threat_level=self.self_defender.get_threat_level(),
            knowledge_items=self.knowledge_harvester.stats.get('total_harvested', 0),
            techniques_learned=self.ai_learner.stats.get('techniques_learned', 0),
            flaws_detected=self.introspector.stats.get('flaws_detected', 0),
            changes_applied=self.code_evolver.stats.get('changes_applied', 0),
            total_pnl=self.profit_maximizer.stats.get('total_pnl', 0),
            uptime_seconds=uptime,
            last_evolution=self.last_evolution,
            active_systems=self._get_active_systems(),
        )
    
    def _get_active_systems(self) -> List[str]:
        """Get list of active systems"""
        systems = []
        
        if self.network_sentinel.is_running:
            systems.append('NetworkSentinel')
        if self.knowledge_harvester.is_running:
            systems.append('KnowledgeHarvester')
        if self.ai_learner.is_running:
            systems.append('AILearner')
        if self.self_defender.is_running:
            systems.append('SelfDefender')
        if self.introspector.is_running:
            systems.append('Introspector')
        if self.profit_maximizer.is_running:
            systems.append('ProfitMaximizer')
        
        return systems
    
    def record_trade(self, trade: TradeResult) -> None:
        """Record a completed trade"""
        self.profit_maximizer.record_trade(trade)
    
    def calculate_position_size(
        self,
        symbol: str,
        entry_price: float,
        stop_loss: float,
        signal_confidence: float = 0.5,
    ) -> float:
        """Calculate optimal position size"""
        return self.profit_maximizer.calculate_position_size(
            symbol, entry_price, stop_loss, signal_confidence
        )
    
    def should_trade(self, signal_confidence: float) -> tuple:
        """Check if we should take a trade"""
        # Check network first
        if not self.network_sentinel.is_ready_for_trading():
            return False, "Network not ready for trading"
        
        # Check security
        if self.self_defender.get_threat_level().value >= ThreatLevel.HIGH.value:
            return False, "High security threat detected"
        
        # Check profit maximizer
        return self.profit_maximizer.should_trade(signal_confidence)
    
    def get_sentiment(self, symbol: str = None) -> Dict[str, Any]:
        """Get current market sentiment"""
        return self.knowledge_harvester.get_sentiment(symbol)
    
    def get_latest_knowledge(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get latest harvested knowledge"""
        items = self.knowledge_harvester.get_latest_knowledge(limit=limit)
        return [item.to_dict() for item in items]
    
    def get_recommended_techniques(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Get recommended techniques to integrate"""
        techniques = self.ai_learner.get_recommended_techniques(limit=limit)
        return [t.to_dict() for t in techniques]
    
    def get_improvement_suggestions(self) -> List[Dict[str, Any]]:
        """Get code improvement suggestions"""
        return self.introspector.get_improvement_suggestions()
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get trading performance metrics"""
        metrics = self.profit_maximizer.get_performance_metrics()
        return {
            'total_trades': metrics.total_trades,
            'win_rate': metrics.win_rate,
            'profit_factor': metrics.profit_factor,
            'sharpe_ratio': metrics.sharpe_ratio,
            'sortino_ratio': metrics.sortino_ratio,
            'max_drawdown': metrics.max_drawdown,
            'total_pnl': metrics.total_pnl,
            'expectancy': metrics.expectancy,
        }
    
    def get_all_stats(self) -> Dict[str, Any]:
        """Get statistics from all subsystems"""
        return {
            'orchestrator': self.stats,
            'network': self.network_sentinel.get_status(),
            'knowledge': self.knowledge_harvester.get_stats(),
            'ai_learner': self.ai_learner.get_stats(),
            'security': self.self_defender.get_stats(),
            'introspector': self.introspector.get_stats(),
            'code_evolver': self.code_evolver.get_stats(),
            'profit_maximizer': self.profit_maximizer.get_stats(),
        }
    
    def is_ready(self) -> bool:
        """Check if system is ready for trading"""
        return (
            self.state == SystemState.TRADING and
            self.network_sentinel.is_ready_for_trading() and
            self.self_defender.get_threat_level().value < ThreatLevel.HIGH.value
        )


# Factory function
def create_sentient_system(config: Dict[str, Any] = None) -> SentientOrchestrator:
    """Create a new sentient trading system"""
    return SentientOrchestrator(config=config)


# Quick start function
async def quick_start(config: Dict[str, Any] = None) -> SentientOrchestrator:
    """Quick start the sentient system"""
    system = create_sentient_system(config)
    await system.start()
    return system
