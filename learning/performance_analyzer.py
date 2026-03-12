"""
Performance Analyzer - Analyzes trade outcomes and identifies patterns
"""

import numpy as np
from collections import deque
from typing import Dict, List
from datetime import datetime


class PerformanceAnalyzer:
    """Analyzes trade performance and identifies patterns."""
    
    def __init__(self, max_history: int = 100):
        self.trade_history = deque(maxlen=max_history)
        
    def add_trade(self, trade_data: Dict):
        """Add trade to history for analysis."""
        self.trade_history.append(trade_data)
    
    def analyze_rsi_effectiveness(self) -> Dict:
        """Analyze which RSI levels are most profitable."""
        if len(self.trade_history) < 10:
            return {'optimal_buy': 40.0, 'optimal_sell': 60.0, 'confidence': 0.0}
        
        recent = list(self.trade_history)[-20:]
        
        buy_trades = [t for t in recent if t.get('type') == 'BUY']
        winning_buy_rsi = [t['rsi'] for t in buy_trades if t['outcome'] == 'win']
        
        sell_trades = [t for t in recent if t.get('type') == 'SELL']
        winning_sell_rsi = [t['rsi'] for t in sell_trades if t['outcome'] == 'win']
        
        optimal_buy = np.mean(winning_buy_rsi) if winning_buy_rsi else 40.0
        optimal_sell = np.mean(winning_sell_rsi) if winning_sell_rsi else 60.0
        
        buy_win_rate = len(winning_buy_rsi) / len(buy_trades) if buy_trades else 0
        sell_win_rate = len(winning_sell_rsi) / len(sell_trades) if sell_trades else 0
        confidence = (buy_win_rate + sell_win_rate) / 2
        
        return {
            'optimal_buy': float(optimal_buy),
            'optimal_sell': float(optimal_sell),
            'confidence': float(confidence),
            'buy_win_rate': float(buy_win_rate),
            'sell_win_rate': float(sell_win_rate)
        }
    
    def analyze_stop_loss_effectiveness(self) -> float:
        """Determine optimal stop loss percentage."""
        if len(self.trade_history) < 10:
            return 0.005
        
        recent = list(self.trade_history)[-20:]
        losses = [abs(t['pnl']) for t in recent if t['outcome'] == 'loss']
        wins = [t['pnl'] for t in recent if t['outcome'] == 'win']
        
        avg_loss = np.mean(losses) if losses else 500
        avg_win = np.mean(wins) if wins else 1500
        
        if avg_win > 0:
            optimal_stop_pct = (avg_loss / avg_win) * 0.015
            return max(0.003, min(0.01, optimal_stop_pct))
        
        return 0.005
    
    def analyze_time_patterns(self) -> Dict:
        """Identify best times to trade."""
        if len(self.trade_history) < 20:
            return {'best_hours': [], 'worst_hours': []}
        
        hour_performance = {}
        for trade in self.trade_history:
            hour = trade.get('hour', 0)
            if hour not in hour_performance:
                hour_performance[hour] = {'wins': 0, 'losses': 0}
            
            if trade['outcome'] == 'win':
                hour_performance[hour]['wins'] += 1
            else:
                hour_performance[hour]['losses'] += 1
        
        hour_win_rates = {}
        for hour, perf in hour_performance.items():
            total = perf['wins'] + perf['losses']
            if total >= 3:
                hour_win_rates[hour] = perf['wins'] / total
        
        if hour_win_rates:
            sorted_hours = sorted(hour_win_rates.items(), key=lambda x: x[1], reverse=True)
            best_hours = [h for h, wr in sorted_hours[:3] if wr > 0.5]
            worst_hours = [h for h, wr in sorted_hours[-3:] if wr < 0.3]
        else:
            best_hours = []
            worst_hours = []
        
        return {'best_hours': best_hours, 'worst_hours': worst_hours}
    
    def get_win_rate(self) -> float:
        """Calculate current win rate."""
        if not self.trade_history:
            return 0.0
        wins = sum(1 for t in self.trade_history if t['outcome'] == 'win')
        return wins / len(self.trade_history)
    
    def get_average_pnl(self) -> float:
        """Calculate average P/L per trade."""
        if not self.trade_history:
            return 0.0
        return np.mean([t['pnl'] for t in self.trade_history])
    
    def analyze_macd_effectiveness(self) -> Dict:
        """Analyze which MACD levels are most profitable."""
        if len(self.trade_history) < 10:
            return {'optimal_buy': 0.0, 'optimal_sell': 0.0, 'confidence': 0.0}
        
        recent = list(self.trade_history)[-20:]
        
        buy_trades = [t for t in recent if t.get('type') == 'BUY' and 'macd' in t]
        winning_buy_macd = [t['macd'] for t in buy_trades if t['outcome'] == 'win']
        
        sell_trades = [t for t in recent if t.get('type') == 'SELL' and 'macd' in t]
        winning_sell_macd = [t['macd'] for t in sell_trades if t['outcome'] == 'win']
        
        optimal_buy = np.mean(winning_buy_macd) if winning_buy_macd else 0.0
        optimal_sell = np.mean(winning_sell_macd) if winning_sell_macd else 0.0
        
        buy_win_rate = len(winning_buy_macd) / len(buy_trades) if buy_trades else 0
        sell_win_rate = len(winning_sell_macd) / len(sell_trades) if sell_trades else 0
        confidence = (buy_win_rate + sell_win_rate) / 2
        
        return {
            'optimal_buy': float(optimal_buy),
            'optimal_sell': float(optimal_sell),
            'confidence': float(confidence)
        }
    
    def analyze_sma_effectiveness(self) -> Dict:
        """Analyze SMA crossover effectiveness."""
        if len(self.trade_history) < 10:
            return {'crossover_required': True, 'confidence': 0.0}
        
        recent = list(self.trade_history)[-20:]
        
        # Check if SMA crossover is necessary for winning trades
        trades_with_crossover = [t for t in recent if t.get('sma_20', 0) > t.get('sma_50', 0)]
        wins_with_crossover = [t for t in trades_with_crossover if t['outcome'] == 'win']
        
        trades_without_crossover = [t for t in recent if t.get('sma_20', 0) <= t.get('sma_50', 0)]
        wins_without_crossover = [t for t in trades_without_crossover if t['outcome'] == 'win']
        
        crossover_win_rate = len(wins_with_crossover) / len(trades_with_crossover) if trades_with_crossover else 0
        no_crossover_win_rate = len(wins_without_crossover) / len(trades_without_crossover) if trades_without_crossover else 0
        
        return {
            'crossover_required': crossover_win_rate > no_crossover_win_rate,
            'crossover_win_rate': float(crossover_win_rate),
            'no_crossover_win_rate': float(no_crossover_win_rate),
            'confidence': abs(crossover_win_rate - no_crossover_win_rate)
        }
    
    def analyze_volatility_impact(self) -> Dict:
        """Analyze how volatility affects trade success."""
        if len(self.trade_history) < 10:
            return {'optimal_volatility_range': (0.0, 100.0), 'confidence': 0.0}
        
        recent = list(self.trade_history)[-20:]
        
        winning_volatility = [t.get('volatility', 0) for t in recent if t['outcome'] == 'win']
        losing_volatility = [t.get('volatility', 0) for t in recent if t['outcome'] == 'loss']
        
        if winning_volatility:
            avg_win_vol = np.mean(winning_volatility)
            std_win_vol = np.std(winning_volatility)
            min_vol = max(0, avg_win_vol - std_win_vol)
            max_vol = avg_win_vol + std_win_vol
        else:
            min_vol, max_vol = 0.0, 100.0
        
        return {
            'optimal_volatility_range': (float(min_vol), float(max_vol)),
            'avg_winning_volatility': float(np.mean(winning_volatility)) if winning_volatility else 0.0,
            'avg_losing_volatility': float(np.mean(losing_volatility)) if losing_volatility else 0.0,
            'confidence': 0.5 if winning_volatility else 0.0
        }
    
    def analyze_symbol_performance(self) -> Dict:
        """Analyze which symbols perform best."""
        if len(self.trade_history) < 10:
            return {'best_symbols': [], 'worst_symbols': []}
        
        symbol_performance = {}
        for trade in self.trade_history:
            symbol = trade.get('symbol', 'UNKNOWN')
            if symbol not in symbol_performance:
                symbol_performance[symbol] = {'wins': 0, 'losses': 0, 'total_pnl': 0}
            
            if trade['outcome'] == 'win':
                symbol_performance[symbol]['wins'] += 1
            else:
                symbol_performance[symbol]['losses'] += 1
            symbol_performance[symbol]['total_pnl'] += trade.get('pnl', 0)
        
        # Calculate win rates
        symbol_win_rates = {}
        for symbol, perf in symbol_performance.items():
            total = perf['wins'] + perf['losses']
            if total >= 3:
                symbol_win_rates[symbol] = {
                    'win_rate': perf['wins'] / total,
                    'total_pnl': perf['total_pnl'],
                    'trades': total
                }
        
        if symbol_win_rates:
            sorted_symbols = sorted(symbol_win_rates.items(), key=lambda x: x[1]['win_rate'], reverse=True)
            best_symbols = [s for s, data in sorted_symbols if data['win_rate'] > 0.6]
            worst_symbols = [s for s, data in sorted_symbols if data['win_rate'] < 0.4]
        else:
            best_symbols = []
            worst_symbols = []
        
        return {
            'best_symbols': best_symbols,
            'worst_symbols': worst_symbols,
            'symbol_performance': symbol_performance
        }
    
    def analyze_indicator_weights(self) -> Dict:
        """Determine which indicators are most predictive."""
        if len(self.trade_history) < 20:
            return {'rsi_weight': 0.33, 'macd_weight': 0.33, 'sma_weight': 0.34}
        
        recent = list(self.trade_history)[-30:]
        
        # Analyze correlation between each indicator and success
        rsi_correct = 0
        macd_correct = 0
        sma_correct = 0
        total = 0
        
        for trade in recent:
            if trade['outcome'] == 'win':
                total += 1
                # RSI predicted correctly if oversold/overbought aligned with trade type
                if trade['type'] == 'BUY' and trade.get('rsi', 50) < 45:
                    rsi_correct += 1
                elif trade['type'] == 'SELL' and trade.get('rsi', 50) > 55:
                    rsi_correct += 1
                
                # MACD predicted correctly if sign aligned with trade type
                if trade['type'] == 'BUY' and trade.get('macd', 0) > 0:
                    macd_correct += 1
                elif trade['type'] == 'SELL' and trade.get('macd', 0) < 0:
                    macd_correct += 1
                
                # SMA predicted correctly if crossover aligned with trade type
                sma_20 = trade.get('sma_20', 0)
                sma_50 = trade.get('sma_50', 0)
                if trade['type'] == 'BUY' and sma_20 > sma_50:
                    sma_correct += 1
                elif trade['type'] == 'SELL' and sma_20 < sma_50:
                    sma_correct += 1
        
        if total > 0:
            rsi_accuracy = rsi_correct / total
            macd_accuracy = macd_correct / total
            sma_accuracy = sma_correct / total
            
            # Normalize to weights that sum to 1
            total_accuracy = rsi_accuracy + macd_accuracy + sma_accuracy
            if total_accuracy > 0:
                rsi_weight = rsi_accuracy / total_accuracy
                macd_weight = macd_accuracy / total_accuracy
                sma_weight = sma_accuracy / total_accuracy
            else:
                rsi_weight = macd_weight = sma_weight = 0.33
        else:
            rsi_weight = macd_weight = sma_weight = 0.33
        
        return {
            'rsi_weight': float(rsi_weight),
            'macd_weight': float(macd_weight),
            'sma_weight': float(sma_weight),
            'rsi_accuracy': float(rsi_correct / total) if total > 0 else 0.0,
            'macd_accuracy': float(macd_correct / total) if total > 0 else 0.0,
            'sma_accuracy': float(sma_correct / total) if total > 0 else 0.0
        }
