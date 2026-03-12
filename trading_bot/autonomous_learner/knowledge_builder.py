"""
Knowledge Builder - Builds Structured Knowledge from Research

Processes raw research into structured, actionable trading knowledge:
- Extracts key concepts and relationships
- Builds knowledge graphs
- Creates learning summaries
- Tracks concept dependencies
"""

import json
import hashlib
import sqlite3
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Set, Tuple
from pathlib import Path
import logging
import re

logger = logging.getLogger(__name__)


class ConceptCategory(Enum):
    """Categories of trading concepts"""
    PRICE_ACTION = auto()
    TECHNICAL_INDICATORS = auto()
    CHART_PATTERNS = auto()
    RISK_MANAGEMENT = auto()
    POSITION_SIZING = auto()
    MONEY_MANAGEMENT = auto()
    TRADING_PSYCHOLOGY = auto()
    MARKET_STRUCTURE = auto()
    ORDER_FLOW = auto()
    VOLUME_ANALYSIS = auto()
    FUNDAMENTAL_ANALYSIS = auto()
    QUANTITATIVE_METHODS = auto()
    MACHINE_LEARNING = auto()
    ALGORITHMIC_TRADING = auto()
    EXECUTION_STRATEGIES = auto()
    PORTFOLIO_MANAGEMENT = auto()


@dataclass
class TradingConcept:
    """A structured trading concept"""
    id: str
    name: str
    category: ConceptCategory
    difficulty_level: int  # 1-7
    description: str
    key_points: List[str]
    formulas: List[str]
    examples: List[str]
    code_template: Optional[str]
    prerequisites: List[str]
    related_concepts: List[str]
    practical_application: str
    common_mistakes: List[str]
    mastery_score: float  # 0-1
    times_studied: int
    last_studied: datetime
    sources: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'name': self.name,
            'category': self.category.name,
            'difficulty_level': self.difficulty_level,
            'description': self.description,
            'key_points': self.key_points,
            'formulas': self.formulas,
            'examples': self.examples,
            'code_template': self.code_template,
            'prerequisites': self.prerequisites,
            'related_concepts': self.related_concepts,
            'practical_application': self.practical_application,
            'common_mistakes': self.common_mistakes,
            'mastery_score': self.mastery_score,
            'times_studied': self.times_studied,
            'last_studied': self.last_studied.isoformat(),
            'sources': self.sources,
        }


@dataclass
class KnowledgeNode:
    """A node in the knowledge graph"""
    id: str
    concept: TradingConcept
    connections: List[str]  # IDs of connected concepts
    strength: float  # Connection strength
    

