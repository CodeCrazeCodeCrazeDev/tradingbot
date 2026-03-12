"""
Eternal Evolution Orchestrator - The Master Controller
=======================================================

The master orchestrator that coordinates all evolution engines:
- Risk Evolution
- Architecture Evolution
- Data Evolution
- Security Evolution

While ALWAYS maintaining the immutable trading core identity.

This bot evolves EVERYTHING except its fundamental purpose:
IT IS AND ALWAYS WILL BE A TRADING BOT.
"""

import asyncio
import logging
import json
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
import threading

from .immutable_core import ImmutableTradingCore, get_immutable_core
from .risk_evolution import RiskEvolutionEngine
from .architecture_evolution import ArchitectureEvolutionEngine
from .data_evolution import DataEvolutionEngine
from .security_evolution import SecurityEvolutionEngine

logger = logging.getLogger(__name__)


class EvolutionDimension(Enum):
    """Dimensions that can evolve"""
    RISK_MANAGEMENT = "risk_management"
    ARCHITECTURE = "architecture"
    DATA_QUALITY = "data_quality"
    LEVEL2_DATA = "level2_data"
    ALTERNATIVE_DATA = "alternative_data"
    SECURITY = "security"


@dataclass
class EvolutionCycle:
    """Record of an evolution cycle"""
    cycle_id: str
    timestamp: datetime
    dimensions_evolved: List[str]
    changes_made: List[Dict[str, Any]]
    performance_before: Dict[str, float]
    performance_after: Optional[Dict[str, float]] = None
    success: bool = True


@dataclass
class TradingSignal:
    """A trading signal from the evolved system"""
    signal_id: str
    symbol: str
    direction: str  # buy, sell, hold
    confidence: float
    entry_price: float
    stop_loss: float
    take_profit: float
    position_size: float
    reasoning: str
    risk_score: float
    data_quality_score: float
    security_validated: bool
    timestamp: datetime = field(default_factory=datetime.now)


