"""
Self-Programming Proposer
==========================

AI engine that continuously proposes improvements to the trading system.
Analyzes performance, identifies weaknesses, and generates improvement code.

Features:
1. Performance analysis
2. Weakness identification
3. Improvement generation
4. Code synthesis
5. Experiment proposal

Author: AlphaAlgo Trading System
"""

import asyncio
import hashlib
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from enum import Enum, auto
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Tuple
import uuid
import random

logger = logging.getLogger(__name__)


class ImprovementType(Enum):
    """Types of improvements."""
    STRATEGY_ENHANCEMENT = "strategy_enhancement"
    NEW_INDICATOR = "new_indicator"
    RISK_OPTIMIZATION = "risk_optimization"
    EXECUTION_IMPROVEMENT = "execution_improvement"
    FEATURE_ENGINEERING = "feature_engineering"
    MODEL_ARCHITECTURE = "model_architecture"
    PARAMETER_TUNING = "parameter_tuning"
    BUG_FIX = "bug_fix"
    PERFORMANCE_OPTIMIZATION = "performance_optimization"
    NEW_STRATEGY = "new_strategy"


class ImprovementStatus(Enum):
    """Status of an improvement proposal."""
    PROPOSED = auto()
    ANALYZING = auto()
    CODE_GENERATED = auto()
    SAFETY_REVIEW = auto()
    APPROVED = auto()
    REJECTED = auto()
    EXPERIMENTING = auto()
    VALIDATED = auto()
    PROMOTED = auto()
    FAILED = auto()


class ImprovementPriority(Enum):
    """Priority levels for improvements."""
    CRITICAL = 1
    HIGH = 2
    MEDIUM = 3
    LOW = 4
    EXPLORATORY = 5


@dataclass
class PerformanceAnalysis:
    """Analysis of system performance."""
    analysis_id: str
    analyzed_at: datetime
    
    # Overall Metrics
    sharpe_ratio: float
    sortino_ratio: float
    max_drawdown: float
    win_rate: float
    profit_factor: float
    total_return: float
    
    # Weaknesses Identified
    weaknesses: List[Dict[str, Any]] = field(default_factory=list)
    
    # Strengths Identified
    strengths: List[Dict[str, Any]] = field(default_factory=list)
    
    # Recommendations
    recommendations: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'analysis_id': self.analysis_id,
            'analyzed_at': self.analyzed_at.isoformat(),
            'sharpe_ratio': self.sharpe_ratio,
            'sortino_ratio': self.sortino_ratio,
            'max_drawdown': self.max_drawdown,
            'win_rate': self.win_rate,
            'profit_factor': self.profit_factor,
            'total_return': self.total_return,
            'weaknesses': self.weaknesses,
            'strengths': self.strengths,
            'recommendations': self.recommendations,
        }


@dataclass
class Improvement:
    """An improvement proposal."""
    improvement_id: str
    improvement_type: ImprovementType
    priority: ImprovementPriority
    
    # Description
    title: str
    description: str
    rationale: str
    expected_impact: str
    
    # Source
    source_analysis_id: Optional[str] = None
    triggered_by: str = "autonomous"  # 'autonomous', 'performance', 'user'
    
    # Status
    status: ImprovementStatus = ImprovementStatus.PROPOSED
    proposed_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Generated Code
    code: Optional[str] = None
    code_hash: Optional[str] = None
    code_generated_at: Optional[datetime] = None
    
    # Experiment
    experiment_id: Optional[str] = None
    experiment_results: Optional[Dict[str, Any]] = None
    
    # Metrics
    estimated_improvement: float = 0.0  # Estimated % improvement
    actual_improvement: Optional[float] = None
    confidence: float = 0.5
    
    # Review
    safety_review_passed: bool = False
    review_notes: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'improvement_id': self.improvement_id,
            'improvement_type': self.improvement_type.value,
            'priority': self.priority.name,
            'title': self.title,
            'description': self.description,
            'rationale': self.rationale,
            'expected_impact': self.expected_impact,
            'status': self.status.name,
            'proposed_at': self.proposed_at.isoformat(),
            'code_hash': self.code_hash,
            'experiment_id': self.experiment_id,
            'estimated_improvement': self.estimated_improvement,
            'actual_improvement': self.actual_improvement,
            'confidence': self.confidence,
            'safety_review_passed': self.safety_review_passed,
        }


