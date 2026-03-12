"""
AAMIS v3.0 - Adversarial Training System
Red Team vs Blue Team AI + Self-Play Trading Wars

This module implements:
1. Red Team vs Blue Team AI - Adversarial training
2. Self-Play Trading Wars (AlphaZero-style)
3. Shadow Mode Learning - Silent observation
4. Agent Duel Training - Simulated opponents
5. Market Manipulation Simulators - Train against fake signals
"""

import logging
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import numpy as np
import random
from collections import deque
import numpy

logger = logging.getLogger(__name__)


class TeamRole(Enum):
    """Team roles in adversarial training"""
    RED_TEAM = "RED_TEAM"  # Attacks and manipulates
    BLUE_TEAM = "BLUE_TEAM"  # Defends and trades
    OBSERVER = "OBSERVER"  # Shadow mode learning


class ManipulationType(Enum):
    """Types of market manipulation"""
    SPOOFING = "SPOOFING"  # Fake orders
    LAYERING = "LAYERING"  # Multiple fake orders
    WASH_TRADING = "WASH_TRADING"  # Self-trading
    PUMP_AND_DUMP = "PUMP_AND_DUMP"  # Price manipulation
    STOP_HUNTING = "STOP_HUNTING"  # Trigger stop losses
    FRONT_RUNNING = "FRONT_RUNNING"  # Trade ahead
    QUOTE_STUFFING = "QUOTE_STUFFING"  # Flood orders
    MOMENTUM_IGNITION = "MOMENTUM_IGNITION"  # Fake momentum


@dataclass
class TrainingAgent:
    """Trading agent for adversarial training"""
    agent_id: str
    role: TeamRole
    strategy: str
    win_rate: float = 0.0
    total_trades: int = 0
    total_wins: int = 0
    total_losses: int = 0
    elo_rating: float = 1500.0  # Chess-style rating
    experience: List[Dict] = field(default_factory=list)
    
    def update_stats(self, won: bool):
        """Update agent statistics"""
        self.total_trades += 1
        if won:
            self.total_wins += 1
        else:
            self.total_losses += 1
        self.win_rate = self.total_wins / self.total_trades if self.total_trades > 0 else 0.0


@dataclass
class TradingDuel:
    """A single trading duel between agents"""
    duel_id: str
    agent1: TrainingAgent
    agent2: TrainingAgent
    start_time: datetime
    end_time: Optional[datetime] = None
    winner: Optional[str] = None
    agent1_pnl: float = 0.0
    agent2_pnl: float = 0.0
    trades_executed: int = 0
    manipulation_detected: int = 0


@dataclass
class ManipulationScenario:
    """Market manipulation scenario"""
    scenario_id: str
    manipulation_type: ManipulationType
    intensity: float  # 0.0 to 1.0
    duration: int  # seconds
    success_rate: float = 0.0
    detection_rate: float = 0.0


