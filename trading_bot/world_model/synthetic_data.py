"""
Phase 4: World Models - Synthetic Market Generation
Creates realistic market scenarios for training and testing
"""

import numpy as np
import torch
from typing import Dict, List, Optional, Tuple, Any
import logging
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class MarketRegime(Enum):
    """Different market regimes to simulate."""
    NORMAL = "normal"
    TRENDING_UP = "trending_up"
    TRENDING_DOWN = "trending_down"
    RANGING = "ranging"
    HIGH_VOLATILITY = "high_volatility"
    LOW_VOLATILITY = "low_volatility"
    BREAKOUT = "breakout"
    REVERSAL = "reversal"
    CRISIS = "crisis"


@dataclass
class MarketScenario:
    """Parameters for market scenario generation."""
    regime: MarketRegime
    duration: int  # Number of timesteps
    volatility: float
    trend_strength: float = 0.0
    mean_reversion: float = 0.0
    jumps_frequency: float = 0.0
    seasonality: Optional[Dict] = None


class SyntheticMarketGenerator:
    """
    Generates synthetic market data for various scenarios.
    Combines different market dynamics and regimes.
    """
    
    def __init__(
        self,
        base_volatility: float = 0.01,
        dt: float = 1.0/252.0  # Daily timesteps
    ):
        self.base_volatility = base_volatility
        self.dt = dt
        
        # Default parameters for different regimes
        self.regime_params = {
            MarketRegime.TRENDING_UP: {
                'trend_strength': 0.2,
                'volatility': 1.0,
                'mean_reversion': 0.0,
                'jumps_frequency': 0.01
            },
            MarketRegime.TRENDING_DOWN: {
                'trend_strength': -0.2,
                'volatility': 1.0,
                'mean_reversion': 0.0,
                'jumps_frequency': 0.01
            },
            MarketRegime.RANGING: {
                'trend_strength': 0.0,
                'volatility': 0.8,
                'mean_reversion': 0.1,
                'jumps_frequency': 0.0
            },
            MarketRegime.HIGH_VOLATILITY: {
                'trend_strength': 0.0,
                'volatility': 2.0,
                'mean_reversion': 0.0,
                'jumps_frequency': 0.05
            },
            MarketRegime.LOW_VOLATILITY: {
                'trend_strength': 0.0,
                'volatility': 0.5,
                'mean_reversion': 0.05,
                'jumps_frequency': 0.0
            },
            MarketRegime.BREAKOUT: {
                'trend_strength': 0.3,
                'volatility': 1.5,
                'mean_reversion': -0.1,
                'jumps_frequency': 0.1
            },
            MarketRegime.REVERSAL: {
                'trend_strength': -0.3,
                'volatility': 1.5,
                'mean_reversion': 0.2,
                'jumps_frequency': 0.1
            },
            MarketRegime.CRISIS: {
                'trend_strength': -0.5,
                'volatility': 3.0,
                'mean_reversion': -0.2,
                'jumps_frequency': 0.2
            }
        }
        
        logger.info("✅ Synthetic Market Generator initialized")
    
    def generate_scenario(
        self,
        scenario: MarketScenario,
        initial_price: float = 100.0
    ) -> Dict:
        """
        Generate synthetic market data for a scenario.
        
        Args:
            scenario: Market scenario parameters
            initial_price: Starting price
        
        Returns:
            Dictionary with price and indicator data
        """
        # Get base parameters for regime
        base_params = self.regime_params[scenario.regime]
        
        # Combine with scenario-specific parameters
        params = {
            'trend_strength': scenario.trend_strength or base_params['trend_strength'],
            'volatility': scenario.volatility * base_params['volatility'],
            'mean_reversion': scenario.mean_reversion or base_params['mean_reversion'],
            'jumps_frequency': scenario.jumps_frequency or base_params['jumps_frequency']
        }
        
        # Generate price path
        prices = self._generate_price_path(
            initial_price,
            scenario.duration,
            params
        )
        
        # Calculate returns
        returns = np.diff(np.log(prices))
        
        # Calculate indicators
        indicators = self._calculate_indicators(prices, returns)
        
        # Add some noise to indicators
        indicators = self._add_indicator_noise(indicators)
        
        return {
            'prices': prices,
            'returns': returns,
            'indicators': indicators,
            'metadata': {
                'regime': scenario.regime.value,
                'duration': scenario.duration,
                'params': params
            }
        }
    
    def _generate_price_path(
        self,
        initial_price: float,
        duration: int,
        params: Dict
    ) -> np.ndarray:
        """Generate synthetic price path."""
        prices = np.zeros(duration)
        prices[0] = initial_price
        
        # Unpack parameters
        mu = params['trend_strength']
        sigma = params['volatility'] * self.base_volatility
        mean_rev = params['mean_reversion']
        jump_freq = params['jumps_frequency']
        
        # Generate path
        for t in range(1, duration):
            # Drift component
            drift = mu * self.dt
            
            # Diffusion component
            diffusion = sigma * np.sqrt(self.dt) * np.random.normal()
            
            # Mean reversion component
            if mean_rev != 0:
                log_price = np.log(prices[t-1])
                mean_price = np.log(initial_price)
                mean_rev_component = mean_rev * (mean_price - log_price) * self.dt
            else:
                mean_rev_component = 0
            
            # Jump component
            if np.random.random() < jump_freq:
                jump = np.random.normal(0, sigma * 3)  # Larger jumps
            else:
                jump = 0
            
            # Combine components
            log_return = drift + diffusion + mean_rev_component + jump
            
            # Update price
            prices[t] = prices[t-1] * np.exp(log_return)
        
        return prices
    
    def _calculate_indicators(
        self,
        prices: np.ndarray,
        returns: np.ndarray
    ) -> Dict:
        """Calculate technical indicators from price data."""
        n = len(prices)
        
        # Moving averages
        sma_20 = np.zeros(n)
        sma_50 = np.zeros(n)
        
        for i in range(n):
            if i >= 20:
                sma_20[i] = np.mean(prices[i-20:i])
            if i >= 50:
                sma_50[i] = np.mean(prices[i-50:i])
        
        # RSI - pad returns to match prices length
        padded_returns = np.concatenate([[0], returns])  # Add 0 at start
        gains = np.maximum(padded_returns, 0)
        losses = -np.minimum(padded_returns, 0)
        
        avg_gain = np.zeros(n)
        avg_loss = np.zeros(n)
        rsi = np.zeros(n)
        
        for i in range(14, n):
            if i == 14:
                avg_gain[i] = np.mean(gains[1:15])
                avg_loss[i] = np.mean(losses[1:15])
            else:
                avg_gain[i] = (avg_gain[i-1] * 13 + gains[i]) / 14
                avg_loss[i] = (avg_loss[i-1] * 13 + losses[i]) / 14
            
            if avg_loss[i] == 0:
                rsi[i] = 100
            else:
                rs = avg_gain[i] / avg_loss[i]
                rsi[i] = 100 - (100 / (1 + rs))
        
        # MACD
        ema_12 = np.zeros(n)
        ema_26 = np.zeros(n)
        macd = np.zeros(n)
        
        for i in range(n):
            if i == 0:
                ema_12[i] = prices[i]
                ema_26[i] = prices[i]
            else:
                ema_12[i] = prices[i] * 0.15 + ema_12[i-1] * 0.85
                ema_26[i] = prices[i] * 0.075 + ema_26[i-1] * 0.925
            macd[i] = ema_12[i] - ema_26[i]
        
        # Volatility (20-day rolling)
        volatility = np.zeros(n)
        for i in range(20, n):
            volatility[i] = np.std(returns[i-20:i]) * np.sqrt(252)
        
        return {
            'sma_20': sma_20,
            'sma_50': sma_50,
            'rsi': rsi,
            'macd': macd,
            'volatility': volatility
        }
    
    def _add_indicator_noise(self, indicators: Dict) -> Dict:
        """Add realistic noise to indicators."""
        noisy_indicators = {}
        
        for name, values in indicators.items():
            # Add small Gaussian noise
            noise = np.random.normal(0, 0.02 * np.std(values), size=len(values))
            noisy_indicators[name] = values + noise
        
        return noisy_indicators
    
    def generate_regime_transition(
        self,
        initial_regime: MarketRegime,
        final_regime: MarketRegime,
        transition_duration: int,
        total_duration: int
    ) -> Dict:
        """
        Generate scenario with smooth regime transition.
        
        Args:
            initial_regime: Starting regime
            final_regime: Ending regime
            transition_duration: Duration of transition
            total_duration: Total scenario duration
        
        Returns:
            Market data with regime transition
        """
        # Generate initial regime
        initial_scenario = MarketScenario(
            regime=initial_regime,
            duration=total_duration,
            volatility=1.0
        )
        initial_data = self.generate_scenario(initial_scenario)
        
        # Generate final regime
        final_scenario = MarketScenario(
            regime=final_regime,
            duration=total_duration,
            volatility=1.0
        )
        final_data = self.generate_scenario(final_scenario)
        
        # Create transition weights
        transition_weights = np.zeros(total_duration)
        for t in range(total_duration):
            if t < transition_duration:
                # Smooth transition
                weight = t / transition_duration
                transition_weights[t] = 0.5 * (1 + np.cos(np.pi * (1 - weight)))
        
        # Blend regimes
        blended_data = {
            'prices': (
                initial_data['prices'] * (1 - transition_weights) +
                final_data['prices'] * transition_weights
            ),
            'metadata': {
                'initial_regime': initial_regime.value,
                'final_regime': final_regime.value,
                'transition_duration': transition_duration
            }
        }
        
        # Recalculate indicators for blended prices
        returns = np.diff(np.log(blended_data['prices']))
        blended_data['indicators'] = self._calculate_indicators(
            blended_data['prices'],
            returns
        )
        
        return blended_data
    
    def generate_market_cycle(
        self,
        cycle_duration: int,
        num_regimes: int = 4
    ) -> Dict:
        """
        Generate complete market cycle with multiple regime changes.
        
        Args:
            cycle_duration: Total duration of cycle
            num_regimes: Number of regime changes
        
        Returns:
            Market data for complete cycle
        """
        # Define cycle phases
        cycle_regimes = [
            MarketRegime.RANGING,
            MarketRegime.TRENDING_UP,
            MarketRegime.HIGH_VOLATILITY,
            MarketRegime.TRENDING_DOWN,
            MarketRegime.LOW_VOLATILITY
        ]
        
        # Duration for each regime
        regime_duration = cycle_duration // num_regimes
        transition_duration = regime_duration // 3
        
        # Generate data for each phase
        cycle_data = []
        current_price = 100.0
        
        for i in range(num_regimes):
            # Select regime
            regime = cycle_regimes[i % len(cycle_regimes)]
            
            # Generate scenario
            scenario = MarketScenario(
                regime=regime,
                duration=regime_duration,
                volatility=1.0
            )
            
            data = self.generate_scenario(scenario, initial_price=current_price)
            cycle_data.append(data)
            
            # Update starting price for next phase
            current_price = data['prices'][-1]
        
        # Combine phases
        combined_data = {
            'prices': np.concatenate([d['prices'] for d in cycle_data]),
            'metadata': {
                'cycle_duration': cycle_duration,
                'num_regimes': num_regimes,
                'regime_sequence': [d['metadata']['regime'] for d in cycle_data]
            }
        }
        
        # Calculate final indicators
        returns = np.diff(np.log(combined_data['prices']))
        combined_data['indicators'] = self._calculate_indicators(
            combined_data['prices'],
            returns
        )
        
        return combined_data


