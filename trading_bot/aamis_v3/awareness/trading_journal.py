"""
AAMIS v3.0 - AI Trading Journal System

This module implements:
1. Detailed trade logging with narrative generation
2. Every Trade Has a Story - Narrative explanations
3. Trade autopsy and analysis
4. Performance insights and recommendations
5. Emotional and behavioral tracking
"""

import logging
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import json
import os
from collections import defaultdict
import numpy as np
import numpy

logger = logging.getLogger(__name__)


class TradeOutcome(Enum):
    """Trade outcome types"""
    WIN = "WIN"
    LOSS = "LOSS"
    BREAKEVEN = "BREAKEVEN"
    PARTIAL_WIN = "PARTIAL_WIN"
    PARTIAL_LOSS = "PARTIAL_LOSS"


class TradeEmotion(Enum):
    """Emotional states during trading"""
    CONFIDENT = "CONFIDENT"
    FEARFUL = "FEARFUL"
    GREEDY = "GREEDY"
    PATIENT = "PATIENT"
    IMPULSIVE = "IMPULSIVE"
    NEUTRAL = "NEUTRAL"
    ANXIOUS = "ANXIOUS"
    EUPHORIC = "EUPHORIC"


class MarketCondition(Enum):
    """Market conditions"""
    TRENDING_UP = "TRENDING_UP"
    TRENDING_DOWN = "TRENDING_DOWN"
    RANGING = "RANGING"
    VOLATILE = "VOLATILE"
    CALM = "CALM"
    UNCERTAIN = "UNCERTAIN"


@dataclass
class TradeEntry:
    """Complete trade journal entry"""
    trade_id: str
    symbol: str
    direction: str  # BUY or SELL
    entry_time: datetime
    exit_time: Optional[datetime] = None
    
    # Prices
    entry_price: float = 0.0
    exit_price: float = 0.0
    stop_loss: float = 0.0
    take_profit: float = 0.0
    
    # Size and P&L
    position_size: float = 0.0
    pnl: float = 0.0
    pnl_percent: float = 0.0
    
    # Risk metrics
    risk_reward_ratio: float = 0.0
    max_adverse_excursion: float = 0.0
    max_favorable_excursion: float = 0.0
    
    # Context
    market_condition: MarketCondition = MarketCondition.UNCERTAIN
    signals_used: List[str] = field(default_factory=list)
    confidence_score: float = 0.0
    
    # Narrative
    entry_reason: str = ""
    exit_reason: str = ""
    narrative: str = ""
    lessons_learned: str = ""
    
    # Emotional tracking
    entry_emotion: TradeEmotion = TradeEmotion.NEUTRAL
    exit_emotion: TradeEmotion = TradeEmotion.NEUTRAL
    
    # Outcome
    outcome: TradeOutcome = TradeOutcome.BREAKEVEN
    
    # Tags
    tags: List[str] = field(default_factory=list)
    
    # Screenshots/charts
    chart_snapshots: List[str] = field(default_factory=list)


@dataclass
class TradingSession:
    """Daily trading session summary"""
    session_id: str
    date: datetime
    trades: List[TradeEntry] = field(default_factory=list)
    
    # Session metrics
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    total_pnl: float = 0.0
    win_rate: float = 0.0
    
    # Session notes
    pre_session_plan: str = ""
    post_session_review: str = ""
    market_observations: str = ""
    
    # Emotional summary
    overall_emotion: TradeEmotion = TradeEmotion.NEUTRAL
    emotional_discipline_score: float = 0.0