class RedTeamAttacker:
    """
    Red Team: Generates market manipulation scenarios
    Goal: Create fake signals and manipulate markets
    """
    
    def __init__(self):
        self.manipulation_history: List[ManipulationScenario] = []
        self.success_count = 0
        self.detection_count = 0
        
    def generate_manipulation(self, market_data: Dict) -> ManipulationScenario:
        """Generate a market manipulation scenario"""
        manipulation_type = random.choice(list(ManipulationType))
        intensity = random.uniform(0.3, 1.0)
        duration = random.randint(10, 300)  # 10 seconds to 5 minutes
        
        scenario = ManipulationScenario(
            scenario_id=f"MANIP_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            manipulation_type=manipulation_type,
            intensity=intensity,
            duration=duration
        )
        
        self.manipulation_history.append(scenario)
        logger.info(f"🔴 Red Team: Generated {manipulation_type.value} manipulation (intensity: {intensity:.2f})")
        
        return scenario
    
    def execute_spoofing(self, market_data: Dict, intensity: float) -> Dict:
        """Execute spoofing attack - fake orders"""
        fake_orders = []
        num_orders = int(10 * intensity)
        
        for i in range(num_orders):
            fake_orders.append({
                'order_id': f"FAKE_{i}",
                'price': market_data.get('price', 1.0) * (1 + random.uniform(-0.01, 0.01)),
                'size': random.uniform(100, 1000) * intensity,
                'side': random.choice(['BUY', 'SELL']),
                'is_fake': True
            })
        
        return {
            'manipulation_type': 'SPOOFING',
            'fake_orders': fake_orders,
            'intensity': intensity
        }
    
    def execute_pump_and_dump(self, market_data: Dict, intensity: float) -> Dict:
        """Execute pump and dump - price manipulation"""
        price = market_data.get('price', 1.0)
        pump_phase_duration = 60 * intensity  # seconds
        dump_phase_duration = 30 * intensity
        
        return {
            'manipulation_type': 'PUMP_AND_DUMP',
            'pump_target': price * (1 + 0.05 * intensity),
            'pump_duration': pump_phase_duration,
            'dump_target': price * (1 - 0.08 * intensity),
            'dump_duration': dump_phase_duration,
            'intensity': intensity
        }
    
    def execute_stop_hunting(self, market_data: Dict, intensity: float) -> Dict:
        """Execute stop hunting - trigger stop losses"""
        price = market_data.get('price', 1.0)
        stop_levels = []
        
        # Common stop loss levels
        for pct in [0.01, 0.02, 0.03, 0.05]:
            stop_levels.append(price * (1 - pct))  # Below current price
            stop_levels.append(price * (1 + pct))  # Above current price
        
        return {
            'manipulation_type': 'STOP_HUNTING',
            'target_levels': stop_levels,
            'intensity': intensity,
            'fake_volume': 1000 * intensity
        }