@dataclass
class CodeTemplate:
    """Template for code generation."""
    template_id: str
    improvement_type: ImprovementType
    template: str
    parameters: Dict[str, Any]
    description: str


class PerformanceAnalyzer:
    """Analyzes trading system performance."""
    
    def __init__(self):
        self._analysis_history: List[PerformanceAnalysis] = []
    
    async def analyze(
        self,
        trade_history: List[Dict],
        positions: Dict[str, Dict],
        metrics: Dict[str, float],
    ) -> PerformanceAnalysis:
        """Analyze system performance."""
        analysis_id = f"ANAL-{uuid.uuid4().hex[:8]}"
        
        # Extract metrics
        sharpe = metrics.get('sharpe_ratio', 0)
        sortino = metrics.get('sortino_ratio', 0)
        max_dd = metrics.get('max_drawdown', 0)
        win_rate = metrics.get('win_rate', 0)
        profit_factor = metrics.get('profit_factor', 0)
        total_return = metrics.get('total_return', 0)
        
        # Identify weaknesses
        weaknesses = []
        
        if sharpe < 1.5:
            weaknesses.append({
                'area': 'risk_adjusted_returns',
                'metric': 'sharpe_ratio',
                'current': sharpe,
                'target': 2.0,
                'severity': 'high' if sharpe < 1.0 else 'medium',
            })
        
        if max_dd > 0.15:
            weaknesses.append({
                'area': 'risk_management',
                'metric': 'max_drawdown',
                'current': max_dd,
                'target': 0.10,
                'severity': 'high' if max_dd > 0.20 else 'medium',
            })
        
        if win_rate < 0.55:
            weaknesses.append({
                'area': 'signal_quality',
                'metric': 'win_rate',
                'current': win_rate,
                'target': 0.60,
                'severity': 'medium',
            })
        
        if profit_factor < 1.5:
            weaknesses.append({
                'area': 'profit_management',
                'metric': 'profit_factor',
                'current': profit_factor,
                'target': 2.0,
                'severity': 'medium' if profit_factor > 1.2 else 'high',
            })
        
        # Identify strengths
        strengths = []
        
        if sharpe > 2.0:
            strengths.append({
                'area': 'risk_adjusted_returns',
                'metric': 'sharpe_ratio',
                'value': sharpe,
            })
        
        if win_rate > 0.65:
            strengths.append({
                'area': 'signal_quality',
                'metric': 'win_rate',
                'value': win_rate,
            })
        
        # Generate recommendations
        recommendations = []
        
        for weakness in weaknesses:
            if weakness['area'] == 'risk_adjusted_returns':
                recommendations.append("Improve signal quality or reduce position sizes")
            elif weakness['area'] == 'risk_management':
                recommendations.append("Implement tighter stop losses or reduce leverage")
            elif weakness['area'] == 'signal_quality':
                recommendations.append("Add confirmation indicators or filter low-quality signals")
            elif weakness['area'] == 'profit_management':
                recommendations.append("Optimize take-profit levels or improve exit timing")
        
        analysis = PerformanceAnalysis(
            analysis_id=analysis_id,
            analyzed_at=datetime.now(timezone.utc),
            sharpe_ratio=sharpe,
            sortino_ratio=sortino,
            max_drawdown=max_dd,
            win_rate=win_rate,
            profit_factor=profit_factor,
            total_return=total_return,
            weaknesses=weaknesses,
            strengths=strengths,
            recommendations=recommendations,
        )
        
        self._analysis_history.append(analysis)
        
        return analysis