class NarrativeGenerator:
    """
    Generates natural language narratives for trades
    Every Trade Has a Story
    """
    
    def __init__(self):
        try:
            self.templates = self._load_templates()
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def _load_templates(self) -> Dict[str, List[str]]:
        """Load narrative templates"""
        return {
            'entry_bullish': [
                "Entered a {direction} position on {symbol} at {price} after observing {signals}. "
                "The market showed {condition} conditions with confidence at {confidence}%.",
                
                "Initiated {direction} trade on {symbol} at {price}. "
                "Key signals: {signals}. Market was {condition}. "
                "Risk-reward ratio: {rr}.",
                
                "Opened {direction} position on {symbol} ({price}). "
                "Entry triggered by {signals}. "
                "Stop loss set at {sl}, target at {tp}."
            ],
            'entry_bearish': [
                "Shorted {symbol} at {price} based on {signals}. "
                "Market conditions: {condition}. Confidence: {confidence}%.",
                
                "Entered short position on {symbol} at {price}. "
                "Bearish signals: {signals}. "
                "Risk-reward: {rr}."
            ],
            'exit_win': [
                "Closed {symbol} trade at {price} for a {pnl_pct}% gain. "
                "Exit reason: {reason}. "
                "The trade played out as expected with {mfe}% maximum favorable excursion.",
                
                "Profitable exit on {symbol} at {price}. "
                "P&L: ${pnl} ({pnl_pct}%). "
                "Trade duration: {duration}."
            ],
            'exit_loss': [
                "Stopped out of {symbol} at {price} for a {pnl_pct}% loss. "
                "Exit reason: {reason}. "
                "Maximum adverse excursion was {mae}%.",
                
                "Closed losing trade on {symbol} at {price}. "
                "Loss: ${pnl} ({pnl_pct}%). "
                "Lesson: {lesson}."
            ],
            'lesson_patterns': [
                "This trade reinforced the importance of {lesson}.",
                "Key takeaway: {lesson}.",
                "Note for future: {lesson}."
            ]
        }
    
    def generate_entry_narrative(self, trade: TradeEntry) -> str:
        """Generate entry narrative"""
        try:
            template_key = 'entry_bullish' if trade.direction == 'BUY' else 'entry_bearish'
            templates = self.templates[template_key]
            template = templates[hash(trade.trade_id) % len(templates)]
        
            narrative = template.format(
                direction=trade.direction,
                symbol=trade.symbol,
                price=f"${trade.entry_price:.4f}",
                signals=", ".join(trade.signals_used) if trade.signals_used else "multiple indicators",
                condition=trade.market_condition.value.lower().replace("_", " "),
                confidence=int(trade.confidence_score * 100),
                rr=f"{trade.risk_reward_ratio:.2f}",
                sl=f"${trade.stop_loss:.4f}",
                tp=f"${trade.take_profit:.4f}"
            )
        
            return narrative
        except Exception as e:
            logger.error(f"Error in generate_entry_narrative: {e}")
            raise
    
    def generate_exit_narrative(self, trade: TradeEntry) -> str:
        """Generate exit narrative"""
        try:
            template_key = 'exit_win' if trade.pnl > 0 else 'exit_loss'
            templates = self.templates[template_key]
            template = templates[hash(trade.trade_id) % len(templates)]
        
            duration = ""
            if trade.exit_time and trade.entry_time:
                delta = trade.exit_time - trade.entry_time
                hours = delta.total_seconds() / 3600
                if hours < 1:
                    duration = f"{int(delta.total_seconds() / 60)} minutes"
                elif hours < 24:
                    duration = f"{hours:.1f} hours"
                else:
                    duration = f"{delta.days} days"
        
            narrative = template.format(
                symbol=trade.symbol,
                price=f"${trade.exit_price:.4f}",
                pnl=abs(trade.pnl),
                pnl_pct=abs(trade.pnl_percent),
                reason=trade.exit_reason or "target reached",
                mfe=abs(trade.max_favorable_excursion * 100),
                mae=abs(trade.max_adverse_excursion * 100),
                duration=duration,
                lesson=trade.lessons_learned or "patience pays off"
            )
        
            return narrative
        except Exception as e:
            logger.error(f"Error in generate_exit_narrative: {e}")
            raise
    
    def generate_full_narrative(self, trade: TradeEntry) -> str:
        """Generate complete trade narrative"""
        try:
            entry_narrative = self.generate_entry_narrative(trade)
        
            if trade.exit_time:
                exit_narrative = self.generate_exit_narrative(trade)
            
                # Add lesson if available
                lesson = ""
                if trade.lessons_learned:
                    lesson_templates = self.templates['lesson_patterns']
                    lesson_template = lesson_templates[hash(trade.trade_id) % len(lesson_templates)]
                    lesson = " " + lesson_template.format(lesson=trade.lessons_learned)
            
                return f"{entry_narrative}\n\n{exit_narrative}{lesson}"
        
            return entry_narrative
        except Exception as e:
            logger.error(f"Error in generate_full_narrative: {e}")
            raise