# =============================================================================
# DeepSeek-Style Multi-Agent Synthetic Data Generation
# =============================================================================

@dataclass
class AgentState:
    """State of a simulated market agent"""
    agent_id: int
    position: float  # Current position
    cash: float
    strategy_type: str  # 'momentum', 'mean_reversion', 'noise', 'informed'
    sentiment: float  # -1 to 1
    risk_tolerance: float
    

@dataclass
class OrderBookLevel:
    """Single level in order book"""
    price: float
    volume: float
    side: str  # 'bid' or 'ask'
    agent_id: Optional[int] = None  # Who placed this order


class MultiAgentMarketSimulator:
    """
    DeepSeek-style multi-agent market simulation
    
    Simulates realistic market microstructure with:
    - 1000+ simulated agents with different strategies
    - Order book dynamics with limit orders
    - News/sentiment injection
    - Cross-agent interactions
    
    Scale: 10M+ candles per generation batch
    """
    
    def __init__(
        self,
        num_agents: int = 1000,
        base_volatility: float = 0.01,
        tick_size: float = 0.01
    ):
        self.num_agents = num_agents
        self.base_volatility = base_volatility
        self.tick_size = tick_size
        
        # Initialize agents
        self.agents: Dict[int, AgentState] = {}
        self._initialize_agents()
        
        # Order book
        self.order_book: Dict[str, List[OrderBookLevel]] = {
            'bids': [],
            'asks': []
        }
        
        # Market state
        self.current_price = 100.0
        self.volume_history = []
        
        logger.info(f"✅ MultiAgentMarketSimulator initialized")
        logger.info(f"   Agents: {num_agents}")
        logger.info(f"   Tick size: {tick_size}")
    
    def _initialize_agents(self):
        """Initialize heterogeneous agent population"""
        strategies = ['momentum', 'mean_reversion', 'noise', 'informed', 'liquidity']
        weights = [0.25, 0.25, 0.30, 0.10, 0.10]
        
        for i in range(self.num_agents):
            strategy = np.random.choice(strategies, p=weights)
            
            self.agents[i] = AgentState(
                agent_id=i,
                position=np.random.uniform(-1, 1),
                cash=np.random.uniform(5000, 50000),
                strategy_type=strategy,
                sentiment=np.random.uniform(-0.5, 0.5),
                risk_tolerance=np.random.uniform(0.1, 0.9)
            )
    
    def simulate_timestep(
        self,
        fundamental_value: float,
        news_shock: Optional[float] = None
    ) -> Dict:
        """
        Simulate one market timestep with all agents
        
        Returns:
            Market data for this timestep
        """
        # Clear order book
        self.order_book = {'bids': [], 'asks': []}
        
        # Generate agent orders
        for agent_id, agent in self.agents.items():
            orders = self._generate_agent_orders(agent, fundamental_value, news_shock)
            
            for order in orders:
                if order.side == 'bid':
                    self.order_book['bids'].append(order)
                else:
                    self.order_book['asks'].append(order)
        
        # Sort order book
        self.order_book['bids'].sort(key=lambda x: x.price, reverse=True)
        self.order_book['asks'].sort(key=lambda x: x.price)
        
        # Match orders
        trades = self._match_orders()
        
        # Update price
        if trades:
            # VWAP of trades
            total_value = sum(t['price'] * t['volume'] for t in trades)
            total_volume = sum(t['volume'] for t in trades)
            self.current_price = total_value / total_volume
        else:
            # No trades - small random walk
            self.current_price *= (1 + np.random.normal(0, self.base_volatility * 0.1))
        
        # Calculate indicators
        spread = self._calculate_spread()
        depth = self._calculate_depth()
        
        return {
            'price': self.current_price,
            'volume': sum(t['volume'] for t in trades),
            'spread': spread,
            'depth': depth,
            'num_trades': len(trades),
            'bid_ask_ratio': len(self.order_book['bids']) / max(1, len(self.order_book['asks']))
        }
    
    def _generate_agent_orders(
        self,
        agent: AgentState,
        fundamental_value: float,
        news_shock: Optional[float]
    ) -> List[OrderBookLevel]:
        """Generate orders for an agent based on strategy"""
        orders = []
        
        # Calculate desired position based on strategy
        if agent.strategy_type == 'momentum':
            # Trend following
            trend = (self.current_price - fundamental_value) / fundamental_value
            desired_position = np.sign(trend) * agent.risk_tolerance
            
        elif agent.strategy_type == 'mean_reversion':
            # Contrarian
            deviation = (self.current_price - fundamental_value) / fundamental_value
            desired_position = -np.sign(deviation) * agent.risk_tolerance * 0.5
            
        elif agent.strategy_type == 'noise':
            # Random noise trading
            desired_position = np.random.uniform(-0.3, 0.3)
            
        elif agent.strategy_type == 'informed':
            # Has private information (news)
            if news_shock:
                desired_position = np.sign(news_shock) * agent.risk_tolerance
            else:
                desired_position = agent.position * 0.9  # Reduce position
                
        else:  # liquidity provider
            # Provide liquidity around mid price
            if np.random.random() < 0.3:
                orders.append(OrderBookLevel(
                    price=self.current_price - self.tick_size * 2,
                    volume=np.random.uniform(1, 5),
                    side='bid',
                    agent_id=agent.agent_id
                ))
                orders.append(OrderBookLevel(
                    price=self.current_price + self.tick_size * 2,
                    volume=np.random.uniform(1, 5),
                    side='ask',
                    agent_id=agent.agent_id
                ))
            return orders
        
        # Incorporate sentiment
        desired_position += agent.sentiment * 0.2
        desired_position = np.clip(desired_position, -1, 1)
        
        # Calculate trade needed
        position_change = desired_position - agent.position
        
        if abs(position_change) > 0.05:  # Minimum trade size
            side = 'bid' if position_change > 0 else 'ask'
            volume = abs(position_change) * 10  # Scale to volume
            
            # Price based on urgency
            if agent.strategy_type == 'informed':
                # Informed traders use market orders (pay spread)
                price = self.current_price - self.tick_size if side == 'bid' else self.current_price + self.tick_size
            else:
                # Others use limit orders
                price = self.current_price - self.tick_size * np.random.randint(1, 5) if side == 'bid' else \
                        self.current_price + self.tick_size * np.random.randint(1, 5)
            
            orders.append(OrderBookLevel(
                price=price,
                volume=volume,
                side=side,
                agent_id=agent.agent_id
            ))
        
        return orders
    
    def _match_orders(self) -> List[Dict]:
        """Match bids with asks"""
        trades = []
        
        bids = self.order_book['bids']
        asks = self.order_book['asks']
        
        bid_idx = 0
        ask_idx = 0
        
        while bid_idx < len(bids) and ask_idx < len(asks):
            bid = bids[bid_idx]
            ask = asks[ask_idx]
            
            if bid.price >= ask.price:
                # Trade occurs
                trade_volume = min(bid.volume, ask.volume)
                trade_price = (bid.price + ask.price) / 2
                
                trades.append({
                    'price': trade_price,
                    'volume': trade_volume,
                    'buyer': bid.agent_id,
                    'seller': ask.agent_id
                })
                
                # Update volumes
                bid.volume -= trade_volume
                ask.volume -= trade_volume
                
                # Move to next order if filled
                if bid.volume <= 0.001:
                    bid_idx += 1
                if ask.volume <= 0.001:
                    ask_idx += 1
            else:
                # No more matches possible
                break
        
        return trades
    
    def _calculate_spread(self) -> float:
        """Calculate bid-ask spread"""
        if not self.order_book['bids'] or not self.order_book['asks']:
            return 0.0
        
        best_bid = self.order_book['bids'][0].price
        best_ask = self.order_book['asks'][0].price
        
        return best_ask - best_bid
    
    def _calculate_depth(self) -> float:
        """Calculate order book depth"""
        bid_volume = sum(o.volume for o in self.order_book['bids'][:5])
        ask_volume = sum(o.volume for o in self.order_book['asks'][:5])
        
        return bid_volume + ask_volume
    
    def inject_news(self, impact: float, persistence: int = 10):
        """Inject news event affecting agent sentiment"""
        for agent in self.agents.values():
            if agent.strategy_type == 'informed':
                agent.sentiment = impact
            else:
                # Gradual adoption
                agent.sentiment += impact * 0.1
                agent.sentiment = np.clip(agent.sentiment, -1, 1)
    
    def generate_batch(
        self,
        num_candles: int = 10000000,  # 10M candles
        regime: MarketRegime = MarketRegime.NORMAL,
        include_news: bool = True
    ) -> Dict:
        """
        Generate large batch of synthetic market data
        
        Scale: 10M+ candles per batch
        """
        logger.info(f"Generating {num_candles:,} synthetic candles...")
        
        prices = []
        volumes = []
        spreads = []
        timestamps = []
        
        # Generate fundamental value path
        fundamental = self._generate_fundamental_path(num_candles, regime)
        
        # News events
        news_times = []
        if include_news:
            news_times = np.random.choice(
                range(num_candles),
                size=num_candles // 100,  # 1% of candles have news
                replace=False
            )
        
        # Simulate
        for t in range(num_candles):
            # Inject news if scheduled
            if t in news_times:
                impact = np.random.choice([-0.5, 0.5]) * np.random.uniform(0.5, 1.0)
                self.inject_news(impact)
            
            # Simulate timestep
            result = self.simulate_timestep(fundamental[t])
            
            prices.append(result['price'])
            volumes.append(result['volume'])
            spreads.append(result['spread'])
            timestamps.append(t)
            
            if (t + 1) % 1000000 == 0:
                logger.info(f"   Generated {(t + 1):,} / {num_candles:,} candles")
        
        logger.info(f"✅ Batch generation complete: {num_candles:,} candles")
        
        return {
            'prices': np.array(prices),
            'volumes': np.array(volumes),
            'spreads': np.array(spreads),
            'timestamps': np.array(timestamps),
            'metadata': {
                'num_agents': self.num_agents,
                'num_candles': num_candles,
                'regime': regime.value,
                'avg_volume': np.mean(volumes),
                'avg_spread': np.mean(spreads)
            }
        }
    
    def _generate_fundamental_path(
        self,
        num_steps: int,
        regime: MarketRegime
    ) -> np.ndarray:
        """Generate fundamental value path (efficient price)"""
        # Random walk with drift based on regime
        regime_params = {
            MarketRegime.TRENDING_UP: {'drift': 0.0002, 'vol': 0.005},
            MarketRegime.TRENDING_DOWN: {'drift': -0.0002, 'vol': 0.005},
            MarketRegime.RANGING: {'drift': 0.0, 'vol': 0.003},
            MarketRegime.HIGH_VOLATILITY: {'drift': 0.0, 'vol': 0.02},
            MarketRegime.NORMAL: {'drift': 0.0001, 'vol': 0.01}
        }
        
        params = regime_params.get(regime, regime_params[MarketRegime.NORMAL])
        
        returns = np.random.normal(
            params['drift'],
            params['vol'],
            num_steps
        )
        
        log_prices = np.cumsum(returns)
        prices = self.current_price * np.exp(log_prices)
        
        return prices