class CodeGenerator:
    """Generates improvement code."""
    
    # Code templates for different improvement types
    TEMPLATES = {
        ImprovementType.NEW_INDICATOR: '''
def {name}(data: pd.DataFrame, period: int = {period}) -> pd.Series:
    """
    {description}
    
    Args:
        data: OHLCV DataFrame
        period: Lookback period
    
    Returns:
        Indicator values
    """
    {implementation}
    return result
''',
        ImprovementType.STRATEGY_ENHANCEMENT: '''
def enhanced_signal(data: pd.DataFrame, base_signal: pd.Series, **params) -> pd.Series:
    """
    {description}
    
    Enhances base signal with additional filters.
    """
    signal = base_signal.copy()
    
    {enhancement_logic}
    
    return signal
''',
        ImprovementType.RISK_OPTIMIZATION: '''
def optimized_position_size(
    equity: float,
    signal_strength: float,
    volatility: float,
    max_risk: float = {max_risk},
) -> float:
    """
    {description}
    
    Calculates optimized position size based on risk parameters.
    """
    {sizing_logic}
    
    return position_size
''',
        ImprovementType.FEATURE_ENGINEERING: '''
def create_features(data: pd.DataFrame) -> pd.DataFrame:
    """
    {description}
    
    Creates new features for ML models.
    """
    features = pd.DataFrame(index=data.index)
    
    {feature_logic}
    
    return features
''',
    }
    
    def __init__(self):
        self._generated_code: Dict[str, str] = {}
    
    async def generate_code(
        self,
        improvement: Improvement,
        context: Dict[str, Any],
    ) -> str:
        """Generate code for an improvement."""
        imp_type = improvement.improvement_type
        
        if imp_type == ImprovementType.NEW_INDICATOR:
            return self._generate_indicator_code(improvement, context)
        elif imp_type == ImprovementType.STRATEGY_ENHANCEMENT:
            return self._generate_enhancement_code(improvement, context)
        elif imp_type == ImprovementType.RISK_OPTIMIZATION:
            return self._generate_risk_code(improvement, context)
        elif imp_type == ImprovementType.FEATURE_ENGINEERING:
            return self._generate_feature_code(improvement, context)
        elif imp_type == ImprovementType.PARAMETER_TUNING:
            return self._generate_tuning_code(improvement, context)
        else:
            return self._generate_generic_code(improvement, context)
    
    def _generate_indicator_code(self, improvement: Improvement, context: Dict) -> str:
        """Generate indicator code."""
        name = improvement.title.lower().replace(' ', '_')
        period = context.get('period', 14)
        
        # Generate implementation based on description
        if 'momentum' in improvement.description.lower():
            implementation = '''
    returns = data['close'].pct_change(period)
    result = returns.rolling(window=period).mean()
'''
        elif 'volatility' in improvement.description.lower():
            implementation = '''
    returns = data['close'].pct_change()
    result = returns.rolling(window=period).std() * (252 ** 0.5)
'''
        elif 'trend' in improvement.description.lower():
            implementation = '''
    ema_fast = data['close'].ewm(span=period, adjust=False).mean()
    ema_slow = data['close'].ewm(span=period*2, adjust=False).mean()
    result = (ema_fast - ema_slow) / ema_slow
'''
        else:
            implementation = '''
    result = data['close'].rolling(window=period).mean()
'''
        
        code = self.TEMPLATES[ImprovementType.NEW_INDICATOR].format(
            name=name,
            period=period,
            description=improvement.description,
            implementation=implementation,
        )
        
        return code
    
    def _generate_enhancement_code(self, improvement: Improvement, context: Dict) -> str:
        """Generate strategy enhancement code."""
        enhancement_logic = '''
    # Volume filter
    avg_volume = data['volume'].rolling(window=20).mean()
    volume_filter = data['volume'] > avg_volume * 1.5
    
    # Trend filter
    sma_50 = data['close'].rolling(window=50).mean()
    trend_filter = data['close'] > sma_50
    
    # Apply filters
    signal = signal.where(volume_filter & trend_filter, 0)
'''
        
        code = self.TEMPLATES[ImprovementType.STRATEGY_ENHANCEMENT].format(
            description=improvement.description,
            enhancement_logic=enhancement_logic,
        )
        
        return code
    
    def _generate_risk_code(self, improvement: Improvement, context: Dict) -> str:
        """Generate risk optimization code."""
        max_risk = context.get('max_risk', 0.02)
        
        sizing_logic = '''
    # Kelly criterion with safety factor
    win_prob = 0.55  # Estimated win probability
    win_loss_ratio = 1.5  # Average win / average loss
    
    kelly = win_prob - ((1 - win_prob) / win_loss_ratio)
    kelly_fraction = kelly * 0.5  # Half Kelly for safety
    
    # Volatility adjustment
    vol_adjustment = 0.02 / max(volatility, 0.01)
    
    # Signal strength adjustment
    strength_factor = min(1.0, signal_strength)
    
    # Calculate position size
    base_size = equity * max_risk * kelly_fraction
    position_size = base_size * vol_adjustment * strength_factor
    
    # Apply limits
    position_size = min(position_size, equity * 0.1)  # Max 10% per position
'''
        
        code = self.TEMPLATES[ImprovementType.RISK_OPTIMIZATION].format(
            description=improvement.description,
            max_risk=max_risk,
            sizing_logic=sizing_logic,
        )
        
        return code
    
    def _generate_feature_code(self, improvement: Improvement, context: Dict) -> str:
        """Generate feature engineering code."""
        feature_logic = '''
    # Price-based features
    features['returns_1d'] = data['close'].pct_change(1)
    features['returns_5d'] = data['close'].pct_change(5)
    features['returns_20d'] = data['close'].pct_change(20)
    
    # Volatility features
    features['volatility_10d'] = data['close'].pct_change().rolling(10).std()
    features['volatility_20d'] = data['close'].pct_change().rolling(20).std()
    
    # Momentum features
    features['rsi_14'] = calculate_rsi(data['close'], 14)
    features['momentum_10'] = data['close'] / data['close'].shift(10) - 1
    
    # Volume features
    features['volume_ratio'] = data['volume'] / data['volume'].rolling(20).mean()
    
    # Technical features
    features['distance_from_high'] = data['close'] / data['high'].rolling(20).max() - 1
    features['distance_from_low'] = data['close'] / data['low'].rolling(20).min() - 1
'''
        
        code = self.TEMPLATES[ImprovementType.FEATURE_ENGINEERING].format(
            description=improvement.description,
            feature_logic=feature_logic,
        )
        
        return code
    
    def _generate_tuning_code(self, improvement: Improvement, context: Dict) -> str:
        """Generate parameter tuning code."""
        return f'''
# Parameter Tuning: {improvement.title}
# {improvement.description}

OPTIMIZED_PARAMETERS = {{
    'fast_period': 8,
    'slow_period': 21,
    'signal_threshold': 0.02,
    'stop_loss_pct': 0.03,
    'take_profit_pct': 0.06,
    'position_size_pct': 0.02,
}}

def apply_optimized_parameters(strategy):
    """Apply optimized parameters to strategy."""
    for param, value in OPTIMIZED_PARAMETERS.items():
        if hasattr(strategy, param):
            setattr(strategy, param, value)
    return strategy
'''
    
    def _generate_generic_code(self, improvement: Improvement, context: Dict) -> str:
        """Generate generic improvement code."""
        return f'''
# Improvement: {improvement.title}
# Type: {improvement.improvement_type.value}
# {improvement.description}

def apply_improvement(**kwargs):
    """
    {improvement.rationale}
    
    Expected impact: {improvement.expected_impact}
    """
    # Implementation placeholder
    result = {{
        'applied': True,
        'improvement_id': '{improvement.improvement_id}',
    }}
    return result
'''


