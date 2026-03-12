"""
Adaptive Systems Integration Demo

This example demonstrates how the various adaptive systems work together
to create a comprehensive trading system that adapts to market conditions.
"""

import sys
import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import asyncio
import logging
import matplotlib.pyplot as plt
from typing import Dict, List, Optional

# Add the project root to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import adaptive systems
from trading_bot.adaptive_systems.market_microstructure import MarketMicrostructureAnalyzer, MicrostructureSignal
from trading_bot.adaptive_systems.market_maker import AdaptiveMarketMaker, MarketMakingParameters, QuoteUpdate
from trading_bot.adaptive_systems.liquidity_provider import LiquidityProvider, LiquidityParameters, LiquidityQuote
from trading_bot.adaptive_systems.order_flow_analyzer import OrderFlowAnalyzer, OrderFlowSignal
from trading_bot.adaptive_systems.volatility_analyzer import VolatilityAnalyzer, VolatilitySignal, VolatilityRegime
from trading_bot.adaptive_systems.correlation_analyzer import CorrelationAnalyzer, CorrelationSignal
from trading_bot.adaptive_systems.regime_detector import RegimeDetector, RegimeSignal, MarketState
from trading_bot.adaptive_systems.sentiment_analyzer import SentimentAnalyzer, SentimentSignal, SentimentSource
import numpy
import pandas

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class AdaptiveSystemsDemo:
    """
    Demo class that integrates all adaptive systems
    """
    
    def __init__(self):
        """Initialize all adaptive systems"""
        logger.info("Initializing Adaptive Systems Demo")
        
        # Initialize all systems
        self.microstructure_analyzer = MarketMicrostructureAnalyzer()
        self.market_maker = AdaptiveMarketMaker(
            MarketMakingParameters(
                gamma=0.1,
                k=1.5,
                sigma=0.02,
                T=3600,  # 1 hour in seconds
                inventory_limit=100,
                position_fade_time=1800,  # 30 minutes
                min_spread=0.01,
                max_spread=0.1,
                tick_size=0.01,
                lot_size=1.0,
                risk_limit=10000
            )
        )
        self.liquidity_provider = LiquidityProvider(
            LiquidityParameters(
                max_position=1000,
                max_risk=50000,
                min_spread=0.01,
                max_spread=0.2,
                tick_size=0.01,
                lot_size=1.0,
                risk_limit=20000,
                capital=100000,
                target_utilization=0.7,
                rebalance_threshold=0.8
            )
        )
        self.order_flow_analyzer = OrderFlowAnalyzer()
        self.volatility_analyzer = VolatilityAnalyzer()
        self.correlation_analyzer = CorrelationAnalyzer()
        self.regime_detector = RegimeDetector()
        self.sentiment_analyzer = SentimentAnalyzer()
        
        # State tracking
        self.current_regime = None
        self.current_signals = []
        self.market_data = {}
        self.performance_metrics = {
            'pnl': [],
            'sharpe': 0,
            'max_drawdown': 0,
            'win_rate': 0
        }
        
        logger.info("All adaptive systems initialized")
    
    async def run_demo(self, data_file: str = None):
        """Run the demo with either real or simulated data"""
        logger.info("Starting Adaptive Systems Demo")
        
        # Load or generate data
        if data_file and os.path.exists(data_file):
            market_data = self._load_market_data(data_file)
        else:
            market_data = self._generate_simulated_data()
        
        # Process data in time sequence
        for timestamp, data in market_data.items():
            logger.info(f"Processing data for {timestamp}")
            
            # Update market data
            self.market_data = data
            
            # Run all adaptive systems
            await self._run_analysis_cycle()
            
            # Simulate trading decisions
            await self._make_trading_decisions()
            
            # Update performance metrics
            self._update_performance()
            
            # Display current state
            self._display_current_state()
        
        # Show final results
        self._display_final_results()
    
    async def _run_analysis_cycle(self):
        """Run a complete analysis cycle with all systems"""
        # Analyze market microstructure
        micro_signals = self.microstructure_analyzer.analyze_microstructure(
            self.market_data.get('tick_data', pd.DataFrame()),
            self.market_data.get('order_book')
        )
        
        # Analyze order flow
        flow_signals = self.order_flow_analyzer.analyze_order_flow(
            self.market_data.get('trades', []),
            self.market_data.get('order_book')
        )
        
        # Analyze volatility
        vol_signals = self.volatility_analyzer.analyze_volatility(
            self.market_data.get('price_data', pd.DataFrame()),
            self.market_data.get('options_data')
        )
        
        # Analyze correlations
        corr_signals = self.correlation_analyzer.analyze_correlations(
            self.market_data.get('correlation_data', {})
        )
        
        # Detect market regime
        regime, regime_signals = self.regime_detector.detect_regime(
            self.market_data.get('price_data', pd.DataFrame())
        )
        self.current_regime = regime
        
        # Analyze sentiment
        sentiment_signals = self.sentiment_analyzer.analyze_sentiment(
            self.market_data.get('sentiment_data', {})
        )
        
        # Combine all signals
        self.current_signals = (
            micro_signals + flow_signals + vol_signals + 
            corr_signals + regime_signals + sentiment_signals
        )
        
        logger.info(f"Analysis cycle complete - {len(self.current_signals)} signals generated")
        logger.info(f"Current regime: {self.current_regime.regime_type if self.current_regime else 'Unknown'}")
    
    async def _make_trading_decisions(self):
        """Make trading decisions based on current signals and regime"""
        if not self.current_regime:
            return
        
        # Generate market maker quotes based on regime
        market_data = {
            'mid_price': self.market_data.get('price_data', pd.DataFrame()).get('close', [100.0])[-1],
            'spread': 0.05,
            'volatility': self.market_data.get('volatility', 0.02)
        }
        quote = self.market_maker.generate_quotes(market_data)
        
        # Generate liquidity quotes based on regime
        venue_data = {
            'venue1': {
                'symbol1': {
                    'mid_price': market_data['mid_price'],
                    'spread': market_data['spread'],
                    'volatility': market_data['volatility'],
                    'volume': 10000
                }
            }
        }
        liquidity_quotes = self.liquidity_provider.optimize_liquidity(venue_data)
        
        # Adapt trading strategy based on regime
        strategy = self._select_strategy_for_regime(self.current_regime.regime_type)
        
        logger.info(f"Selected strategy: {strategy}")
        logger.info(f"Market maker quote - Bid: {quote.bid_price:.2f}, Ask: {quote.ask_price:.2f}, Spread: {quote.spread:.4f}")
    
    def _select_strategy_for_regime(self, regime_type: str) -> str:
        """Select appropriate trading strategy based on market regime"""
        strategy_map = {
            MarketState.TRENDING_UP: "momentum_following",
            MarketState.TRENDING_DOWN: "momentum_following",
            MarketState.RANGING: "mean_reversion",
            MarketState.VOLATILE: "volatility_harvesting",
            MarketState.BREAKOUT: "breakout_momentum",
            MarketState.REVERSAL: "counter_trend",
            MarketState.ACCUMULATION: "liquidity_provision",
            MarketState.DISTRIBUTION: "liquidity_taking"
        }
        
        return strategy_map.get(regime_type, "balanced")
    
    def _update_performance(self):
        """Update performance metrics"""
        # Simulate PnL based on regime and strategy alignment
        pnl = 0
        
        if self.current_regime:
            # Better performance when strategy aligns with regime
            strategy = self._select_strategy_for_regime(self.current_regime.regime_type)
            alignment_score = 0.8  # Assume good alignment
            
            # Base PnL on regime characteristics
            if self.current_regime.regime_type in [MarketState.TRENDING_UP, MarketState.BREAKOUT]:
                pnl = np.random.normal(100 * alignment_score, 50)
            elif self.current_regime.regime_type in [MarketState.TRENDING_DOWN]:
                pnl = np.random.normal(80 * alignment_score, 40)
            elif self.current_regime.regime_type in [MarketState.RANGING]:
                pnl = np.random.normal(50 * alignment_score, 30)
            elif self.current_regime.regime_type in [MarketState.VOLATILE]:
                pnl = np.random.normal(120 * alignment_score, 80)
            else:
                pnl = np.random.normal(70 * alignment_score, 40)
        
        self.performance_metrics['pnl'].append(pnl)
        
        # Update other metrics
        if len(self.performance_metrics['pnl']) > 1:
            returns = np.diff(self.performance_metrics['pnl'])
            self.performance_metrics['sharpe'] = np.mean(returns) / (np.std(returns) + 1e-6)
            self.performance_metrics['max_drawdown'] = self._calculate_max_drawdown(self.performance_metrics['pnl'])
            self.performance_metrics['win_rate'] = np.mean([1 if r > 0 else 0 for r in returns])
    
    def _calculate_max_drawdown(self, pnl_history: List[float]) -> float:
        """Calculate maximum drawdown from PnL history"""
        cumulative = np.cumsum(pnl_history)
        max_dd = 0
        peak = cumulative[0]
        
        for value in cumulative:
            if value > peak:
                peak = value
            dd = (peak - value) / (peak + 1e-6)
            max_dd = max(max_dd, dd)
        
        return max_dd
    
    def _display_current_state(self):
        """Display current state of the system"""
        logger.info(f"Current PnL: ${self.performance_metrics['pnl'][-1]:.2f}")
        logger.info(f"Cumulative PnL: ${sum(self.performance_metrics['pnl']):.2f}")
        logger.info(f"Sharpe Ratio: {self.performance_metrics['sharpe']:.2f}")
        logger.info(f"Win Rate: {self.performance_metrics['win_rate']:.2%}")
        logger.info("-" * 50)
    
    def _display_final_results(self):
        """Display final performance results"""
        logger.info("=" * 50)
        logger.info("FINAL RESULTS")
        logger.info("=" * 50)
        logger.info(f"Total Trading Periods: {len(self.performance_metrics['pnl'])}")
        logger.info(f"Total PnL: ${sum(self.performance_metrics['pnl']):.2f}")
        logger.info(f"Sharpe Ratio: {self.performance_metrics['sharpe']:.2f}")
        logger.info(f"Maximum Drawdown: {self.performance_metrics['max_drawdown']:.2%}")
        logger.info(f"Win Rate: {self.performance_metrics['win_rate']:.2%}")
        
        # Plot PnL curve
        plt.figure(figsize=(12, 6))
        plt.plot(np.cumsum(self.performance_metrics['pnl']))
        plt.title('Cumulative PnL')
        plt.xlabel('Trading Period')
        plt.ylabel('PnL ($)')
        plt.grid(True)
        plt.savefig('adaptive_systems_pnl.png')
        logger.info("PnL chart saved as 'adaptive_systems_pnl.png'")
    
    def _load_market_data(self, data_file: str) -> Dict:
        """Load market data from file"""
        logger.info(f"Loading market data from {data_file}")
        
        try:
            # Load data (format depends on your data structure)
            data = pd.read_csv(data_file)
            
            # Convert to time-indexed dictionary
            result = {}
            for _, row in data.iterrows():
                timestamp = pd.to_datetime(row['timestamp'])
                
                # Create data structure for this timestamp
                result[timestamp] = {
                    'price_data': self._create_price_data_frame(row),
                    'tick_data': self._create_tick_data_frame(row),
                    'trades': self._create_trades_list(row),
                    'order_book': self._create_order_book(row),
                    'volatility': row.get('volatility', 0.02),
                    'sentiment_data': self._create_sentiment_data(row),
                    'correlation_data': self._create_correlation_data(row),
                    'options_data': self._create_options_data(row)
                }
            
            return result
            
        except Exception as e:
            logger.error(f"Error loading market data: {e}")
            return self._generate_simulated_data()
    
    def _generate_simulated_data(self) -> Dict:
        """Generate simulated market data"""
        logger.info("Generating simulated market data")
        
        result = {}
        start_date = datetime.now() - timedelta(days=30)
        price = 100.0
        volatility = 0.02
        
        # Generate daily data for 30 days
        for i in range(30):
            timestamp = start_date + timedelta(days=i)
            
            # Simulate price movement
            daily_return = np.random.normal(0, volatility)
            price *= (1 + daily_return)
            
            # Simulate regime changes
            if i % 10 == 0:
                volatility = max(0.01, min(0.05, volatility + np.random.normal(0, 0.01)))
            
            # Create data for this timestamp
            result[timestamp] = {
                'price_data': self._create_simulated_price_data(price, volatility),
                'tick_data': self._create_simulated_tick_data(price, volatility),
                'trades': self._create_simulated_trades(price, volatility),
                'order_book': self._create_simulated_order_book(price, volatility),
                'volatility': volatility,
                'sentiment_data': self._create_simulated_sentiment_data(i),
                'correlation_data': self._create_simulated_correlation_data(i),
                'options_data': self._create_simulated_options_data(price, volatility)
            }
        
        return result
    
    def _create_simulated_price_data(self, price: float, volatility: float) -> pd.DataFrame:
        """Create simulated price data"""
        periods = 100
        prices = [price]
        
        for _ in range(periods - 1):
            new_price = prices[-1] * (1 + np.random.normal(0, volatility / 10))
            prices.append(new_price)
        
        high = [p * (1 + abs(np.random.normal(0, volatility / 5))) for p in prices]
        low = [p * (1 - abs(np.random.normal(0, volatility / 5))) for p in prices]
        
        return pd.DataFrame({
            'open': prices[:-1],
            'high': high[:-1],
            'low': low[:-1],
            'close': prices[1:],
            'volume': np.random.randint(1000, 10000, periods - 1)
        })
    
    def _create_simulated_tick_data(self, price: float, volatility: float) -> pd.DataFrame:
        """Create simulated tick data"""
        periods = 100
        prices = []
        
        for _ in range(periods):
            tick_price = price * (1 + np.random.normal(0, volatility / 20))
            prices.append(tick_price)
        
        return pd.DataFrame({
            'price': prices,
            'volume': np.random.randint(10, 100, periods),
            'bid': [p * 0.999 for p in prices],
            'ask': [p * 1.001 for p in prices]
        })
    
    def _create_simulated_trades(self, price: float, volatility: float) -> List[Dict]:
        """Create simulated trades"""
        num_trades = 50
        trades = []
        
        for _ in range(num_trades):
            side = 'buy' if np.random.random() > 0.5 else 'sell'
            trade_price = price * (1 + np.random.normal(0, volatility / 30))
            
            trades.append({
                'price': trade_price,
                'volume': np.random.randint(10, 1000),
                'side': side,
                'timestamp': datetime.now(),
                'aggressive': np.random.random() > 0.7
            })
        
        return trades
    
    def _create_simulated_order_book(self, price: float, volatility: float) -> Dict:
        """Create simulated order book"""
        num_levels = 10
        
        bids = []
        asks = []
        
        for i in range(num_levels):
            bid_price = price * (1 - (i + 1) * 0.001)
            ask_price = price * (1 + (i + 1) * 0.001)
            
            bids.append([bid_price, np.random.randint(100, 1000)])
            asks.append([ask_price, np.random.randint(100, 1000)])
        
        return {
            'bids': bids,
            'asks': asks
        }
    
    def _create_simulated_sentiment_data(self, day: int) -> Dict:
        """Create simulated sentiment data"""
        # Simulate news articles
        num_articles = np.random.randint(5, 15)
        news = []
        
        for _ in range(num_articles):
            sentiment = np.random.normal(0, 0.5)
            news.append({
                'title': f"Simulated news article {_}",
                'content': f"This is simulated content with sentiment {sentiment:.2f}",
                'timestamp': datetime.now(),
                'source': np.random.choice(['Bloomberg', 'Reuters', 'CNBC', 'WSJ'])
            })
        
        # Simulate social media posts
        num_posts = np.random.randint(20, 50)
        social = []
        
        for _ in range(num_posts):
            social.append({
                'content': f"Simulated social media post {_}",
                'platform': np.random.choice(['twitter', 'reddit', 'stocktwits']),
                'timestamp': datetime.now()
            })
        
        return {
            'news': news,
            'social': social
        }
    
    def _create_simulated_correlation_data(self, day: int) -> Dict:
        """Create simulated correlation data"""
        assets = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META']
        data = {}
        
        for asset in assets:
            # Generate random price series
            prices = 100 + np.cumsum(np.random.normal(0, 1, 100))
            
            data[asset] = pd.DataFrame({
                'close': prices,
                'volume': np.random.randint(1000, 10000, 100)
            })
        
        return data
    
    def _create_simulated_options_data(self, price: float, volatility: float) -> Dict:
        """Create simulated options data"""
        return {
            'atm_iv': volatility * 100,  # Convert to percentage
            'term_structure': {
                30: volatility * 95,
                60: volatility * 100,
                90: volatility * 105
            }
        }
    
    # Helper methods for loading real data
    def _create_price_data_frame(self, row) -> pd.DataFrame:
        """Create price data frame from row data"""
        # Implementation depends on your data format
        return pd.DataFrame()
    
    def _create_tick_data_frame(self, row) -> pd.DataFrame:
        """Create tick data frame from row data"""
        # Implementation depends on your data format
        return pd.DataFrame()
    
    def _create_trades_list(self, row) -> List[Dict]:
        """Create trades list from row data"""
        # Implementation depends on your data format
        return []
    
    def _create_order_book(self, row) -> Dict:
        """Create order book from row data"""
        # Implementation depends on your data format
        return {'bids': [], 'asks': []}
    
    def _create_sentiment_data(self, row) -> Dict:
        """Create sentiment data from row data"""
        # Implementation depends on your data format
        return {}
    
    def _create_correlation_data(self, row) -> Dict:
        """Create correlation data from row data"""
        # Implementation depends on your data format
        return {}
    
    def _create_options_data(self, row) -> Dict:
        """Create options data from row data"""
        # Implementation depends on your data format
        return {}


async def main():
    """Main function to run the demo"""
    demo = AdaptiveSystemsDemo()
    await demo.run_demo()


if __name__ == "__main__":
    asyncio.run(main())
