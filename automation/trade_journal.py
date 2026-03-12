"""
Trade Journal Automation ($0 Budget)
Auto-document trade decisions and outcomes
PDF report generation
"""

import json
import os
from typing import Dict, List
from dataclasses import dataclass, asdict
from datetime import datetime
import numpy as np


@dataclass
class TradeEntry:
    """Trade journal entry"""
    trade_id: str
    timestamp: datetime
    symbol: str
    direction: str  # 'long' or 'short'
    entry_price: float
    exit_price: float
    quantity: float
    pnl: float
    return_pct: float
    duration_hours: float
    strategy: str
    reasoning: str
    market_conditions: Dict
    emotions: str
    lessons_learned: str
    tags: List[str]


class TradeJournal:
    """Automated trade journal"""
    
    def __init__(self, journal_dir: str = './trade_journal'):
        self.journal_dir = journal_dir
        self.entries: List[TradeEntry] = []
        
        # Create directory
        os.makedirs(journal_dir, exist_ok=True)
        
        # Load existing entries
        self._load_entries()
        
    def add_trade(
        self,
        trade_id: str,
        symbol: str,
        direction: str,
        entry_price: float,
        exit_price: float,
        quantity: float,
        strategy: str,
        reasoning: str,
        market_conditions: Dict,
        emotions: str = '',
        lessons_learned: str = '',
        tags: List[str] = None,
        entry_time: datetime = None,
        exit_time: datetime = None
    ) -> TradeEntry:
        """Add trade to journal"""
        
        # Calculate metrics
        if direction == 'long':
            pnl = (exit_price - entry_price) * quantity
            return_pct = (exit_price - entry_price) / entry_price
        else:  # short
            pnl = (entry_price - exit_price) * quantity
            return_pct = (entry_price - exit_price) / entry_price
        
        # Calculate duration
        if entry_time and exit_time:
            duration_hours = (exit_time - entry_time).total_seconds() / 3600
        else:
            duration_hours = 0
        
        # Create entry
        entry = TradeEntry(
            trade_id=trade_id,
            timestamp=exit_time or datetime.now(),
            symbol=symbol,
            direction=direction,
            entry_price=entry_price,
            exit_price=exit_price,
            quantity=quantity,
            pnl=pnl,
            return_pct=return_pct,
            duration_hours=duration_hours,
            strategy=strategy,
            reasoning=reasoning,
            market_conditions=market_conditions,
            emotions=emotions,
            lessons_learned=lessons_learned,
            tags=tags or []
        )
        
        # Add to journal
        self.entries.append(entry)
        
        # Save
        self._save_entry(entry)
        
        return entry
    
    def get_statistics(self) -> Dict:
        """Calculate journal statistics"""
        
        if not self.entries:
            return {}
        
        # Basic stats
        total_trades = len(self.entries)
        winning_trades = [e for e in self.entries if e.pnl > 0]
        losing_trades = [e for e in self.entries if e.pnl < 0]
        
        win_rate = len(winning_trades) / total_trades
        
        # P&L stats
        total_pnl = sum(e.pnl for e in self.entries)
        avg_win = np.mean([e.pnl for e in winning_trades]) if winning_trades else 0
        avg_loss = np.mean([e.pnl for e in losing_trades]) if losing_trades else 0
        
        # Profit factor
        gross_profit = sum(e.pnl for e in winning_trades)
        gross_loss = abs(sum(e.pnl for e in losing_trades))
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else 0
        
        # Return stats
        returns = [e.return_pct for e in self.entries]
        avg_return = np.mean(returns)
        sharpe_ratio = np.mean(returns) / np.std(returns) * np.sqrt(252) if np.std(returns) > 0 else 0
        
        # Duration stats
        avg_duration = np.mean([e.duration_hours for e in self.entries])
        
        # Strategy breakdown
        strategies = {}
        for entry in self.entries:
            if entry.strategy not in strategies:
                strategies[entry.strategy] = {'trades': 0, 'pnl': 0, 'wins': 0}
            strategies[entry.strategy]['trades'] += 1
            strategies[entry.strategy]['pnl'] += entry.pnl
            if entry.pnl > 0:
                strategies[entry.strategy]['wins'] += 1
        
        # Calculate win rate per strategy
        for strategy in strategies:
            strategies[strategy]['win_rate'] = strategies[strategy]['wins'] / strategies[strategy]['trades']
        
        return {
            'total_trades': total_trades,
            'winning_trades': len(winning_trades),
            'losing_trades': len(losing_trades),
            'win_rate': win_rate,
            'total_pnl': total_pnl,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'profit_factor': profit_factor,
            'avg_return': avg_return,
            'sharpe_ratio': sharpe_ratio,
            'avg_duration_hours': avg_duration,
            'strategies': strategies
        }
    
    def generate_html_report(self, output_file: str = None) -> str:
        """Generate HTML report (free)"""
        
        if output_file is None:
            output_file = os.path.join(self.journal_dir, f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html")
        
        stats = self.get_statistics()
        
        # Recent trades
        recent_trades = self.entries[-20:] if len(self.entries) > 20 else self.entries
        
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Trade Journal Report</title>
    <meta charset="UTF-8">
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            color: #333;
        }}
        
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 15px;
            padding: 40px;
            box-shadow: 0 10px 50px rgba(0,0,0,0.3);
        }}
        
        h1 {{
            color: #667eea;
            text-align: center;
            margin-bottom: 10px;
            font-size: 2.5em;
        }}
        
        .subtitle {{
            text-align: center;
            color: #666;
            margin-bottom: 30px;
        }}
        
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 40px;
        }}
        
        .stat-card {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 10px;
            text-align: center;
        }}
        
        .stat-label {{
            font-size: 0.9em;
            opacity: 0.9;
            margin-bottom: 10px;
        }}
        
        .stat-value {{
            font-size: 2em;
            font-weight: bold;
        }}
        
        .trades-table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }}
        
        .trades-table th {{
            background: #667eea;
            color: white;
            padding: 12px;
            text-align: left;
            font-weight: 600;
        }}
        
        .trades-table td {{
            padding: 12px;
            border-bottom: 1px solid #eee;
        }}
        
        .trades-table tr:hover {{
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
        
        .section {{
            margin: 40px 0;
        }}
        
        .section h2 {{
            color: #667eea;
            margin-bottom: 20px;
            border-bottom: 2px solid #667eea;
            padding-bottom: 10px;
        }}
        
        .strategy-card {{
            background: #f8f9fa;
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 15px;
        }}
        
        .strategy-name {{
            font-size: 1.2em;
            font-weight: bold;
            color: #667eea;
            margin-bottom: 10px;
        }}
        
        .strategy-stats {{
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 10px;
        }}
        
        .footer {{
            text-align: center;
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #eee;
            color: #666;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📊 Trade Journal Report</h1>
        <div class="subtitle">Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</div>
        
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-label">Total Trades</div>
                <div class="stat-value">{stats.get('total_trades', 0)}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Win Rate</div>
                <div class="stat-value">{stats.get('win_rate', 0):.1%}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Total P&L</div>
                <div class="stat-value">${stats.get('total_pnl', 0):,.0f}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Profit Factor</div>
                <div class="stat-value">{stats.get('profit_factor', 0):.2f}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Avg Return</div>
                <div class="stat-value">{stats.get('avg_return', 0):.2%}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Sharpe Ratio</div>
                <div class="stat-value">{stats.get('sharpe_ratio', 0):.2f}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Avg Win</div>
                <div class="stat-value">${stats.get('avg_win', 0):,.0f}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Avg Loss</div>
                <div class="stat-value">${stats.get('avg_loss', 0):,.0f}</div>
            </div>
        </div>
        
        <div class="section">
            <h2>Strategy Performance</h2>
            {''.join([f'''
            <div class="strategy-card">
                <div class="strategy-name">{strategy}</div>
                <div class="strategy-stats">
                    <div>Trades: <strong>{data['trades']}</strong></div>
                    <div>Win Rate: <strong>{data['win_rate']:.1%}</strong></div>
                    <div>P&L: <strong class="{'positive' if data['pnl'] > 0 else 'negative'}">${data['pnl']:,.0f}</strong></div>
                    <div>Wins: <strong>{data['wins']}</strong></div>
                </div>
            </div>
            ''' for strategy, data in stats.get('strategies', {}).items()])}
        </div>
        
        <div class="section">
            <h2>Recent Trades</h2>
            <table class="trades-table">
                <thead>
                    <tr>
                        <th>Date</th>
                        <th>Symbol</th>
                        <th>Direction</th>
                        <th>Entry</th>
                        <th>Exit</th>
                        <th>P&L</th>
                        <th>Return</th>
                        <th>Strategy</th>
                    </tr>
                </thead>
                <tbody>
                    {''.join([f'''
                    <tr>
                        <td>{trade.timestamp.strftime('%Y-%m-%d %H:%M')}</td>
                        <td><strong>{trade.symbol}</strong></td>
                        <td>{trade.direction.upper()}</td>
                        <td>${trade.entry_price:.2f}</td>
                        <td>${trade.exit_price:.2f}</td>
                        <td class="{'positive' if trade.pnl > 0 else 'negative'}">${trade.pnl:,.2f}</td>
                        <td class="{'positive' if trade.return_pct > 0 else 'negative'}">{trade.return_pct:.2%}</td>
                        <td>{trade.strategy}</td>
                    </tr>
                    ''' for trade in reversed(recent_trades)])}
                </tbody>
            </table>
        </div>
        
        <div class="footer">
            <p>Trade Journal - Automated Documentation System</p>
            <p>Cost: $0 (FREE)</p>
        </div>
    </div>
</body>
</html>
"""
        
        # Write to file
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        return output_file
    
    def _save_entry(self, entry: TradeEntry):
        """Save entry to JSON file"""
        
        filename = f"trade_{entry.trade_id}.json"
        filepath = os.path.join(self.journal_dir, filename)
        
        # Convert to dict
        entry_dict = asdict(entry)
        entry_dict['timestamp'] = entry.timestamp.isoformat()
        
        with open(filepath, 'w') as f:
            json.dump(entry_dict, f, indent=2)
    
    def _load_entries(self):
        """Load existing entries"""
        
        if not os.path.exists(self.journal_dir):
            return
        
        for filename in os.listdir(self.journal_dir):
            if filename.startswith('trade_') and filename.endswith('.json'):
                filepath = os.path.join(self.journal_dir, filename)
                
                try:
                    with open(filepath, 'r') as f:
                        data = json.load(f)
                    
                    # Convert timestamp
                    data['timestamp'] = datetime.fromisoformat(data['timestamp'])
                    
                    # Create entry
                    entry = TradeEntry(**data)
                    self.entries.append(entry)
                except Exception as e:
                    print(f"Error loading {filename}: {e}")


# Example usage
if __name__ == '__main__':
    # Initialize journal
    journal = TradeJournal()
    
    # Add sample trades
    trades = [
        {
            'trade_id': 'T001',
            'symbol': 'BTCUSD',
            'direction': 'long',
            'entry_price': 45000,
            'exit_price': 48000,
            'quantity': 0.5,
            'strategy': 'Momentum',
            'reasoning': 'Strong bullish momentum, RSI oversold',
            'market_conditions': {'trend': 'bullish', 'volatility': 'medium'},
            'emotions': 'Confident',
            'lessons_learned': 'Entry timing was good',
            'tags': ['crypto', 'momentum']
        },
        {
            'trade_id': 'T002',
            'symbol': 'ETHUSD',
            'direction': 'long',
            'entry_price': 2500,
            'exit_price': 2400,
            'quantity': 2,
            'strategy': 'Breakout',
            'reasoning': 'False breakout above resistance',
            'market_conditions': {'trend': 'neutral', 'volatility': 'high'},
            'emotions': 'Frustrated',
            'lessons_learned': 'Wait for confirmation on breakouts',
            'tags': ['crypto', 'breakout', 'loss']
        }
    ]
    
    for trade_data in trades:
        journal.add_trade(**trade_data)
    
    # Get statistics
    stats = journal.get_statistics()
    
    print("Trade Journal Statistics:")
    print("="*60)
    print(f"Total Trades: {stats['total_trades']}")
    print(f"Win Rate: {stats['win_rate']:.1%}")
    print(f"Total P&L: ${stats['total_pnl']:,.2f}")
    print(f"Profit Factor: {stats['profit_factor']:.2f}")
    print(f"Sharpe Ratio: {stats['sharpe_ratio']:.2f}")
    
    # Generate report
    report_file = journal.generate_html_report()
    print(f"\n✓ Report generated: {report_file}")
    print(f"✓ Open in browser to view")
    print(f"✓ Cost: $0 (FREE)")