class SelfProgrammingProposer:
    """
    AI engine that continuously proposes improvements.
    
    Analyzes system performance, identifies areas for improvement,
    generates code, and proposes experiments to validate improvements.
    """
    
    def __init__(self, storage_path: str = "self_programming"):
        """
        Initialize the self-programming proposer.
        
        Args:
            storage_path: Path for storage
        """
        self._analyzer = PerformanceAnalyzer()
        self._generator = CodeGenerator()
        
        # Improvements
        self._improvements: Dict[str, Improvement] = {}
        
        # Indices
        self._by_status: Dict[ImprovementStatus, Set[str]] = {s: set() for s in ImprovementStatus}
        self._by_type: Dict[ImprovementType, Set[str]] = {t: set() for t in ImprovementType}
        self._by_priority: Dict[ImprovementPriority, Set[str]] = {p: set() for p in ImprovementPriority}
        
        # Analysis history
        self._analyses: List[PerformanceAnalysis] = []
        
        # Callbacks
        self._proposal_callbacks: List[Callable] = []
        
        # Running state
        self._is_running = False
        self._proposal_task: Optional[asyncio.Task] = None
        
        # Configuration
        self._proposal_interval = 3600  # 1 hour
        self._max_active_proposals = 10
        
        # Statistics
        self._stats = {
            'total_analyses': 0,
            'total_proposals': 0,
            'code_generated': 0,
            'experiments_created': 0,
            'improvements_promoted': 0,
        }
        
        # Storage
        self._storage_path = Path(storage_path)
        self._storage_path.mkdir(parents=True, exist_ok=True)
        
        logger.info("SelfProgrammingProposer initialized")
    
    async def start(self):
        """Start the proposer."""
        self._is_running = True
        self._proposal_task = asyncio.create_task(self._proposal_loop())
        logger.info("SelfProgrammingProposer started")
    
    async def stop(self):
        """Stop the proposer."""
        self._is_running = False
        if self._proposal_task:
            self._proposal_task.cancel()
            try:
                await self._proposal_task
            except asyncio.CancelledError:
                pass
        logger.info("SelfProgrammingProposer stopped")
    
    async def _proposal_loop(self):
        """Main proposal loop."""
        while self._is_running:
            try:
                # Analyze performance
                analysis = await self._analyze_performance()
                
                # Generate proposals based on analysis
                await self._generate_proposals(analysis)
                
                # Generate code for pending proposals
                await self._generate_pending_code()
                
                await asyncio.sleep(self._proposal_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Proposal loop error: {e}")
                await asyncio.sleep(300)
    
    async def _analyze_performance(self) -> PerformanceAnalysis:
        """Analyze current system performance."""
        # Get performance data (simulated)
        metrics = await self._get_performance_metrics()
        trade_history = await self._get_trade_history()
        positions = await self._get_positions()
        
        analysis = await self._analyzer.analyze(trade_history, positions, metrics)
        
        self._analyses.append(analysis)
        self._stats['total_analyses'] += 1
        
        return analysis
    
    async def _get_performance_metrics(self) -> Dict[str, float]:
        """Get current performance metrics (simulated)."""
        return {
            'sharpe_ratio': random.uniform(0.8, 2.5),
            'sortino_ratio': random.uniform(1.0, 3.0),
            'max_drawdown': random.uniform(0.05, 0.25),
            'win_rate': random.uniform(0.45, 0.70),
            'profit_factor': random.uniform(1.0, 2.5),
            'total_return': random.uniform(-0.10, 0.50),
        }
    
    async def _get_trade_history(self) -> List[Dict]:
        """Get trade history (simulated)."""
        return []
    
    async def _get_positions(self) -> Dict[str, Dict]:
        """Get current positions (simulated)."""
        return {}
    
    async def _generate_proposals(self, analysis: PerformanceAnalysis):
        """Generate improvement proposals based on analysis."""
        # Check limits
        active_count = len(self._by_status[ImprovementStatus.PROPOSED])
        if active_count >= self._max_active_proposals:
            return
        
        # Generate proposals for each weakness
        for weakness in analysis.weaknesses:
            improvement = await self._create_improvement_for_weakness(weakness, analysis)
            if improvement:
                await self._register_improvement(improvement)
        
        # Generate exploratory proposals
        if random.random() < 0.2:  # 20% chance
            exploratory = await self._create_exploratory_improvement()
            if exploratory:
                await self._register_improvement(exploratory)
    
    async def _create_improvement_for_weakness(
        self,
        weakness: Dict[str, Any],
        analysis: PerformanceAnalysis,
    ) -> Optional[Improvement]:
        """Create improvement proposal for a weakness."""
        area = weakness.get('area', '')
        severity = weakness.get('severity', 'medium')
        
        # Determine improvement type and priority
        if area == 'risk_adjusted_returns':
            imp_type = ImprovementType.STRATEGY_ENHANCEMENT
            title = "Enhance Signal Quality for Better Risk-Adjusted Returns"
            description = "Add confirmation filters to improve signal quality and reduce false positives"
            rationale = f"Current Sharpe ratio ({weakness.get('current', 0):.2f}) is below target"
            expected_impact = "Expected 20-30% improvement in Sharpe ratio"
            
        elif area == 'risk_management':
            imp_type = ImprovementType.RISK_OPTIMIZATION
            title = "Optimize Risk Management Parameters"
            description = "Implement dynamic position sizing based on volatility and drawdown"
            rationale = f"Current max drawdown ({weakness.get('current', 0):.1%}) exceeds target"
            expected_impact = "Expected 30-40% reduction in max drawdown"
            
        elif area == 'signal_quality':
            imp_type = ImprovementType.NEW_INDICATOR
            title = "Add Confirmation Indicator"
            description = "Create new indicator to filter low-quality signals"
            rationale = f"Current win rate ({weakness.get('current', 0):.1%}) needs improvement"
            expected_impact = "Expected 10-15% improvement in win rate"
            
        elif area == 'profit_management':
            imp_type = ImprovementType.PARAMETER_TUNING
            title = "Optimize Take-Profit Parameters"
            description = "Tune take-profit levels for better profit capture"
            rationale = f"Current profit factor ({weakness.get('current', 0):.2f}) is suboptimal"
            expected_impact = "Expected 15-25% improvement in profit factor"
            
        else:
            return None
        
        priority = ImprovementPriority.HIGH if severity == 'high' else ImprovementPriority.MEDIUM
        
        improvement = Improvement(
            improvement_id=f"IMP-{uuid.uuid4().hex[:12]}",
            improvement_type=imp_type,
            priority=priority,
            title=title,
            description=description,
            rationale=rationale,
            expected_impact=expected_impact,
            source_analysis_id=analysis.analysis_id,
            triggered_by='performance',
            estimated_improvement=random.uniform(0.10, 0.30),
            confidence=0.6 + random.uniform(0, 0.3),
        )
        
        return improvement
    
    async def _create_exploratory_improvement(self) -> Optional[Improvement]:
        """Create an exploratory improvement proposal."""
        exploratory_ideas = [
            {
                'type': ImprovementType.FEATURE_ENGINEERING,
                'title': "Create Advanced Feature Set",
                'description': "Engineer new features combining price, volume, and volatility data",
            },
            {
                'type': ImprovementType.NEW_INDICATOR,
                'title': "Develop Custom Momentum Indicator",
                'description': "Create momentum indicator optimized for current market conditions",
            },
            {
                'type': ImprovementType.MODEL_ARCHITECTURE,
                'title': "Experiment with Ensemble Models",
                'description': "Combine multiple models for more robust predictions",
            },
            {
                'type': ImprovementType.NEW_STRATEGY,
                'title': "Explore Mean Reversion Strategy",
                'description': "Develop mean reversion strategy for range-bound markets",
            },
        ]
        
        idea = random.choice(exploratory_ideas)
        
        improvement = Improvement(
            improvement_id=f"IMP-{uuid.uuid4().hex[:12]}",
            improvement_type=idea['type'],
            priority=ImprovementPriority.EXPLORATORY,
            title=idea['title'],
            description=idea['description'],
            rationale="Exploratory improvement to discover new alpha sources",
            expected_impact="Potential for significant improvement if successful",
            triggered_by='autonomous',
            estimated_improvement=random.uniform(0.05, 0.20),
            confidence=0.4 + random.uniform(0, 0.2),
        )
        
        return improvement
    
    async def _register_improvement(self, improvement: Improvement):
        """Register a new improvement proposal."""
        self._improvements[improvement.improvement_id] = improvement
        
        # Update indices
        self._by_status[ImprovementStatus.PROPOSED].add(improvement.improvement_id)
        self._by_type[improvement.improvement_type].add(improvement.improvement_id)
        self._by_priority[improvement.priority].add(improvement.improvement_id)
        
        self._stats['total_proposals'] += 1
        
        # Notify callbacks
        for callback in self._proposal_callbacks:
            try:
                await callback(improvement)
            except Exception as e:
                logger.error(f"Proposal callback error: {e}")
        
        # Persist
        await self._persist_improvement(improvement)
        
        logger.info(
            f"Proposed improvement: {improvement.improvement_id} - "
            f"{improvement.title} ({improvement.priority.name})"
        )
    
    async def _generate_pending_code(self):
        """Generate code for pending improvements."""
        pending = list(self._by_status[ImprovementStatus.PROPOSED])
        
        for imp_id in pending[:5]:  # Process up to 5 at a time
            improvement = self._improvements.get(imp_id)
            if not improvement:
                continue
            
            try:
                # Generate code
                code = await self._generator.generate_code(
                    improvement,
                    context={'period': 14, 'max_risk': 0.02},
                )
                
                improvement.code = code
                improvement.code_hash = hashlib.sha256(code.encode()).hexdigest()
                improvement.code_generated_at = datetime.now(timezone.utc)
                
                await self._update_status(imp_id, ImprovementStatus.CODE_GENERATED)
                
                self._stats['code_generated'] += 1
                
                logger.info(f"Generated code for {imp_id}")
                
            except Exception as e:
                logger.error(f"Code generation failed for {imp_id}: {e}")
    
    async def _update_status(self, improvement_id: str, new_status: ImprovementStatus):
        """Update improvement status."""
        improvement = self._improvements.get(improvement_id)
        if not improvement:
            return
        
        old_status = improvement.status
        
        self._by_status[old_status].discard(improvement_id)
        self._by_status[new_status].add(improvement_id)
        
        improvement.status = new_status
    
    async def submit_for_safety_review(self, improvement_id: str) -> bool:
        """Submit improvement for safety review."""
        improvement = self._improvements.get(improvement_id)
        if not improvement:
            return False
        
        if improvement.status != ImprovementStatus.CODE_GENERATED:
            return False
        
        await self._update_status(improvement_id, ImprovementStatus.SAFETY_REVIEW)
        
        return True
    
    async def complete_safety_review(
        self,
        improvement_id: str,
        passed: bool,
        notes: List[str],
    ) -> bool:
        """Complete safety review for improvement."""
        improvement = self._improvements.get(improvement_id)
        if not improvement:
            return False
        
        improvement.safety_review_passed = passed
        improvement.review_notes = notes
        
        if passed:
            await self._update_status(improvement_id, ImprovementStatus.APPROVED)
        else:
            await self._update_status(improvement_id, ImprovementStatus.REJECTED)
        
        return True
    
    async def create_experiment(
        self,
        improvement_id: str,
        experiment_id: str,
    ) -> bool:
        """Link improvement to an experiment."""
        improvement = self._improvements.get(improvement_id)
        if not improvement:
            return False
        
        improvement.experiment_id = experiment_id
        await self._update_status(improvement_id, ImprovementStatus.EXPERIMENTING)
        
        self._stats['experiments_created'] += 1
        
        return True
    
    async def record_experiment_results(
        self,
        improvement_id: str,
        results: Dict[str, Any],
        actual_improvement: float,
    ) -> bool:
        """Record experiment results for improvement."""
        improvement = self._improvements.get(improvement_id)
        if not improvement:
            return False
        
        improvement.experiment_results = results
        improvement.actual_improvement = actual_improvement
        
        # Determine if validated
        if actual_improvement > 0 and actual_improvement >= improvement.estimated_improvement * 0.5:
            await self._update_status(improvement_id, ImprovementStatus.VALIDATED)
        else:
            await self._update_status(improvement_id, ImprovementStatus.FAILED)
        
        return True
    
    async def mark_promoted(self, improvement_id: str) -> bool:
        """Mark improvement as promoted to production."""
        improvement = self._improvements.get(improvement_id)
        if not improvement:
            return False
        
        await self._update_status(improvement_id, ImprovementStatus.PROMOTED)
        self._stats['improvements_promoted'] += 1
        
        return True
    
    async def _persist_improvement(self, improvement: Improvement):
        """Persist improvement to disk."""
        try:
            imp_file = self._storage_path / f"{improvement.improvement_id}.json"
            
            data = improvement.to_dict()
            if improvement.code:
                data['code'] = improvement.code
            
            with open(imp_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to persist improvement: {e}")
    
    def get_improvement(self, improvement_id: str) -> Optional[Improvement]:
        """Get improvement by ID."""
        return self._improvements.get(improvement_id)
    
    def get_improvements_by_status(self, status: ImprovementStatus) -> List[Improvement]:
        """Get improvements by status."""
        return [self._improvements[iid] for iid in self._by_status.get(status, set())]
    
    def get_improvements_by_priority(self, priority: ImprovementPriority) -> List[Improvement]:
        """Get improvements by priority."""
        return [self._improvements[iid] for iid in self._by_priority.get(priority, set())]
    
    def get_pending_improvements(self) -> List[Improvement]:
        """Get all pending improvements sorted by priority."""
        pending = []
        for priority in ImprovementPriority:
            pending.extend(self.get_improvements_by_priority(priority))
        
        return [imp for imp in pending if imp.status in [
            ImprovementStatus.PROPOSED,
            ImprovementStatus.CODE_GENERATED,
            ImprovementStatus.APPROVED,
        ]]
    
    def register_proposal_callback(self, callback: Callable):
        """Register callback for new proposals."""
        self._proposal_callbacks.append(callback)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get proposer statistics."""
        status_counts = {s.name: len(ids) for s, ids in self._by_status.items()}
        type_counts = {t.value: len(ids) for t, ids in self._by_type.items()}
        
        return {
            **self._stats,
            'total_improvements': len(self._improvements),
            'by_status': status_counts,
            'by_type': type_counts,
            'total_analyses': len(self._analyses),
        }