class TradeAnalyzer:
    """
    Analyzes trades for patterns and insights
    """
    
    def __init__(self):
        try:
            self.pattern_cache = {}
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def analyze_trade(self, trade: TradeEntry) -> Dict:
        """Analyze a single trade"""
        try:
            analysis = {
                'trade_id': trade.trade_id,
                'outcome': trade.outcome.value,
                'quality_score': self._calculate_quality_score(trade),
                'execution_score': self._calculate_execution_score(trade),
                'risk_management_score': self._calculate_risk_score(trade),
                'emotional_discipline_score': self._calculate_emotional_score(trade),
                'insights': [],
                'recommendations': []
            }
        
            # Generate insights
            if trade.pnl > 0:
                if trade.max_adverse_excursion > 0.02:
                    analysis['insights'].append(
                        "Trade went against you significantly before becoming profitable. "
                        "Consider tighter entries or wider initial stops."
                    )
                if trade.pnl_percent > 2:
                    analysis['insights'].append(
                        "Excellent trade! Consider documenting the setup for future reference."
                    )
            else:
                if trade.max_favorable_excursion > 0.01:
                    analysis['insights'].append(
                        "Trade was profitable at one point. "
                        "Consider trailing stops or partial profit taking."
                    )
                if trade.entry_emotion == TradeEmotion.IMPULSIVE:
                    analysis['insights'].append(
                        "Impulsive entry detected. Wait for confirmation signals."
                    )
        
            # Generate recommendations
            if analysis['quality_score'] < 0.5:
                analysis['recommendations'].append(
                    "Review entry criteria. This trade didn't meet quality standards."
                )
            if analysis['risk_management_score'] < 0.6:
                analysis['recommendations'].append(
                    "Improve risk management. Consider smaller position sizes."
                )
        
            return analysis
        except Exception as e:
            logger.error(f"Error in analyze_trade: {e}")
            raise
    
    def _calculate_quality_score(self, trade: TradeEntry) -> float:
        """Calculate trade quality score (0-1)"""
        try:
            score = 0.0
        
            # Confidence factor
            score += trade.confidence_score * 0.3
        
            # Risk-reward factor
            if trade.risk_reward_ratio >= 2:
                score += 0.3
            elif trade.risk_reward_ratio >= 1.5:
                score += 0.2
            elif trade.risk_reward_ratio >= 1:
                score += 0.1
        
            # Signals factor
            if len(trade.signals_used) >= 3:
                score += 0.2
            elif len(trade.signals_used) >= 2:
                score += 0.1
        
            # Outcome factor
            if trade.outcome == TradeOutcome.WIN:
                score += 0.2
            elif trade.outcome == TradeOutcome.PARTIAL_WIN:
                score += 0.1
        
            return min(1.0, score)
        except Exception as e:
            logger.error(f"Error in _calculate_quality_score: {e}")
            raise
    
    def _calculate_execution_score(self, trade: TradeEntry) -> float:
        """Calculate execution quality score"""
        try:
            score = 0.5  # Base score
        
            # Entry timing
            if trade.max_adverse_excursion < 0.01:
                score += 0.25  # Good entry
            elif trade.max_adverse_excursion < 0.02:
                score += 0.15
        
            # Exit timing
            if trade.pnl > 0 and trade.max_favorable_excursion > 0:
                captured_ratio = trade.pnl_percent / (trade.max_favorable_excursion * 100)
                score += 0.25 * min(1.0, captured_ratio)
        
            return min(1.0, score)
        except Exception as e:
            logger.error(f"Error in _calculate_execution_score: {e}")
            raise
    
    def _calculate_risk_score(self, trade: TradeEntry) -> float:
        """Calculate risk management score"""
        try:
            score = 0.5
        
            # Stop loss set
            if trade.stop_loss > 0:
                score += 0.2
        
            # Position sizing
            if trade.position_size > 0:
                # Assume proper sizing if position exists
                score += 0.15
        
            # Risk-reward
            if trade.risk_reward_ratio >= 1.5:
                score += 0.15
        
            return min(1.0, score)
        except Exception as e:
            logger.error(f"Error in _calculate_risk_score: {e}")
            raise
    
    def _calculate_emotional_score(self, trade: TradeEntry) -> float:
        """Calculate emotional discipline score"""
        try:
            score = 0.5
        
            # Entry emotion
            if trade.entry_emotion in [TradeEmotion.CONFIDENT, TradeEmotion.PATIENT, TradeEmotion.NEUTRAL]:
                score += 0.25
            elif trade.entry_emotion in [TradeEmotion.IMPULSIVE, TradeEmotion.FEARFUL, TradeEmotion.GREEDY]:
                score -= 0.15
        
            # Exit emotion
            if trade.exit_emotion in [TradeEmotion.CONFIDENT, TradeEmotion.PATIENT, TradeEmotion.NEUTRAL]:
                score += 0.25
            elif trade.exit_emotion in [TradeEmotion.IMPULSIVE, TradeEmotion.FEARFUL, TradeEmotion.GREEDY]:
                score -= 0.15
        
            return max(0.0, min(1.0, score))
        except Exception as e:
            logger.error(f"Error in _calculate_emotional_score: {e}")
            raise
    
    def analyze_patterns(self, trades: List[TradeEntry]) -> Dict:
        """Analyze patterns across multiple trades"""
        try:
            if not trades:
                return {'patterns': [], 'statistics': {}}
        
            patterns = {
                'winning_conditions': defaultdict(int),
                'losing_conditions': defaultdict(int),
                'best_signals': defaultdict(lambda: {'wins': 0, 'losses': 0}),
                'time_patterns': defaultdict(lambda: {'wins': 0, 'losses': 0}),
                'emotional_patterns': defaultdict(lambda: {'wins': 0, 'losses': 0})
            }
        
            for trade in trades:
                is_win = trade.pnl > 0
            
                # Market condition patterns
                if is_win:
                    patterns['winning_conditions'][trade.market_condition.value] += 1
                else:
                    patterns['losing_conditions'][trade.market_condition.value] += 1
            
                # Signal patterns
                for signal in trade.signals_used:
                    if is_win:
                        patterns['best_signals'][signal]['wins'] += 1
                    else:
                        patterns['best_signals'][signal]['losses'] += 1
            
                # Time patterns
                if trade.entry_time:
                    hour = trade.entry_time.hour
                    time_slot = f"{hour:02d}:00-{(hour+1):02d}:00"
                    if is_win:
                        patterns['time_patterns'][time_slot]['wins'] += 1
                    else:
                        patterns['time_patterns'][time_slot]['losses'] += 1
            
                # Emotional patterns
                emotion = trade.entry_emotion.value
                if is_win:
                    patterns['emotional_patterns'][emotion]['wins'] += 1
                else:
                    patterns['emotional_patterns'][emotion]['losses'] += 1
        
            # Calculate statistics
            statistics = {
                'total_trades': len(trades),
                'winning_trades': sum(1 for t in trades if t.pnl > 0),
                'losing_trades': sum(1 for t in trades if t.pnl < 0),
                'win_rate': sum(1 for t in trades if t.pnl > 0) / len(trades),
                'average_pnl': np.mean([t.pnl for t in trades]),
                'total_pnl': sum(t.pnl for t in trades),
                'best_trade': max(trades, key=lambda t: t.pnl).pnl,
                'worst_trade': min(trades, key=lambda t: t.pnl).pnl,
                'average_win': np.mean([t.pnl for t in trades if t.pnl > 0]) if any(t.pnl > 0 for t in trades) else 0,
                'average_loss': np.mean([t.pnl for t in trades if t.pnl < 0]) if any(t.pnl < 0 for t in trades) else 0
            }
        
            return {
                'patterns': patterns,
                'statistics': statistics
            }
        except Exception as e:
            logger.error(f"Error in analyze_patterns: {e}")
            raise


