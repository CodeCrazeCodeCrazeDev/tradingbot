"""
Feedback Loop System
Collects production data to inform system improvements
"""

import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
import sqlite3


@dataclass
class TradePerformance:
    """Trade performance metrics."""
    trade_id: str
    symbol: str
    entry_time: datetime
    exit_time: Optional[datetime]
    entry_price: float
    exit_price: Optional[float]
    pnl: float
    pnl_percent: float
    duration_seconds: Optional[int]
    strategy: str
    signal_confidence: float
    market_regime: str


@dataclass
class SignalQuality:
    """Signal quality metrics."""
    signal_id: str
    timestamp: datetime
    symbol: str
    direction: str
    predicted_move: float
    actual_move: float
    prediction_error: float
    confidence: float
    accuracy: float
    time_to_result: int  # seconds


class FeedbackAnalyzer:
    """Analyzes trading performance and generates improvement recommendations."""
    
    def __init__(self, data_dir: str = "feedback_data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        self.db_path = self.data_dir / "feedback.db"
        self._init_database()
    
    def _init_database(self):
        """Initialize SQLite database for feedback storage."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS trade_performance (
                    trade_id TEXT PRIMARY KEY,
                    symbol TEXT,
                    entry_time TEXT,
                    exit_time TEXT,
                    entry_price REAL,
                    exit_price REAL,
                    pnl REAL,
                    pnl_percent REAL,
                    duration_seconds INTEGER,
                    strategy TEXT,
                    signal_confidence REAL,
                    market_regime TEXT
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS signal_quality (
                    signal_id TEXT PRIMARY KEY,
                    timestamp TEXT,
                    symbol TEXT,
                    direction TEXT,
                    predicted_move REAL,
                    actual_move REAL,
                    prediction_error REAL,
                    confidence REAL,
                    accuracy REAL,
                    time_to_result INTEGER
                )
            """)
    
    def record_trade(self, performance: TradePerformance):
        """Record trade performance data."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """INSERT OR REPLACE INTO trade_performance 
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    performance.trade_id,
                    performance.symbol,
                    performance.entry_time.isoformat(),
                    performance.exit_time.isoformat() if performance.exit_time else None,
                    performance.entry_price,
                    performance.exit_price,
                    performance.pnl,
                    performance.pnl_percent,
                    performance.duration_seconds,
                    performance.strategy,
                    performance.signal_confidence,
                    performance.market_regime
                )
            )
    
    def record_signal(self, quality: SignalQuality):
        """Record signal quality data."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """INSERT OR REPLACE INTO signal_quality 
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    quality.signal_id,
                    quality.timestamp.isoformat(),
                    quality.symbol,
                    quality.direction,
                    quality.predicted_move,
                    quality.actual_move,
                    quality.prediction_error,
                    quality.confidence,
                    quality.accuracy,
                    quality.time_to_result
                )
            )
    
    def analyze_performance(self, lookback_days: int = 30) -> Dict[str, Any]:
        """Analyze recent trading performance."""
        start_date = datetime.now() - timedelta(days=lookback_days)
        
        with sqlite3.connect(self.db_path) as conn:
            # Get trades
            trades_df = pd.read_sql_query(
                """SELECT * FROM trade_performance 
                   WHERE entry_time >= ?""",
                conn,
                params=(start_date.isoformat(),)
            )
            
            if trades_df.empty:
                return {"error": "No trades found in lookback period"}
            
            # Calculate metrics
            metrics = {
                "total_trades": len(trades_df),
                "winning_trades": int((trades_df['pnl'] > 0).sum()),
                "losing_trades": int((trades_df['pnl'] < 0).sum()),
                "win_rate": float((trades_df['pnl'] > 0).mean()),
                "total_pnl": float(trades_df['pnl'].sum()),
                "avg_pnl": float(trades_df['pnl'].mean()),
                "avg_win": float(trades_df[trades_df['pnl'] > 0]['pnl'].mean()) if (trades_df['pnl'] > 0).any() else 0,
                "avg_loss": float(trades_df[trades_df['pnl'] < 0]['pnl'].mean()) if (trades_df['pnl'] < 0).any() else 0,
                "profit_factor": self._calculate_profit_factor(trades_df),
                "sharpe_ratio": self._calculate_sharpe(trades_df),
                "max_drawdown": self._calculate_max_drawdown(trades_df),
                "avg_trade_duration": float(trades_df['duration_seconds'].mean()) if 'duration_seconds' in trades_df else 0
            }
            
            return metrics
    
    def analyze_signal_quality(self, lookback_days: int = 30) -> Dict[str, Any]:
        """Analyze signal prediction accuracy."""
        start_date = datetime.now() - timedelta(days=lookback_days)
        
        with sqlite3.connect(self.db_path) as conn:
            signals_df = pd.read_sql_query(
                """SELECT * FROM signal_quality 
                   WHERE timestamp >= ?""",
                conn,
                params=(start_date.isoformat(),)
            )
            
            if signals_df.empty:
                return {"error": "No signals found in lookback period"}
            
            metrics = {
                "total_signals": len(signals_df),
                "avg_accuracy": float(signals_df['accuracy'].mean()),
                "avg_confidence": float(signals_df['confidence'].mean()),
                "avg_prediction_error": float(signals_df['prediction_error'].mean()),
                "correlation_confidence_accuracy": float(
                    signals_df['confidence'].corr(signals_df['accuracy'])
                ) if len(signals_df) > 1 else 0,
                "signals_by_symbol": signals_df.groupby('symbol').size().to_dict(),
                "accuracy_by_direction": signals_df.groupby('direction')['accuracy'].mean().to_dict()
            }
            
            return metrics
    
    def detect_signal_degradation(self, lookback_days: int = 30, threshold: float = 0.1) -> List[Dict]:
        """Identify signals with degraded performance."""
        start_date = datetime.now() - timedelta(days=lookback_days)
        
        with sqlite3.connect(self.db_path) as conn:
            signals_df = pd.read_sql_query(
                """SELECT * FROM signal_quality 
                   WHERE timestamp >= ?""",
                conn,
                params=(start_date.isoformat(),)
            )
            
            if signals_df.empty:
                return []
            
            # Group by symbol and calculate rolling accuracy
            degraded = []
            for symbol in signals_df['symbol'].unique():
                symbol_data = signals_df[signals_df['symbol'] == symbol]
                
                if len(symbol_data) < 20:  # Need minimum samples
                    continue
                
                # Split into first and second half
                mid = len(symbol_data) // 2
                early_accuracy = symbol_data.iloc[:mid]['accuracy'].mean()
                late_accuracy = symbol_data.iloc[mid:]['accuracy'].mean()
                
                # Check for degradation
                if (early_accuracy - late_accuracy) > threshold:
                    degraded.append({
                        "symbol": symbol,
                        "early_accuracy": float(early_accuracy),
                        "late_accuracy": float(late_accuracy),
                        "degradation": float(early_accuracy - late_accuracy),
                        "recommendation": "review_strategy"
                    })
            
            return degraded
    
    def generate_improvement_recommendations(self) -> List[Dict]:
        """Generate system improvement recommendations."""
        recommendations = []
        
        # Analyze performance
        perf = self.analyze_performance(lookback_days=30)
        signals = self.analyze_signal_quality(lookback_days=30)
        degraded = self.detect_signal_degradation()
        
        # Win rate recommendations
        if perf.get('win_rate', 0) < 0.5:
            recommendations.append({
                "category": "strategy",
                "priority": "high",
                "issue": "Low win rate",
                "current_value": f"{perf.get('win_rate', 0):.1%}",
                "recommendation": "Review entry criteria and reduce false signals"
            })
        
        # Risk/Reward recommendations
        if perf.get('profit_factor', 0) < 1.5:
            recommendations.append({
                "category": "risk_management",
                "priority": "medium",
                "issue": "Low profit factor",
                "current_value": f"{perf.get('profit_factor', 0):.2f}",
                "recommendation": "Optimize take-profit and stop-loss levels"
            })
        
        # Signal quality recommendations
        if signals.get('correlation_confidence_accuracy', 0) < 0.3:
            recommendations.append({
                "category": "ml_model",
                "priority": "high",
                "issue": "Confidence not predictive of accuracy",
                "current_value": f"{signals.get('correlation_confidence_accuracy', 0):.3f}",
                "recommendation": "Recalibrate confidence scores or retrain model"
            })
        
        # Degraded signals
        for deg in degraded:
            recommendations.append({
                "category": "strategy",
                "priority": "high",
                "issue": f"Signal degradation for {deg['symbol']}",
                "current_value": f"Accuracy dropped from {deg['early_accuracy']:.1%} to {deg['late_accuracy']:.1%}",
                "recommendation": "Review and update strategy parameters"
            })
        
        return recommendations
    
    def export_feedback_report(self, output_path: str):
        """Export comprehensive feedback report."""
        report = {
            "generated_at": datetime.now().isoformat(),
            "period": "last_30_days",
            "performance": self.analyze_performance(),
            "signal_quality": self.analyze_signal_quality(),
            "degraded_signals": self.detect_signal_degradation(),
            "recommendations": self.generate_improvement_recommendations()
        }
        
        Path(output_path).write_text(json.dumps(report, indent=2, default=str))
    
    @staticmethod
    def _calculate_profit_factor(trades_df: pd.DataFrame) -> float:
        """Calculate profit factor (gross profit / gross loss)."""
        gross_profit = trades_df[trades_df['pnl'] > 0]['pnl'].sum()
        gross_loss = abs(trades_df[trades_df['pnl'] < 0]['pnl'].sum())
        return gross_profit / gross_loss if gross_loss > 0 else float('inf')
    
    @staticmethod
    def _calculate_sharpe(trades_df: pd.DataFrame, risk_free_rate: float = 0.02) -> float:
        """Calculate Sharpe ratio."""
        returns = trades_df['pnl_percent']
        if returns.std() == 0:
            return 0
        return (returns.mean() - risk_free_rate) / returns.std()
    
    @staticmethod
    def _calculate_max_drawdown(trades_df: pd.DataFrame) -> float:
        """Calculate maximum drawdown."""
        cumulative = trades_df['pnl'].cumsum()
        peak = cumulative.expanding().max()
        drawdown = (cumulative - peak) / peak
        return abs(drawdown.min()) if not drawdown.empty else 0


