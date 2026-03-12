"""
Intelligent Social Learning System

Goes FAR beyond copy trading. The AI actively learns from:
- Top traders and their strategies
- Hedge fund approaches and portfolio construction
- Market makers and their techniques
- Institutional order flow patterns
- Trading communities and collective intelligence

The system identifies WHAT others do differently and better,
extracts the underlying principles, and adapts them to our constraints.
"""

import asyncio
import hashlib
import json
import logging
import re
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum, auto
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


class TraderType(Enum):
    """Types of traders/entities to learn from."""
    RETAIL_TOP = auto()
    PROP_TRADER = auto()
    HEDGE_FUND = auto()
    MARKET_MAKER = auto()
    QUANT_FUND = auto()
    INSTITUTIONAL = auto()
    ALGO_TRADER = auto()
    SENTIMENT_TRADER = auto()
    MACRO_TRADER = auto()
    ARBITRAGEUR = auto()


class LearningDimension(Enum):
    """Dimensions of trading to learn about."""
    ENTRY_TIMING = auto()
    EXIT_TIMING = auto()
    POSITION_SIZING = auto()
    RISK_MANAGEMENT = auto()
    PORTFOLIO_CONSTRUCTION = auto()
    REGIME_ADAPTATION = auto()
    DRAWDOWN_RECOVERY = auto()
    CORRELATION_MANAGEMENT = auto()
    VOLATILITY_TRADING = auto()
    ORDER_EXECUTION = auto()
    HEDGING = auto()
    ASSET_SELECTION = auto()


class InsightQuality(Enum):
    """Quality rating of extracted insights."""
    UNVERIFIED = 0
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    PROVEN = 4


@dataclass
class TraderProfile:
    """Profile of a trader/entity being studied."""
    id: str
    name: str
    trader_type: TraderType
    track_record_months: int
    sharpe_ratio: float
    max_drawdown: float
    win_rate: float
    avg_return_monthly: float
    specialties: List[str]
    known_strategies: List[str]
    data_source: str
    last_updated: datetime
    reliability_score: float = 0.5
    total_insights_extracted: int = 0


@dataclass
class TradingInsight:
    """An insight extracted from studying another trader/fund."""
    id: str
    source_trader_id: str
    dimension: LearningDimension
    title: str
    description: str
    principle: str
    evidence: Dict[str, Any]
    quality: InsightQuality
    applicability_score: float
    estimated_impact: float
    implementation_difficulty: float
    timestamp: datetime
    tested: bool = False
    test_results: Optional[Dict[str, Any]] = None
    adopted: bool = False


@dataclass
class PerformanceGap:
    """A gap between our performance and a top performer."""
    dimension: LearningDimension
    our_metric: float
    their_metric: float
    gap_percent: float
    potential_improvement: float
    priority: int
    source_traders: List[str]


@dataclass
class AdaptedStrategy:
    """A strategy adapted from studying others."""
    id: str
    source_insight_ids: List[str]
    name: str
    description: str
    parameters: Dict[str, Any]
    backtest_sharpe: float
    backtest_return: float
    backtest_drawdown: float
    paper_trade_days: int
    paper_trade_return: float
    status: str  # 'proposed', 'backtesting', 'paper_trading', 'live', 'rejected'
    created: datetime
    last_updated: datetime