class BlueTeamDefender:
    """
    Blue Team: Detects manipulation and trades profitably
    Goal: Detect fake signals and make profitable trades
    """
    
    def __init__(self):
        self.detection_history: List[Dict] = []
        self.true_positives = 0
        self.false_positives = 0
        self.true_negatives = 0
        self.false_negatives = 0
        
    def detect_manipulation(self, market_data: Dict, scenario: Optional[ManipulationScenario] = None) -> Dict:
        """Detect market manipulation"""
        # Analyze market data for manipulation signals
        manipulation_score = 0.0
        detected_type = None
        
        # Check for spoofing indicators
        if self._check_spoofing_indicators(market_data):
            manipulation_score += 0.3
            detected_type = ManipulationType.SPOOFING
        
        # Check for pump and dump
        if self._check_pump_dump_indicators(market_data):
            manipulation_score += 0.3
            detected_type = ManipulationType.PUMP_AND_DUMP
        
        # Check for wash trading
        if self._check_wash_trading_indicators(market_data):
            manipulation_score += 0.2
            detected_type = ManipulationType.WASH_TRADING
        
        # Check for stop hunting
        if self._check_stop_hunting_indicators(market_data):
            manipulation_score += 0.2
            detected_type = ManipulationType.STOP_HUNTING
        
        is_manipulation = manipulation_score > 0.5
        
        # Update detection statistics
        if scenario:
            if is_manipulation and scenario.manipulation_type != ManipulationType.SPOOFING:
                self.true_positives += 1
            elif is_manipulation and scenario.manipulation_type == ManipulationType.SPOOFING:
                self.false_positives += 1
            elif not is_manipulation and scenario.manipulation_type != ManipulationType.SPOOFING:
                self.false_negatives += 1
            else:
                self.true_negatives += 1
        
        detection = {
            'is_manipulation': is_manipulation,
            'manipulation_score': manipulation_score,
            'detected_type': detected_type,
            'confidence': manipulation_score,
            'timestamp': datetime.now()
        }
        
        self.detection_history.append(detection)
        
        if is_manipulation:
            logger.info(f"🔵 Blue Team: Detected {detected_type.value if detected_type else 'UNKNOWN'} manipulation (score: {manipulation_score:.2f})")
        
        return detection
    
    def _check_spoofing_indicators(self, market_data: Dict) -> bool:
        """Check for spoofing indicators"""
        # High order-to-trade ratio
        # Rapid order cancellations
        # Orders far from market price
        order_book = market_data.get('order_book', {})
        if not order_book:
            return False
        
        # Simplified check: too many orders at similar prices
        bid_prices = [o['price'] for o in order_book.get('bids', [])]
        if len(bid_prices) > 10:
            price_variance = np.var(bid_prices) if len(bid_prices) > 1 else 0
            if price_variance < 0.0001:  # Very similar prices
                return True
        
        return False
    
    def _check_pump_dump_indicators(self, market_data: Dict) -> bool:
        """Check for pump and dump indicators"""
        # Rapid price increase with high volume
        # Followed by rapid price decrease
        price_history = market_data.get('price_history', [])
        if len(price_history) < 10:
            return False
        
        recent_prices = price_history[-10:]
        price_change = (recent_prices[-1] - recent_prices[0]) / recent_prices[0]
        
        # Check for rapid price movement
        if abs(price_change) > 0.05:  # 5% move
            volume = market_data.get('volume', 0)
            avg_volume = market_data.get('avg_volume', 1)
            if volume > avg_volume * 3:  # 3x normal volume
                return True
        
        return False
    
    def _check_wash_trading_indicators(self, market_data: Dict) -> bool:
        """Check for wash trading indicators"""
        # Same entity buying and selling
        # No change in ownership
        # High volume with minimal price change
        volume = market_data.get('volume', 0)
        price_change = market_data.get('price_change', 0)
        
        if volume > 1000 and abs(price_change) < 0.001:  # High volume, minimal price change
            return True
        
        return False
    
    def _check_stop_hunting_indicators(self, market_data: Dict) -> bool:
        """Check for stop hunting indicators"""
        # Sudden price spike to common stop levels
        # Immediate reversal
        price_history = market_data.get('price_history', [])
        if len(price_history) < 5:
            return False
        
        recent_prices = price_history[-5:]
        
        # Check for spike and reversal
        if len(recent_prices) >= 3:
            spike = abs(recent_prices[-2] - recent_prices[-3]) / recent_prices[-3]
            reversal = abs(recent_prices[-1] - recent_prices[-2]) / recent_prices[-2]
            
            if spike > 0.02 and reversal > 0.015:  # Spike and reversal
                return True
        
        return False
    
    def get_detection_accuracy(self) -> float:
        """Calculate detection accuracy"""
        total = self.true_positives + self.true_negatives + self.false_positives + self.false_negatives
        if total == 0:
            return 0.0
        
        accuracy = (self.true_positives + self.true_negatives) / total
        return accuracy