class ModelPerformanceTracker:
    """Track ML model performance over time."""
    
    def __init__(self, tracking_dir: str = "model_tracking"):
        self.tracking_dir = Path(tracking_dir)
        self.tracking_dir.mkdir(exist_ok=True)
    
    def record_prediction(
        self,
        model_name: str,
        prediction: Any,
        actual: Any,
        metadata: Optional[Dict] = None
    ):
        """Record a model prediction for later evaluation."""
        record = {
            "timestamp": datetime.now().isoformat(),
            "model_name": model_name,
            "prediction": prediction,
            "actual": actual,
            "metadata": metadata or {}
        }
        
        # Append to model's tracking file
        tracking_file = self.tracking_dir / f"{model_name}.jsonl"
        with open(tracking_file, 'a') as f:
            f.write(json.dumps(record) + '\n')
    
    def calculate_model_accuracy(self, model_name: str, lookback_days: int = 7) -> Dict:
        """Calculate model accuracy over recent period."""
        tracking_file = self.tracking_dir / f"{model_name}.jsonl"
        
        if not tracking_file.exists():
            return {"error": "No tracking data found"}
        
        cutoff = datetime.now() - timedelta(days=lookback_days)
        
        records = []
        with open(tracking_file) as f:
            for line in f:
                record = json.loads(line)
                record_time = datetime.fromisoformat(record['timestamp'])
                if record_time >= cutoff:
                    records.append(record)
        
        if not records:
            return {"error": "No recent records found"}
        
        # Calculate accuracy
        correct = sum(
            1 for r in records
            if abs(r['prediction'] - r['actual']) < 0.001  # Tolerance for float comparison
        )
        
        return {
            "total_predictions": len(records),
            "correct_predictions": correct,
            "accuracy": correct / len(records) if records else 0,
            "lookback_days": lookback_days
        }