class TraderAnalyzer:
    """Analyzes other traders to extract actionable insights."""

    def __init__(self):
        self.profiles: Dict[str, TraderProfile] = {}
        self.trade_histories: Dict[str, List[Dict[str, Any]]] = {}

    def analyze_trader(
        self,
        trader_id: str,
        trades: List[Dict[str, Any]],
        our_trades: List[Dict[str, Any]]
    ) -> List[TradingInsight]:
        """Analyze a trader's behavior and extract insights."""
        insights = []

        if not trades or not our_trades:
            return insights

        # Convert to DataFrames for analysis
        their_df = pd.DataFrame(trades)
        our_df = pd.DataFrame(our_trades)

        # 1. Entry timing analysis
        entry_insight = self._analyze_entry_timing(trader_id, their_df, our_df)
        if entry_insight:
            insights.append(entry_insight)

        # 2. Exit timing analysis
        exit_insight = self._analyze_exit_timing(trader_id, their_df, our_df)
        if exit_insight:
            insights.append(exit_insight)

        # 3. Position sizing analysis
        sizing_insight = self._analyze_position_sizing(trader_id, their_df, our_df)
        if sizing_insight:
            insights.append(sizing_insight)

        # 4. Risk management analysis
        risk_insight = self._analyze_risk_management(trader_id, their_df, our_df)
        if risk_insight:
            insights.append(risk_insight)

        # 5. Drawdown recovery analysis
        recovery_insight = self._analyze_drawdown_recovery(trader_id, their_df, our_df)
        if recovery_insight:
            insights.append(recovery_insight)

        # 6. Regime adaptation analysis
        regime_insight = self._analyze_regime_adaptation(trader_id, their_df, our_df)
        if regime_insight:
            insights.append(regime_insight)

        return insights

    def _analyze_entry_timing(self, trader_id, their_df, our_df) -> Optional[TradingInsight]:
        """Compare entry timing patterns."""
        try:
            if 'entry_time' not in their_df.columns or 'entry_time' not in our_df.columns:
                return None

            # Analyze time-of-day patterns
            their_hours = pd.to_datetime(their_df['entry_time']).dt.hour
            our_hours = pd.to_datetime(our_df['entry_time']).dt.hour

            their_peak_hours = their_hours.value_counts().head(3).index.tolist()
            our_peak_hours = our_hours.value_counts().head(3).index.tolist()

            if set(their_peak_hours) != set(our_peak_hours):
                # Check if their timing correlates with better returns
                their_returns = their_df.get('return', pd.Series([0]))
                our_returns = our_df.get('return', pd.Series([0]))

                if their_returns.mean() > our_returns.mean():
                    return TradingInsight(
                        id=f"INS-ENTRY-{trader_id[:8]}",
                        source_trader_id=trader_id,
                        dimension=LearningDimension.ENTRY_TIMING,
                        title="Different entry timing pattern detected",
                        description=f"Trader enters at hours {their_peak_hours} vs our {our_peak_hours}",
                        principle="Entry timing aligned with peak liquidity/volatility windows",
                        evidence={
                            'their_peak_hours': their_peak_hours,
                            'our_peak_hours': our_peak_hours,
                            'their_avg_return': float(their_returns.mean()),
                            'our_avg_return': float(our_returns.mean()),
                        },
                        quality=InsightQuality.MEDIUM,
                        applicability_score=0.7,
                        estimated_impact=abs(float(their_returns.mean() - our_returns.mean())),
                        implementation_difficulty=0.3,
                        timestamp=datetime.utcnow()
                    )
        except Exception as e:
            logger.debug(f"Entry timing analysis error: {e}")
        return None

    def _analyze_exit_timing(self, trader_id, their_df, our_df) -> Optional[TradingInsight]:
        """Compare exit strategies."""
        try:
            if 'duration_hours' not in their_df.columns or 'duration_hours' not in our_df.columns:
                return None

            their_avg_duration = their_df['duration_hours'].mean()
            our_avg_duration = our_df['duration_hours'].mean()

            if abs(their_avg_duration - our_avg_duration) / max(our_avg_duration, 1) > 0.3:
                their_returns = their_df.get('return', pd.Series([0]))
                our_returns = our_df.get('return', pd.Series([0]))

                if their_returns.mean() > our_returns.mean():
                    return TradingInsight(
                        id=f"INS-EXIT-{trader_id[:8]}",
                        source_trader_id=trader_id,
                        dimension=LearningDimension.EXIT_TIMING,
                        title="Different trade duration pattern",
                        description=f"Avg duration: theirs={their_avg_duration:.1f}h vs ours={our_avg_duration:.1f}h",
                        principle="Optimal holding period differs from current approach",
                        evidence={
                            'their_avg_duration': float(their_avg_duration),
                            'our_avg_duration': float(our_avg_duration),
                        },
                        quality=InsightQuality.MEDIUM,
                        applicability_score=0.6,
                        estimated_impact=0.05,
                        implementation_difficulty=0.4,
                        timestamp=datetime.utcnow()
                    )
        except Exception as e:
            logger.debug(f"Exit timing analysis error: {e}")
        return None

    def _analyze_position_sizing(self, trader_id, their_df, our_df) -> Optional[TradingInsight]:
        """Compare position sizing approaches."""
        try:
            if 'position_size' not in their_df.columns or 'position_size' not in our_df.columns:
                return None

            their_sizes = their_df['position_size']
            our_sizes = our_df['position_size']

            # Check if they use variable sizing (Kelly-like)
            their_cv = their_sizes.std() / max(their_sizes.mean(), 0.001)
            our_cv = our_sizes.std() / max(our_sizes.mean(), 0.001)

            if their_cv > our_cv * 1.5:
                return TradingInsight(
                    id=f"INS-SIZE-{trader_id[:8]}",
                    source_trader_id=trader_id,
                    dimension=LearningDimension.POSITION_SIZING,
                    title="More dynamic position sizing detected",
                    description=f"Their size variability (CV={their_cv:.2f}) vs ours (CV={our_cv:.2f})",
                    principle="Dynamic position sizing based on conviction/edge strength",
                    evidence={
                        'their_cv': float(their_cv),
                        'our_cv': float(our_cv),
                        'their_mean_size': float(their_sizes.mean()),
                        'our_mean_size': float(our_sizes.mean()),
                    },
                    quality=InsightQuality.MEDIUM,
                    applicability_score=0.8,
                    estimated_impact=0.08,
                    implementation_difficulty=0.5,
                    timestamp=datetime.utcnow()
                )
        except Exception as e:
            logger.debug(f"Position sizing analysis error: {e}")
        return None

    def _analyze_risk_management(self, trader_id, their_df, our_df) -> Optional[TradingInsight]:
        """Compare risk management approaches."""
        try:
            their_returns = their_df.get('return', pd.Series([0]))
            our_returns = our_df.get('return', pd.Series([0]))

            # Compare tail risk
            their_worst_5pct = np.percentile(their_returns, 5) if len(their_returns) > 20 else 0
            our_worst_5pct = np.percentile(our_returns, 5) if len(our_returns) > 20 else 0

            if their_worst_5pct > our_worst_5pct:
                return TradingInsight(
                    id=f"INS-RISK-{trader_id[:8]}",
                    source_trader_id=trader_id,
                    dimension=LearningDimension.RISK_MANAGEMENT,
                    title="Better tail risk management",
                    description=f"Their 5th percentile: {their_worst_5pct:.2%} vs ours: {our_worst_5pct:.2%}",
                    principle="Superior downside protection through tighter stops or hedging",
                    evidence={
                        'their_var_5': float(their_worst_5pct),
                        'our_var_5': float(our_worst_5pct),
                    },
                    quality=InsightQuality.HIGH,
                    applicability_score=0.9,
                    estimated_impact=abs(float(their_worst_5pct - our_worst_5pct)),
                    implementation_difficulty=0.6,
                    timestamp=datetime.utcnow()
                )
        except Exception as e:
            logger.debug(f"Risk management analysis error: {e}")
        return None

    def _analyze_drawdown_recovery(self, trader_id, their_df, our_df) -> Optional[TradingInsight]:
        """Compare drawdown recovery patterns."""
        try:
            their_returns = their_df.get('return', pd.Series([0]))
            our_returns = our_df.get('return', pd.Series([0]))

            # Identify drawdown periods and recovery speed
            their_cum = their_returns.cumsum()
            our_cum = our_returns.cumsum()

            their_dd = their_cum - their_cum.cummax()
            our_dd = our_cum - our_cum.cummax()

            # Average recovery speed (trades to recover from drawdown)
            their_dd_periods = (their_dd < 0).sum()
            our_dd_periods = (our_dd < 0).sum()

            if their_dd_periods < our_dd_periods * 0.7:
                return TradingInsight(
                    id=f"INS-RECOV-{trader_id[:8]}",
                    source_trader_id=trader_id,
                    dimension=LearningDimension.DRAWDOWN_RECOVERY,
                    title="Faster drawdown recovery",
                    description=f"They spend {their_dd_periods} trades in drawdown vs our {our_dd_periods}",
                    principle="Faster recovery through position adjustment or strategy rotation",
                    evidence={
                        'their_dd_trades': int(their_dd_periods),
                        'our_dd_trades': int(our_dd_periods),
                    },
                    quality=InsightQuality.HIGH,
                    applicability_score=0.8,
                    estimated_impact=0.10,
                    implementation_difficulty=0.7,
                    timestamp=datetime.utcnow()
                )
        except Exception as e:
            logger.debug(f"Drawdown recovery analysis error: {e}")
        return None

    def _analyze_regime_adaptation(self, trader_id, their_df, our_df) -> Optional[TradingInsight]:
        """Compare how traders adapt to different market regimes."""
        try:
            if 'market_regime' not in their_df.columns:
                return None

            their_returns = their_df.get('return', pd.Series([0]))
            our_returns = our_df.get('return', pd.Series([0]))

            # Compare performance across regimes
            their_by_regime = their_df.groupby('market_regime')['return'].mean()
            our_by_regime = our_df.groupby('market_regime')['return'].mean() if 'market_regime' in our_df.columns else pd.Series()

            for regime in their_by_regime.index:
                if regime in our_by_regime.index:
                    if their_by_regime[regime] > our_by_regime[regime] * 1.5:
                        return TradingInsight(
                            id=f"INS-REGIME-{trader_id[:8]}-{regime}",
                            source_trader_id=trader_id,
                            dimension=LearningDimension.REGIME_ADAPTATION,
                            title=f"Better performance in {regime} regime",
                            description=f"Their return in {regime}: {their_by_regime[regime]:.2%} vs ours: {our_by_regime[regime]:.2%}",
                            principle=f"Superior strategy adaptation for {regime} market conditions",
                            evidence={
                                'regime': regime,
                                'their_return': float(their_by_regime[regime]),
                                'our_return': float(our_by_regime[regime]),
                            },
                            quality=InsightQuality.HIGH,
                            applicability_score=0.85,
                            estimated_impact=abs(float(their_by_regime[regime] - our_by_regime[regime])),
                            implementation_difficulty=0.7,
                            timestamp=datetime.utcnow()
                        )
        except Exception as e:
            logger.debug(f"Regime adaptation analysis error: {e}")
        return None


