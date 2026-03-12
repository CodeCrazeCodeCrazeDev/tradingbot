# Advanced Algorithmic Trading Bot for MetaTrader 5

## 🤖 NEW: Thinking Bot - Complete Trading System

**The Thinking Bot is now available!** A fully autonomous trading system that thinks, validates, executes, monitors, and learns.

### Quick Start
```bash
# Validate system
python validate_thinking_bot.py

# Run the bot
python thinking_bot.py
# or
RUN_THINKING_BOT.bat
```

📚 **Documentation:** See `THINKING_BOT_GUIDE.md` for complete details  
📋 **Quick Reference:** See `QUICK_REFERENCE.md` for commands and tips  
✅ **Implementation:** See `THINKING_BOT_COMPLETE.md` for full feature list

---

## Overview
This project aims to create a professional‐grade, fully automated trading bot for the MetaTrader 5 (MT5) platform. The bot focuses on sophisticated price-action analysis, advanced market-structure and liquidity concepts, multiple institutional trading methodologies, AI/ML-powered predictions, strict risk-management and reporting practices, and high-performance optimization features.

Key objectives:
* Consistent profitability across diverse market conditions
* Advanced Market Structure (BOS, CHOCH, COS) & Liquidity analysis
* Integration of Wyckoff, SMC, ICT, Supply & Demand, Fair-Value-Gap (FVG) and Order-Block (OB) concepts
* AI/ML-powered price prediction, pattern recognition, and sentiment analysis
* Smart order execution with TWAP/VWAP algorithms to minimize market impact
* Reinforcement learning for strategy optimization and parameter tuning
* Emotional state tracking for trader psychology monitoring and improvement
* Robust risk management (dynamic position sizing, drawdown limits, multi-target exits)
* Comprehensive logging, real-time dashboards and scheduled performance reports
* High-performance optimization with parallel processing and memory efficiency
* Real-time monitoring dashboard with advanced analytics visualization
* Modular, extensible architecture with strong test coverage

## Project Structure
```
trading bot/             # Workspace root
│
├── docs/                # Documentation
│   ├── prompt_comparison.md
│   ├── elite_trading_bot_specification.md
│   ├── deepseek_prompt_comparison.md
│   ├── performance_optimization_guide.md
│   └── advanced_features_usage_guide.md
│
├── examples/            # Example scripts demonstrating usage
│   ├── advanced_trading_example.py
│   ├── elite_system_demo.py      # Elite Trading System demonstration

│   ├── advanced_market_analysis_demo.py  # Advanced market analysis visualization
│   ├── performance_optimization_demo.py  # Performance optimization features demo
│   ├── performance_optimization_integration.py  # Integrated performance features
│   └── real_time_dashboard_demo.py  # Real-time monitoring dashboard
│
├── trading_bot/         # Core Python package
│   ├── __init__.py
│   ├── config/
│   │   ├── __init__.py
│   │   └── config.yaml  # User-editable settings
│   ├── data/            # MT5 connectivity & market-data adapters
│   │   ├── __init__.py
│   │   └── mt5_interface.py
│   ├── analysis/        # Market-structure & liquidity analytics
│   │   ├── __init__.py
│   │   ├── market_structure.py
│   │   └── liquidity.py
│   ├── elite_system/    # Institutional-grade trading system
│   │   ├── __init__.py
│   │   ├── market_psychology.py   # Market sentiment & psychology analysis
│   │   ├── regime_detection.py    # Market regime classification
│   │   ├── risk_management.py     # Institutional-grade risk management
│   │   ├── pattern_recognition.py # Proprietary pattern detection
│   │   └── market_analysis.py     # Multi-timeframe market analysis
│   ├── ml/              # Machine learning & AI capabilities
│   │   ├── __init__.py
│   │   ├── predictive_models.py  # Price prediction & pattern recognition
│   │   ├── reinforcement.py      # Strategy optimization via RL
│   │   └── sentiment.py          # News & social media sentiment analysis
│   ├── execution/        # Order execution & algorithms
│   │   ├── __init__.py
│   │   ├── algorithms.py  # TWAP/VWAP execution algorithms
│   │   ├── paper_executor.py  # Paper trading execution
│   │   └── live_executor.py   # Live trading execution
│   ├── strategy/        # High-level signal-generation engine
│   │   ├── __init__.py
│   │   ├── strategy_engine.py
│   │   └── ml_strategy.py     # ML-enhanced strategy engine
│   ├── risk/            # Position-sizing & trade-management
│   │   ├── __init__.py
│   │   └── risk_manager.py
│   ├── analytics/       # Performance analytics & tracking
│   │   ├── __init__.py
│   │   ├── performance.py
│   │   ├── emotional_tracker.py  # Trader psychology monitoring
│   │   └── enhanced_performance.py  # Emotion-aware performance analytics
│   ├── performance/     # Performance optimization features
│   │   ├── __init__.py
│   │   ├── parallel_processor.py  # Multi-threading and multi-processing
│   │   ├── memory_optimization.py  # Memory-efficient data structures
│   │   ├── algorithm_optimizer.py  # Algorithmic optimizations
│   │   └── performance_monitor.py  # Performance monitoring and profiling
│   ├── dashboard/       # Real-time monitoring dashboard
│   │   ├── __init__.py
│   │   ├── dashboard_server.py  # Dashboard server and configuration
│   │   ├── components.py  # Base dashboard components
│   │   ├── components_risk_signal.py  # Risk and signal panels
│   │   ├── components_analytics.py  # Analytics panels
│   │   ├── components_system.py  # System monitoring panels
│   │   └── data_provider.py  # Real-time data providers
│   ├── reporting/       # Logging & scheduled performance reports
│   │   ├── __init__.py
│   │   ├── logger.py
│   │   └── reporter.py
│   ├── backtesting/     # Historical & paper-trading utilities
│   │   ├── __init__.py
│   │   └── backtester.py
│   └── tests/           # Unit & integration tests
│       ├── __init__.py
│       ├── test_ml_strategy.py
│       ├── test_execution_algorithms.py
│       ├── test_emotional_tracking.py
│       ├── test_elite_imports.py  # Elite system import validation
│       └── test_main_integration.py
│
├── requirements.txt     # Python dependencies
└── main.py              # Entrypoint – starts live or paper execution
```