class EternalEvolutionOrchestrator:
    """
    Eternal Evolution Orchestrator
    
    The master controller that:
    1. Maintains the immutable trading core
    2. Coordinates all evolution engines
    3. Ensures the bot remains a trading bot
    4. Continuously improves all dimensions
    5. Tracks evolution progress
    6. Provides unified trading interface
    
    CORE PRINCIPLE: Everything evolves EXCEPT the trading identity.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # The immutable core - THIS NEVER CHANGES
        self.immutable_core = get_immutable_core()
        
        # Verify we are still a trading bot
        if not self.immutable_core.is_trading_bot():
            raise RuntimeError("CRITICAL: System is no longer a trading bot!")
        
        # Evolution engines - THESE EVOLVE
        self.risk_engine = RiskEvolutionEngine(config.get('risk', {}))
        self.architecture_engine = ArchitectureEvolutionEngine(config.get('architecture', {}))
        self.data_engine = DataEvolutionEngine(config.get('data', {}))
        self.security_engine = SecurityEvolutionEngine(config.get('security', {}))
        
        # Evolution configuration
        self.evolution_interval = timedelta(
            hours=config.get('evolution_interval_hours', 6)
        )
        self.last_evolution = datetime.now()
        self.auto_evolve = config.get('auto_evolve', True)
        
        # Evolution history
        self.evolution_cycles: List[EvolutionCycle] = []
        self.total_evolutions = 0
        
        # Performance tracking
        self.performance_history: List[Dict] = []
        
        # State
        self.running = False
        self._evolution_lock = threading.Lock()
        
        # Persistence
        self.state_path = Path(config.get('state_path', 'eternal_evolution_state'))
        self.state_path.mkdir(parents=True, exist_ok=True)
        
        self._load_state()
        
        try:
            # Log identity declaration (avoid print for Unicode issues)
            logger.info(self.immutable_core.declare_identity())
        except UnicodeEncodeError:
            logger.info("Eternal Evolution Orchestrator identity initialized")
        logger.info("Eternal Evolution Orchestrator initialized")
        logger.info(f"Evolution dimensions: {[d.value for d in EvolutionDimension]}")
    
    async def start(self):
        """Start the eternal evolution system"""
        self.running = True
        logger.info("Starting Eternal Evolution System...")
        
        # Start background evolution loop
        if self.auto_evolve:
            asyncio.create_task(self._evolution_loop())
        
        logger.info("Eternal Evolution System started")
    
    async def stop(self):
        """Stop the system"""
        self.running = False
        self.architecture_engine.shutdown()
        self._save_state()
        logger.info("Eternal Evolution System stopped")
    
    async def _evolution_loop(self):
        """Background evolution loop"""
        while self.running:
            try:
                # Check if it's time to evolve
                if datetime.now() - self.last_evolution >= self.evolution_interval:
                    await self.evolve_all()
                
                await asyncio.sleep(60)  # Check every minute
                
            except Exception as e:
                logger.error(f"Evolution loop error: {e}")
                await asyncio.sleep(300)  # Wait 5 minutes on error
    
    async def evolve_all(self) -> EvolutionCycle:
        """
        Run evolution cycle on all dimensions.
        
        This is where the magic happens - the bot improves itself
        while NEVER changing its core trading identity.
        """
        with self._evolution_lock:
            logger.info("=" * 60)
            logger.info("STARTING ETERNAL EVOLUTION CYCLE")
            logger.info("=" * 60)
            
            # First, verify we're still a trading bot
            if not self.immutable_core.is_trading_bot():
                raise RuntimeError("CRITICAL: Identity compromised!")
            
            cycle_id = f"evo_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            changes = []
            dimensions_evolved = []
            
            # Capture performance before
            performance_before = self._capture_performance()
            
            # Evolve Risk Management
            logger.info("Evolving Risk Management...")
            try:
                risk_changes = await self.risk_engine.evolve()
                if risk_changes:
                    for c in risk_changes:
                        change_dict = c.__dict__ if hasattr(c, '__dict__') else c if isinstance(c, dict) else {'change': str(c)}
                        changes.append({'dimension': 'risk', **change_dict})
                    dimensions_evolved.append(EvolutionDimension.RISK_MANAGEMENT.value)
                    logger.info(f"  - {len(risk_changes)} risk improvements")
            except Exception as e:
                logger.error(f"Risk evolution failed: {e}")
            
            # Evolve Architecture
            logger.info("Evolving Architecture & Stability...")
            try:
                arch_changes = await self.architecture_engine.evolve()
                if arch_changes:
                    for c in arch_changes:
                        change_dict = c.__dict__ if hasattr(c, '__dict__') else c if isinstance(c, dict) else {'change': str(c)}
                        changes.append({'dimension': 'architecture', **change_dict})
                    dimensions_evolved.append(EvolutionDimension.ARCHITECTURE.value)
                    logger.info(f"  - {len(arch_changes)} architecture improvements")
            except Exception as e:
                logger.error(f"Architecture evolution failed: {e}")
            
            # Evolve Data Quality
            logger.info("Evolving Data Quality & Processing...")
            try:
                data_changes = await self.data_engine.evolve()
                if data_changes:
                    changes.extend([{'dimension': 'data', **c} for c in data_changes])
                    dimensions_evolved.append(EvolutionDimension.DATA_QUALITY.value)
                    if any('level2' in str(c).lower() for c in data_changes):
                        dimensions_evolved.append(EvolutionDimension.LEVEL2_DATA.value)
                    if any('alt' in str(c).lower() for c in data_changes):
                        dimensions_evolved.append(EvolutionDimension.ALTERNATIVE_DATA.value)
                    logger.info(f"  - {len(data_changes)} data improvements")
            except Exception as e:
                logger.error(f"Data evolution failed: {e}")
            
            # Evolve Security
            logger.info("Evolving Security...")
            try:
                security_changes = await self.security_engine.evolve()
                if security_changes:
                    changes.extend([{'dimension': 'security', **c} for c in security_changes])
                    dimensions_evolved.append(EvolutionDimension.SECURITY.value)
                    logger.info(f"  - {len(security_changes)} security improvements")
            except Exception as e:
                logger.error(f"Security evolution failed: {e}")
            
            # Create evolution cycle record
            cycle = EvolutionCycle(
                cycle_id=cycle_id,
                timestamp=datetime.now(),
                dimensions_evolved=dimensions_evolved,
                changes_made=changes,
                performance_before=performance_before,
                success=True
            )
            
            self.evolution_cycles.append(cycle)
            self.total_evolutions += 1
            self.last_evolution = datetime.now()
            
            # Final identity check
            if not self.immutable_core.is_trading_bot():
                raise RuntimeError("CRITICAL: Evolution corrupted identity!")
            
            logger.info("=" * 60)
            logger.info(f"EVOLUTION CYCLE COMPLETE: {len(changes)} total changes")
            logger.info(f"Dimensions evolved: {dimensions_evolved}")
            logger.info("Identity verified: Still a trading bot ✓")
            logger.info("=" * 60)
            
            self._save_state()
            return cycle
    
    async def generate_signal(
        self,
        symbol: str,
        market_data: Dict[str, Any]
    ) -> TradingSignal:
        """
        Generate a trading signal using all evolved systems.
        
        This is the core trading function - what makes this a TRADING BOT.
        """
        # Verify identity
        if not self.immutable_core.is_trading_bot():
            raise RuntimeError("Cannot generate signal: Not a trading bot!")
        
        # Security validation
        is_valid, reason = self.security_engine.validate_request({
            'type': 'signal_generation',
            'symbol': symbol,
            'data': market_data,
            'ip': 'internal',
            'nonce': self.security_engine.generate_nonce()
        })
        
        if not is_valid:
            logger.warning(f"Security validation failed: {reason}")
            return TradingSignal(
                signal_id=f"blocked_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                symbol=symbol,
                direction='hold',
                confidence=0,
                entry_price=0,
                stop_loss=0,
                take_profit=0,
                position_size=0,
                reasoning=f"Security blocked: {reason}",
                risk_score=1.0,
                data_quality_score=0,
                security_validated=False
            )
        
        # Data quality validation
        is_quality, issues = self.data_engine.validate_data(market_data, 'market')
        data_quality_score = 1.0 if is_quality else 0.5
        
        if not is_quality:
            logger.warning(f"Data quality issues: {issues}")
            market_data = self.data_engine.clean_data(market_data)
        
        # Get alternative data signal
        alt_signal = self.data_engine.get_alternative_signal(symbol)
        
        # Analyze market (using immutable core interface)
        analysis = self.immutable_core._analyze_market(market_data)
        
        # Make trading decision (using immutable core interface)
        decision = self.immutable_core._make_trading_decision({
            **analysis,
            'alt_signal': alt_signal,
            'symbol': symbol
        })
        
        # Calculate position size using evolved risk engine
        current_price = market_data.get('price', market_data.get('close', 0))
        volatility = market_data.get('volatility', market_data.get('atr', 0.02))
        
        # Determine direction based on analysis
        direction = 'hold'
        confidence = 0.5
        
        if alt_signal.get('composite_signal', 0) > 0.3:
            direction = 'buy'
            confidence = 0.5 + alt_signal.get('strength', 0) * 0.3
        elif alt_signal.get('composite_signal', 0) < -0.3:
            direction = 'sell'
            confidence = 0.5 + alt_signal.get('strength', 0) * 0.3
        
        # Calculate risk-adjusted position
        account_balance = market_data.get('account_balance', 10000)
        
        if direction != 'hold' and current_price > 0:
            # Calculate stop loss using evolved parameters
            atr = volatility * current_price
            stop_loss = self.risk_engine.get_stop_loss(
                current_price, atr, 'long' if direction == 'buy' else 'short'
            )
            
            # Calculate take profit using evolved parameters
            take_profit = self.risk_engine.get_take_profit(
                current_price, stop_loss, 'long' if direction == 'buy' else 'short'
            )
            
            # Calculate position size using evolved parameters
            position_size = self.risk_engine.get_position_size(
                account_balance, current_price, stop_loss, volatility
            )
        else:
            stop_loss = 0
            take_profit = 0
            position_size = 0
        
        # Validate action against immutable core
        action = {
            'type': direction,
            'risk_percent': (abs(current_price - stop_loss) / current_price) if current_price > 0 else 0,
            'stop_loss': stop_loss,
            'confidence': confidence
        }
        
        is_valid_action, action_reason = self.immutable_core.validate_action(action)
        
        if not is_valid_action:
            logger.warning(f"Action validation failed: {action_reason}")
            direction = 'hold'
            position_size = 0
        
        # Calculate risk score
        risk_score = self._calculate_risk_score(market_data, direction, position_size)
        
        # Record trade for learning
        self.risk_engine.record_trade({
            'symbol': symbol,
            'direction': direction,
            'entry_price': current_price,
            'stop_loss': stop_loss,
            'take_profit': take_profit,
            'position_size': position_size,
            'confidence': confidence
        })
        
        signal = TradingSignal(
            signal_id=f"sig_{datetime.now().strftime('%Y%m%d%H%M%S')}_{symbol}",
            symbol=symbol,
            direction=direction,
            confidence=confidence,
            entry_price=current_price,
            stop_loss=stop_loss,
            take_profit=take_profit,
            position_size=position_size,
            reasoning=self._generate_reasoning(analysis, alt_signal, direction),
            risk_score=risk_score,
            data_quality_score=data_quality_score,
            security_validated=True
        )
        
        return signal
    
    def _calculate_risk_score(
        self,
        market_data: Dict,
        direction: str,
        position_size: float
    ) -> float:
        """Calculate overall risk score"""
        risk_score = 0.5  # Base risk
        
        # Volatility risk
        volatility = market_data.get('volatility', 0.02)
        if volatility > 0.05:
            risk_score += 0.2
        elif volatility > 0.03:
            risk_score += 0.1
        
        # Position size risk
        account_balance = market_data.get('account_balance', 10000)
        if account_balance > 0:
            position_risk = (position_size * market_data.get('price', 0)) / account_balance
            if position_risk > 0.1:
                risk_score += 0.2
        
        # Direction risk (trading against trend)
        trend = market_data.get('trend', 'neutral')
        if (direction == 'buy' and trend == 'down') or (direction == 'sell' and trend == 'up'):
            risk_score += 0.1
        
        return min(risk_score, 1.0)
    
    def _generate_reasoning(
        self,
        analysis: Dict,
        alt_signal: Dict,
        direction: str
    ) -> str:
        """Generate human-readable reasoning for the signal"""
        reasons = []
        
        if direction == 'buy':
            reasons.append("Bullish signal detected")
        elif direction == 'sell':
            reasons.append("Bearish signal detected")
        else:
            reasons.append("No clear directional signal")
        
        if alt_signal.get('composite_signal', 0) != 0:
            strength = alt_signal.get('strength', 0)
            sources = len(alt_signal.get('sources', []))
            reasons.append(f"Alternative data: {alt_signal.get('direction', 'neutral')} ({sources} sources, strength: {strength:.2f})")
        
        if alt_signal.get('confidence', 0) > 0.7:
            reasons.append("High confidence from multiple data sources")
        
        return " | ".join(reasons)
    
    def _capture_performance(self) -> Dict[str, float]:
        """Capture current performance metrics"""
        risk_stats = self.risk_engine.get_statistics()
        arch_stats = self.architecture_engine.get_statistics()
        data_stats = self.data_engine.get_statistics()
        security_stats = self.security_engine.get_statistics()
        
        return {
            'risk_sharpe': risk_stats.get('best_sharpe_achieved', 0),
            'risk_evolutions': risk_stats.get('evolutions_performed', 0),
            'arch_uptime': arch_stats.get('uptime_hours', 0),
            'arch_errors': arch_stats.get('errors_recovered', 0),
            'data_quality': data_stats.get('avg_source_reliability', 0),
            'security_blocked': security_stats.get('attacks_blocked', 0),
            'total_evolutions': self.total_evolutions
        }
    
    def get_evolution_summary(self) -> Dict[str, Any]:
        """Get summary of all evolutions"""
        return {
            'identity': {
                'name': self.immutable_core.identity.name,
                'is_trading_bot': self.immutable_core.is_trading_bot(),
                'identity_hash': self.immutable_core.identity.get_identity_hash()[:16]
            },
            'evolution_stats': {
                'total_cycles': len(self.evolution_cycles),
                'total_changes': sum(len(c.changes_made) for c in self.evolution_cycles),
                'last_evolution': self.last_evolution.isoformat(),
                'next_evolution': (self.last_evolution + self.evolution_interval).isoformat()
            },
            'dimension_stats': {
                'risk': self.risk_engine.get_statistics(),
                'architecture': self.architecture_engine.get_statistics(),
                'data': self.data_engine.get_statistics(),
                'security': self.security_engine.get_statistics()
            },
            'current_performance': self._capture_performance()
        }
    
    def get_evolution_history(self, limit: int = 10) -> List[Dict]:
        """Get recent evolution history"""
        return [
            {
                'cycle_id': c.cycle_id,
                'timestamp': c.timestamp.isoformat(),
                'dimensions': c.dimensions_evolved,
                'changes_count': len(c.changes_made),
                'success': c.success
            }
            for c in self.evolution_cycles[-limit:]
        ]
    
    def _save_state(self):
        """Save orchestrator state"""
        state = {
            'total_evolutions': self.total_evolutions,
            'last_evolution': self.last_evolution.isoformat(),
            'evolution_cycles': [
                {
                    'cycle_id': c.cycle_id,
                    'timestamp': c.timestamp.isoformat(),
                    'dimensions_evolved': c.dimensions_evolved,
                    'changes_count': len(c.changes_made),
                    'success': c.success
                }
                for c in self.evolution_cycles[-100:]  # Keep last 100
            ],
            'performance_history': self.performance_history[-100:]
        }
        
        state_file = self.state_path / 'orchestrator_state.json'
        with open(state_file, 'w') as f:
            json.dump(state, f, indent=2, default=str)
    
    def _load_state(self):
        """Load previous state"""
        state_file = self.state_path / 'orchestrator_state.json'
        
        if state_file.exists():
            try:
                with open(state_file, 'r') as f:
                    state = json.load(f)
                
                self.total_evolutions = state.get('total_evolutions', 0)
                self.last_evolution = datetime.fromisoformat(state.get('last_evolution', datetime.now().isoformat()))
                self.performance_history = state.get('performance_history', [])
                
                logger.info(f"Loaded state: {self.total_evolutions} previous evolutions")
                
            except Exception as e:
                logger.error(f"Failed to load orchestrator state: {e}")
    
    def declare_purpose(self) -> str:
        """Declare the bot's purpose and evolution status"""
        summary = self.get_evolution_summary()
        
        return f"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                     ETERNAL EVOLUTION TRADING BOT                             ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                                                                              ║
