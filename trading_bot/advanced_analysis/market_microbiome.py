"""
Market Microbiome - Ecosystem Modeling

Models the market as an ecosystem, identifying and tracking the behavior of
different "species" (High-Frequency Algorithms, Retail Herd, Institutional Whales)
through their order flow signatures.

Features:
- Market participant classification
- Species behavior tracking
- Reaction prediction to events
- Ecosystem health monitoring
- Predator-prey dynamics
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
from collections import deque

logger = logging.getLogger(__name__)


class MarketSpecies(Enum):
    """Types of market participants (species)"""
    HFT_PREDATOR = "hft_predator"           # High-frequency market makers
    HFT_ARBITRAGEUR = "hft_arbitrageur"     # Statistical arbitrage HFTs
    INSTITUTIONAL_WHALE = "institutional_whale"  # Large institutional investors
    INSTITUTIONAL_DOLPHIN = "institutional_dolphin"  # Medium institutions
    RETAIL_HERD = "retail_herd"             # Retail traders following trends
    RETAIL_CONTRARIAN = "retail_contrarian"  # Retail counter-trend traders
    ALGO_MOMENTUM = "algo_momentum"          # Momentum algorithms
    ALGO_MEAN_REVERSION = "algo_mean_reversion"  # Mean reversion algos
    MARKET_MAKER = "market_maker"           # Traditional market makers
    NEWS_TRADER = "news_trader"             # News-driven traders


class BehaviorPattern(Enum):
    """Behavioral patterns"""
    ACCUMULATING = "accumulating"
    DISTRIBUTING = "distributing"
    HUNTING = "hunting"          # Stop hunting
    PROVIDING = "providing"      # Liquidity provision
    CONSUMING = "consuming"      # Liquidity consumption
    FLEEING = "fleeing"          # Risk-off behavior
    CHASING = "chasing"          # Momentum chasing
    FADING = "fading"            # Counter-trend
    DORMANT = "dormant"          # Inactive


class EcosystemHealth(Enum):
    """Market ecosystem health states"""
    THRIVING = "thriving"        # Balanced, healthy market
    STRESSED = "stressed"        # Elevated stress
    FRAGILE = "fragile"          # Vulnerable to shocks
    CRISIS = "crisis"            # Active crisis
    RECOVERING = "recovering"    # Post-crisis recovery


@dataclass
class SpeciesSignature:
    """Order flow signature for a species"""
    species: MarketSpecies
    avg_order_size: float
    order_frequency: float  # Orders per minute
    cancel_ratio: float
    aggression_ratio: float  # Market vs limit orders
    time_in_market: float  # Average order lifetime
    clustering_coefficient: float  # How clustered orders are
    
    def to_dict(self) -> Dict[str, Any]:
        """
        to_dict function.

    Auto-documented by QwenCodeMender.
        """
        return {
            'species': self.species.value,
            'avg_order_size': self.avg_order_size,
            'order_frequency': self.order_frequency,
            'cancel_ratio': self.cancel_ratio,
            'aggression_ratio': self.aggression_ratio,
            'time_in_market': self.time_in_market,
            'clustering_coefficient': self.clustering_coefficient
        }


@dataclass
class SpeciesActivity:
    """Current activity of a species"""
    species: MarketSpecies
    timestamp: datetime
    activity_level: float  # 0-1
    behavior: BehaviorPattern
    estimated_position: float  # Net position estimate
    confidence: float
    recent_orders: int
    
    def to_dict(self) -> Dict[str, Any]:
        """
        to_dict function.

    Auto-documented by QwenCodeMender.
        """
        return {
            'species': self.species.value,
            'timestamp': self.timestamp.isoformat(),
            'activity_level': self.activity_level,
            'behavior': self.behavior.value,
            'estimated_position': self.estimated_position,
            'confidence': self.confidence,
            'recent_orders': self.recent_orders
        }


@dataclass
class EcosystemState:
    """Current state of market ecosystem"""
    timestamp: datetime
    health: EcosystemHealth
    diversity_index: float  # Species diversity
    predator_prey_ratio: float
    liquidity_depth: float
    volatility_regime: str
    dominant_species: MarketSpecies
    species_activities: List[SpeciesActivity]
    
    def to_dict(self) -> Dict[str, Any]:
        """
        to_dict function.

    Auto-documented by QwenCodeMender.
        """
        return {
            'timestamp': self.timestamp.isoformat(),
            'health': self.health.value,
            'diversity_index': self.diversity_index,
            'predator_prey_ratio': self.predator_prey_ratio,
            'liquidity_depth': self.liquidity_depth,
            'volatility_regime': self.volatility_regime,
            'dominant_species': self.dominant_species.value,
            'species_activities': [a.to_dict() for a in self.species_activities]
        }


@dataclass
class ReactionPrediction:
    """Predicted reaction of species to event"""
    event_type: str
    species: MarketSpecies
    predicted_behavior: BehaviorPattern
    intensity: float  # 0-1
    timing: str  # IMMEDIATE, DELAYED, GRADUAL
    confidence: float
    reasoning: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'event_type': self.event_type,
            'species': self.species.value,
            'predicted_behavior': self.predicted_behavior.value,
            'intensity': self.intensity,
            'timing': self.timing,
            'confidence': self.confidence,
            'reasoning': self.reasoning
        }


class MarketMicrobiome:
    """
    Market Microbiome Analysis System
    
    Models the market as an ecosystem with different species
    of participants, tracking their behaviors and predicting
    their reactions to market events.
    """
    
    # Species signatures (baseline characteristics)
    SPECIES_SIGNATURES = {
        MarketSpecies.HFT_PREDATOR: SpeciesSignature(
            species=MarketSpecies.HFT_PREDATOR,
            avg_order_size=100,
            order_frequency=1000,  # Very high
            cancel_ratio=0.95,     # Very high cancellation
            aggression_ratio=0.3,
            time_in_market=0.001,  # Milliseconds
            clustering_coefficient=0.9
        ),
        MarketSpecies.INSTITUTIONAL_WHALE: SpeciesSignature(
            species=MarketSpecies.INSTITUTIONAL_WHALE,
            avg_order_size=50000,
            order_frequency=0.5,   # Low frequency
            cancel_ratio=0.2,
            aggression_ratio=0.4,
            time_in_market=300,    # Minutes
            clustering_coefficient=0.3
        ),
        MarketSpecies.RETAIL_HERD: SpeciesSignature(
            species=MarketSpecies.RETAIL_HERD,
            avg_order_size=500,
            order_frequency=5,
            cancel_ratio=0.1,
            aggression_ratio=0.7,  # More market orders
            time_in_market=60,
            clustering_coefficient=0.6
        ),
        MarketSpecies.ALGO_MOMENTUM: SpeciesSignature(
            species=MarketSpecies.ALGO_MOMENTUM,
            avg_order_size=5000,
            order_frequency=20,
            cancel_ratio=0.4,
            aggression_ratio=0.6,
            time_in_market=10,
            clustering_coefficient=0.7
        ),
        MarketSpecies.MARKET_MAKER: SpeciesSignature(
            species=MarketSpecies.MARKET_MAKER,
            avg_order_size=1000,
            order_frequency=100,
            cancel_ratio=0.8,
            aggression_ratio=0.1,  # Mostly limit orders
            time_in_market=5,
            clustering_coefficient=0.5
        ),
    }
    
    # Reaction patterns to events
    EVENT_REACTIONS = {
        'liquidity_sweep': {
            MarketSpecies.HFT_PREDATOR: (BehaviorPattern.HUNTING, 0.9),
            MarketSpecies.INSTITUTIONAL_WHALE: (BehaviorPattern.ACCUMULATING, 0.6),
            MarketSpecies.RETAIL_HERD: (BehaviorPattern.FLEEING, 0.8),
            MarketSpecies.MARKET_MAKER: (BehaviorPattern.PROVIDING, 0.7),
        },
        'news_spike': {
            MarketSpecies.HFT_PREDATOR: (BehaviorPattern.CONSUMING, 0.95),
            MarketSpecies.NEWS_TRADER: (BehaviorPattern.CHASING, 0.9),
            MarketSpecies.RETAIL_HERD: (BehaviorPattern.CHASING, 0.7),
            MarketSpecies.INSTITUTIONAL_WHALE: (BehaviorPattern.DORMANT, 0.5),
        },
        'volatility_spike': {
            MarketSpecies.HFT_PREDATOR: (BehaviorPattern.PROVIDING, 0.6),
            MarketSpecies.RETAIL_HERD: (BehaviorPattern.FLEEING, 0.8),
            MarketSpecies.ALGO_MEAN_REVERSION: (BehaviorPattern.ACCUMULATING, 0.7),
            MarketSpecies.MARKET_MAKER: (BehaviorPattern.FLEEING, 0.6),
        },
        'trend_breakout': {
            MarketSpecies.ALGO_MOMENTUM: (BehaviorPattern.CHASING, 0.9),
            MarketSpecies.RETAIL_HERD: (BehaviorPattern.CHASING, 0.8),
            MarketSpecies.RETAIL_CONTRARIAN: (BehaviorPattern.FADING, 0.6),
            MarketSpecies.INSTITUTIONAL_WHALE: (BehaviorPattern.DISTRIBUTING, 0.5),
        },
    }
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        try:
            self.config = config or {}
        
            # Species activity tracking
            self.species_activities: Dict[MarketSpecies, deque] = {
                species: deque(maxlen=1000) for species in MarketSpecies
            }
        
            # Current estimates
            self.current_activities: Dict[MarketSpecies, SpeciesActivity] = {}
        
            # Ecosystem history
            self.ecosystem_history: deque = deque(maxlen=500)
        
            # Order flow buffer for classification
            self.order_buffer: deque = deque(maxlen=10000)
        
            logger.info("MarketMicrobiome initialized")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def classify_order(self, order: Dict[str, Any]) -> MarketSpecies:
        """
        Classify an order to a species based on characteristics
        """
        try:
            size = order.get('size', 0)
            order_type = order.get('type', 'limit')
            lifetime_ms = order.get('lifetime_ms', 1000)
            is_cancel = order.get('is_cancel', False)
        
            # Classification logic
            scores = {}
        
            for species, sig in self.SPECIES_SIGNATURES.items():
                score = 0
            
                # Size matching
                size_ratio = size / sig.avg_order_size if sig.avg_order_size > 0 else 0
                if 0.5 < size_ratio < 2.0:
                    score += 0.3
            
                # Order type matching
                is_aggressive = order_type == 'market'
                if is_aggressive and sig.aggression_ratio > 0.5:
                    score += 0.2
                elif not is_aggressive and sig.aggression_ratio < 0.5:
                    score += 0.2
            
                # Lifetime matching
                lifetime_ratio = lifetime_ms / (sig.time_in_market * 1000) if sig.time_in_market > 0 else 0
                if 0.1 < lifetime_ratio < 10:
                    score += 0.2
            
                # Cancel behavior
                if is_cancel and sig.cancel_ratio > 0.5:
                    score += 0.3
                elif not is_cancel and sig.cancel_ratio < 0.5:
                    score += 0.3
            
                scores[species] = score
        
            # Return highest scoring species
            return max(scores.items(), key=lambda x: x[1])[0]
        except Exception as e:
            logger.error(f"Error in classify_order: {e}")
            raise
    
    def process_order_flow(
        self,
        orders: List[Dict[str, Any]]
    ) -> Dict[MarketSpecies, SpeciesActivity]:
        """
        Process batch of orders and update species activities
        """
        # Classify orders
        try:
            species_orders: Dict[MarketSpecies, List[Dict]] = {s: [] for s in MarketSpecies}
        
            for order in orders:
                species = self.classify_order(order)
                species_orders[species].append(order)
                self.order_buffer.append((species, order))
        
            # Update activities
            now = datetime.now()
        
            for species, species_order_list in species_orders.items():
                if not species_order_list:
                    continue
            
                # Calculate activity metrics
                total_volume = sum(o.get('size', 0) for o in species_order_list)
                buy_volume = sum(o.get('size', 0) for o in species_order_list if o.get('side') == 'buy')
                sell_volume = total_volume - buy_volume
            
                # Determine behavior
                if buy_volume > sell_volume * 1.5:
                    behavior = BehaviorPattern.ACCUMULATING
                    estimated_position = buy_volume - sell_volume
                elif sell_volume > buy_volume * 1.5:
                    behavior = BehaviorPattern.DISTRIBUTING
                    estimated_position = buy_volume - sell_volume
                else:
                    behavior = BehaviorPattern.PROVIDING
                    estimated_position = 0
            
                # Activity level
                sig = self.SPECIES_SIGNATURES.get(species)
                if sig:
                    expected_orders = sig.order_frequency * 5  # 5 minute window
                    activity_level = min(1.0, len(species_order_list) / max(1, expected_orders))
                else:
                    activity_level = 0.5
            
                activity = SpeciesActivity(
                    species=species,
                    timestamp=now,
                    activity_level=activity_level,
                    behavior=behavior,
                    estimated_position=estimated_position,
                    confidence=0.6 + 0.1 * min(len(species_order_list), 4),
                    recent_orders=len(species_order_list)
                )
            
                self.current_activities[species] = activity
                self.species_activities[species].append(activity)
        
            return self.current_activities
        except Exception as e:
            logger.error(f"Error in process_order_flow: {e}")
            raise
    
    def get_ecosystem_state(self) -> EcosystemState:
        """
        Get current ecosystem state
        """
        try:
            now = datetime.now()
        
            # Calculate diversity index (Shannon entropy)
            activities = list(self.current_activities.values())
            if activities:
                total_activity = sum(a.activity_level for a in activities)
                if total_activity > 0:
                    proportions = [a.activity_level / total_activity for a in activities]
                    diversity = -sum(p * np.log(p + 1e-10) for p in proportions if p > 0)
                    diversity_index = diversity / np.log(len(MarketSpecies))  # Normalize
                else:
                    diversity_index = 0
            else:
                diversity_index = 0
        
            # Predator-prey ratio
            predators = [MarketSpecies.HFT_PREDATOR, MarketSpecies.HFT_ARBITRAGEUR]
            prey = [MarketSpecies.RETAIL_HERD, MarketSpecies.RETAIL_CONTRARIAN]
        
            predator_activity = sum(
                self.current_activities.get(s, SpeciesActivity(
                    species=s, timestamp=now, activity_level=0,
                    behavior=BehaviorPattern.DORMANT, estimated_position=0,
                    confidence=0, recent_orders=0
                )).activity_level
                for s in predators
            )
            prey_activity = sum(
                self.current_activities.get(s, SpeciesActivity(
                    species=s, timestamp=now, activity_level=0,
                    behavior=BehaviorPattern.DORMANT, estimated_position=0,
                    confidence=0, recent_orders=0
                )).activity_level
                for s in prey
            )
        
            predator_prey_ratio = predator_activity / (prey_activity + 0.01)
        
            # Determine health
            if diversity_index > 0.7 and 0.3 < predator_prey_ratio < 3:
                health = EcosystemHealth.THRIVING
            elif diversity_index > 0.5 and 0.2 < predator_prey_ratio < 5:
                health = EcosystemHealth.STRESSED
            elif predator_prey_ratio > 5:
                health = EcosystemHealth.FRAGILE
            elif diversity_index < 0.3:
                health = EcosystemHealth.CRISIS
            else:
                health = EcosystemHealth.RECOVERING
        
            # Find dominant species
            if activities:
                dominant = max(activities, key=lambda a: a.activity_level).species
            else:
                dominant = MarketSpecies.MARKET_MAKER
        
            # Volatility regime (simplified)
            volatility_regime = "normal"  # Would be calculated from price data
        
            state = EcosystemState(
                timestamp=now,
                health=health,
                diversity_index=diversity_index,
                predator_prey_ratio=predator_prey_ratio,
                liquidity_depth=0.5,  # Would be calculated from order book
                volatility_regime=volatility_regime,
                dominant_species=dominant,
                species_activities=activities
            )
        
            self.ecosystem_history.append(state)
        
            return state
        except Exception as e:
            logger.error(f"Error in get_ecosystem_state: {e}")
            raise
    
    def predict_reactions(
        self,
        event_type: str
    ) -> List[ReactionPrediction]:
        """
        Predict how each species will react to an event
        """
        try:
            predictions = []
        
            reactions = self.EVENT_REACTIONS.get(event_type, {})
        
            for species in MarketSpecies:
                if species in reactions:
                    behavior, intensity = reactions[species]
                    timing = "IMMEDIATE" if species in [MarketSpecies.HFT_PREDATOR, MarketSpecies.HFT_ARBITRAGEUR] else "DELAYED"
                else:
                    behavior = BehaviorPattern.DORMANT
                    intensity = 0.3
                    timing = "GRADUAL"
            
                # Adjust based on current activity
                current = self.current_activities.get(species)
                if current:
                    intensity *= current.activity_level
            
                prediction = ReactionPrediction(
                    event_type=event_type,
                    species=species,
                    predicted_behavior=behavior,
                    intensity=intensity,
                    timing=timing,
                    confidence=0.6,
                    reasoning=f"{species.value} typically shows {behavior.value} behavior during {event_type}"
                )
                predictions.append(prediction)
        
            # Sort by intensity
            predictions.sort(key=lambda p: p.intensity, reverse=True)
        
            return predictions
        except Exception as e:
            logger.error(f"Error in predict_reactions: {e}")
            raise
    
    def get_species_summary(self) -> Dict[str, Any]:
        """Get summary of all species activities"""
        try:
            summary = {
                'timestamp': datetime.now().isoformat(),
                'species': {}
            }
        
            for species in MarketSpecies:
                activity = self.current_activities.get(species)
                history = list(self.species_activities[species])
            
                if activity:
                    avg_activity = np.mean([a.activity_level for a in history[-10:]]) if history else 0
                
                    summary['species'][species.value] = {
                        'current_activity': activity.activity_level,
                        'average_activity': avg_activity,
                        'behavior': activity.behavior.value,
                        'estimated_position': activity.estimated_position,
                        'recent_orders': activity.recent_orders
                    }
                else:
                    summary['species'][species.value] = {
                        'current_activity': 0,
                        'behavior': 'dormant'
                    }
        
            return summary
        except Exception as e:
            logger.error(f"Error in get_species_summary: {e}")
            raise
    
    def detect_unusual_activity(self) -> List[Dict[str, Any]]:
        """Detect unusual species activity"""
        try:
            alerts = []
        
            for species in MarketSpecies:
                history = list(self.species_activities[species])
                if len(history) < 10:
                    continue
            
                recent = history[-5:]
                baseline = history[-50:-5] if len(history) > 50 else history[:-5]
            
                if not baseline:
                    continue
            
                recent_avg = np.mean([a.activity_level for a in recent])
                baseline_avg = np.mean([a.activity_level for a in baseline])
                baseline_std = np.std([a.activity_level for a in baseline])
            
                if baseline_std > 0:
                    z_score = (recent_avg - baseline_avg) / baseline_std
                
                    if abs(z_score) > 2:
                        alerts.append({
                            'species': species.value,
                            'z_score': z_score,
                            'direction': 'increased' if z_score > 0 else 'decreased',
                            'recent_activity': recent_avg,
                            'baseline_activity': baseline_avg,
                            'severity': 'HIGH' if abs(z_score) > 3 else 'MEDIUM'
                        })
        
            return alerts
        except Exception as e:
            logger.error(f"Error in detect_unusual_activity: {e}")
            raise


# Factory function
def create_market_microbiome(config: Optional[Dict[str, Any]] = None) -> MarketMicrobiome:
    """Create market microbiome analyzer"""
    return MarketMicrobiome(config)