class SelfPlayArena:
    """
    Self-Play Trading Wars (AlphaZero-style)
    Agents compete against each other to improve
    """
    
    def __init__(self):
        self.agents: List[TrainingAgent] = []
        self.duel_history: List[TradingDuel] = []
        self.generation = 0
        
    def create_agent(self, strategy: str, role: TeamRole = TeamRole.BLUE_TEAM) -> TrainingAgent:
        """Create a new training agent"""
        agent = TrainingAgent(
            agent_id=f"AGENT_{len(self.agents)}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            role=role,
            strategy=strategy
        )
        self.agents.append(agent)
        logger.info(f"⚔️ Created agent: {agent.agent_id} ({strategy})")
        return agent
    
    def run_duel(self, agent1: TrainingAgent, agent2: TrainingAgent, market_data: Dict) -> TradingDuel:
        """Run a trading duel between two agents"""
        duel = TradingDuel(
            duel_id=f"DUEL_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            agent1=agent1,
            agent2=agent2,
            start_time=datetime.now()
        )
        
        logger.info(f"⚔️ Duel started: {agent1.agent_id} vs {agent2.agent_id}")
        
        # Simulate trading duel
        for round_num in range(10):  # 10 rounds
            # Agent 1 trades
            agent1_trade = self._execute_agent_trade(agent1, market_data)
            duel.agent1_pnl += agent1_trade['pnl']
            
            # Agent 2 trades
            agent2_trade = self._execute_agent_trade(agent2, market_data)
            duel.agent2_pnl += agent2_trade['pnl']
            
            duel.trades_executed += 2
        
        # Determine winner
        if duel.agent1_pnl > duel.agent2_pnl:
            duel.winner = agent1.agent_id
            agent1.update_stats(won=True)
            agent2.update_stats(won=False)
        else:
            duel.winner = agent2.agent_id
            agent1.update_stats(won=False)
            agent2.update_stats(won=True)
        
        duel.end_time = datetime.now()
        
        # Update ELO ratings
        self._update_elo_ratings(agent1, agent2, duel.winner == agent1.agent_id)
        
        self.duel_history.append(duel)
        
        logger.info(f"⚔️ Duel finished: Winner = {duel.winner}, PnL: {duel.agent1_pnl:.2f} vs {duel.agent2_pnl:.2f}")
        
        return duel
    
    def _execute_agent_trade(self, agent: TrainingAgent, market_data: Dict) -> Dict:
        """Execute a trade for an agent"""
        # Simplified trading logic
        price = market_data.get('price', 1.0)
        
        # Random trade decision based on strategy
        if random.random() < 0.6:  # 60% chance to trade
            side = random.choice(['BUY', 'SELL'])
            size = random.uniform(0.1, 1.0)
            
            # Simulate PnL
            price_change = random.uniform(-0.02, 0.02)  # -2% to +2%
            pnl = size * price * price_change * (1 if side == 'BUY' else -1)
            
            return {
                'side': side,
                'size': size,
                'price': price,
                'pnl': pnl
            }
        
        return {'side': 'HOLD', 'size': 0, 'price': price, 'pnl': 0.0}
    
    def _update_elo_ratings(self, agent1: TrainingAgent, agent2: TrainingAgent, agent1_won: bool):
        """Update ELO ratings (chess-style)"""
        K = 32  # K-factor
        
        # Expected scores
        expected1 = 1 / (1 + 10 ** ((agent2.elo_rating - agent1.elo_rating) / 400))
        expected2 = 1 / (1 + 10 ** ((agent1.elo_rating - agent2.elo_rating) / 400))
        
        # Actual scores
        actual1 = 1.0 if agent1_won else 0.0
        actual2 = 0.0 if agent1_won else 1.0
        
        # Update ratings
        agent1.elo_rating += K * (actual1 - expected1)
        agent2.elo_rating += K * (actual2 - expected2)
    
    def run_tournament(self, num_rounds: int = 10, market_data: Dict = None) -> Dict:
        """Run a tournament with all agents"""
        if market_data is None:
            market_data = {'price': 1.0, 'volume': 1000}
        
        logger.info(f"🏆 Tournament started: {num_rounds} rounds, {len(self.agents)} agents")
        
        tournament_results = {
            'generation': self.generation,
            'num_rounds': num_rounds,
            'duels': [],
            'rankings': []
        }
        
        # Run round-robin tournament
        for round_num in range(num_rounds):
            for i in range(len(self.agents)):
                for j in range(i + 1, len(self.agents)):
                    duel = self.run_duel(self.agents[i], self.agents[j], market_data)
                    tournament_results['duels'].append(duel)
        
        # Rank agents by ELO rating
        ranked_agents = sorted(self.agents, key=lambda a: a.elo_rating, reverse=True)
        tournament_results['rankings'] = [
            {
                'rank': idx + 1,
                'agent_id': agent.agent_id,
                'elo_rating': agent.elo_rating,
                'win_rate': agent.win_rate,
                'total_trades': agent.total_trades
            }
            for idx, agent in enumerate(ranked_agents)
        ]
        
        self.generation += 1
        
        logger.info(f"🏆 Tournament finished: Champion = {ranked_agents[0].agent_id} (ELO: {ranked_agents[0].elo_rating:.0f})")
        
        return tournament_results