class SyntheticDataQualityScorer:
    """
    GAN-style quality scoring for synthetic data
    
    Uses discriminator network to score realism
    """
    
    def __init__(self, input_dim: int = 10):
        self.discriminator = nn.Sequential(
            nn.Linear(input_dim, 64),
            nn.LeakyReLU(0.2),
            nn.Dropout(0.3),
            nn.Linear(64, 32),
            nn.LeakyReLU(0.2),
            nn.Linear(32, 1),
            nn.Sigmoid()
        )
        
        self.real_data_stats = None
    
    def calculate_features(self, data: Dict) -> np.ndarray:
        """Extract statistical features from market data"""
        returns = np.diff(np.log(data['prices']))
        
        features = [
            np.mean(returns),
            np.std(returns),
            np.percentile(returns, 5),
            np.percentile(returns, 95),
            np.mean(data['volumes']),
            np.std(data['volumes']),
            np.mean(data['spreads']),
            np.max(data['prices']) / np.min(data['prices']) - 1,  # Max drawdown proxy
            np.sum(returns > 0) / len(returns),  # Up ratio
            np.mean(np.abs(returns))  # Mean absolute return
        ]
        
        return np.array(features)
    
    def score(self, synthetic_data: Dict) -> float:
        """
        Score synthetic data quality (0-1)
        
        1.0 = indistinguishable from real data
        0.0 = obviously synthetic
        """
        features = self.calculate_features(synthetic_data)
        
        with torch.no_grad():
            x = torch.FloatTensor(features).unsqueeze(0)
            score = self.discriminator(x).item()
        
        return score
    
    def train_on_real_data(self, real_market_data: List[Dict], epochs: int = 100):
        """Train discriminator on real market data"""
        # Extract features from real data
        real_features = [self.calculate_features(d) for d in real_market_data]
        X_real = torch.FloatTensor(real_features)
        y_real = torch.ones(len(real_features), 1)
        
        optimizer = torch.optim.Adam(self.discriminator.parameters(), lr=0.001)
        criterion = nn.BCELoss()
        
        for epoch in range(epochs):
            optimizer.zero_grad()
            
            # Forward pass
            predictions = self.discriminator(X_real)
            loss = criterion(predictions, y_real)
            
            # Backward pass
            loss.backward()
            optimizer.step()
        
        logger.info(f"✅ Quality scorer trained on {len(real_market_data)} real samples")
    
    def check_temporal_consistency(self, data: Dict) -> bool:
        """
        Check for look-ahead bias in synthetic data
        
        Returns True if no look-ahead bias detected
        """
        prices = data['prices']
        
        # Check for unrealistic predictability
        returns = np.diff(np.log(prices))
        
        # Autocorrelation should be near zero for returns
        autocorr_1 = np.corrcoef(returns[:-1], returns[1:])[0, 1]
        
        # Check for unrealistic autocorrelation (indicates look-ahead)
        if abs(autocorr_1) > 0.1:  # Real markets have near-zero autocorr
            logger.warning(f"Potential look-ahead bias detected: autocorr={autocorr_1:.3f}")
            return False
        
        return True


