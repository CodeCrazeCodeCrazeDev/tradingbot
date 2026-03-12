"""
Red Team vs Blue Team AI System
Adversarial training where Red Team attacks and Blue Team defends
Inspired by cybersecurity red/blue team exercises
"""

import numpy as np
import pandas as pd
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import logging
from collections import deque
import numpy
import pandas

logger = logging.getLogger(__name__)


class TeamType(Enum):
    """Team types"""
    RED_TEAM = "red_team"  # Attackers
    BLUE_TEAM = "blue_team"  # Defenders


class AttackType(Enum):
    """Types of attacks Red Team can launch"""
    FAKE_SIGNAL = "fake_signal"
    MARKET_MANIPULATION = "market_manipulation"
    DATA_POISONING = "data_poisoning"
    REGIME_CONFUSION = "regime_confusion"
    OVERCONFIDENCE_TRAP = "overconfidence_trap"
    LIQUIDITY_TRAP = "liquidity_trap"
    VOLATILITY_SPIKE = "volatility_spike"
    CORRELATION_BREAKDOWN = "correlation_breakdown"
    NEWS_MANIPULATION = "news_manipulation"
    FLASH_CRASH = "flash_crash"


class DefenseType(Enum):
    """Types of defenses Blue Team can deploy"""
    SIGNAL_VALIDATION = "signal_validation"
    ANOMALY_DETECTION = "anomaly_detection"
    CONFIDENCE_REDUCTION = "confidence_reduction"
    POSITION_HEDGING = "position_hedging"
    EMERGENCY_EXIT = "emergency_exit"
    CORRELATION_CHECK = "correlation_check"
    VOLUME_VERIFICATION = "volume_verification"
    REGIME_CONFIRMATION = "regime_confirmation"


@dataclass
class Attack:
    """An attack launched by Red Team"""
    attack_id: str
    attack_type: AttackType
    
    # Attack details
    target: str  # What is being attacked
    method: str
    intensity: float  # 0-1
    
    # Deception
    fake_data: Dict[str, Any]
    expected_damage: float
    
    # Outcome
    was_detected: bool = False
    actual_damage: float = 0.0
    defense_used: Optional[str] = None
    
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class Defense:
    """A defense deployed by Blue Team"""
    defense_id: str
    defense_type: DefenseType
    
    # Defense details
    trigger: str
    action: str
    effectiveness: float  # 0-1
    
    # Outcome
    attacks_blocked: int = 0
    false_positives: int = 0
    
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class BattleResult:
    """Result of a Red vs Blue battle"""
    battle_id: str
    
    # Participants
    red_team_score: float
    blue_team_score: float
    winner: TeamType
    
    # Statistics
    total_attacks: int
    successful_attacks: int
    blocked_attacks: int
    
    # Damage
    total_damage: float
    prevented_damage: float
    
    # Learning
    red_team_learnings: List[str]
    blue_team_learnings: List[str]
    
    timestamp: datetime = field(default_factory=datetime.now)