## Quick Start

### Standard Setup
1. **Install dependencies**
   ```bash
   python -m venv .venv && source .venv/bin/activate  # Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```
2. **Configure MT5 credentials**
   Edit `trading_bot/config/config.yaml` and fill in your account **login**, **password**, and **server**. Ensure the MT5 terminal is installed and logged in.
3. **Run the bot**
   *Smoke-test only (connectivity):*
   ```bash
   python main.py --mode smoke --symbol EURUSD --timeframe M15 --bars 100
   ```
   *Paper-trading (simulated orders):*
   ```bash
   python main.py --mode paper --symbol EURUSD --timeframe M15 --bars 300
   ```
   *Paper-trading with ML strategy and Smart Order Router:*
   ```bash
   python main.py --mode paper --symbol EURUSD --timeframe M15 --bars 300 --use-ml --execution-algo smart
   ```
   *Paper-trading with emotional tracking:*
   ```bash
   python main.py --mode paper --symbol EURUSD --timeframe M15 --bars 300 --track-emotions
   ```
   *Full-featured trading with all capabilities:*
   ```bash
   python main.py --mode paper --symbol EURUSD --timeframe M15 --bars 300 --use-ml --execution-algo smart --track-emotions --use-sentiment
   ```
4. **Run unit tests**
   ```bash
   pytest -q trading_bot/tests
   ```

### Survival System Deployment

The Elite Trading Bot now includes a robust Survival Core system designed for long-term trading success with enhanced risk management and system monitoring.

1. **Automated Deployment**
   ```bash
   python deploy.py
   ```
   This script will:
   - Create necessary directories
   - Set up configuration files
   - Encrypt API keys
   - Run system checks
   - Create a backup
   - Run unit tests

2. **Start the Survival System**
   
   **Windows:**
   ```bash
   start_trading_bot.bat [options]
   ```
   
   **Linux/Mac:**
   ```bash
   ./start_trading_bot.sh [options]
   ```
   
   **Options:**
   - `--risk-level [conservative|moderate|aggressive]`: Set risk level
   - `--config [path]`: Specify config file path
   - `--emergency-mode`: Enable emergency mode with reduced risk
   - `--no-trading`: Run in analysis-only mode (no trading)

3. **Manual Start**
   ```bash
   python run_survival_system.py --config config/survival_config.yaml --risk-level moderate
   ```

4. **Deployment Verification**
   ```bash
   python -m trading_bot.tools.system_check
   ```

## Documentation
* Inline docstrings explain module APIs, expected inputs/outputs, and performance considerations.
* The `docs/` directory contains:
  * `prompt_comparison.md` - Detailed comparison of trading bot prompt designs
  * `elite_trading_bot_specification.md` - Advanced specification for an elite AI-powered MT5 trading bot
  * `deepseek_prompt_comparison.md` - Analysis comparing DeepSeek prompt with other prompts

## Command Line Options
The trading bot supports the following command line options:

* `--symbol`: Trading symbol (e.g., EURUSD)
* `--timeframe`: MT5 timeframe key (M1, M5, M15, H1, etc.)
* `--bars`: Number of historical bars to fetch for analysis
* `--mode`: Execution mode (smoke, paper, live)
* `--log-level`: Logging level (DEBUG, INFO, WARNING, ERROR)
* `--profile`: Enable performance profiling
* `--use-ml`: Enable ML-enhanced strategy engine
* `--execution-algo`: Select execution algorithm (default, twap, vwap, smart)
* `--track-emotions`: Enable emotional state tracking
* `--use-sentiment`: Enable sentiment analysis for trading decisions

## Elite Trading System

The Elite Trading System is an institutional-grade trading system that provides advanced market analysis, risk management, and trading capabilities. It consists of several specialized modules that can be used independently or together for comprehensive market analysis.

### Survival Core System

The Survival Core is a critical enhancement to the Elite Trading System, designed to ensure long-term trading success and system reliability. It implements the five pillars necessary for sustained profitability:

1. **Market Data & Analysis (Brain)**
   - Comprehensive market data processing
   - Multi-timeframe analysis
   - Signal generation with confidence scoring

2. **Execution (Hands)**
   - Smart order execution
   - Position management
   - Order type optimization

3. **Risk & Money Management (Shield)**
   - Dynamic position sizing
   - Portfolio-level risk controls
   - Drawdown protection
   - Correlation management

4. **Monitoring & Control (Eyes)**
   - Real-time system health monitoring
   - Component status tracking
   - Performance metrics
   - Automated notifications

5. **Security & Reliability (Foundation)**
   - Encrypted API key storage
   - Key rotation and integrity verification
   - Error handling and recovery
   - Backup and restore capabilities

The Survival Core provides robust error handling, automatic recovery from failures, and comprehensive monitoring to ensure the trading system remains operational and profitable in all market conditions.

### Using the Elite System

All Elite System components are now available for direct import from the root package:

```python
from trading_bot import (
    # Market Psychology
    EliteMarketPsychology, SentimentSource, MarketSentiment,
    # Regime Detection
    EliteRegimeDetector, MarketRegime,
    # Risk Management
    EliteRiskManager, RiskLevel,
    # Pattern Recognition
    ElitePatternRecognizer, PatternType,
    # Market Analysis
    EliteMarketAnalyzer, TimeFrame
)
```

### Elite System Components

#### Market Psychology Analysis
* Analyzes market sentiment from news, social media, and price action
* Detects smart money activity and crowd behavior patterns
* Provides contrarian trading signals based on sentiment extremes
* Tracks behavioral biases and their impact on market movements
* Maintains historical sentiment data for trend analysis

#### Market Regime Detection
* Classifies market conditions into distinct regimes (trending, mean-reverting, volatile)
* Uses advanced statistical methods including Hurst exponent and volatility forecasting
* Provides adaptive parameters for position sizing and stop placement
* Detects regime transitions for strategic adjustments
* Optimizes trading approach based on current market conditions

#### Institutional-Grade Risk Management
* Calculates optimal position sizes based on account balance and market conditions
* Determines appropriate stop loss levels using volatility-based methods
* Validates trade risk against portfolio risk limits
* Calculates portfolio Value-at-Risk (VaR) with multiple methodologies
* Generates comprehensive risk reports and monitors drawdowns

#### Proprietary Pattern Recognition
* Detects harmonic patterns (Gartley, Butterfly, Bat, etc.)
* Identifies candlestick patterns using TA-Lib integration
* Recognizes chart patterns (head and shoulders, double tops/bottoms)
* Detects institutional patterns (stop hunts, order blocks, fair value gaps)
* Analyzes order flow patterns for market depth insights

#### Multi-Timeframe Market Analysis
* Performs comprehensive market structure analysis across timeframes
* Identifies key support and resistance levels with strength ratings
* Detects trend direction and strength with multiple indicators
* Finds confluence zones where multiple timeframes align
* Provides actionable trading recommendations based on analysis

### Example Usage

See `examples/elite_system_demo.py` for a complete demonstration of the Elite Trading System components. This example shows how to:

* Generate synthetic market data for testing
* Analyze market psychology and sentiment
* Detect market regimes and adapt parameters
* Apply institutional risk management principles
* Recognize proprietary trading patterns
* Perform multi-timeframe market analysis
* Generate comprehensive trading recommendations

## AI/ML Capabilities

### ML Strategy Engine
* Extends traditional strategy engine with ML-powered capabilities
* Integrates multiple ML models for comprehensive market analysis
* Combines traditional technical analysis with ML predictions
* Resolves conflicting signals using strategy optimization
* Adjustable confidence thresholds for signal generation