║  IMMUTABLE IDENTITY:                                                         ║
║  ─────────────────────────────────────────────────────────────────────────── ║
║  Name: {summary['identity']['name']:<67} ║
║  Is Trading Bot: {'YES ✓' if summary['identity']['is_trading_bot'] else 'NO ✗':<64} ║
║  Identity Hash: {summary['identity']['identity_hash']:<65} ║
║                                                                              ║
║  EVOLUTION STATUS:                                                           ║
║  ─────────────────────────────────────────────────────────────────────────── ║
║  Total Evolution Cycles: {summary['evolution_stats']['total_cycles']:<55} ║
║  Total Changes Made: {summary['evolution_stats']['total_changes']:<59} ║
║  Last Evolution: {summary['evolution_stats']['last_evolution'][:19]:<63} ║
║                                                                              ║
║  EVOLVING DIMENSIONS:                                                        ║
║  ─────────────────────────────────────────────────────────────────────────── ║
║  ✓ Risk Management      - Position sizing, stops, portfolio allocation       ║
║  ✓ Architecture         - Stability, performance, error handling             ║
║  ✓ Data Quality         - Validation, cleaning, enrichment                   ║
║  ✓ Level 2 Data         - Order book, liquidity, microstructure              ║
║  ✓ Alternative Data     - Sentiment, news, social, blockchain                ║
║  ✓ Security             - Attack prevention, encryption, access control      ║
║                                                                              ║
║  NEVER CHANGES:                                                              ║
║  ─────────────────────────────────────────────────────────────────────────── ║
║  ✗ Core Purpose         - Generate profitable trades                         ║
║  ✗ Trading Identity     - Is and always will be a trading bot                ║
║  ✗ Ethical Boundaries   - No manipulation, fair trading only                 ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""


# Factory function
def create_eternal_evolution_system(config: Optional[Dict] = None) -> EternalEvolutionOrchestrator:
    """Create an eternal evolution trading system"""
    return EternalEvolutionOrchestrator(config)


# Quick start helper
async def quick_start(config: Optional[Dict] = None):
    """Quick start the eternal evolution system"""
    system = create_eternal_evolution_system(config)
    await system.start()
    return system