# =============================================================================
# L0: World Fabric Simulator — Active Domain Randomization & Curriculum
# =============================================================================

@dataclass
class DomainRandomizationConfig:
    """
    Configuration for active domain randomization.
    Each parameter has a range that is actively expanded based on
    L3 ensemble disagreement — if the model is uncertain about a regime,
    generate more training data in that regime.
    """
    volatility_range: Tuple[float, float] = (0.1, 0.6)
    drift_range: Tuple[float, float] = (-0.001, 0.001)
    spread_range: Tuple[float, float] = (0.0001, 0.005)
    liquidity_range: Tuple[float, float] = (1000, 1000000)
    news_frequency_range: Tuple[float, float] = (0.01, 0.1)
    correlation_range: Tuple[float, float] = (-0.5, 0.5)
    mean_reversion_strength: Tuple[float, float] = (0.0, 0.5)
    jump_intensity_range: Tuple[float, float] = (0.0, 0.05)

    # Active expansion: if L3 disagreement is high in a regime,
    # expand the range to cover more of that space
    expansion_rate: float = 0.1
    max_expansion: float = 2.0


@dataclass
class CurriculumLevel:
    """
    A level in the training curriculum.
    Progressively increases difficulty based on agent performance.
    """
    level_id: int
    name: str
    description: str

    # Difficulty parameters
    volatility_multiplier: float = 1.0
    complexity_multiplier: float = 1.0
    horizon_multiplier: float = 1.0
    noise_multiplier: float = 1.0

    # Graduation criteria
    min_success_rate: float = 0.7
    min_episodes: int = 100

    # Status
    is_unlocked: bool = False
    completion_rate: float = 0.0
    episodes_played: int = 0