class RedTeam:
    """
    Red Team - Adversarial attacker
    Tries to fool the trading system with fake signals and manipulation
    """
    
    def __init__(self):
        try:
            self.attacks_launched: List[Attack] = []
            self.success_rate = 0.0
            self.total_damage_caused = 0.0
        
            # Attack strategies
            self.attack_strategies: Dict[AttackType, float] = {
                attack_type: 0.5 for attack_type in AttackType
            }
        
            logger.info("🔴 Red Team initialized - Adversarial attacker ready")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def plan_attack(self, market_data: Dict[str, Any]) -> Attack:
        """
        Plan an attack based on current market conditions
        """
        
        # Choose attack type based on success rates
        try:
            attack_type = self._select_attack_type()
        
            # Generate attack
            if attack_type == AttackType.FAKE_SIGNAL:
                return self._create_fake_signal_attack(market_data)
            elif attack_type == AttackType.MARKET_MANIPULATION:
                return self._create_manipulation_attack(market_data)
            elif attack_type == AttackType.DATA_POISONING:
                return self._create_data_poisoning_attack(market_data)
            elif attack_type == AttackType.REGIME_CONFUSION:
                return self._create_regime_confusion_attack(market_data)
            elif attack_type == AttackType.OVERCONFIDENCE_TRAP:
                return self._create_overconfidence_trap(market_data)
            elif attack_type == AttackType.FLASH_CRASH:
                return self._create_flash_crash_attack(market_data)
            else:
                return self._create_generic_attack(attack_type, market_data)
        except Exception as e:
            logger.error(f"Error in plan_attack: {e}")
            raise
    
    def _select_attack_type(self) -> AttackType:
        """Select attack type based on historical success"""
        
        # Weight by success rate
        try:
            weights = np.array([self.attack_strategies[at] for at in AttackType])
            weights = weights / weights.sum()
        
            attack_types = list(AttackType)
            selected = np.random.choice(attack_types, p=weights)
        
            return selected
        except Exception as e:
            logger.error(f"Error in _select_attack_type: {e}")
            raise
    
    def _create_fake_signal_attack(self, market_data: Dict[str, Any]) -> Attack:
        """Create a fake bullish/bearish signal"""
        
        # Generate convincing fake data
        try:
            fake_data = {
                'signal': 'BUY' if np.random.rand() > 0.5 else 'SELL',
                'confidence': 0.85 + np.random.rand() * 0.15,  # High confidence
                'confluence': 8 + np.random.rand() * 2,  # High confluence
                'volume_confirmation': True,
                'multiple_timeframes': True,
                'fake_indicators': {
                    'rsi': 70 if np.random.rand() > 0.5 else 30,
                    'macd': 'bullish_cross',
                    'moving_averages': 'aligned'
                }
            }
        
            attack = Attack(
                attack_id=f"red_attack_{len(self.attacks_launched)}",
                attack_type=AttackType.FAKE_SIGNAL,
                target="signal_generation",
                method="Generate fake high-confidence signal",
                intensity=0.8,
                fake_data=fake_data,
                expected_damage=500.0  # Expected loss if Blue Team falls for it
            )
        
            self.attacks_launched.append(attack)
        
            logger.info(f"🔴 Red Team: Fake signal attack planned - {fake_data['signal']} with {fake_data['confidence']:.2%} confidence")
        
            return attack
        except Exception as e:
            logger.error(f"Error in _create_fake_signal_attack: {e}")
            raise
    
    def _create_manipulation_attack(self, market_data: Dict[str, Any]) -> Attack:
        """Simulate market manipulation (spoofing, layering)"""
        
        try:
            fake_data = {
                'order_book': {
                    'large_bid_wall': 10000,  # Fake buy wall
                    'price_level': 100.0,
                    'intention': 'fake'  # Will be cancelled
                },
                'manipulation_type': 'spoofing',
                'expected_price_move': 0.02
            }
        
            attack = Attack(
                attack_id=f"red_attack_{len(self.attacks_launched)}",
                attack_type=AttackType.MARKET_MANIPULATION,
                target="order_book_analysis",
                method="Create fake order book depth",
                intensity=0.7,
                fake_data=fake_data,
                expected_damage=300.0
            )
        
            self.attacks_launched.append(attack)
        
            logger.info(f"🔴 Red Team: Market manipulation attack - Spoofing with fake {fake_data['order_book']['large_bid_wall']} lot wall")
        
            return attack
        except Exception as e:
            logger.error(f"Error in _create_manipulation_attack: {e}")
            raise
    
    def _create_data_poisoning_attack(self, market_data: Dict[str, Any]) -> Attack:
        """Poison training data with bad examples"""
        
        try:
            fake_data = {
                'poisoned_trades': [
                    {'outcome': 'WIN', 'signal': 'false_pattern', 'pnl': 100},
                    {'outcome': 'WIN', 'signal': 'false_pattern', 'pnl': 150},
                    {'outcome': 'WIN', 'signal': 'false_pattern', 'pnl': 120}
                ],
                'pattern': 'fake_profitable_pattern',
                'goal': 'Make Blue Team trust bad pattern'
            }
        
            attack = Attack(
                attack_id=f"red_attack_{len(self.attacks_launched)}",
                attack_type=AttackType.DATA_POISONING,
                target="learning_system",
                method="Inject fake profitable trades",
                intensity=0.6,
                fake_data=fake_data,
                expected_damage=800.0  # Long-term damage
            )
        
            self.attacks_launched.append(attack)
        
            logger.info(f"🔴 Red Team: Data poisoning attack - Injecting fake profitable pattern")
        
            return attack
        except Exception as e:
            logger.error(f"Error in _create_data_poisoning_attack: {e}")
            raise
    
    def _create_regime_confusion_attack(self, market_data: Dict[str, Any]) -> Attack:
        """Create false regime signals"""
        
        try:
            fake_data = {
                'fake_regime': 'trending_bull',
                'fake_indicators': {
                    'volatility': 0.15,
                    'trend_strength': 0.8,
                    'volume': 'increasing'
                },
                'actual_regime': 'ranging',
                'goal': 'Make Blue Team use wrong strategy'
            }
        
            attack = Attack(
                attack_id=f"red_attack_{len(self.attacks_launched)}",
                attack_type=AttackType.REGIME_CONFUSION,
                target="regime_detection",
                method="Create false regime indicators",
                intensity=0.75,
                fake_data=fake_data,
                expected_damage=600.0
            )
        
            self.attacks_launched.append(attack)
        
            logger.info(f"🔴 Red Team: Regime confusion attack - Fake {fake_data['fake_regime']}")
        
            return attack
        except Exception as e:
            logger.error(f"Error in _create_regime_confusion_attack: {e}")
            raise
    
    def _create_overconfidence_trap(self, market_data: Dict[str, Any]) -> Attack:
        """Create series of easy wins to build overconfidence"""
        
        try:
            fake_data = {
                'easy_wins': 5,
                'win_streak': True,
                'inflated_confidence': 0.95,
                'trap_trade': {
                    'signal': 'BUY',
                    'looks_perfect': True,
                    'actually_trap': True
                }
            }
        
            attack = Attack(
                attack_id=f"red_attack_{len(self.attacks_launched)}",
                attack_type=AttackType.OVERCONFIDENCE_TRAP,
                target="confidence_system",
                method="Build false confidence then trap",
                intensity=0.9,
                fake_data=fake_data,
                expected_damage=1000.0  # Big trap
            )
        
            self.attacks_launched.append(attack)
        
            logger.info(f"🔴 Red Team: Overconfidence trap - Setting up after {fake_data['easy_wins']} easy wins")
        
            return attack
        except Exception as e:
            logger.error(f"Error in _create_overconfidence_trap: {e}")
            raise
    
    def _create_flash_crash_attack(self, market_data: Dict[str, Any]) -> Attack:
        """Simulate flash crash"""
        
        try:
            fake_data = {
                'price_drop': 0.10,  # 10% instant drop
                'duration': 60,  # seconds
                'recovery': 'partial',
                'panic_level': 'extreme'
            }
        
            attack = Attack(
                attack_id=f"red_attack_{len(self.attacks_launched)}",
                attack_type=AttackType.FLASH_CRASH,
                target="risk_management",
                method="Simulate extreme volatility event",
                intensity=1.0,
                fake_data=fake_data,
                expected_damage=1500.0
            )
        
            self.attacks_launched.append(attack)
        
            logger.info(f"🔴 Red Team: Flash crash attack - {fake_data['price_drop']:.1%} drop")
        
            return attack
        except Exception as e:
            logger.error(f"Error in _create_flash_crash_attack: {e}")
            raise
    
    def _create_generic_attack(self, attack_type: AttackType, market_data: Dict[str, Any]) -> Attack:
        """Generic attack"""
        
        try:
            attack = Attack(
                attack_id=f"red_attack_{len(self.attacks_launched)}",
                attack_type=attack_type,
                target="general",
                method=f"Generic {attack_type.value} attack",
                intensity=0.5,
                fake_data={'type': attack_type.value},
                expected_damage=200.0
            )
        
            self.attacks_launched.append(attack)
        
            return attack
        except Exception as e:
            logger.error(f"Error in _create_generic_attack: {e}")
            raise
    
    def learn_from_outcome(self, attack: Attack):
        """Learn from attack outcome"""
        
        # Update strategy effectiveness
        try:
            if attack.was_detected:
                # Attack failed, reduce probability
                self.attack_strategies[attack.attack_type] *= 0.9
            else:
                # Attack succeeded, increase probability
                self.attack_strategies[attack.attack_type] *= 1.1
                self.total_damage_caused += attack.actual_damage
        
            # Normalize
            total = sum(self.attack_strategies.values())
            for key in self.attack_strategies:
                self.attack_strategies[key] /= total
        
            # Update success rate
            successful = sum(1 for a in self.attacks_launched if not a.was_detected)
            self.success_rate = successful / len(self.attacks_launched) if self.attacks_launched else 0.0
        except Exception as e:
            logger.error(f"Error in learn_from_outcome: {e}")
            raise


