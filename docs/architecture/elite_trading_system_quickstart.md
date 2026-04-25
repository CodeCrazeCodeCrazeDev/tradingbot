# Elite Trading System Quick Start Guide

This guide will help you quickly set up and start using the Elite Trading System.

## Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/trading-bot.git
   cd trading-bot
   ```

2. **Install dependencies**
   ```bash
   pip install -e .
   ```

3. **Install optional quantum computing dependencies** (recommended)
   ```bash
   pip install qiskit qiskit-aer
   ```

## Basic Usage

### 1. Configure the System

Create or modify `elite_config.yaml` in the project root:

```yaml
general:
  debug_mode: true
  log_level: "INFO"
  save_signals: true

visualization:
  default_theme: "dark"
  chart_style: "professional"
  show_indicators: ["RSI", "MACD"]
  show_overlays: ["EMA", "LIQUIDITY_ZONES"]

quantum:
  enabled: true
  simulator_mode: true

blockchain:
  enabled: true
  storage_path: "blockchain_data"

ai_ml:
  use_online_learning: true
  use_reinforcement_learning: true
  
risk:
  max_position_size: 0.02
  max_drawdown: 0.05
  use_kelly_criterion: true
```

### 2. Run Market Analysis

Create a Python script (`analyze_market.py`):

```python
import asyncio
import pandas as pd
from trading_bot.elite_system.elite_system import EliteSystem
from trading_bot.elite_system.config import EliteConfig

async def main():
    # Load configuration
    config = EliteConfig()
    
    # Initialize Elite System
    elite_system = EliteSystem(config)
    
    # Load market data (replace with your data source)
    market_data = pd.read_csv("your_market_data.csv", index_col=0, parse_dates=True)
    
    # Analyze market
    signal = await elite_system.analyze_market(
        market_data=market_data,
        symbol="EURUSD",
        timeframe="1H"
    )
    
    # Print signal details
    print(f"Direction: {signal.direction.value}")
    print(f"Strength: {signal.strength:.2f}")
    print(f"Confidence: {signal.confidence:.2f}")
    print(f"Recommended Action: {signal.action}")

if __name__ == "__main__":
    asyncio.run(main())
```

Run the script:
```bash
python analyze_market.py
```

### 3. Visualize Market Analysis

Create a visualization script (`visualize_market.py`):

```python
import asyncio
import pandas as pd
from trading_bot.elite_system.elite_system import EliteSystem
from trading_bot.elite_system.config import EliteConfig
from trading_bot.elite_system.visualization import EliteVisualizer, ChartType

async def main():
    # Load configuration
    config = EliteConfig()
    
    # Initialize Elite System and Visualizer
    elite_system = EliteSystem(config)
    visualizer = EliteVisualizer(config.visualization)
    
    # Load market data
    market_data = pd.read_csv("your_market_data.csv", index_col=0, parse_dates=True)
    
    # Analyze market
    signal = await elite_system.analyze_market(
        market_data=market_data,
        symbol="EURUSD",
        timeframe="1H"
    )
    
    # Create and show market chart
    chart = visualizer.create_market_chart(
        market_data=market_data,
        signals=[signal],
        chart_type=ChartType.CANDLESTICK,
        title="Market Analysis"
    )
    
    # Save chart to HTML file
    visualizer.save_chart(chart, "market_analysis.html")
    print("Chart saved to market_analysis.html")
    
    # Show chart in browser
    visualizer.show_chart(chart)

if __name__ == "__main__":
    asyncio.run(main())
```

Run the script:
```bash
python visualize_market.py
```

### 4. Launch Interactive Dashboard

Create a dashboard script (`run_dashboard.py`):

```python
from trading_bot.examples.elite_system_simple_dashboard import EliteSimpleDashboard

def main():
    # Initialize dashboard
    dashboard = EliteSimpleDashboard()
    
    # Run dashboard
    dashboard.run(port=8050)
    
    print("Dashboard running at http://localhost:8050")

if __name__ == "__main__":
    main()
```

Run the script:
```bash
python run_dashboard.py
```

Then open your browser to http://localhost:8050

### 5. Use the HTML Visualization

For a standalone visualization without running a server:

1. Open `examples/elite_system_visualization.html` in your browser
2. Use the dropdown menus to select different symbols and timeframes
3. Toggle indicators and liquidity zones using the buttons

## Next Steps

1. **Explore advanced features**:
   - Quantum portfolio optimization
   - Blockchain validation
   - Performance benchmarking

2. **Customize the system**:
   - Modify configuration parameters
   - Extend with your own strategies
   - Integrate with your trading platform

3. **Read the documentation**:
   - See `docs/elite_trading_system_documentation.md` for complete documentation
   - Check `examples/` directory for more example scripts

## Troubleshooting

- **Issue**: "No module named 'trading_bot'"
  **Solution**: Install the package in development mode: `pip install -e .`

- **Issue**: Visualization not working
  **Solution**: Ensure you have installed all dependencies: `pip install plotly dash dash-bootstrap-components`

- **Issue**: Dashboard not starting
  **Solution**: Check if port 8050 is already in use. Change the port in `dashboard.run(port=8051)`

For more help, see the full documentation or open an issue on GitHub.