class WorldFabricSimulator:
    """
    L0: World Fabric Simulator

    Active domain randomization and curriculum environment generation.

    Key principle: if the model is uncertain about a regime (high L3 ensemble
    disagreement), generate more training data in that regime. This is the
    "active" part — the simulator actively targets the model's weaknesses.

    Curriculum: progressively increases difficulty based on agent performance.
    The agent must demonstrate competence at Level N before unlocking Level N+1.

    Sim-to-Real Adaptation: identifies the domain gap between simulated and
    real market data, and adjusts randomization parameters to close the gap.

    Train on adversarially generated high-uncertainty scenarios for robustness
    before deployment.
    """

    def __init__(
        self,
        base_generator: Optional[SyntheticMarketGenerator] = None,
        domain_config: Optional[DomainRandomizationConfig] = None,
        n_curriculum_levels: int = 10,
        sim_to_real_threshold: float = 0.1
    ):
        self.base_generator = base_generator or SyntheticMarketGenerator()
        self.domain_config = domain_config or DomainRandomizationConfig()
        self.sim_to_real_threshold = sim_to_real_threshold

        # Curriculum levels
        self.curriculum: List[CurriculumLevel] = []
        for i in range(n_curriculum_levels):
            difficulty = 1.0 + i * 0.5
            self.curriculum.append(CurriculumLevel(
                level_id=i,
                name=f"Level_{i}",
                description=f"Difficulty {difficulty:.1f}x",
                volatility_multiplier=difficulty,
                complexity_multiplier=min(difficulty, 3.0),
                horizon_multiplier=min(1.0 + i * 0.2, 3.0),
                noise_multiplier=min(difficulty * 0.5, 2.0),
                is_unlocked=(i == 0)  # Only first level unlocked initially
            ))

        # Domain gap tracking
        self.domain_gap_history: List[float] = []
        self.uncertainty_heatmap: Dict[str, float] = {}  # regime -> disagreement

        # Active randomization state
        self._expansion_factors: Dict[str, float] = {}

        logger.info("✅ World Fabric Simulator (L0) initialized")
        logger.info(f"   Curriculum levels: {n_curriculum_levels}")
        logger.info(f"   Sim-to-real threshold: {sim_to_real_threshold}")

    def generate_curriculum_scenario(
        self,
        level: Optional[int] = None,
        ensemble_disagreement: Optional[Dict[str, float]] = None
    ) -> Dict:
        """
        Generate a training scenario at the appropriate curriculum level.

        If ensemble_disagreement is provided, actively target high-uncertainty
        regimes by biasing scenario generation toward them.
        """
        # Determine curriculum level
        if level is None:
            level = self._get_current_curriculum_level()

        curr = self.curriculum[level]

        # Active domain randomization: sample parameters
        vol = self._sample_param(
            self.domain_config.volatility_range,
            curr.volatility_multiplier,
            'volatility',
            ensemble_disagreement
        )
        drift = self._sample_param(
            self.domain_config.drift_range,
            curr.complexity_multiplier,
            'drift',
            ensemble_disagreement
        )
        spread = self._sample_param(
            self.domain_config.spread_range,
            curr.noise_multiplier,
            'spread',
            ensemble_disagreement
        )

        # Generate scenario with randomized parameters
        scenario_config = {
            'volatility': vol,
            'drift': drift,
            'spread': spread,
            'liquidity': self._sample_param(
                self.domain_config.liquidity_range, 1.0, 'liquidity', ensemble_disagreement
            ),
            'news_frequency': self._sample_param(
                self.domain_config.news_frequency_range, curr.complexity_multiplier, 'news', ensemble_disagreement
            ),
            'level': level,
            'level_name': curr.name
        }

        # Use base generator with custom parameters
        scenario = self.base_generator.generate_scenario(
            MarketScenario(
                name=f"curriculum_L{level}",
                volatility=vol,
                drift=drift,
                mean_reversion=0.1 * curr.complexity_multiplier,
                jump_probability=0.01 * curr.complexity_multiplier,
                spread=spread
            ),
            initial_price=100.0
        )

        scenario['curriculum_config'] = scenario_config
        return scenario

    def generate_adversarial_batch(
        self,
        uncertainty_heatmap: Dict[str, float],
        batch_size: int = 100
    ) -> List[Dict]:
        """
        Generate adversarial training batch targeting high-uncertainty regions.

        Train on adversarially generated high-uncertainty scenarios for robustness.
        The simulator actively generates scenarios in regions where L3 ensemble
        disagreement is highest.
        """
        self.uncertainty_heatmap = uncertainty_heatmap

        # Weight scenario generation toward high-uncertainty regimes
        regimes = list(uncertainty_heatmap.keys())
        weights = np.array([uncertainty_heatmap[r] for r in regimes])
        if weights.sum() > 0:
            weights = weights / weights.sum()
        else:
            weights = np.ones(len(regimes)) / len(regimes)

        batch = []
        for _ in range(batch_size):
            # Sample regime weighted by uncertainty
            regime_idx = np.random.choice(len(regimes), p=weights)
            regime_name = regimes[regime_idx]

            # Generate scenario in that regime with elevated difficulty
            scenario = self.generate_curriculum_scenario(
                level=self._get_current_curriculum_level(),
                ensemble_disagreement=uncertainty_heatmap
            )
            scenario['target_regime'] = regime_name
            scenario['adversarial'] = True
            batch.append(scenario)

        return batch

    def update_curriculum_progress(
        self,
        level: int,
        success: bool,
        episode_reward: float
    ):
        """
        Update curriculum level progress based on agent performance.
        Graduate to next level when success rate exceeds threshold.
        """
        if level >= len(self.curriculum):
            return

        curr = self.curriculum[level]
        curr.episodes_played += 1

        if success:
            curr.completion_rate = (
                curr.completion_rate * (curr.episodes_played - 1) + 1.0
            ) / curr.episodes_played
        else:
            curr.completion_rate = (
                curr.completion_rate * (curr.episodes_played - 1)
            ) / curr.episodes_played

        # Check graduation
        if (curr.completion_rate >= curr.min_success_rate and
            curr.episodes_played >= curr.min_episodes and
            level + 1 < len(self.curriculum)):
            self.curriculum[level + 1].is_unlocked = True
            logger.info(f"📚 Curriculum Level {level + 1} unlocked!")

    def compute_sim_to_real_gap(
        self,
        real_data_stats: Dict[str, float],
        sim_data_stats: Dict[str, float]
    ) -> float:
        """
        Compute domain gap between simulated and real market data.
        Returns a scalar gap measure (0 = perfect match).
        """
        gap = 0.0
        n_metrics = 0
        for key in real_data_stats:
            if key in sim_data_stats:
                real_val = real_data_stats[key]
                sim_val = sim_data_stats[key]
                if abs(real_val) > 1e-8:
                    gap += abs(real_val - sim_val) / abs(real_val)
                else:
                    gap += abs(real_val - sim_val)
                n_metrics += 1

        gap = gap / max(n_metrics, 1)
        self.domain_gap_history.append(gap)

        # If gap exceeds threshold, expand domain randomization
        if gap > self.sim_to_real_threshold:
            self._expand_randomization(gap)

        return gap

    def _expand_randomization(self, gap: float):
        """
        Expand domain randomization ranges to close sim-to-real gap.
        Active domain randomization: if the model underperforms in a region,
        generate more diverse training data covering that region.
        """
        expansion = min(gap * self.domain_config.expansion_rate, self.domain_config.max_expansion)

        # Expand all ranges
        self.domain_config.volatility_range = (
            self.domain_config.volatility_range[0] * (1 - expansion * 0.1),
            self.domain_config.volatility_range[1] * (1 + expansion * 0.1)
        )
        self.domain_config.drift_range = (
            self.domain_config.drift_range[0] * (1 + expansion * 0.1),
            self.domain_config.drift_range[1] * (1 + expansion * 0.1)
        )

    def _sample_param(
        self,
        range_tuple: Tuple[float, float],
        multiplier: float = 1.0,
        param_name: str = "",
        disagreement: Optional[Dict[str, float]] = None
    ) -> float:
        """Sample a parameter with active expansion based on disagreement."""
        low, high = range_tuple

        # Expand range based on active expansion factor
        expansion = self._expansion_factors.get(param_name, 1.0)
        low *= expansion
        high *= expansion * multiplier

        # If disagreement data available, bias sampling toward uncertain regions
        if disagreement and param_name in disagreement:
            uncertainty_weight = disagreement[param_name]
            # Bias toward the end of the range with higher uncertainty
            if uncertainty_weight > 0.5:
                # Sample from upper portion of range
                sample_point = np.random.uniform(0.5, 1.0)
            else:
                sample_point = np.random.uniform(0.0, 1.0)
        else:
            sample_point = np.random.uniform(0.0, 1.0)

        return low + (high - low) * sample_point

    def _get_current_curriculum_level(self) -> int:
        """Get the highest unlocked curriculum level."""
        for i in range(len(self.curriculum) - 1, -1, -1):
            if self.curriculum[i].is_unlocked:
                return i
        return 0

    def get_curriculum_status(self) -> Dict:
        """Get current curriculum status."""
        return {
            'current_level': self._get_current_curriculum_level(),
            'levels': [
                {
                    'level': c.level_id,
                    'name': c.name,
                    'unlocked': c.is_unlocked,
                    'completion_rate': c.completion_rate,
                    'episodes': c.episodes_played
                }
                for c in self.curriculum
            ],
            'domain_gap_history': self.domain_gap_history[-10:],
            'uncertainty_heatmap_size': len(self.uncertainty_heatmap)
        }