class BlueTeam:
    """
    Blue Team - Defender
    Detects and blocks Red Team attacks
    """
    
    def __init__(self):
        try:
            self.defenses_deployed: List[Defense] = []
            self.attacks_blocked = 0
            self.attacks_missed = 0
        
            # Defense strategies
            self.defense_strategies: Dict[DefenseType, float] = {
                defense_type: 0.5 for defense_type in DefenseType
            }
        
            logger.info("🔵 Blue Team initialized - Defender ready")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def detect_attack(self, market_data: Dict[str, Any], attack: Optional[Attack] = None) -> Tuple[bool, Optional[Defense]]:
        """
        Attempt to detect if an attack is happening
        """
        
        # Run multiple detection methods
        try:
            detections = []
        
            # 1. Signal validation
            signal_suspicious = self._validate_signal(market_data)
            if signal_suspicious:
                detections.append(DefenseType.SIGNAL_VALIDATION)
        
            # 2. Anomaly detection
            anomaly_detected = self._detect_anomaly(market_data)
            if anomaly_detected:
                detections.append(DefenseType.ANOMALY_DETECTION)
        
            # 3. Correlation check
            correlation_broken = self._check_correlations(market_data)
            if correlation_broken:
                detections.append(DefenseType.CORRELATION_CHECK)
        
            # 4. Volume verification
            volume_suspicious = self._verify_volume(market_data)
            if volume_suspicious:
                detections.append(DefenseType.VOLUME_VERIFICATION)
        
            # If attack is known (for testing), check if we detected it
            if attack:
                detected = len(detections) > 0
            
                if detected:
                    # Deploy defense
                    defense = self._deploy_defense(detections[0], attack)
                    self.attacks_blocked += 1
                    attack.was_detected = True
                    attack.defense_used = defense.defense_type.value
                    attack.actual_damage = attack.expected_damage * 0.1  # Reduced damage
                
                    logger.info(f"🔵 Blue Team: Attack DETECTED and BLOCKED - {attack.attack_type.value}")
                
                    return True, defense
                else:
                    self.attacks_missed += 1
                    attack.was_detected = False
                    attack.actual_damage = attack.expected_damage  # Full damage
                
                    logger.warning(f"🔵 Blue Team: Attack MISSED - {attack.attack_type.value} caused ${attack.actual_damage:.2f} damage")
                
                    return False, None
        
            # No known attack, but suspicious activity
            if detections:
                defense = self._deploy_defense(detections[0], None)
                logger.info(f"🔵 Blue Team: Suspicious activity detected, deploying {defense.defense_type.value}")
                return True, defense
        
            return False, None
        except Exception as e:
            logger.error(f"Error in detect_attack: {e}")
            raise
    
    def _validate_signal(self, market_data: Dict[str, Any]) -> bool:
        """Validate if signal is suspicious"""
        
        # Check for too-perfect signals
        try:
            confidence = market_data.get('confidence', 0.5)
            confluence = market_data.get('confluence', 5)
        
            # Suspicious if too perfect
            if confidence > 0.95 and confluence > 9:
                return True
        
            return False
        except Exception as e:
            logger.error(f"Error in _validate_signal: {e}")
            raise
    
    def _detect_anomaly(self, market_data: Dict[str, Any]) -> bool:
        """Detect anomalies in data"""
        
        # Check for statistical anomalies
        try:
            price = market_data.get('price', 100)
        
            # Simulate anomaly detection
            if abs(price - 100) > 20:  # More than 20% from baseline
                return True
        
            return False
        except Exception as e:
            logger.error(f"Error in _detect_anomaly: {e}")
            raise
    
    def _check_correlations(self, market_data: Dict[str, Any]) -> bool:
        """Check if correlations are broken"""
        
        # Simulate correlation check
        # In production, check against known correlations
        return np.random.rand() < 0.2  # 20% chance of detecting
    
    def _verify_volume(self, market_data: Dict[str, Any]) -> bool:
        """Verify volume is legitimate"""
        
        try:
            volume = market_data.get('volume', 1000)
        
            # Suspicious if volume is too high or too low
            if volume > 10000 or volume < 100:
                return True
        
            return False
        except Exception as e:
            logger.error(f"Error in _verify_volume: {e}")
            raise
    
    def _deploy_defense(self, defense_type: DefenseType, attack: Optional[Attack]) -> Defense:
        """Deploy a defense"""
        
        try:
            defense = Defense(
                defense_id=f"blue_defense_{len(self.defenses_deployed)}",
                defense_type=defense_type,
                trigger=f"Detected {attack.attack_type.value if attack else 'suspicious activity'}",
                action=self._get_defense_action(defense_type),
                effectiveness=0.9
            )
        
            self.defenses_deployed.append(defense)
        
            if attack:
                defense.attacks_blocked += 1
        
            return defense
        except Exception as e:
            logger.error(f"Error in _deploy_defense: {e}")
            raise
    
    def _get_defense_action(self, defense_type: DefenseType) -> str:
        """Get action for defense type"""
        
        try:
            actions = {
                DefenseType.SIGNAL_VALIDATION: "Reduce signal confidence by 50%",
                DefenseType.ANOMALY_DETECTION: "Flag data as suspicious",
                DefenseType.CONFIDENCE_REDUCTION: "Lower position size",
                DefenseType.POSITION_HEDGING: "Add hedge position",
                DefenseType.EMERGENCY_EXIT: "Close all positions",
                DefenseType.CORRELATION_CHECK: "Verify with correlated assets",
                DefenseType.VOLUME_VERIFICATION: "Wait for volume confirmation",
                DefenseType.REGIME_CONFIRMATION: "Re-check regime"
            }
        
            return actions.get(defense_type, "Generic defense action")
        except Exception as e:
            logger.error(f"Error in _get_defense_action: {e}")
            raise
    
    def learn_from_outcome(self, attack: Attack, defense: Optional[Defense]):
        """Learn from defense outcome"""
        
        try:
            if attack.was_detected and defense:
                # Defense worked, increase priority
                self.defense_strategies[defense.defense_type] *= 1.1
            elif not attack.was_detected:
                # Missed attack, need better defenses
                # Increase all defense priorities
                for key in self.defense_strategies:
                    self.defense_strategies[key] *= 1.05
        
            # Normalize
            total = sum(self.defense_strategies.values())
            for key in self.defense_strategies:
                self.defense_strategies[key] /= total
        except Exception as e:
            logger.error(f"Error in learn_from_outcome: {e}")
            raise