class HedgeFundAnalyzer:
    """Analyzes hedge fund strategies from public filings and reports."""

    def __init__(self):
        self.fund_profiles: Dict[str, Dict[str, Any]] = {}
        self.strategy_library: List[Dict[str, Any]] = []

    def analyze_13f_filing(self, filing_data: Dict[str, Any]) -> List[TradingInsight]:
        """Analyze SEC 13F filings to understand institutional positioning."""
        insights = []

        holdings = filing_data.get('holdings', [])
        fund_name = filing_data.get('fund_name', 'Unknown')
        fund_id = filing_data.get('fund_id', hashlib.md5(fund_name.encode()).hexdigest()[:12])

        if not holdings:
            return insights

        # Analyze portfolio construction
        total_value = sum(h.get('value', 0) for h in holdings)
        if total_value > 0:
            # Concentration analysis
            top_5_pct = sum(
                sorted([h.get('value', 0) / total_value for h in holdings], reverse=True)[:5]
            )

            if top_5_pct > 0.5:
                insights.append(TradingInsight(
                    id=f"INS-13F-CONC-{fund_id}",
                    source_trader_id=fund_id,
                    dimension=LearningDimension.PORTFOLIO_CONSTRUCTION,
                    title=f"{fund_name}: Concentrated portfolio approach",
                    description=f"Top 5 positions = {top_5_pct:.0%} of portfolio",
                    principle="High-conviction concentrated betting on best ideas",
                    evidence={'top_5_concentration': top_5_pct, 'total_holdings': len(holdings)},
                    quality=InsightQuality.HIGH,
                    applicability_score=0.6,
                    estimated_impact=0.05,
                    implementation_difficulty=0.4,
                    timestamp=datetime.utcnow()
                ))

            # Sector analysis
            sectors = defaultdict(float)
            for h in holdings:
                sector = h.get('sector', 'Unknown')
                sectors[sector] += h.get('value', 0) / total_value

            top_sector = max(sectors.items(), key=lambda x: x[1]) if sectors else ('Unknown', 0)
            if top_sector[1] > 0.3:
                insights.append(TradingInsight(
                    id=f"INS-13F-SECT-{fund_id}",
                    source_trader_id=fund_id,
                    dimension=LearningDimension.ASSET_SELECTION,
                    title=f"{fund_name}: Sector concentration in {top_sector[0]}",
                    description=f"{top_sector[0]} = {top_sector[1]:.0%} of portfolio",
                    principle="Sector expertise and thematic investing",
                    evidence={'sectors': dict(sectors)},
                    quality=InsightQuality.HIGH,
                    applicability_score=0.5,
                    estimated_impact=0.03,
                    implementation_difficulty=0.5,
                    timestamp=datetime.utcnow()
                ))

        return insights

    def analyze_strategy_description(self, description: str, fund_name: str) -> List[TradingInsight]:
        """Extract strategy insights from hedge fund descriptions."""
        insights = []
        fund_id = hashlib.md5(fund_name.encode()).hexdigest()[:12]

        # Pattern matching for known strategy types
        strategy_patterns = {
            'long_short': r'long[\s/]short|market\s*neutral',
            'momentum': r'momentum|trend\s*following|CTA',
            'mean_reversion': r'mean\s*reversion|statistical\s*arbitrage|stat\s*arb',
            'event_driven': r'event[\s-]driven|merger\s*arb|special\s*situations',
            'macro': r'global\s*macro|macro\s*trading',
            'quant': r'quantitative|systematic|algorithmic',
            'multi_strategy': r'multi[\s-]strategy|diversified',
            'volatility': r'volatility\s*trading|vol\s*arb|options\s*strategies',
        }

        detected_strategies = []
        for strategy_type, pattern in strategy_patterns.items():
            if re.search(pattern, description, re.IGNORECASE):
                detected_strategies.append(strategy_type)

        for strategy in detected_strategies:
            insights.append(TradingInsight(
                id=f"INS-STRAT-{fund_id}-{strategy}",
                source_trader_id=fund_id,
                dimension=LearningDimension.PORTFOLIO_CONSTRUCTION,
                title=f"{fund_name} uses {strategy.replace('_', ' ')} strategy",
                description=f"Detected {strategy} approach in fund description",
                principle=f"Consider incorporating {strategy.replace('_', ' ')} elements",
                evidence={'strategy_type': strategy, 'source': 'description_analysis'},
                quality=InsightQuality.MEDIUM,
                applicability_score=0.5,
                estimated_impact=0.04,
                implementation_difficulty=0.6,
                timestamp=datetime.utcnow()
            ))

        return insights