class ShadowModeObserver:
    """
    Shadow Mode Learning: Silent observation without trading
    Learns from market without risking capital
    """
    
    def __init__(self):
        self.observations: deque = deque(maxlen=10000)
        self.learned_patterns: List[Dict] = []
        self.observation_count = 0
        
    def observe(self, market_data: Dict, actual_outcome: Optional[Dict] = None):
        """Observe market without trading"""
        observation = {
            'timestamp': datetime.now(),
            'market_data': market_data,
            'actual_outcome': actual_outcome,
            'observation_id': self.observation_count
        }
        
        self.observations.append(observation)
        self.observation_count += 1
        
        # Learn patterns from observations
        if self.observation_count % 100 == 0:
            self._extract_patterns()
    
    def _extract_patterns(self):
        """Extract patterns from observations"""
        if len(self.observations) < 10:
            return
        
        # Analyze recent observations
        recent_obs = list(self.observations)[-100:]
        
        # Simple pattern: price movements after certain conditions
        for obs in recent_obs:
            market_data = obs.get('market_data', {})
            outcome = obs.get('actual_outcome', {})
            
            if outcome:
                pattern = {
                    'condition': self._extract_condition(market_data),
                    'outcome': outcome,
                    'confidence': 0.5,
                    'observed_count': 1
                }
                
                # Check if pattern already exists
                existing = next((p for p in self.learned_patterns if p['condition'] == pattern['condition']), None)
                if existing:
                    existing['observed_count'] += 1
                    existing['confidence'] = min(0.95, existing['confidence'] + 0.05)
                else:
                    self.learned_patterns.append(pattern)
        
        logger.info(f"👁️ Shadow Mode: Learned {len(self.learned_patterns)} patterns from {self.observation_count} observations")
    
    def _extract_condition(self, market_data: Dict) -> str:
        """Extract condition from market data"""
        price = market_data.get('price', 0)
        volume = market_data.get('volume', 0)
        
        # Simplified condition extraction
        if volume > 1000:
            return "HIGH_VOLUME"
        elif price > 1.05:
            return "HIGH_PRICE"
        elif price < 0.95:
            return "LOW_PRICE"
        else:
            return "NORMAL"
    
    def get_learned_knowledge(self) -> Dict:
        """Get learned knowledge from observations"""
        return {
            'total_observations': self.observation_count,
            'patterns_learned': len(self.learned_patterns),
            'patterns': self.learned_patterns,
            'observation_window': len(self.observations)
        }