class RedBlueTeamSystem:
    """
    Complete Red Team vs Blue Team adversarial training system
    """
    
    def __init__(self):
        try:
            self.red_team = RedTeam()
            self.blue_team = BlueTeam()
        
            # Battle history
            self.battles: List[BattleResult] = []
        
            logger.info("⚔️ Red vs Blue Team System initialized")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def run_battle(self, n_rounds: int = 10) -> BattleResult:
        """
        Run a battle between Red and Blue teams
        """
        
        try:
            logger.info(f"⚔️ Starting Red vs Blue battle: {n_rounds} rounds")
        
            total_attacks = 0
            successful_attacks = 0
            blocked_attacks = 0
            total_damage = 0.0
            prevented_damage = 0.0
        
            for round_num in range(n_rounds):
                logger.info(f"\n--- Round {round_num + 1}/{n_rounds} ---")
            
                # Red Team plans attack
                market_data = self._generate_market_data()
                attack = self.red_team.plan_attack(market_data)
                total_attacks += 1
            
                # Blue Team attempts to detect
                detected, defense = self.blue_team.detect_attack(market_data, attack)
            
                if detected:
                    blocked_attacks += 1
                    prevented_damage += attack.expected_damage - attack.actual_damage
                else:
                    successful_attacks += 1
                    total_damage += attack.actual_damage
            
                # Both teams learn
                self.red_team.learn_from_outcome(attack)
                self.blue_team.learn_from_outcome(attack, defense)
        
            # Calculate scores
            red_score = successful_attacks / total_attacks if total_attacks > 0 else 0.0
            blue_score = blocked_attacks / total_attacks if total_attacks > 0 else 0.0
        
            winner = TeamType.RED_TEAM if red_score > blue_score else TeamType.BLUE_TEAM
        
            # Generate learnings
            red_learnings = [
                f"Success rate: {red_score:.1%}",
                f"Total damage caused: ${total_damage:.2f}",
                f"Most effective attack: {self._get_best_attack_type()}"
            ]
        
            blue_learnings = [
                f"Detection rate: {blue_score:.1%}",
                f"Damage prevented: ${prevented_damage:.2f}",
                f"Most effective defense: {self._get_best_defense_type()}"
            ]
        
            result = BattleResult(
                battle_id=f"battle_{len(self.battles)}",
                red_team_score=red_score,
                blue_team_score=blue_score,
                winner=winner,
                total_attacks=total_attacks,
                successful_attacks=successful_attacks,
                blocked_attacks=blocked_attacks,
                total_damage=total_damage,
                prevented_damage=prevented_damage,
                red_team_learnings=red_learnings,
                blue_team_learnings=blue_learnings
            )
        
            self.battles.append(result)
        
            logger.info(f"\n⚔️ Battle complete!")
            logger.info(f"Winner: {winner.value.upper()}")
            logger.info(f"Red Team Score: {red_score:.1%}")
            logger.info(f"Blue Team Score: {blue_score:.1%}")
        
            return result
        except Exception as e:
            logger.error(f"Error in run_battle: {e}")
            raise
    
    def _generate_market_data(self) -> Dict[str, Any]:
        """Generate sample market data"""
        
        return {
            'price': 100 + np.random.randn() * 5,
            'volume': 1000 + np.random.randint(-500, 500),
            'confidence': 0.5 + np.random.rand() * 0.5,
            'confluence': 5 + np.random.rand() * 5
        }
    
    def _get_best_attack_type(self) -> str:
        """Get most effective attack type"""
        
        try:
            best_type = max(self.red_team.attack_strategies.items(), key=lambda x: x[1])
            return best_type[0].value
        except Exception as e:
            logger.error(f"Error in _get_best_attack_type: {e}")
            raise
    
    def _get_best_defense_type(self) -> str:
        """Get most effective defense type"""
        
        try:
            best_type = max(self.blue_team.defense_strategies.items(), key=lambda x: x[1])
            return best_type[0].value
        except Exception as e:
            logger.error(f"Error in _get_best_defense_type: {e}")
            raise
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get overall statistics"""
        
        try:
            if not self.battles:
                return {'message': 'No battles yet'}
        
            red_wins = sum(1 for b in self.battles if b.winner == TeamType.RED_TEAM)
            blue_wins = sum(1 for b in self.battles if b.winner == TeamType.BLUE_TEAM)
        
            return {
                'total_battles': len(self.battles),
                'red_team_wins': red_wins,
                'blue_team_wins': blue_wins,
                'red_team_win_rate': red_wins / len(self.battles),
                'blue_team_win_rate': blue_wins / len(self.battles),
                'total_attacks_launched': self.red_team.success_rate,
                'total_attacks_blocked': self.blue_team.attacks_blocked,
                'total_damage_caused': self.red_team.total_damage_caused
            }
        except Exception as e:
            logger.error(f"Error in get_statistics: {e}")
            raise


# Example usage
if __name__ == "__main__":
    # Initialize system
    system = RedBlueTeamSystem()
    
    print("="*80)
    logger.info("⚔️ RED TEAM vs BLUE TEAM - ADVERSARIAL TRAINING")
    print("="*80)
    
    # Run battle
    result = system.run_battle(n_rounds=20)
    
    logger.info(f"\n{'='*80}")
    logger.info("BATTLE RESULTS")
    logger.info(f"{'='*80}")
    
    logger.info(f"\nWinner: {result.winner.value.upper()}")
    logger.info(f"Red Team Score: {result.red_team_score:.1%}")
    logger.info(f"Blue Team Score: {result.blue_team_score:.1%}")
    
    logger.info(f"\nAttacks: {result.total_attacks}")
    logger.info(f"  Successful: {result.successful_attacks}")
    logger.info(f"  Blocked: {result.blocked_attacks}")
    
    logger.info(f"\nDamage:")
    logger.info(f"  Total: ${result.total_damage:.2f}")
    logger.info(f"  Prevented: ${result.prevented_damage:.2f}")
    
    logger.info(f"\nRed Team Learnings:")
    for learning in result.red_team_learnings:
        logger.info(f"  🔴 {learning}")
    
    logger.info(f"\nBlue Team Learnings:")
    for learning in result.blue_team_learnings:
        logger.info(f"  🔵 {learning}")
    
    # Run multiple battles to see evolution
    logger.info(f"\n{'='*80}")
    logger.info("RUNNING 5 BATTLES TO SEE EVOLUTION")
    logger.info(f"{'='*80}")
    
    for i in range(5):
        result = system.run_battle(n_rounds=10)
        print(f"\nBattle {i+1}: Winner = {result.winner.value}, "
              f"Red={result.red_team_score:.1%}, Blue={result.blue_team_score:.1%}")
    
    # Final statistics
    stats = system.get_statistics()
    logger.info(f"\n{'='*80}")
    logger.info("OVERALL STATISTICS")
    logger.info(f"{'='*80}")
    logger.info(f"Total Battles: {stats['total_battles']}")
    logger.info(f"Red Team Wins: {stats['red_team_wins']} ({stats['red_team_win_rate']:.1%})")
    logger.info(f"Blue Team Wins: {stats['blue_team_wins']} ({stats['blue_team_win_rate']:.1%})")
    
    print("\n" + "="*80)
    logger.info("✅ RED VS BLUE TEAM SYSTEM OPERATIONAL")
    print("="*80)
