"""
Portfolio Health Dashboard ($0 Budget)
Web-based dashboard using Flask + Plotly Dash
Real-time performance visualization
"""

import json
from datetime import datetime, timedelta
from typing import Dict, List
import numpy as np


# Free dashboard using simple HTML + JavaScript (no Flask needed for basic version)
class PortfolioHealthDashboard:
    """Portfolio health dashboard generator"""
    
    def __init__(self):
        self.portfolio_data: Dict = {}
        self.performance_history: List[Dict] = []
        
    def update_portfolio(self, portfolio: Dict):
        """Update portfolio data"""
        self.portfolio_data = portfolio
        self.performance_history.append({
            'timestamp': datetime.now(),
            'value': portfolio.get('total_value', 0),
            'return': portfolio.get('total_return', 0)
        })
        
    def calculate_health_score(self) -> Dict:
        """Calculate portfolio health score"""
        
        if not self.portfolio_data:
            return {'score': 0, 'grade': 'N/A'}
        
        # Factors
        factors = {}
        
        # 1. Diversification (0-25 points)
        num_positions = len(self.portfolio_data.get('positions', []))
        factors['diversification'] = min(num_positions * 5, 25)
        
        # 2. Performance (0-25 points)
        total_return = self.portfolio_data.get('total_return', 0)
        factors['performance'] = min(max(total_return * 100, 0), 25)
        
        # 3. Risk Management (0-25 points)
        sharpe = self.portfolio_data.get('sharpe_ratio', 0)
        factors['risk_management'] = min(max(sharpe * 10, 0), 25)
        
        # 4. Consistency (0-25 points)
        if len(self.performance_history) >= 10:
            returns = [h['return'] for h in self.performance_history[-10:]]
            consistency = 1 - np.std(returns)
            factors['consistency'] = min(max(consistency * 25, 0), 25)
        else:
            factors['consistency'] = 12.5  # Neutral
        
        # Total score
        total_score = sum(factors.values())
        
        # Grade
        if total_score >= 90:
            grade = 'A+'
        elif total_score >= 80:
            grade = 'A'
        elif total_score >= 70:
            grade = 'B'
        elif total_score >= 60:
            grade = 'C'
        else:
            grade = 'D'
        
        return {
            'score': total_score,
            'grade': grade,
            'factors': factors,
            'timestamp': datetime.now()
        }
    
    def generate_html_dashboard(self, output_file: str = 'portfolio_dashboard.html'):
        """Generate HTML dashboard (free, no server needed)"""
        
        health = self.calculate_health_score()
        
        # Prepare data for charts
        if self.performance_history:
            timestamps = [h['timestamp'].strftime('%H:%M:%S') for h in self.performance_history[-50:]]
            values = [h['value'] for h in self.performance_history[-50:]]
            returns = [h['return'] * 100 for h in self.performance_history[-50:]]
        else:
            timestamps = []
            values = []
            returns = []
        
        positions = self.portfolio_data.get('positions', [])
        
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Portfolio Health Dashboard</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: #333;
            padding: 20px;
        }}
        
        .container {{
            max-width: 1400px;
            margin: 0 auto;
        }}
        
        .header {{
            text-align: center;
            color: white;
            margin-bottom: 30px;
        }}
        
        .header h1 {{
            font-size: 2.5em;
            margin-bottom: 10px;
        }}
        
        .dashboard {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 20px;
        }}
        
        .card {{
            background: white;
            border-radius: 15px;
            padding: 25px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            transition: transform 0.3s ease;
        }}
        
        .card:hover {{
            transform: translateY(-5px);
        }}
        
        .card h2 {{
            color: #667eea;
            margin-bottom: 15px;
            font-size: 1.3em;
        }}
        
        .metric {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin: 10px 0;
            padding: 10px;
            background: #f8f9fa;
            border-radius: 8px;
        }}
        
        .metric-label {{
            font-weight: 600;
            color: #666;
        }}
        
        .metric-value {{
            font-size: 1.2em;
            font-weight: bold;
            color: #667eea;
        }}
        
        .health-score {{
            text-align: center;
            padding: 30px;
        }}
        
        .score-circle {{
            width: 150px;
            height: 150px;
            border-radius: 50%;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            margin: 0 auto 20px;
            color: white;
            box-shadow: 0 5px 20px rgba(102, 126, 234, 0.4);
        }}
        
        .score-number {{
            font-size: 3em;
            font-weight: bold;
        }}
        
        .score-grade {{
            font-size: 1.5em;
            margin-top: 5px;
        }}
        
        .chart-container {{
            background: white;
            border-radius: 15px;
            padding: 25px;
            margin-bottom: 20px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }}
        
        .positions-table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 15px;
        }}
        
        .positions-table th {{
            background: #667eea;
            color: white;
            padding: 12px;
            text-align: left;
        }}
        
        .positions-table td {{
            padding: 12px;
            border-bottom: 1px solid #eee;
        }}
        
        .positions-table tr:hover {{
            background: #f8f9fa;
        }}
        
        .positive {{
            color: #28a745;
            font-weight: bold;
        }}
        
        .negative {{
            color: #dc3545;
            font-weight: bold;
        }}
        
        .timestamp {{
            text-align: center;
            color: white;
            margin-top: 20px;
            font-size: 0.9em;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 Portfolio Health Dashboard</h1>
            <p>Real-Time Performance Monitoring (FREE)</p>
        </div>
        
        <div class="dashboard">
            <!-- Health Score Card -->
            <div class="card health-score">
                <h2>Health Score</h2>
                <div class="score-circle">
                    <div class="score-number">{health['score']:.0f}</div>
                    <div class="score-grade">{health['grade']}</div>
                </div>
                <div class="metric">
                    <span class="metric-label">Diversification</span>
                    <span class="metric-value">{health['factors']['diversification']:.0f}/25</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Performance</span>
                    <span class="metric-value">{health['factors']['performance']:.0f}/25</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Risk Management</span>
                    <span class="metric-value">{health['factors']['risk_management']:.0f}/25</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Consistency</span>
                    <span class="metric-value">{health['factors']['consistency']:.0f}/25</span>
                </div>
            </div>
            
            <!-- Portfolio Summary Card -->
            <div class="card">
                <h2>Portfolio Summary</h2>
                <div class="metric">
                    <span class="metric-label">Total Value</span>
                    <span class="metric-value">${self.portfolio_data.get('total_value', 0):,.2f}</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Total Return</span>
                    <span class="metric-value {'positive' if self.portfolio_data.get('total_return', 0) > 0 else 'negative'}">
                        {self.portfolio_data.get('total_return', 0):.2%}
                    </span>
                </div>
                <div class="metric">
                    <span class="metric-label">Sharpe Ratio</span>
                    <span class="metric-value">{self.portfolio_data.get('sharpe_ratio', 0):.2f}</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Max Drawdown</span>
                    <span class="metric-value negative">{self.portfolio_data.get('max_drawdown', 0):.2%}</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Positions</span>
                    <span class="metric-value">{len(positions)}</span>
                </div>
            </div>
            
            <!-- Risk Metrics Card -->
            <div class="card">
                <h2>Risk Metrics</h2>
                <div class="metric">
                    <span class="metric-label">Volatility</span>
                    <span class="metric-value">{self.portfolio_data.get('volatility', 0):.2%}</span>
                </div>
                <div class="metric">
                    <span class="metric-label">VaR (95%)</span>
                    <span class="metric-value negative">{self.portfolio_data.get('var_95', 0):.2%}</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Beta</span>
                    <span class="metric-value">{self.portfolio_data.get('beta', 1.0):.2f}</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Win Rate</span>
                    <span class="metric-value">{self.portfolio_data.get('win_rate', 0):.1%}</span>
                </div>
            </div>
        </div>
        
        <!-- Portfolio Value Chart -->
        <div class="chart-container">
            <h2>Portfolio Value Over Time</h2>
            <div id="valueChart"></div>
        </div>
        
        <!-- Returns Chart -->
        <div class="chart-container">
            <h2>Returns Over Time</h2>
            <div id="returnsChart"></div>
        </div>
        
        <!-- Positions Table -->
        <div class="chart-container">
            <h2>Current Positions</h2>
            <table class="positions-table">
                <thead>
                    <tr>
                        <th>Symbol</th>
                        <th>Quantity</th>
                        <th>Entry Price</th>
                        <th>Current Price</th>
                        <th>Value</th>
                        <th>P&L</th>
                        <th>Return</th>
                    </tr>
                </thead>
                <tbody>
                    {''.join([f'''
                    <tr>
                        <td><strong>{pos.get('symbol', 'N/A')}</strong></td>
                        <td>{pos.get('quantity', 0):.4f}</td>
                        <td>${pos.get('entry_price', 0):.2f}</td>
                        <td>${pos.get('current_price', 0):.2f}</td>
                        <td>${pos.get('value', 0):,.2f}</td>
                        <td class="{'positive' if pos.get('pnl', 0) > 0 else 'negative'}">${pos.get('pnl', 0):,.2f}</td>
                        <td class="{'positive' if pos.get('return', 0) > 0 else 'negative'}">{pos.get('return', 0):.2%}</td>
                    </tr>
                    ''' for pos in positions])}
                </tbody>
            </table>
        </div>
        
        <div class="timestamp">
            Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Cost: $0 (FREE)
        </div>
    </div>
    
    <script>
        // Portfolio Value Chart
        var valueTrace = {{
            x: {json.dumps(timestamps)},
            y: {json.dumps(values)},
            type: 'scatter',
            mode: 'lines+markers',
            name: 'Portfolio Value',
            line: {{color: '#667eea', width: 3}},
            marker: {{size: 6}}
        }};
        
        var valueLayout = {{
            xaxis: {{title: 'Time'}},
            yaxis: {{title: 'Value ($)'}},
            hovermode: 'closest',
            showlegend: false
        }};
        
        Plotly.newPlot('valueChart', [valueTrace], valueLayout, {{responsive: true}});
        
        // Returns Chart
        var returnsTrace = {{
            x: {json.dumps(timestamps)},
            y: {json.dumps(returns)},
            type: 'bar',
            name: 'Returns',
            marker: {{
                color: {json.dumps(returns)},
                colorscale: [
                    [0, '#dc3545'],
                    [0.5, '#ffc107'],
                    [1, '#28a745']
                ],
                cmin: -5,
                cmax: 5
            }}
        }};
        
        var returnsLayout = {{
            xaxis: {{title: 'Time'}},
            yaxis: {{title: 'Return (%)'}},
            hovermode: 'closest',
            showlegend: false
        }};
        
        Plotly.newPlot('returnsChart', [returnsTrace], returnsLayout, {{responsive: true}});
        
        // Auto-refresh every 30 seconds
        setTimeout(function() {{
            location.reload();
        }}, 30000);
    </script>
</body>
</html>
"""
        
        # Write to file
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        return output_file


# Example usage
if __name__ == '__main__':
    # Initialize dashboard
    dashboard = PortfolioHealthDashboard()
    
    # Sample portfolio data
    portfolio = {
        'total_value': 125000,
        'total_return': 0.25,
        'sharpe_ratio': 1.8,
        'max_drawdown': -0.12,
        'volatility': 0.18,
        'var_95': -0.03,
        'beta': 1.2,
        'win_rate': 0.65,
        'positions': [
            {
                'symbol': 'BTC',
                'quantity': 2.5,
                'entry_price': 40000,
                'current_price': 50000,
                'value': 125000,
                'pnl': 25000,
                'return': 0.25
            },
            {
                'symbol': 'ETH',
                'quantity': 50,
                'entry_price': 2000,
                'current_price': 2500,
                'value': 125000,
                'pnl': 25000,
                'return': 0.25
            }
        ]
    }
    
    # Update portfolio
    dashboard.update_portfolio(portfolio)
    
    # Simulate some history
    for i in range(20):
        portfolio['total_value'] = 100000 + i * 1000 + np.random.randn() * 500
        portfolio['total_return'] = (portfolio['total_value'] - 100000) / 100000
        dashboard.update_portfolio(portfolio)
    
    # Generate dashboard
    output_file = dashboard.generate_html_dashboard()
    
    print(f"✓ Dashboard generated: {output_file}")
    print(f"✓ Open in browser to view")
    print(f"✓ Auto-refreshes every 30 seconds")
    print(f"✓ Cost: $0 (FREE)")