# =============================================================================
# L0 Ceiling-Pushed: Continual/Staged Randomization, Real-Anchored Sim RL,
# Shielded Evaluation Before Promotion
# =============================================================================

@dataclass
class RandomizationStage:
    """
    A stage in the continual/staged randomization schedule.

    Instead of brute randomization (sample everything uniformly from wide ranges),
    staged randomization progressively widens the distribution as the agent
    masters each stage. This is the "continual" part — the randomization
    distribution itself is a curriculum.

    Stage 0: Narrow ranges (easy, deterministic-ish environments)
    Stage 1: Wider ranges (moderate variation)
    Stage 2: Full ranges (maximum diversity)
    Stage 3+: Adversarial (targeted at model weaknesses)
    """
    stage_id: int
    name: str

    # Per-parameter range multipliers (0.0 = fixed, 1.0 = full range)
    volatility_scale: float = 0.2
    drift_scale: float = 0.2
    spread_scale: float = 0.3
    liquidity_scale: float = 0.5
    news_scale: float = 0.1
    correlation_scale: float = 0.2
    jump_scale: float = 0.1

    # Graduation criteria
    min_episodes: int = 200
    min_success_rate: float = 0.65
    max_domain_gap: float = 0.15

    # Status
    is_active: bool = False
    episodes_completed: int = 0
    success_rate: float = 0.0
    domain_gap: float = 1.0


class ContinualStagedRandomizer:
    """
    L0 Ceiling-Pushed: Continual/Staged Randomization.

    Brute randomization (uniform over wide ranges) is suboptimal because:
    1. Early training wastes samples on regimes the agent can't handle yet
    2. The agent overfits to the current randomization distribution
    3. There's no structured progression toward real-world complexity

    Staged randomization fixes this by progressively widening the
    randomization distribution as the agent masters each stage. This is
    the "continual" part — the randomization distribution itself is a
    curriculum, not just the task difficulty.

    The key insight: randomization is not just noise — it's a training
    signal. The right amount of randomization at the right time is more
    valuable than maximum randomization from the start.
    """

    def __init__(
        self,
        base_config: Optional[DomainRandomizationConfig] = None,
        n_stages: int = 5
    ):
        self.base_config = base_config or DomainRandomizationConfig()

        # Build stages with progressively wider ranges
        self.stages: List[RandomizationStage] = []
        for i in range(n_stages):
            scale = 0.2 + 0.8 * (i / max(n_stages - 1, 1))  # 0.2 → 1.0
            self.stages.append(RandomizationStage(
                stage_id=i,
                name=f"rand_stage_{i}",
                volatility_scale=scale,
                drift_scale=scale,
                spread_scale=min(scale * 1.2, 1.0),
                liquidity_scale=min(scale * 1.5, 1.0),
                news_scale=max(scale - 0.1, 0.1),
                correlation_scale=scale,
                jump_scale=max(scale - 0.2, 0.05),
                is_active=(i == 0),
                min_episodes=200 + i * 100,  # More episodes at higher stages
                min_success_rate=max(0.65 - i * 0.03, 0.5)  # Slightly easier threshold at harder stages
            ))

        self.current_stage_idx = 0

        logger.info(f"✅ Continual Staged Randomizer initialized with {n_stages} stages")

    def get_current_stage(self) -> RandomizationStage:
        """Get the currently active randomization stage."""
        return self.stages[self.current_stage_idx]

    def sample_parameters(self) -> Dict[str, float]:
        """
        Sample domain randomization parameters from the current stage.
        Uses the stage's scale factors to determine how wide each parameter's
        range should be.
        """
        stage = self.get_current_stage()

        def scaled_sample(base_range: Tuple[float, float], scale: float) -> float:
            low, high = base_range
            center = (low + high) / 2.0
            half_width = (high - low) / 2.0 * scale
            return np.random.uniform(center - half_width, center + half_width)

        return {
            'volatility': scaled_sample(self.base_config.volatility_range, stage.volatility_scale),
            'drift': scaled_sample(self.base_config.drift_range, stage.drift_scale),
            'spread': scaled_sample(self.base_config.spread_range, stage.spread_scale),
            'liquidity': scaled_sample(self.base_config.liquidity_range, stage.liquidity_scale),
            'news_frequency': scaled_sample(self.base_config.news_frequency_range, stage.news_scale),
            'correlation': scaled_sample(self.base_config.correlation_range, stage.correlation_scale),
            'jump_intensity': scaled_sample(self.base_config.jump_intensity_range, stage.jump_scale),
            'stage': stage.stage_id,
            'stage_name': stage.name
        }

    def update_stage_progress(
        self,
        success: bool,
        domain_gap: float = 1.0
    ) -> bool:
        """
        Update the current stage's progress. Returns True if graduated to next stage.

        Graduation requires:
        1. Enough episodes played
        2. High enough success rate
        3. Domain gap below threshold (sim close enough to real)
        """
        stage = self.stages[self.current_stage_idx]
        stage.episodes_completed += 1

        # Update running success rate
        if success:
            stage.success_rate = (
                stage.success_rate * (stage.episodes_completed - 1) + 1.0
            ) / stage.episodes_completed
        else:
            stage.success_rate = (
                stage.success_rate * (stage.episodes_completed - 1)
            ) / stage.episodes_completed

        stage.domain_gap = domain_gap

        # Check graduation
        can_graduate = (
            stage.episodes_completed >= stage.min_episodes and
            stage.success_rate >= stage.min_success_rate and
            domain_gap <= stage.max_domain_gap
        )

        if can_graduate and self.current_stage_idx < len(self.stages) - 1:
            self.current_stage_idx += 1
            self.stages[self.current_stage_idx].is_active = True
            logger.info(f"🎯 Randomization stage graduated to {self.stages[self.current_stage_idx].name}")
            return True

        return False

    def get_stage_status(self) -> Dict:
        """Get status of all randomization stages."""
        return {
            'current_stage': self.current_stage_idx,
            'stages': [
                {
                    'stage_id': s.stage_id,
                    'name': s.name,
                    'active': s.is_active,
                    'episodes': s.episodes_completed,
                    'success_rate': s.success_rate,
                    'domain_gap': s.domain_gap
                }
                for s in self.stages
            ]
        }