class KnowledgeBuilder:
    """
    Builds structured knowledge from research materials.
    
    Features:
    - Concept extraction and structuring
    - Knowledge graph construction
    - Prerequisite mapping
    - Learning path optimization
    """
    
    # Pre-defined trading concepts with structured knowledge
    TRADING_KNOWLEDGE_BASE = {
        # BEGINNER LEVEL (1)
        "candlestick_basics": {
            "name": "Candlestick Chart Basics",
            "category": ConceptCategory.PRICE_ACTION,
            "difficulty_level": 1,
            "description": "Candlestick charts display price movements using candle-shaped figures showing open, high, low, and close prices.",
            "key_points": [
                "Each candle represents a time period (1min, 1hr, 1day, etc.)",
                "Body shows open-to-close range",
                "Wicks/shadows show high and low",
                "Green/white = bullish (close > open)",
                "Red/black = bearish (close < open)",
            ],
            "formulas": [
                "Body = |Close - Open|",
                "Upper Wick = High - max(Open, Close)",
                "Lower Wick = min(Open, Close) - Low",
            ],
            "code_template": """
def is_bullish_candle(open_price, close_price):
    return close_price > open_price

def candle_body_size(open_price, close_price):
    return abs(close_price - open_price)
""",
            "prerequisites": [],
            "related_concepts": ["support_resistance", "trend_identification"],
            "practical_application": "Use candlesticks to identify price direction and potential reversals",
            "common_mistakes": ["Ignoring context", "Trading single candles in isolation"],
        },
        
        "support_resistance": {
            "name": "Support and Resistance Levels",
            "category": ConceptCategory.PRICE_ACTION,
            "difficulty_level": 1,
            "description": "Support is a price level where buying pressure exceeds selling. Resistance is where selling exceeds buying.",
            "key_points": [
                "Support acts as a floor for price",
                "Resistance acts as a ceiling",
                "Broken support becomes resistance",
                "Broken resistance becomes support",
                "More touches = stronger level",
            ],
            "formulas": [],
            "code_template": """
def find_support_resistance(prices, window=20):
    highs = []
    lows = []
    for i in range(window, len(prices) - window):
        if prices[i] == max(prices[i-window:i+window+1]):
            highs.append(prices[i])
        if prices[i] == min(prices[i-window:i+window+1]):
            lows.append(prices[i])
    return {'resistance': highs, 'support': lows}
""",
            "prerequisites": ["candlestick_basics"],
            "related_concepts": ["trend_lines", "breakout_trading"],
            "practical_application": "Place entries near support, exits near resistance",
            "common_mistakes": ["Using exact prices instead of zones", "Ignoring volume at levels"],
        },
        
        # ELEMENTARY LEVEL (2)
        "moving_averages": {
            "name": "Moving Averages",
            "category": ConceptCategory.TECHNICAL_INDICATORS,
            "difficulty_level": 2,
            "description": "Moving averages smooth price data to identify trend direction by calculating average price over a period.",
            "key_points": [
                "SMA = Simple Moving Average (equal weights)",
                "EMA = Exponential Moving Average (recent prices weighted more)",
                "Common periods: 20, 50, 100, 200",
                "Price above MA = bullish, below = bearish",
                "MA crossovers signal trend changes",
            ],
            "formulas": [
                "SMA = (P1 + P2 + ... + Pn) / n",
                "EMA = Price * k + EMA_prev * (1-k), where k = 2/(n+1)",
            ],
            "code_template": """
import numpy as np

def sma(prices, period):
    return np.convolve(prices, np.ones(period)/period, mode='valid')

def ema(prices, period):
    k = 2 / (period + 1)
    ema_values = [prices[0]]
    for price in prices[1:]:
        ema_values.append(price * k + ema_values[-1] * (1 - k))
    return np.array(ema_values)
""",
            "prerequisites": ["candlestick_basics"],
            "related_concepts": ["macd", "trend_identification"],
            "practical_application": "Use MA crossovers for entry signals, MA as dynamic support/resistance",
            "common_mistakes": ["Using wrong period for timeframe", "Lagging nature causes late entries"],
        },
        
        "risk_reward_ratio": {
            "name": "Risk-Reward Ratio",
            "category": ConceptCategory.RISK_MANAGEMENT,
            "difficulty_level": 2,
            "description": "The ratio between potential loss (risk) and potential gain (reward) on a trade.",
            "key_points": [
                "R:R = Potential Profit / Potential Loss",
                "Minimum recommended: 1:2 (risk 1 to make 2)",
                "Higher R:R allows lower win rate to be profitable",
                "Calculate before entering trade",
                "Never move stop loss to increase risk",
            ],
            "formulas": [
                "Risk = Entry Price - Stop Loss",
                "Reward = Take Profit - Entry Price",
                "R:R Ratio = Reward / Risk",
                "Required Win Rate = 1 / (1 + R:R)",
            ],
            "code_template": """
def calculate_risk_reward(entry, stop_loss, take_profit):
    risk = abs(entry - stop_loss)
    reward = abs(take_profit - entry)
    ratio = reward / risk if risk > 0 else 0
    required_win_rate = 1 / (1 + ratio) if ratio > 0 else 1
    return {
        'risk': risk,
        'reward': reward,
        'ratio': ratio,
        'required_win_rate': required_win_rate
    }
""",
            "prerequisites": ["support_resistance"],
            "related_concepts": ["position_sizing", "stop_loss_placement"],
            "practical_application": "Only take trades with R:R >= 1:2",
            "common_mistakes": ["Ignoring R:R", "Moving targets to worse levels"],
        },
        
        # INTERMEDIATE LEVEL (3)
        "rsi_indicator": {
            "name": "Relative Strength Index (RSI)",
            "category": ConceptCategory.TECHNICAL_INDICATORS,
            "difficulty_level": 3,
            "description": "RSI measures speed and magnitude of price changes to identify overbought/oversold conditions.",
            "key_points": [
                "Oscillates between 0 and 100",
                "Above 70 = overbought (potential sell)",
                "Below 30 = oversold (potential buy)",
                "Divergence signals reversals",
                "Default period is 14",
            ],
            "formulas": [
                "RS = Average Gain / Average Loss",
                "RSI = 100 - (100 / (1 + RS))",
            ],
            "code_template": """

def calculate_rsi(prices, period=14):
    deltas = np.diff(prices)
    gains = np.where(deltas > 0, deltas, 0)
    losses = np.where(deltas < 0, -deltas, 0)
    
    avg_gain = np.convolve(gains, np.ones(period)/period, mode='valid')
    avg_loss = np.convolve(losses, np.ones(period)/period, mode='valid')
    
    rs = avg_gain / (avg_loss + 1e-10)
    rsi = 100 - (100 / (1 + rs))
    return rsi
""",
            "prerequisites": ["moving_averages"],
            "related_concepts": ["macd", "stochastic", "divergence"],
            "practical_application": "Use RSI divergence for reversal trades, overbought/oversold for mean reversion",
            "common_mistakes": ["Trading overbought/oversold alone", "Ignoring trend context"],
        },
        
        "macd": {
            "name": "MACD (Moving Average Convergence Divergence)",
            "category": ConceptCategory.TECHNICAL_INDICATORS,
            "difficulty_level": 3,
            "description": "MACD shows relationship between two EMAs to identify momentum and trend changes.",
            "key_points": [
                "MACD Line = 12 EMA - 26 EMA",
                "Signal Line = 9 EMA of MACD Line",
                "Histogram = MACD Line - Signal Line",
                "Crossover above signal = bullish",
                "Crossover below signal = bearish",
            ],
            "formulas": [
                "MACD = EMA(12) - EMA(26)",
                "Signal = EMA(MACD, 9)",
                "Histogram = MACD - Signal",
            ],
            "code_template": """
def calculate_macd(prices, fast=12, slow=26, signal=9):
    def ema(data, period):
        k = 2 / (period + 1)
        result = [data[0]]
        for val in data[1:]:
            result.append(val * k + result[-1] * (1 - k))
        return result
    
    ema_fast = ema(prices, fast)
    ema_slow = ema(prices, slow)
    macd_line = [f - s for f, s in zip(ema_fast, ema_slow)]
    signal_line = ema(macd_line, signal)
    histogram = [m - s for m, s in zip(macd_line, signal_line)]
    
    return {'macd': macd_line, 'signal': signal_line, 'histogram': histogram}
""",
            "prerequisites": ["moving_averages"],
            "related_concepts": ["rsi_indicator", "momentum"],
            "practical_application": "Use MACD crossovers with trend direction for entries",
            "common_mistakes": ["Using in ranging markets", "Ignoring histogram divergence"],
        },
        
        # UPPER INTERMEDIATE LEVEL (4)
        "fibonacci_retracement": {
            "name": "Fibonacci Retracement",
            "category": ConceptCategory.TECHNICAL_INDICATORS,
            "difficulty_level": 4,
            "description": "Fibonacci levels identify potential support/resistance based on mathematical ratios.",
            "key_points": [
                "Key levels: 23.6%, 38.2%, 50%, 61.8%, 78.6%",
                "Draw from swing low to swing high (uptrend)",
                "Draw from swing high to swing low (downtrend)",
                "61.8% is the golden ratio",
                "Confluence with other levels increases probability",
            ],
            "formulas": [
                "Fib Level = High - (High - Low) * Fib%",
                "Golden Ratio = 1.618 (or 0.618)",
            ],
            "code_template": """
def fibonacci_levels(high, low, direction='up'):
    levels = [0, 0.236, 0.382, 0.5, 0.618, 0.786, 1.0]
    diff = high - low
    
    if direction == 'up':
        return {f'{l*100:.1f}%': high - diff * l for l in levels}
    else:
        return {f'{l*100:.1f}%': low + diff * l for l in levels}
""",
            "prerequisites": ["support_resistance", "trend_identification"],
            "related_concepts": ["elliott_wave", "harmonic_patterns"],
            "practical_application": "Enter at 61.8% retracement with stop below 78.6%",
            "common_mistakes": ["Using without trend context", "Expecting exact bounces"],
        },
        
        "order_flow_basics": {
            "name": "Order Flow Analysis",
            "category": ConceptCategory.ORDER_FLOW,
            "difficulty_level": 4,
            "description": "Analyzing the flow of buy and sell orders to understand market dynamics.",
            "key_points": [
                "Delta = Buy Volume - Sell Volume",
                "Positive delta = buyers aggressive",
                "Negative delta = sellers aggressive",
                "Absorption = large orders stopping price",
                "Imbalance = one side dominating",
            ],
            "formulas": [
                "Delta = Σ(Buy Volume at Ask) - Σ(Sell Volume at Bid)",
                "Cumulative Delta = Running sum of Delta",
            ],
            "code_template": """
def calculate_delta(trades):
    buy_volume = sum(t['volume'] for t in trades if t['side'] == 'buy')
    sell_volume = sum(t['volume'] for t in trades if t['side'] == 'sell')
    return buy_volume - sell_volume

def cumulative_delta(deltas):
    cum_delta = []
    running = 0
    for d in deltas:
        running += d
        cum_delta.append(running)
    return cum_delta
""",
            "prerequisites": ["volume_analysis", "support_resistance"],
            "related_concepts": ["market_profile", "footprint_charts"],
            "practical_application": "Look for delta divergence with price for reversals",
            "common_mistakes": ["Ignoring context", "Over-relying on single delta readings"],
        },
        
        # ADVANCED LEVEL (5)
        "position_sizing_kelly": {
            "name": "Kelly Criterion Position Sizing",
            "category": ConceptCategory.POSITION_SIZING,
            "difficulty_level": 5,
            "description": "Mathematical formula for optimal position sizing based on edge and odds.",
            "key_points": [
                "Maximizes long-term growth rate",
                "Requires known win rate and R:R",
                "Full Kelly is aggressive, use fractional",
                "Half Kelly is common (50% of optimal)",
                "Never risk more than Kelly suggests",
            ],
            "formulas": [
                "Kelly% = W - (1-W)/R",
                "W = Win Rate, R = Win/Loss Ratio",
                "Fractional Kelly = Kelly% * Fraction",
            ],
            "code_template": """
def kelly_criterion(win_rate, win_loss_ratio):
    kelly = win_rate - (1 - win_rate) / win_loss_ratio
    return max(0, kelly)  # Never negative

def fractional_kelly(win_rate, win_loss_ratio, fraction=0.5):
    full_kelly = kelly_criterion(win_rate, win_loss_ratio)
    return full_kelly * fraction

def position_size(capital, kelly_pct, risk_per_trade):
    kelly_risk = capital * kelly_pct
    return min(kelly_risk, capital * risk_per_trade)
""",
            "prerequisites": ["risk_reward_ratio", "probability_basics"],
            "related_concepts": ["optimal_f", "risk_of_ruin"],
            "practical_application": "Use half-Kelly for position sizing with known statistics",
            "common_mistakes": ["Using full Kelly (too aggressive)", "Inaccurate win rate estimates"],
        },
        
        "mean_reversion": {
            "name": "Mean Reversion Trading",
            "category": ConceptCategory.QUANTITATIVE_METHODS,
            "difficulty_level": 5,
            "description": "Strategy based on prices returning to their average over time.",
            "key_points": [
                "Prices oscillate around a mean",
                "Extreme deviations tend to revert",
                "Use Bollinger Bands, Z-score",
                "Works best in ranging markets",
                "Fails in trending markets",
            ],
            "formulas": [
                "Z-Score = (Price - Mean) / StdDev",
                "Half-Life = ln(2) / (-ln(β))",
            ],
            "code_template": """

def z_score(prices, window=20):
    mean = np.mean(prices[-window:])
    std = np.std(prices[-window:])
    return (prices[-1] - mean) / std if std > 0 else 0

def mean_reversion_signal(prices, entry_z=2, exit_z=0):
    z = z_score(prices)
    if z < -entry_z:
        return 'BUY'
    elif z > entry_z:
        return 'SELL'
    elif abs(z) < exit_z:
        return 'EXIT'
    return 'HOLD'
""",
            "prerequisites": ["moving_averages", "bollinger_bands"],
            "related_concepts": ["pairs_trading", "statistical_arbitrage"],
            "practical_application": "Trade when Z-score exceeds 2, exit at 0",
            "common_mistakes": ["Trading mean reversion in trends", "Ignoring regime changes"],
        },
        
        # EXPERT LEVEL (6)
        "statistical_arbitrage": {
            "name": "Statistical Arbitrage",
            "category": ConceptCategory.QUANTITATIVE_METHODS,
            "difficulty_level": 6,
            "description": "Exploiting statistical mispricings between related securities.",
            "key_points": [
                "Pairs trading is simplest form",
                "Cointegration > Correlation",
                "Market neutral strategy",
                "Requires fast execution",
                "Risk: Spread can widen before converging",
            ],
            "formulas": [
                "Spread = Price_A - β * Price_B",
                "β = Cov(A,B) / Var(B)",
                "ADF Test for cointegration",
            ],
            "code_template": """
from scipy import stats

def calculate_spread(prices_a, prices_b):
    beta = np.cov(prices_a, prices_b)[0,1] / np.var(prices_b)
    spread = prices_a - beta * prices_b
    return spread, beta

def adf_test(spread):
    # Simplified ADF test
    diff = np.diff(spread)
    lagged = spread[:-1]
    slope, _, _, p_value, _ = stats.linregress(lagged, diff)
    return {'statistic': slope, 'p_value': p_value, 'cointegrated': p_value < 0.05}
""",
            "prerequisites": ["mean_reversion", "correlation_analysis"],
            "related_concepts": ["pairs_trading", "market_neutral"],
            "practical_application": "Trade spread when it deviates 2+ std from mean",
            "common_mistakes": ["Ignoring transaction costs", "Assuming correlation = cointegration"],
        },
        
        "market_microstructure": {
            "name": "Market Microstructure",
            "category": ConceptCategory.MARKET_STRUCTURE,
            "difficulty_level": 6,
            "description": "Study of how markets operate at the order level.",
            "key_points": [
                "Bid-Ask spread reflects liquidity",
                "Market makers provide liquidity",
                "Order book shows supply/demand",
                "Price impact of large orders",
                "Adverse selection risk",
            ],
            "formulas": [
                "Spread = Ask - Bid",
                "Mid Price = (Bid + Ask) / 2",
                "VWAP = Σ(Price * Volume) / Σ(Volume)",
            ],
            "code_template": """
def calculate_vwap(prices, volumes):
    return sum(p * v for p, v in zip(prices, volumes)) / sum(volumes)

def order_book_imbalance(bids, asks):
    bid_volume = sum(b['volume'] for b in bids[:5])
    ask_volume = sum(a['volume'] for a in asks[:5])
    return (bid_volume - ask_volume) / (bid_volume + ask_volume)

def price_impact(order_size, average_volume, volatility):
    return volatility * (order_size / average_volume) ** 0.5
""",
            "prerequisites": ["order_flow_basics", "volume_analysis"],
            "related_concepts": ["execution_algorithms", "market_making"],
            "practical_application": "Use microstructure to optimize execution",
            "common_mistakes": ["Ignoring market impact", "Trading illiquid markets"],
        },
        
        # MASTER LEVEL (7)
        "reinforcement_learning_trading": {
            "name": "Reinforcement Learning for Trading",
            "category": ConceptCategory.MACHINE_LEARNING,
            "difficulty_level": 7,
            "description": "Using RL agents to learn optimal trading policies through interaction.",
            "key_points": [
                "Agent learns from rewards/penalties",
                "State = market features",
                "Actions = buy/sell/hold",
                "Reward = risk-adjusted returns",
                "Common: DQN, PPO, A2C, SAC",
            ],
            "formulas": [
                "Q(s,a) = r + γ * max(Q(s',a'))",
                "Policy Gradient: ∇J(θ) = E[∇log(π(a|s)) * A(s,a)]",
            ],
            "code_template": """

class SimpleTradingAgent:
    def __init__(self, state_size, action_size):
        self.q_table = np.zeros((state_size, action_size))
        self.learning_rate = 0.1
        self.gamma = 0.99
        self.epsilon = 0.1
    
    def act(self, state):
        if np.random.random() < self.epsilon:
            return np.random.randint(3)  # Random action
        return np.argmax(self.q_table[state])
    
    def learn(self, state, action, reward, next_state):
        current_q = self.q_table[state, action]
        next_max_q = np.max(self.q_table[next_state])
        new_q = current_q + self.learning_rate * (reward + self.gamma * next_max_q - current_q)
        self.q_table[state, action] = new_q
""",
            "prerequisites": ["machine_learning_basics", "neural_networks"],
            "related_concepts": ["deep_q_learning", "policy_gradient"],
            "practical_application": "Train RL agent on historical data, validate on out-of-sample",
            "common_mistakes": ["Overfitting to training data", "Ignoring transaction costs in reward"],
        },
        
        "transformer_models": {
            "name": "Transformer Models for Finance",
            "category": ConceptCategory.MACHINE_LEARNING,
            "difficulty_level": 7,
            "description": "Using attention-based models for financial prediction.",
            "key_points": [
                "Self-attention captures long-range dependencies",
                "Positional encoding for sequence order",
                "Multi-head attention for different patterns",
                "Pre-training on large datasets",
                "Fine-tuning for specific tasks",
            ],
            "formulas": [
                "Attention(Q,K,V) = softmax(QK^T/√d_k)V",
                "MultiHead = Concat(head_1,...,head_h)W^O",
            ],
            "code_template": """
import torch
import torch.nn as nn

class FinancialTransformer(nn.Module):
    def __init__(self, d_model=64, nhead=4, num_layers=2):
        super().__init__()
        self.embedding = nn.Linear(5, d_model)  # OHLCV
        encoder_layer = nn.TransformerEncoderLayer(d_model, nhead)
        self.transformer = nn.TransformerEncoder(encoder_layer, num_layers)
        self.fc = nn.Linear(d_model, 3)  # Buy/Sell/Hold
    
    def forward(self, x):
        x = self.embedding(x)
        x = self.transformer(x)
        return self.fc(x[:, -1, :])
""",
            "prerequisites": ["neural_networks", "attention_mechanism"],
            "related_concepts": ["bert_finance", "gpt_trading"],
            "practical_application": "Use transformers for multi-asset prediction",
            "common_mistakes": ["Insufficient data", "Ignoring non-stationarity"],
        },
    }
    
    def __init__(self, data_dir: str = "autonomous_learner_data"):
        try:
            self.data_dir = Path(data_dir)
            self.data_dir.mkdir(parents=True, exist_ok=True)
        
            self.db_path = self.data_dir / "knowledge_base.db"
            self._init_database()
        
            self.concepts: Dict[str, TradingConcept] = {}
            self.knowledge_graph: Dict[str, KnowledgeNode] = {}
        
            # Load pre-built knowledge
            self._load_knowledge_base()
        
            logger.info(f"KnowledgeBuilder initialized with {len(self.concepts)} concepts")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def _init_database(self):
        """Initialize knowledge database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
        
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS concepts (
                    id TEXT PRIMARY KEY,
                    name TEXT,
                    category TEXT,
                    difficulty_level INTEGER,
                    description TEXT,
                    key_points TEXT,
                    formulas TEXT,
                    examples TEXT,
                    code_template TEXT,
                    prerequisites TEXT,
                    related_concepts TEXT,
                    practical_application TEXT,
                    common_mistakes TEXT,
                    mastery_score REAL,
                    times_studied INTEGER,
                    last_studied TEXT,
                    sources TEXT
                )
            ''')
        
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS knowledge_graph (
                    source_id TEXT,
                    target_id TEXT,
                    relationship TEXT,
                    strength REAL,
                    PRIMARY KEY (source_id, target_id)
                )
            ''')
        
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Error in _init_database: {e}")
            raise
    
    def _load_knowledge_base(self):
        """Load pre-built trading knowledge"""
        try:
            for concept_id, data in self.TRADING_KNOWLEDGE_BASE.items():
                concept = TradingConcept(
                    id=concept_id,
                    name=data['name'],
                    category=data['category'],
                    difficulty_level=data['difficulty_level'],
                    description=data['description'],
                    key_points=data['key_points'],
                    formulas=data['formulas'],
                    examples=[],
                    code_template=data.get('code_template'),
                    prerequisites=data['prerequisites'],
                    related_concepts=data['related_concepts'],
                    practical_application=data['practical_application'],
                    common_mistakes=data['common_mistakes'],
                    mastery_score=0.0,
                    times_studied=0,
                    last_studied=datetime.now(),
                    sources=['internal_knowledge_base'],
                )
                self.concepts[concept_id] = concept
                self._store_concept(concept)
        except Exception as e:
            logger.error(f"Error in _load_knowledge_base: {e}")
            raise
    
    def _store_concept(self, concept: TradingConcept):
        """Store concept in database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
        
            cursor.execute('''
                INSERT OR REPLACE INTO concepts 
                (id, name, category, difficulty_level, description, key_points, formulas, 
                 examples, code_template, prerequisites, related_concepts, practical_application,
                 common_mistakes, mastery_score, times_studied, last_studied, sources)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                concept.id,
                concept.name,
                concept.category.name,
                concept.difficulty_level,
                concept.description,
                json.dumps(concept.key_points),
                json.dumps(concept.formulas),
                json.dumps(concept.examples),
                concept.code_template,
                json.dumps(concept.prerequisites),
                json.dumps(concept.related_concepts),
                concept.practical_application,
                json.dumps(concept.common_mistakes),
                concept.mastery_score,
                concept.times_studied,
                concept.last_studied.isoformat(),
                json.dumps(concept.sources),
            ))
        
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Error in _store_concept: {e}")
            raise
    
    def get_concepts_by_level(self, level: int) -> List[TradingConcept]:
        """Get all concepts at a specific difficulty level"""
        return [c for c in self.concepts.values() if c.difficulty_level == level]
    
    def get_learning_path(self, target_concept: str) -> List[str]:
        """Get ordered list of concepts to learn before target"""
        if target_concept not in self.concepts:
            return []
        
        path = []
        visited = set()
        
        def dfs(concept_id):
            try:
                if concept_id in visited:
                    return
                visited.add(concept_id)
            
                if concept_id in self.concepts:
                    for prereq in self.concepts[concept_id].prerequisites:
                        dfs(prereq)
                    path.append(concept_id)
            except Exception as e:
                logger.error(f"Error in dfs: {e}")
                raise
        
        dfs(target_concept)
        return path
    
    def study_concept(self, concept_id: str) -> Dict[str, Any]:
        """Study a concept and update mastery"""
        try:
            if concept_id not in self.concepts:
                return {'error': f'Concept {concept_id} not found'}
        
            concept = self.concepts[concept_id]
            concept.times_studied += 1
            concept.last_studied = datetime.now()
        
            # Increase mastery based on study
            mastery_increase = 0.1 * (1 - concept.mastery_score)  # Diminishing returns
            concept.mastery_score = min(1.0, concept.mastery_score + mastery_increase)
        
            self._store_concept(concept)
        
            return {
                'concept': concept.name,
                'mastery_score': concept.mastery_score,
                'times_studied': concept.times_studied,
                'key_points': concept.key_points,
                'code_template': concept.code_template,
            }
        except Exception as e:
            logger.error(f"Error in study_concept: {e}")
            raise
    
    def get_knowledge_summary(self) -> Dict[str, Any]:
        """Get summary of all knowledge"""
        try:
            by_level = {}
            for level in range(1, 8):
                concepts = self.get_concepts_by_level(level)
                by_level[level] = {
                    'count': len(concepts),
                    'avg_mastery': sum(c.mastery_score for c in concepts) / len(concepts) if concepts else 0,
                    'concepts': [c.name for c in concepts],
                }
        
            total_mastery = sum(c.mastery_score for c in self.concepts.values())
            avg_mastery = total_mastery / len(self.concepts) if self.concepts else 0
        
            return {
                'total_concepts': len(self.concepts),
                'average_mastery': avg_mastery,
                'by_level': by_level,
                'categories': list(set(c.category.name for c in self.concepts.values())),
            }
        except Exception as e:
            logger.error(f"Error in get_knowledge_summary: {e}")
            raise