class AITradingJournal:
    """
    Complete AI Trading Journal System
    """
    
    def __init__(self, journal_path: str = "trading_journal"):
        try:
            self.journal_path = journal_path
            self.narrative_generator = NarrativeGenerator()
            self.analyzer = TradeAnalyzer()
        
            self.trades: List[TradeEntry] = []
            self.sessions: List[TradingSession] = []
        
            # Create journal directory
            os.makedirs(journal_path, exist_ok=True)
        
            logger.info(f"AI Trading Journal initialized at {journal_path}")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def log_trade(
        self,
        symbol: str,
        direction: str,
        entry_price: float,
        position_size: float,
        stop_loss: float = 0.0,
        take_profit: float = 0.0,
        signals: List[str] = None,
        confidence: float = 0.5,
        market_condition: MarketCondition = MarketCondition.UNCERTAIN,
        entry_emotion: TradeEmotion = TradeEmotion.NEUTRAL,
        entry_reason: str = ""
    ) -> TradeEntry:
        """Log a new trade entry"""
        try:
            trade = TradeEntry(
                trade_id=f"TRADE_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self.trades)}",
                symbol=symbol,
                direction=direction,
                entry_time=datetime.now(),
                entry_price=entry_price,
                position_size=position_size,
                stop_loss=stop_loss,
                take_profit=take_profit,
                signals_used=signals or [],
                confidence_score=confidence,
                market_condition=market_condition,
                entry_emotion=entry_emotion,
                entry_reason=entry_reason
            )
        
            # Calculate risk-reward
            if stop_loss > 0 and take_profit > 0:
                risk = abs(entry_price - stop_loss)
                reward = abs(take_profit - entry_price)
                trade.risk_reward_ratio = reward / risk if risk > 0 else 0
        
            # Generate entry narrative
            trade.narrative = self.narrative_generator.generate_entry_narrative(trade)
        
            self.trades.append(trade)
        
            logger.info(f"📝 Trade logged: {trade.trade_id} - {direction} {symbol} @ {entry_price}")
        
            return trade
        except Exception as e:
            logger.error(f"Error in log_trade: {e}")
            raise
    
    def close_trade(
        self,
        trade_id: str,
        exit_price: float,
        exit_reason: str = "",
        exit_emotion: TradeEmotion = TradeEmotion.NEUTRAL,
        lessons_learned: str = ""
    ) -> Optional[TradeEntry]:
        """Close an existing trade"""
        try:
            trade = next((t for t in self.trades if t.trade_id == trade_id), None)
        
            if not trade:
                logger.warning(f"Trade not found: {trade_id}")
                return None
        
            trade.exit_time = datetime.now()
            trade.exit_price = exit_price
            trade.exit_reason = exit_reason
            trade.exit_emotion = exit_emotion
            trade.lessons_learned = lessons_learned
        
            # Calculate P&L
            if trade.direction == 'BUY':
                trade.pnl = (exit_price - trade.entry_price) * trade.position_size
            else:
                trade.pnl = (trade.entry_price - exit_price) * trade.position_size
        
            trade.pnl_percent = (trade.pnl / (trade.entry_price * trade.position_size)) * 100
        
            # Determine outcome
            if trade.pnl > 0:
                trade.outcome = TradeOutcome.WIN
            elif trade.pnl < 0:
                trade.outcome = TradeOutcome.LOSS
            else:
                trade.outcome = TradeOutcome.BREAKEVEN
        
            # Generate full narrative
            trade.narrative = self.narrative_generator.generate_full_narrative(trade)
        
            logger.info(f"📝 Trade closed: {trade_id} - P&L: ${trade.pnl:.2f} ({trade.pnl_percent:.2f}%)")
        
            return trade
        except Exception as e:
            logger.error(f"Error in close_trade: {e}")
            raise
    
    def get_trade_story(self, trade_id: str) -> str:
        """Get the complete story of a trade"""
        try:
            trade = next((t for t in self.trades if t.trade_id == trade_id), None)
        
            if not trade:
                return "Trade not found"
        
            story = f"""
    ╔══════════════════════════════════════════════════════════════════╗
    ║                        TRADE STORY                                ║
    ╠══════════════════════════════════════════════════════════════════╣
    ║ Trade ID: {trade.trade_id}
    ║ Symbol: {trade.symbol}
    ║ Direction: {trade.direction}
    ║ Entry: ${trade.entry_price:.4f} @ {trade.entry_time.strftime('%Y-%m-%d %H:%M')}
    ║ Exit: ${trade.exit_price:.4f} @ {trade.exit_time.strftime('%Y-%m-%d %H:%M') if trade.exit_time else 'Open'}
    ║ P&L: ${trade.pnl:.2f} ({trade.pnl_percent:.2f}%)
    ║ Outcome: {trade.outcome.value}
    ╠══════════════════════════════════════════════════════════════════╣
    ║ THE STORY:
    ║ {trade.narrative}
    ╠══════════════════════════════════════════════════════════════════╣
    ║ SIGNALS USED: {', '.join(trade.signals_used)}
    ║ MARKET CONDITION: {trade.market_condition.value}
    ║ CONFIDENCE: {trade.confidence_score * 100:.0f}%
    ║ RISK/REWARD: {trade.risk_reward_ratio:.2f}
    ╠══════════════════════════════════════════════════════════════════╣
    ║ EMOTIONAL STATE:
    ║ Entry: {trade.entry_emotion.value}
    ║ Exit: {trade.exit_emotion.value}
    ╠══════════════════════════════════════════════════════════════════╣
    ║ LESSONS LEARNED:
    ║ {trade.lessons_learned or 'No lessons recorded'}
    ╚══════════════════════════════════════════════════════════════════╝
    """
            return story
        except Exception as e:
            logger.error(f"Error in get_trade_story: {e}")
            raise
    
    def get_daily_summary(self, date: datetime = None) -> Dict:
        """Get daily trading summary"""
        try:
            if date is None:
                date = datetime.now()
        
            day_start = date.replace(hour=0, minute=0, second=0, microsecond=0)
            day_end = day_start + timedelta(days=1)
        
            day_trades = [
                t for t in self.trades
                if day_start <= t.entry_time < day_end
            ]
        
            if not day_trades:
                return {
                    'date': date.strftime('%Y-%m-%d'),
                    'total_trades': 0,
                    'message': 'No trades on this day'
                }
        
            analysis = self.analyzer.analyze_patterns(day_trades)
        
            summary = {
                'date': date.strftime('%Y-%m-%d'),
                'total_trades': len(day_trades),
                'winning_trades': sum(1 for t in day_trades if t.pnl > 0),
                'losing_trades': sum(1 for t in day_trades if t.pnl < 0),
                'total_pnl': sum(t.pnl for t in day_trades),
                'win_rate': sum(1 for t in day_trades if t.pnl > 0) / len(day_trades),
                'best_trade': max(day_trades, key=lambda t: t.pnl),
                'worst_trade': min(day_trades, key=lambda t: t.pnl),
                'patterns': analysis['patterns'],
                'statistics': analysis['statistics']
            }
        
            return summary
        except Exception as e:
            logger.error(f"Error in get_daily_summary: {e}")
            raise
    
    def get_performance_insights(self) -> Dict:
        """Get performance insights and recommendations"""
        try:
            if not self.trades:
                return {'message': 'No trades to analyze'}
        
            analysis = self.analyzer.analyze_patterns(self.trades)
        
            insights = {
                'overall_statistics': analysis['statistics'],
                'patterns': analysis['patterns'],
                'recommendations': [],
                'strengths': [],
                'weaknesses': []
            }
        
            # Analyze win rate
            win_rate = analysis['statistics']['win_rate']
            if win_rate >= 0.6:
                insights['strengths'].append(f"Strong win rate: {win_rate:.1%}")
            elif win_rate < 0.4:
                insights['weaknesses'].append(f"Low win rate: {win_rate:.1%}")
                insights['recommendations'].append("Focus on trade quality over quantity")
        
            # Analyze risk-reward
            avg_win = analysis['statistics']['average_win']
            avg_loss = abs(analysis['statistics']['average_loss'])
            if avg_loss > 0:
                profit_factor = avg_win / avg_loss
                if profit_factor >= 1.5:
                    insights['strengths'].append(f"Good profit factor: {profit_factor:.2f}")
                elif profit_factor < 1:
                    insights['weaknesses'].append(f"Poor profit factor: {profit_factor:.2f}")
                    insights['recommendations'].append("Let winners run longer, cut losses faster")
        
            # Analyze best conditions
            winning_conditions = analysis['patterns']['winning_conditions']
            if winning_conditions:
                best_condition = max(winning_conditions, key=winning_conditions.get)
                insights['strengths'].append(f"Best performance in {best_condition} markets")
        
            # Analyze emotional patterns
            emotional_patterns = analysis['patterns']['emotional_patterns']
            for emotion, stats in emotional_patterns.items():
                total = stats['wins'] + stats['losses']
                if total >= 5:
                    wr = stats['wins'] / total
                    if wr < 0.4:
                        insights['weaknesses'].append(f"Poor performance when {emotion}: {wr:.1%} win rate")
                        insights['recommendations'].append(f"Avoid trading when feeling {emotion}")
        
            return insights
        except Exception as e:
            logger.error(f"Error in get_performance_insights: {e}")
            raise
    
    def export_journal(self, format: str = 'json') -> str:
        """Export journal to file"""
        try:
            filename = f"{self.journal_path}/journal_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{format}"
        
            if format == 'json':
                data = {
                    'trades': [
                        {
                            'trade_id': t.trade_id,
                            'symbol': t.symbol,
                            'direction': t.direction,
                            'entry_time': t.entry_time.isoformat(),
                            'exit_time': t.exit_time.isoformat() if t.exit_time else None,
                            'entry_price': t.entry_price,
                            'exit_price': t.exit_price,
                            'pnl': t.pnl,
                            'pnl_percent': t.pnl_percent,
                            'outcome': t.outcome.value,
                            'narrative': t.narrative,
                            'lessons_learned': t.lessons_learned
                        }
                        for t in self.trades
                    ],
                    'statistics': self.analyzer.analyze_patterns(self.trades)['statistics'] if self.trades else {}
                }
            
                with open(filename, 'w') as f:
                    json.dump(data, f, indent=2)
        
            logger.info(f"Journal exported to {filename}")
            return filename
        except Exception as e:
            logger.error(f"Error in export_journal: {e}")
            raise
    
    def get_journal_report(self) -> Dict:
        """Get comprehensive journal report"""
        return {
            'total_trades': len(self.trades),
            'open_trades': sum(1 for t in self.trades if t.exit_time is None),
            'closed_trades': sum(1 for t in self.trades if t.exit_time is not None),
            'total_pnl': sum(t.pnl for t in self.trades),
            'insights': self.get_performance_insights(),
            'recent_trades': [
                {
                    'trade_id': t.trade_id,
                    'symbol': t.symbol,
                    'pnl': t.pnl,
                    'outcome': t.outcome.value
                }
                for t in self.trades[-10:]
            ]
        }


# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Create journal
    journal = AITradingJournal()
    
    # Log some trades
    trade1 = journal.log_trade(
        symbol="EURUSD",
        direction="BUY",
        entry_price=1.0850,
        position_size=10000,
        stop_loss=1.0800,
        take_profit=1.0950,
        signals=["RSI oversold", "MACD bullish cross", "Support level"],
        confidence=0.75,
        market_condition=MarketCondition.TRENDING_UP,
        entry_emotion=TradeEmotion.CONFIDENT,
        entry_reason="Strong bullish setup with multiple confirmations"
    )
    
    # Close trade
    journal.close_trade(
        trade_id=trade1.trade_id,
        exit_price=1.0920,
        exit_reason="Take profit hit",
        exit_emotion=TradeEmotion.PATIENT,
        lessons_learned="Patience paid off - let the trade reach target"
    )
    
    # Get trade story
    print(journal.get_trade_story(trade1.trade_id))
    
    # Get insights
    insights = journal.get_performance_insights()
    print("\n" + "="*60)
    logger.info("PERFORMANCE INSIGHTS")
    print("="*60)
    logger.info(f"Strengths: {insights.get('strengths', [])}")
    logger.info(f"Weaknesses: {insights.get('weaknesses', [])}")
    logger.info(f"Recommendations: {insights.get('recommendations', [])}")