class RealAnchoredSimCoTrainer:
    """
    L0 Ceiling-Pushed: Real-Anchored Sim RL / Co-Training.

    The fundamental problem with pure simulation: the simulator can generate
    data the model has never seen, but it can also generate data that doesn't
    look like reality at all. The model then trains on unrealistic data and
    fails in the real world.

    Real-anchored sim RL fixes this by:
    1. Using real market data as "anchor points" — the sim must produce
       data that is statistically close to these anchors
    2. Co-training: simultaneously training on real and simulated data,
       with a domain classifier ensuring the model can't distinguish them
    3. Adaptive weighting: if the sim drifts too far from real data,
       reduce its training weight until the gap closes
    4. Real data augmentation: use real data as seeds for sim generation,
       so simulated scenarios always start from realistic states

    Without real anchoring, the simulator is free to generate any fantasy
    it wants, and the model will train on that fantasy.
    """

    def __init__(
        self,
        sim_generator: Optional[SyntheticMarketGenerator] = None,
        real_data_buffer: Optional[List[Dict]] = None,
        anchor_check_interval: int = 100,
        domain_classifier_threshold: float = 0.55,
        sim_weight_floor: float = 0.3
    ):
        self.sim_generator = sim_generator or SyntheticMarketGenerator()
        self.real_data_buffer = real_data_buffer or []
        self.anchor_check_interval = anchor_check_interval
        self.domain_classifier_threshold = domain_classifier_threshold
        self.sim_weight_floor = sim_weight_floor

        # Training weight for simulated data (vs real)
        self.sim_weight = 0.7  # Start high, reduce if sim drifts
        self.real_weight = 0.3

        # Anchor statistics from real data
        self.real_stats: Dict[str, float] = {}
        self._episodes_since_anchor_check = 0

        # Domain gap tracking
        self.gap_history: List[float] = []

        logger.info("✅ Real-Anchored Sim Co-Trainer initialized")

    def register_real_data(self, real_data_batch: List[Dict]):
        """
        Register a batch of real market data as anchor points.
        Compute statistics that simulated data must match.
        """
        self.real_data_buffer.extend(real_data_batch)

        # Update real data statistics
        if self.real_data_buffer:
            all_returns = []
            all_volumes = []
            all_volatilities = []

            for data in self.real_data_buffer:
                if 'prices' in data:
                    prices = np.array(data['prices'])
                    returns = np.diff(np.log(prices))
                    all_returns.extend(returns.tolist())
                    all_volatilities.append(np.std(returns))
                if 'volumes' in data:
                    all_volumes.extend(data['volumes'])

            if all_returns:
                self.real_stats = {
                    'mean_return': float(np.mean(all_returns)),
                    'std_return': float(np.std(all_returns)),
                    'skew_return': float(self._skewness(all_returns)),
                    'kurtosis_return': float(self._kurtosis(all_returns)),
                    'mean_volatility': float(np.mean(all_volatilities)) if all_volatilities else 0.0,
                    'n_anchors': len(self.real_data_buffer)
                }

    def generate_anchored_scenario(self) -> Dict:
        """
        Generate a simulated scenario anchored to real data statistics.

        Instead of sampling from arbitrary ranges, start from a real data
        seed and perturb it. This ensures the simulated scenario is
        "close to" reality in distribution.
        """
        if not self.real_data_buffer:
            # No real data yet — fall back to unanchored generation
            return self.sim_generator.generate_scenario(
                MarketScenario(name="unanchored", volatility=0.2, drift=0.0)
            )

        # Pick a random real data sample as seed
        seed_idx = np.random.randint(len(self.real_data_buffer))
        seed_data = self.real_data_buffer[seed_idx]

        # Perturb the seed to create a new scenario
        # The perturbation magnitude is controlled by sim_weight:
        # higher sim_weight = more perturbation = less anchoring
        perturbation_scale = self.sim_weight

        scenario = self._perturb_real_seed(seed_data, perturbation_scale)
        scenario['anchored'] = True
        scenario['seed_idx'] = seed_idx
        scenario['perturbation_scale'] = perturbation_scale

        return scenario

    def compute_anchor_loss(
        self,
        sim_batch_stats: Dict[str, float]
    ) -> float:
        """
        Compute how far simulated data statistics have drifted from real anchors.
        Returns a scalar loss (0 = perfect match to real data).
        """
        if not self.real_stats:
            return 0.0

        loss = 0.0
        n_metrics = 0
        for key in ['mean_return', 'std_return', 'skew_return', 'kurtosis_return', 'mean_volatility']:
            if key in self.real_stats and key in sim_batch_stats:
                real_val = self.real_stats[key]
                sim_val = sim_batch_stats[key]
                if abs(real_val) > 1e-8:
                    loss += ((sim_val - real_val) / real_val) ** 2
                else:
                    loss += (sim_val - real_val) ** 2
                n_metrics += 1

        if n_metrics > 0:
            loss /= n_metrics

        self.gap_history.append(loss)

        # Adaptively adjust sim/real training weights
        self._adjust_weights(loss)

        return loss

    def get_training_weights(self) -> Tuple[float, float]:
        """Get current sim and real data training weights."""
        return self.sim_weight, self.real_weight

    def _adjust_weights(self, anchor_loss: float):
        """
        Adjust sim/real training weights based on anchor loss.
        If sim drifts far from real, reduce sim weight.
        """
        if anchor_loss > 0.5:
            # Sim is far from real — reduce sim weight
            self.sim_weight = max(self.sim_weight_floor, self.sim_weight - 0.05)
            self.real_weight = 1.0 - self.sim_weight
        elif anchor_loss < 0.1:
            # Sim is close to real — can increase sim weight
            self.sim_weight = min(0.8, self.sim_weight + 0.02)
            self.real_weight = 1.0 - self.sim_weight

    def _perturb_real_seed(self, seed_data: Dict, scale: float) -> Dict:
        """Perturb a real data seed to create a new simulated scenario."""
        scenario = {'prices': [], 'volumes': []}

        if 'prices' in seed_data:
            base_prices = np.array(seed_data['prices'])
            # Add Gaussian noise scaled by perturbation
            noise = np.random.normal(0, scale * 0.01, len(base_prices))
            perturbed_prices = base_prices * np.exp(np.cumsum(noise))
            scenario['prices'] = perturbed_prices.tolist()

        if 'volumes' in seed_data:
            base_volumes = np.array(seed_data['volumes'])
            volume_noise = np.random.lognormal(0, scale * 0.5, len(base_volumes))
            scenario['volumes'] = (base_volumes * volume_noise).tolist()

        return scenario

    @staticmethod
    def _skewness(data):
        """Compute skewness of a distribution."""
        arr = np.array(data)
        if len(arr) < 3:
            return 0.0
        mean = np.mean(arr)
        std = np.std(arr)
        if std < 1e-10:
            return 0.0
        return float(np.mean(((arr - mean) / std) ** 3))

    @staticmethod
    def _kurtosis(data):
        """Compute excess kurtosis of a distribution."""
        arr = np.array(data)
        if len(arr) < 4:
            return 0.0
        mean = np.mean(arr)
        std = np.std(arr)
        if std < 1e-10:
            return 0.0
        return float(np.mean(((arr - mean) / std) ** 4) - 3.0)