class AdversarialTrainingSystem:
    """
    Complete Adversarial Training System
    Combines all training methods
    """
    
    def __init__(self):
        self.red_team = RedTeamAttacker()
        self.blue_team = BlueTeamDefender()
        self.self_play_arena = SelfPlayArena()
        self.shadow_observer = ShadowModeObserver()
        self.training_sessions: List[Dict] = []
        
    def run_training_session(self, market_data: Dict, num_rounds: int = 10) -> Dict:
        """Run a complete training session"""
        session_id = f"SESSION_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        logger.info(f"🎓 Training session started: {session_id}")
        
        session_results = {
            'session_id': session_id,
            'start_time': datetime.now(),
            'num_rounds': num_rounds,
            'red_team_attacks': [],
            'blue_team_detections': [],
            'self_play_duels': [],
            'shadow_observations': []
        }
        
        for round_num in range(num_rounds):
            # Red Team: Generate manipulation
            manipulation = self.red_team.generate_manipulation(market_data)
            session_results['red_team_attacks'].append(manipulation)
            
            # Blue Team: Detect manipulation
            detection = self.blue_team.detect_manipulation(market_data, manipulation)
            session_results['blue_team_detections'].append(detection)
            
            # Shadow Mode: Observe
            self.shadow_observer.observe(market_data, {'manipulation': manipulation, 'detection': detection})
            
            # Update manipulation success/detection rates
            if detection['is_manipulation']:
                manipulation.detection_rate = 1.0
                self.red_team.detection_count += 1
            else:
                manipulation.success_rate = 1.0
                self.red_team.success_count += 1
        
        # Run self-play tournament
        if len(self.self_play_arena.agents) >= 2:
            tournament = self.self_play_arena.run_tournament(num_rounds=5, market_data=market_data)
            session_results['self_play_duels'] = tournament['duels']
        
        session_results['end_time'] = datetime.now()
        session_results['duration'] = (session_results['end_time'] - session_results['start_time']).total_seconds()
        
        # Summary statistics
        session_results['summary'] = {
            'red_team_success_rate': self.red_team.success_count / (self.red_team.success_count + self.red_team.detection_count) if (self.red_team.success_count + self.red_team.detection_count) > 0 else 0.0,
            'blue_team_detection_accuracy': self.blue_team.get_detection_accuracy(),
            'shadow_observations': self.shadow_observer.observation_count,
            'patterns_learned': len(self.shadow_observer.learned_patterns)
        }
        
        self.training_sessions.append(session_results)
        
        logger.info(f"🎓 Training session completed: {session_id}")
        logger.info(f"   Red Team Success: {session_results['summary']['red_team_success_rate']:.2%}")
        logger.info(f"   Blue Team Accuracy: {session_results['summary']['blue_team_detection_accuracy']:.2%}")
        logger.info(f"   Patterns Learned: {session_results['summary']['patterns_learned']}")
        
        return session_results
    
    def get_training_report(self) -> Dict:
        """Get comprehensive training report"""
        return {
            'total_sessions': len(self.training_sessions),
            'red_team_stats': {
                'total_attacks': len(self.red_team.manipulation_history),
                'success_count': self.red_team.success_count,
                'detection_count': self.red_team.detection_count,
                'success_rate': self.red_team.success_count / len(self.red_team.manipulation_history) if self.red_team.manipulation_history else 0.0
            },
            'blue_team_stats': {
                'total_detections': len(self.blue_team.detection_history),
                'true_positives': self.blue_team.true_positives,
                'false_positives': self.blue_team.false_positives,
                'accuracy': self.blue_team.get_detection_accuracy()
            },
            'self_play_stats': {
                'total_agents': len(self.self_play_arena.agents),
                'total_duels': len(self.self_play_arena.duel_history),
                'generation': self.self_play_arena.generation
            },
            'shadow_mode_stats': self.shadow_observer.get_learned_knowledge()
        }


# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Create adversarial training system
    training_system = AdversarialTrainingSystem()
    
    # Create some agents for self-play
    training_system.self_play_arena.create_agent("AGGRESSIVE", TeamRole.BLUE_TEAM)
    training_system.self_play_arena.create_agent("CONSERVATIVE", TeamRole.BLUE_TEAM)
    training_system.self_play_arena.create_agent("BALANCED", TeamRole.BLUE_TEAM)
    
    # Run training session
    market_data = {
        'price': 1.0,
        'volume': 1000,
        'price_history': [0.98, 0.99, 1.0, 1.01, 1.02],
        'order_book': {'bids': [], 'asks': []},
        'avg_volume': 800
    }
    
    session_results = training_system.run_training_session(market_data, num_rounds=20)
    
    # Get training report
    report = training_system.get_training_report()
    print("\n" + "="*80)
    logger.info("ADVERSARIAL TRAINING REPORT")
    print("="*80)
    logger.info(f"Total Sessions: {report['total_sessions']}")
    logger.info(f"\nRed Team (Attacker):")
    logger.info(f"  Total Attacks: {report['red_team_stats']['total_attacks']}")
    logger.info(f"  Success Rate: {report['red_team_stats']['success_rate']:.2%}")
    logger.info(f"\nBlue Team (Defender):")
    logger.info(f"  Total Detections: {report['blue_team_stats']['total_detections']}")
    logger.info(f"  Detection Accuracy: {report['blue_team_stats']['accuracy']:.2%}")
    logger.info(f"\nSelf-Play Arena:")
    logger.info(f"  Total Agents: {report['self_play_stats']['total_agents']}")
    logger.info(f"  Total Duels: {report['self_play_stats']['total_duels']}")
    logger.info(f"\nShadow Mode:")
    logger.info(f"  Total Observations: {report['shadow_mode_stats']['total_observations']}")
    logger.info(f"  Patterns Learned: {report['shadow_mode_stats']['patterns_learned']}")
    print("="*80)