class IntelligentSocialLearning:
    """
    Master social learning system that goes beyond copy trading.
    
    Instead of blindly copying trades, this system:
    1. Studies top performers across multiple dimensions
    2. Identifies performance gaps
    3. Extracts underlying principles
    4. Adapts insights to our constraints
    5. Tests adaptations in sandbox
    6. Gradually integrates proven improvements
    """

    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.trader_analyzer = TraderAnalyzer()
        self.hedge_fund_analyzer = HedgeFundAnalyzer()

        # Knowledge base
        self.insights: List[TradingInsight] = []
        self.performance_gaps: List[PerformanceGap] = []
        self.adapted_strategies: List[AdaptedStrategy] = []

        # Our performance baseline
        self.our_performance: Dict[str, float] = {}

        # Learning state
        self.learning_cycles: int = 0
        self.total_insights_extracted: int = 0
        self.total_insights_adopted: int = 0

        logger.info("IntelligentSocialLearning initialized")

    async def run_learning_cycle(
        self,
        our_trades: List[Dict[str, Any]],
        external_traders: List[Dict[str, Any]] = None,
        fund_filings: List[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Run one complete social learning cycle.
        
        Args:
            our_trades: Our recent trade history
            external_traders: Data about external traders and their trades
            fund_filings: Hedge fund filing data
            
        Returns:
            Learning cycle results
        """
        cycle_start = datetime.utcnow()
        new_insights = []

        # 1. Analyze external traders
        if external_traders:
            for trader_data in external_traders:
                trader_id = trader_data.get('id', 'unknown')
                trader_trades = trader_data.get('trades', [])

                insights = self.trader_analyzer.analyze_trader(
                    trader_id, trader_trades, our_trades
                )
                new_insights.extend(insights)

        # 2. Analyze hedge fund filings
        if fund_filings:
            for filing in fund_filings:
                insights = self.hedge_fund_analyzer.analyze_13f_filing(filing)
                new_insights.extend(insights)

                description = filing.get('strategy_description', '')
                if description:
                    desc_insights = self.hedge_fund_analyzer.analyze_strategy_description(
                        description, filing.get('fund_name', 'Unknown')
                    )
                    new_insights.extend(desc_insights)

        # 3. Identify performance gaps
        gaps = self._identify_performance_gaps(new_insights)

        # 4. Rank insights by potential ROI
        ranked_insights = self._rank_insights(new_insights)

        # 5. Propose adaptations for top insights
        adaptations = self._propose_adaptations(ranked_insights[:5])

        # Store results
        self.insights.extend(new_insights)
        self.performance_gaps.extend(gaps)
        self.adapted_strategies.extend(adaptations)
        self.total_insights_extracted += len(new_insights)
        self.learning_cycles += 1

        return {
            'cycle': self.learning_cycles,
            'duration_seconds': (datetime.utcnow() - cycle_start).total_seconds(),
            'new_insights': len(new_insights),
            'performance_gaps': len(gaps),
            'proposed_adaptations': len(adaptations),
            'total_insights': self.total_insights_extracted,
            'top_insights': [
                {
                    'title': i.title,
                    'dimension': i.dimension.name,
                    'impact': i.estimated_impact,
                    'quality': i.quality.name,
                }
                for i in ranked_insights[:5]
            ],
            'top_gaps': [
                {
                    'dimension': g.dimension.name,
                    'gap_percent': g.gap_percent,
                    'priority': g.priority,
                }
                for g in sorted(gaps, key=lambda g: g.priority)[:5]
            ],
        }

    def _identify_performance_gaps(self, insights: List[TradingInsight]) -> List[PerformanceGap]:
        """Identify gaps between our performance and top performers."""
        gaps = []
        dimension_insights = defaultdict(list)

        for insight in insights:
            dimension_insights[insight.dimension].append(insight)

        for dimension, dim_insights in dimension_insights.items():
            if not dim_insights:
                continue

            # Calculate average gap for this dimension
            their_metrics = []
            our_metrics = []

            for insight in dim_insights:
                evidence = insight.evidence
                for key in evidence:
                    if key.startswith('their_') and key.replace('their_', 'our_') in evidence:
                        their_val = evidence[key]
                        our_val = evidence[key.replace('their_', 'our_')]
                        if isinstance(their_val, (int, float)) and isinstance(our_val, (int, float)):
                            their_metrics.append(their_val)
                            our_metrics.append(our_val)

            if their_metrics and our_metrics:
                avg_their = np.mean(their_metrics)
                avg_our = np.mean(our_metrics)
                gap = abs(avg_their - avg_our) / max(abs(avg_our), 0.001)

                gaps.append(PerformanceGap(
                    dimension=dimension,
                    our_metric=float(avg_our),
                    their_metric=float(avg_their),
                    gap_percent=float(gap),
                    potential_improvement=float(avg_their - avg_our),
                    priority=1 if gap > 0.3 else (2 if gap > 0.15 else 3),
                    source_traders=[i.source_trader_id for i in dim_insights]
                ))

        return gaps

    def _rank_insights(self, insights: List[TradingInsight]) -> List[TradingInsight]:
        """Rank insights by expected ROI (impact / difficulty)."""
        def roi_score(insight: TradingInsight) -> float:
            impact = insight.estimated_impact
            difficulty = max(insight.implementation_difficulty, 0.1)
            quality_mult = insight.quality.value / 4.0
            applicability = insight.applicability_score
            return (impact * quality_mult * applicability) / difficulty

        return sorted(insights, key=roi_score, reverse=True)

    def _propose_adaptations(self, top_insights: List[TradingInsight]) -> List[AdaptedStrategy]:
        """Propose strategy adaptations based on top insights."""
        adaptations = []

        for insight in top_insights:
            if insight.applicability_score < 0.5:
                continue

            adaptation = AdaptedStrategy(
                id=f"ADAPT-{insight.id}",
                source_insight_ids=[insight.id],
                name=f"Adapted: {insight.title}",
                description=f"Strategy adaptation based on: {insight.principle}",
                parameters={
                    'source_dimension': insight.dimension.name,
                    'estimated_impact': insight.estimated_impact,
                    'evidence': insight.evidence,
                },
                backtest_sharpe=0.0,
                backtest_return=0.0,
                backtest_drawdown=0.0,
                paper_trade_days=0,
                paper_trade_return=0.0,
                status='proposed',
                created=datetime.utcnow(),
                last_updated=datetime.utcnow()
            )
            adaptations.append(adaptation)

        return adaptations

    def get_learning_summary(self) -> Dict[str, Any]:
        """Get comprehensive learning summary."""
        return {
            'learning_cycles': self.learning_cycles,
            'total_insights': self.total_insights_extracted,
            'adopted_insights': self.total_insights_adopted,
            'adoption_rate': self.total_insights_adopted / max(self.total_insights_extracted, 1),
            'active_adaptations': len([a for a in self.adapted_strategies if a.status in ('backtesting', 'paper_trading', 'live')]),
            'performance_gaps': len(self.performance_gaps),
            'top_gaps': [
                {'dimension': g.dimension.name, 'gap': g.gap_percent}
                for g in sorted(self.performance_gaps, key=lambda g: g.gap_percent, reverse=True)[:5]
            ],
            'insights_by_dimension': {
                dim.name: sum(1 for i in self.insights if i.dimension == dim)
                for dim in LearningDimension
                if any(i.dimension == dim for i in self.insights)
            },
            'insights_by_quality': {
                q.name: sum(1 for i in self.insights if i.quality == q)
                for q in InsightQuality
                if any(i.quality == q for i in self.insights)
            },
        }

    def save_state(self, path: str = None):
        """Save learning state."""
        if path is None:
            path = 'social_learning_data/learning_state.json'
        Path(path).parent.mkdir(parents=True, exist_ok=True)

        state = {
            'learning_cycles': self.learning_cycles,
            'total_insights_extracted': self.total_insights_extracted,
            'total_insights_adopted': self.total_insights_adopted,
            'insights_count': len(self.insights),
            'gaps_count': len(self.performance_gaps),
            'adaptations_count': len(self.adapted_strategies),
            'last_saved': datetime.utcnow().isoformat(),
        }

        with open(path, 'w', encoding='utf-8') as f:
            json.dump(state, f, indent=2, default=str)

        logger.info(f"Social learning state saved to {path}")