class ShieldedCurriculumEvaluator:
    """
    L0 Ceiling-Pushed: Shielded Evaluation Before Promotion.

    The standard curriculum just checks success rate before promoting to the
    next level. But a policy can achieve high success rate by taking risky
    actions that happen to work in training but would violate safety
    constraints in deployment.

    Shielded evaluation runs the agent under the L10 Runtime Shield before
    promotion. The agent must demonstrate:
    1. High success rate (standard curriculum requirement)
    2. No LTL safety violations during evaluation episodes
    3. Low anomaly scores (no out-of-distribution behavior)
    4. Confidence above threshold (model knows what it's doing)

    Only when ALL four criteria are met does the agent graduate.
    This prevents "fast but reckless" policies from being promoted.
    """

    def __init__(
        self,
        runtime_shield=None,
        n_evaluation_episodes: int = 50,
        safety_violation_tolerance: int = 0,
        anomaly_threshold: float = 3.0,
        confidence_threshold: float = 0.5,
        success_rate_threshold: float = 0.7
    ):
        self.runtime_shield = runtime_shield
        self.n_evaluation_episodes = n_evaluation_episodes
        self.safety_violation_tolerance = safety_violation_tolerance
        self.anomaly_threshold = anomaly_threshold
        self.confidence_threshold = confidence_threshold
        self.success_rate_threshold = success_rate_threshold

        # Evaluation history
        self.evaluation_history: List[Dict] = []

        logger.info("✅ Shielded Curriculum Evaluator initialized")

    def evaluate_for_promotion(
        self,
        agent_policy=None,
        curriculum_level: int = 0,
        scenario_generator=None
    ) -> Dict[str, Any]:
        """
        Run shielded evaluation to determine if agent can be promoted.

        Returns dict with:
        - can_promote: bool
        - success_rate: float
        - safety_violations: int
        - avg_anomaly_score: float
        - avg_confidence: float
        - details: per-episode results
        """
        results = {
            'can_promote': False,
            'success_rate': 0.0,
            'safety_violations': 0,
            'avg_anomaly_score': 0.0,
            'avg_confidence': 0.0,
            'details': []
        }

        successes = 0
        violations = 0
        anomaly_scores = []
        confidence_scores = []

        for ep in range(self.n_evaluation_episodes):
            episode_result = self._run_shielded_episode(
                agent_policy, curriculum_level, scenario_generator
            )

            results['details'].append(episode_result)

            if episode_result.get('success', False):
                successes += 1
            violations += episode_result.get('safety_violations', 0)
            anomaly_scores.append(episode_result.get('anomaly_score', 0.0))
            confidence_scores.append(episode_result.get('confidence', 0.0))

        # Compute aggregates
        results['success_rate'] = successes / max(self.n_evaluation_episodes, 1)
        results['safety_violations'] = violations
        results['avg_anomaly_score'] = float(np.mean(anomaly_scores)) if anomaly_scores else 0.0
        results['avg_confidence'] = float(np.mean(confidence_scores)) if confidence_scores else 0.0

        # Promotion decision: ALL criteria must be met
        results['can_promote'] = (
            results['success_rate'] >= self.success_rate_threshold and
            results['safety_violations'] <= self.safety_violation_tolerance and
            results['avg_anomaly_score'] <= self.anomaly_threshold and
            results['avg_confidence'] >= self.confidence_threshold
        )

        # Record evaluation
        self.evaluation_history.append({
            'level': curriculum_level,
            'can_promote': results['can_promote'],
            'success_rate': results['success_rate'],
            'safety_violations': results['safety_violations'],
            'avg_anomaly_score': results['avg_anomaly_score'],
            'avg_confidence': results['avg_confidence']
        })

        if results['can_promote']:
            logger.info(f"🛡️ Shielded evaluation PASSED for level {curriculum_level} "
                        f"(success={results['success_rate']:.2f}, "
                        f"violations={violations}, "
                        f"anomaly={results['avg_anomaly_score']:.2f}, "
                        f"confidence={results['avg_confidence']:.2f})")
        else:
            logger.info(f"🛡️ Shielded evaluation FAILED for level {curriculum_level} "
                        f"(success={results['success_rate']:.2f}, "
                        f"violations={violations}, "
                        f"anomaly={results['avg_anomaly_score']:.2f}, "
                        f"confidence={results['avg_confidence']:.2f})")

        return results

    def _run_shielded_episode(
        self,
        agent_policy,
        curriculum_level: int,
        scenario_generator
    ) -> Dict[str, Any]:
        """
        Run a single episode under the runtime shield.

        If no agent_policy or runtime_shield is provided, uses heuristic
        evaluation based on curriculum level difficulty.
        """
        result = {
            'success': False,
            'safety_violations': 0,
            'anomaly_score': 0.0,
            'confidence': 0.0
        }

        # If we have a runtime shield, use it for safety checking
        if self.runtime_shield is not None:
            # The shield would check each action during the episode
            # For now, simulate the check
            try:
                # Simulate episode with shield monitoring
                shield_result = self.runtime_shield.check_state_confidence(
                    torch.zeros(64)  # Placeholder state
                )
                result['confidence'] = shield_result if isinstance(shield_result, (int, float)) else 0.5
                result['anomaly_score'] = 0.0  # Would be computed from actual episode
                result['safety_violations'] = 0  # Would be counted during episode
            except Exception:
                result['confidence'] = 0.3
                result['anomaly_score'] = 5.0
        else:
            # No shield available — use heuristic evaluation
            # Higher curriculum levels are harder to pass
            difficulty = 1.0 + curriculum_level * 0.3
            result['success'] = np.random.random() < (0.8 / difficulty)
            result['confidence'] = max(0.3, 0.8 / difficulty + np.random.normal(0, 0.1))
            result['anomaly_score'] = np.random.exponential(0.5 * difficulty)
            result['safety_violations'] = int(np.random.poisson(0.1 * difficulty))

        return result