### Predictive Models
* Deep learning price prediction models
* Pattern recognition for chart patterns and candlestick formations
* Anomaly detection for unusual market behavior
* Time series forecasting with confidence intervals
* Feature engineering for technical indicators

### Reinforcement Learning
* Strategy optimization through reinforcement learning
* Dynamic parameter tuning based on market conditions
* Market regime detection and adaptation
* Multi-agent simulation for strategy testing
* Reward function optimization for trading objectives

### Sentiment Analysis
* News sentiment analysis for market-moving events
* Social media sentiment tracking for retail trader sentiment
* Economic data impact assessment
* Market mood aggregation and trend correlation
* Integration with strategy signals for sentiment-aware trading

### Execution Optimization
* TWAP (Time-Weighted Average Price) algorithm for large order execution
* VWAP (Volume-Weighted Average Price) algorithm based on historical volume profiles
* Smart Order Router for optimal execution venue selection
* Execution analytics and performance tracking
* Composable execution algorithm wrappers

### Trader Psychology Monitoring
* Emotional state tracking during trading sessions
* Correlation analysis between emotions and trading performance
* Trading journal with emotional context
* Performance improvement recommendations based on psychological patterns
* Integration with performance analytics for comprehensive insights

## Performance Optimization

### Parallel Processing
* Multi-threading and multi-processing execution frameworks
* Task submission, mapping, and result retrieval
* Automatic workload optimization based on task type
* Resource usage tracking and performance metrics
* Parallel processing of market data across symbols and timeframes

### Memory Optimization
* Memory-efficient data structures for large datasets
* DataFrame optimization with dtype reduction
* Specialized optimizations for price series and OHLCV data
* Memory-efficient cache with weak references
* Ring buffer implementation for streaming data

### Algorithm Optimization
* Vectorized implementations of common trading algorithms
* Function optimization through memoization and caching
* Optimized versions of technical indicators (SMA, EMA, RSI, Bollinger Bands)
* Performance tracking for critical computational paths
* Bottleneck identification and optimization

### Performance Monitoring
* Function profiling with execution time tracking
* Resource usage monitoring (CPU, memory, disk, network)
* Bottleneck detection and analysis
* Performance snapshots and trend analysis
* Comprehensive performance reporting

### Example Usage

See `examples/performance_optimization_demo.py` and `examples/performance_optimization_integration.py` for demonstrations of the performance optimization features. These examples show how to:

* Use parallel processing for market analysis across multiple symbols
* Optimize memory usage for large datasets
* Apply algorithmic optimizations to critical computational paths
* Monitor and profile performance to identify bottlenecks
* Integrate all performance features in a real-world trading scenario

## Real-Time Dashboard

### Dashboard Server
* Web-based dashboard for real-time monitoring and analytics
* Modular component architecture for easy customization
* Configurable refresh intervals and display options
* Authentication and SSL support for secure access
* Event-driven data updates for real-time visualization

### Dashboard Components
* Market Panel: Price charts, indicators, and market data visualization
* Performance Panel: Equity curve, trade history, and performance metrics
* Risk Panel: Position sizing, risk allocation, and VaR analysis
* Signal Panel: Entry/exit signals and signal history tracking
* Analytics Panel: Liquidity zones, order flow, and microstructure analysis
* System Panel: Performance monitoring, resource usage, and system status

### Data Providers
* Real-time data updates from various sources
* Configurable update intervals for different data types
* Event-driven architecture for efficient updates
* Data caching for improved performance
* Support for multiple data sources and formats

### Example Usage

See `examples/real_time_dashboard_demo.py` for a demonstration of the real-time dashboard. This example shows how to:

* Create and configure a dashboard server
* Register dashboard components and layouts
* Provide real-time data updates
* Visualize trading performance and market analysis
* Monitor system resources and performance metrics

To run the dashboard demo:

```bash
python examples/real_time_dashboard_demo.py
```

This will start the dashboard server on http://localhost:8050, where you can interact with all the features.

## Testing
We use the `pytest` framework plus custom utilities in `trading_bot/tests` for strategy-level and module-level testing. Backtests require at least **5 years** of historical tick & bar data.

### Integration Tests
The project includes comprehensive integration tests for all major components:
* ML Strategy Engine tests verify proper signal generation and feature preparation
* Execution Algorithm tests validate TWAP, VWAP, and Smart Order Router functionality
* Emotional Tracking tests ensure proper correlation between emotions and performance
* Main Integration tests verify the complete execution flow with all components

## Contributing
Pull requests are welcome. Please open an issue first to discuss major changes.

## License
MIT
