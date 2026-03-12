"""
Trade Autopsy

Automated analysis of losing trades to identify patterns and generate insights.
"""

import json
import logging
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Optional
import numpy as np
try:
    from scipy import stats
except ImportError:
    scipy = None
import numpy

logger = logging.getLogger(__name__)


@dataclass
class AutopsyReport:
    """Autopsy report for a failed trade."""
    trade_id: str
    timestamp: str
    patterns_detected: List[str]
    feature_analysis: Dict[str, Any]
    recommendations: List[str]
    severity: str  # low, medium, high


class TradeAutopsy:
    """
    Analyzes losing trades to identify failure patterns.
    
    Features:
    - Immediate pattern detection
    - Daily batch analysis (winners vs losers)
    - Statistical significance testing
    - Actionable recommendations
    """
    
    def __init__(self, log_dir: str = "logs/autopsy"):
        """
        Initialize trade autopsy system.
        
        Args:
            log_dir: Directory for autopsy reports
        """
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Trade Autopsy initialized: {self.log_dir}")
    
    def analyze_failed_trade(self, trade_log: Any):
        """
        Immediate analysis of a failed trade.
        
        Args:
            trade_log: StructuredTradeLog object
        """
        logger.info(f"🔍 Autopsy for losing trade {trade_log.trade_id}")
        
        patterns = []
        
        # Pattern 1: Overbought/Oversold + Low Volume
        rsi = trade_log.inputs.features.get('rsi', 50)
        volume_ratio = trade_log.inputs.features.get('volume_ratio', 1.0)
        
        if rsi > 70 and volume_ratio < 0.5:
            patterns.append("Overbought + Low Volume")
        elif rsi < 30 and volume_ratio < 0.5:
            patterns.append("Oversold + Low Volume")
        
        # Pattern 2: Counter-trend trade
        if trade_log.inputs.market_regime == "trending_bearish":
            if trade_log.model_outputs.policy == "long":
                patterns.append("Counter-trend long in bearish market")
        elif trade_log.inputs.market_regime == "trending_bullish":
            if trade_log.model_outputs.policy == "short":
                patterns.append("Counter-trend short in bullish market")
        
        # Pattern 3: Low confidence
        if trade_log.model_outputs.confidence < 0.6:
            patterns.append("Low model confidence (<0.6)")
        
        # Pattern 4: High slippage
        if trade_log.execution.slippage_pips > 2.0:
            patterns.append("High slippage (>2 pips)")
        
        # Pattern 5: Poor risk/reward
        if trade_log.outcome:
            mae = abs(trade_log.outcome.max_adverse_excursion)
            mfe = abs(trade_log.outcome.max_favorable_excursion)
            if mae > mfe * 2:
                patterns.append("Poor risk/reward (MAE > 2x MFE)")
        
        # Generate recommendations
        recommendations = self._generate_recommendations(patterns, trade_log)
        
        # Determine severity
        severity = "high" if len(patterns) >= 3 else "medium" if len(patterns) >= 2 else "low"
        
        # Create report
        report = AutopsyReport(
            trade_id=trade_log.trade_id,
            timestamp=datetime.utcnow().isoformat(),
            patterns_detected=patterns,
            feature_analysis=self._analyze_features(trade_log),
            recommendations=recommendations,
            severity=severity
        )
        
        # Save report
        self._save_report(report)
        
        # Log findings
        if patterns:
            logger.warning(f"Failure patterns detected: {', '.join(patterns)}")
        for rec in recommendations:
            logger.info(f"💡 Recommendation: {rec}")
    
    def daily_batch_analysis(self, trades_file: str):
        """
        Daily batch analysis comparing winners vs losers.
        
        Args:
            trades_file: Path to trades JSONL file
        """
        logger.info("Running daily trade autopsy batch analysis...")
        
        # Load trades
        trades = self._load_trades(trades_file)
        
        if len(trades) < 10:
            logger.info("Not enough trades for statistical analysis")
            return
        
        # Separate winners and losers
        winners = [t for t in trades if t.get('outcome') and t['outcome']['pnl'] > 0]
        losers = [t for t in trades if t.get('outcome') and t['outcome']['pnl'] < 0]
        
        logger.info(f"Analyzing {len(winners)} winners vs {len(losers)} losers")
        
        if len(winners) < 5 or len(losers) < 5:
            logger.info("Not enough winners/losers for comparison")
            return
        
        # Compare feature distributions
        insights = self._compare_distributions(winners, losers)
        
        # Generate report
        self._generate_daily_report(insights, winners, losers)
    
    def _analyze_features(self, trade_log: Any) -> Dict[str, Any]:
        """Analyze features for anomalies."""
        analysis = {}
        
        features = trade_log.inputs.features
        
        # Check for extreme values
        for name, value in features.items():
            if 'rsi' in name.lower():
                if value > 80 or value < 20:
                    analysis[name] = f"Extreme value: {value:.2f}"
            elif 'volume' in name.lower():
                if value < 0.3:
                    analysis[name] = f"Very low: {value:.2f}"
                elif value > 3.0:
                    analysis[name] = f"Very high: {value:.2f}"
        
        return analysis
    
    def _generate_recommendations(self, patterns: List[str], trade_log: Any) -> List[str]:
        """Generate actionable recommendations."""
        recommendations = []
        
        for pattern in patterns:
            if "Overbought" in pattern or "Oversold" in pattern:
                recommendations.append("Add volume confirmation filter")
            
            if "Counter-trend" in pattern:
                recommendations.append("Increase trend strength threshold")
            
            if "Low model confidence" in pattern:
                recommendations.append("Increase minimum confidence to 0.65")
            
            if "High slippage" in pattern:
                recommendations.append("Use limit orders or improve execution timing")
            
            if "Poor risk/reward" in pattern:
                recommendations.append("Tighten stop loss or widen take profit")
        
        return list(set(recommendations))  # Remove duplicates
    
    def _load_trades(self, trades_file: str) -> List[Dict]:
        """Load trades from JSONL file."""
        trades = []
        try:
            with open(trades_file, 'r') as f:
                for line in f:
                    trades.append(json.loads(line))
        except Exception as e:
            logger.error(f"Failed to load trades: {e}")
        
        return trades
    
    def _compare_distributions(self, winners: List[Dict], losers: List[Dict]) -> Dict[str, Any]:
        """Compare feature distributions between winners and losers."""
        insights = {}
        
        # Extract features
        winner_features = self._extract_features(winners)
        loser_features = self._extract_features(losers)
        
        # Get common features
        common_features = set(winner_features.keys()) & set(loser_features.keys())
        
        for feature in common_features:
            winner_vals = winner_features[feature]
            loser_vals = loser_features[feature]
            
            if len(winner_vals) < 5 or len(loser_vals) < 5:
                continue
            try:
            
            # T-test
                t_stat, p_value = stats.ttest_ind(winner_vals, loser_vals)
                
                if p_value < 0.05:  # Significant difference
                    winner_mean = np.mean(winner_vals)
                    loser_mean = np.mean(loser_vals)
                    
                    insights[feature] = {
                        'winner_mean': float(winner_mean),
                        'loser_mean': float(loser_mean),
                        'p_value': float(p_value),
                        'significant': True,
                        'interpretation': self._interpret_difference(
                            feature, winner_mean, loser_mean
                        )
                    }
            except Exception as e:
                logger.debug(f"Statistical test failed for {feature}: {e}")
        
        return insights
    
    def _extract_features(self, trades: List[Dict]) -> Dict[str, List[float]]:
        """Extract features from trades."""
        features = {}
        
        for trade in trades:
            if 'inputs' not in trade or 'features' not in trade['inputs']:
                continue
            
            for name, value in trade['inputs']['features'].items():
                if name not in features:
                    features[name] = []
                features[name].append(float(value))
        
        return features
    
    def _interpret_difference(self, feature: str, winner_mean: float, loser_mean: float) -> str:
        """Generate human-readable interpretation."""
        diff = winner_mean - loser_mean
        direction = "higher" if diff > 0 else "lower"
        
        return f"Winners have {direction} {feature} ({winner_mean:.2f} vs {loser_mean:.2f})"
    
    def _generate_daily_report(self, insights: Dict, winners: List, losers: List):
        """Generate daily autopsy report."""
        report = {
            'date': datetime.utcnow().strftime("%Y-%m-%d"),
            'total_trades': len(winners) + len(losers),
            'winners': len(winners),
            'losers': len(losers),
            'win_rate': len(winners) / (len(winners) + len(losers)),
            'significant_insights': insights,
            'recommendations': self._generate_batch_recommendations(insights)
        }
        
        # Save report
        report_file = self.log_dir / f"daily_report_{report['date']}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Daily autopsy report saved: {report_file}")
        
        # Log key insights
        logger.info(f"📊 Daily Analysis: {report['win_rate']:.1%} win rate")
        for feature, insight in insights.items():
            if insight['significant']:
                logger.info(f"📊 {insight['interpretation']}")
    
    def _generate_batch_recommendations(self, insights: Dict) -> List[str]:
        """Generate recommendations from batch analysis."""
        recommendations = []
        
        for feature, insight in insights.items():
            if not insight['significant']:
                continue
            
            if 'rsi' in feature.lower():
                if insight['loser_mean'] > 70:
                    recommendations.append("Avoid trades when RSI > 70")
                elif insight['loser_mean'] < 30:
                    recommendations.append("Avoid trades when RSI < 30")
            
            if 'volume' in feature.lower():
                if insight['loser_mean'] < insight['winner_mean']:
                    recommendations.append("Require higher volume confirmation")
            
            if 'confidence' in feature.lower():
                if insight['loser_mean'] < 0.6:
                    recommendations.append("Increase minimum confidence threshold to 0.65")
        
        return list(set(recommendations))
    
    def _save_report(self, report: AutopsyReport):
        """Save autopsy report."""
        try:
            report_file = self.log_dir / f"autopsy_{report.trade_id}.json"
            with open(report_file, 'w') as f:
                json.dump(asdict(report), f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save autopsy report: {e}")
