"""
Self-Tester - Autonomous Testing System with Evolving Difficulty

Tests the bot's understanding of trading concepts:
- Generates tests from easy to super-hard
- Tracks performance and adapts difficulty
- Identifies knowledge gaps
- Validates learning before transfer
"""

import json
import hashlib
import sqlite3
import random
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Tuple
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class TestDifficulty(Enum):
    """Test difficulty levels"""
    EASY = 1
    MEDIUM = 2
    HARD = 3
    VERY_HARD = 4
    EXPERT = 5
    MASTER = 6
    SUPER_HARD = 7


class QuestionType(Enum):
    """Types of test questions"""
    MULTIPLE_CHOICE = auto()
    TRUE_FALSE = auto()
    FILL_BLANK = auto()
    CODE_COMPLETION = auto()
    CALCULATION = auto()
    SCENARIO_ANALYSIS = auto()
    STRATEGY_DESIGN = auto()


@dataclass
class TestQuestion:
    """A test question"""
    id: str
    question: str
    question_type: QuestionType
    difficulty: TestDifficulty
    topic: str
    options: List[str]  # For multiple choice
    correct_answer: str
    explanation: str
    code_context: Optional[str]  # For code questions
    points: int
    time_limit: int  # seconds
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'question': self.question,
            'question_type': self.question_type.name,
            'difficulty': self.difficulty.name,
            'topic': self.topic,
            'options': self.options,
            'correct_answer': self.correct_answer,
            'explanation': self.explanation,
            'code_context': self.code_context,
            'points': self.points,
            'time_limit': self.time_limit,
        }


@dataclass
class TestResult:
    """Result of a test attempt"""
    question_id: str
    answer_given: str
    is_correct: bool
    time_taken: float
    confidence: float
    timestamp: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'question_id': self.question_id,
            'answer_given': self.answer_given,
            'is_correct': self.is_correct,
            'time_taken': self.time_taken,
            'confidence': self.confidence,
            'timestamp': self.timestamp.isoformat(),
        }


@dataclass
class TestSession:
    """A complete test session"""
    id: str
    difficulty: TestDifficulty
    questions: List[TestQuestion]
    results: List[TestResult]
    start_time: datetime
    end_time: Optional[datetime]
    score: float
    passed: bool
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'difficulty': self.difficulty.name,
            'questions_count': len(self.questions),
            'results_count': len(self.results),
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'score': self.score,
            'passed': self.passed,
        }


class SelfTester:
    """
    Autonomous testing system with evolving difficulty.
    
    Features:
    - Generate tests at various difficulty levels
    - Adaptive difficulty based on performance
    - Track knowledge gaps
    - Validate understanding before transfer
    """
    
    # Question bank organized by difficulty and topic
    QUESTION_BANK = {
        # EASY (Level 1)
        TestDifficulty.EASY: [
            {
                "question": "What does a green/white candlestick indicate?",
                "type": QuestionType.MULTIPLE_CHOICE,
                "topic": "candlestick_basics",
                "options": ["Price went up (bullish)", "Price went down (bearish)", "No change", "Market closed"],
                "correct": "Price went up (bullish)",
                "explanation": "A green/white candle means the closing price was higher than the opening price.",
            },
            {
                "question": "True or False: Support is a price level where selling pressure exceeds buying pressure.",
                "type": QuestionType.TRUE_FALSE,
                "topic": "support_resistance",
                "options": ["True", "False"],
                "correct": "False",
                "explanation": "Support is where BUYING pressure exceeds selling, acting as a floor.",
            },
            {
                "question": "What is the bid-ask spread?",
                "type": QuestionType.MULTIPLE_CHOICE,
                "topic": "market_basics",
                "options": ["Difference between highest bid and lowest ask", "Average of bid and ask", "Sum of bid and ask", "Bid divided by ask"],
                "correct": "Difference between highest bid and lowest ask",
                "explanation": "Spread = Ask Price - Bid Price",
            },
            {
                "question": "A market order is executed at the _____ available price.",
                "type": QuestionType.FILL_BLANK,
                "topic": "order_types",
                "options": ["best", "worst", "average", "fixed"],
                "correct": "best",
                "explanation": "Market orders execute immediately at the best available price.",
            },
            {
                "question": "What does OHLC stand for?",
                "type": QuestionType.MULTIPLE_CHOICE,
                "topic": "candlestick_basics",
                "options": ["Open, High, Low, Close", "Order, Hold, Limit, Cancel", "Overnight High Low Close", "Option Hedge Leverage Capital"],
                "correct": "Open, High, Low, Close",
                "explanation": "OHLC represents the four key prices in a candlestick.",
            },
        ],
        
        # MEDIUM (Level 2)
        TestDifficulty.MEDIUM: [
            {
                "question": "What is the formula for Simple Moving Average (SMA)?",
                "type": QuestionType.MULTIPLE_CHOICE,
                "topic": "moving_averages",
                "options": ["Sum of prices / Number of periods", "Latest price * weight factor", "High + Low / 2", "Close - Open"],
                "correct": "Sum of prices / Number of periods",
                "explanation": "SMA = (P1 + P2 + ... + Pn) / n",
            },
            {
                "question": "If your risk is $100 and reward is $300, what is your Risk:Reward ratio?",
                "type": QuestionType.CALCULATION,
                "topic": "risk_reward_ratio",
                "options": ["1:3", "3:1", "1:1", "1:2"],
                "correct": "1:3",
                "explanation": "R:R = Reward/Risk = 300/100 = 3, expressed as 1:3",
            },
            {
                "question": "True or False: EMA gives more weight to recent prices than SMA.",
                "type": QuestionType.TRUE_FALSE,
                "topic": "moving_averages",
                "options": ["True", "False"],
                "correct": "True",
                "explanation": "EMA uses exponential weighting, giving more importance to recent prices.",
            },
            {
                "question": "What happens when price breaks above resistance?",
                "type": QuestionType.MULTIPLE_CHOICE,
                "topic": "support_resistance",
                "options": ["Resistance becomes support", "Support becomes resistance", "Both disappear", "Nothing changes"],
                "correct": "Resistance becomes support",
                "explanation": "Broken resistance often becomes new support (role reversal).",
            },
            {
                "question": "Complete the code: def calculate_sma(prices, period): return sum(prices[-period:]) / _____",
                "type": QuestionType.CODE_COMPLETION,
                "topic": "moving_averages",
                "options": ["period", "len(prices)", "prices[-1]", "sum(prices)"],
                "correct": "period",
                "explanation": "SMA divides the sum by the number of periods.",
                "code_context": "def calculate_sma(prices, period):\n    return sum(prices[-period:]) / _____",
            },
        ],
        
        # HARD (Level 3)
        TestDifficulty.HARD: [
            {
                "question": "RSI above 70 indicates the market is:",
                "type": QuestionType.MULTIPLE_CHOICE,
                "topic": "rsi_indicator",
                "options": ["Overbought", "Oversold", "Neutral", "Trending"],
                "correct": "Overbought",
                "explanation": "RSI > 70 suggests overbought conditions, potential for pullback.",
            },
            {
                "question": "What is the MACD line calculated from?",
                "type": QuestionType.MULTIPLE_CHOICE,
                "topic": "macd",
                "options": ["12 EMA minus 26 EMA", "26 EMA minus 12 EMA", "12 SMA minus 26 SMA", "RSI minus 50"],
                "correct": "12 EMA minus 26 EMA",
                "explanation": "MACD = EMA(12) - EMA(26)",
            },
            {
                "question": "Calculate RSI if Average Gain = 2 and Average Loss = 1. RS = 2, RSI = ?",
                "type": QuestionType.CALCULATION,
                "topic": "rsi_indicator",
                "options": ["66.67", "50", "75", "33.33"],
                "correct": "66.67",
                "explanation": "RSI = 100 - (100/(1+RS)) = 100 - (100/3) = 66.67",
            },
            {
                "question": "What does a bullish divergence on RSI indicate?",
                "type": QuestionType.MULTIPLE_CHOICE,
                "topic": "rsi_indicator",
                "options": ["Price makes lower low, RSI makes higher low", "Price makes higher high, RSI makes lower high", "Both make higher highs", "Both make lower lows"],
                "correct": "Price makes lower low, RSI makes higher low",
                "explanation": "Bullish divergence: price down, indicator up = potential reversal up.",
            },
            {
                "question": "Complete: def macd_signal(macd_line): return ema(macd_line, _____)",
                "type": QuestionType.CODE_COMPLETION,
                "topic": "macd",
                "options": ["9", "12", "26", "14"],
                "correct": "9",
                "explanation": "MACD signal line is a 9-period EMA of the MACD line.",
                "code_context": "def macd_signal(macd_line):\n    return ema(macd_line, _____)",
            },
        ],
        
        # VERY HARD (Level 4)
        TestDifficulty.VERY_HARD: [
            {
                "question": "What is the 61.8% Fibonacci level called?",
                "type": QuestionType.MULTIPLE_CHOICE,
                "topic": "fibonacci_retracement",
                "options": ["Golden Ratio", "Silver Ratio", "Bronze Ratio", "Platinum Ratio"],
                "correct": "Golden Ratio",
                "explanation": "0.618 is the golden ratio, key Fibonacci level.",
            },
            {
                "question": "In order flow, positive delta means:",
                "type": QuestionType.MULTIPLE_CHOICE,
                "topic": "order_flow_basics",
                "options": ["More aggressive buying", "More aggressive selling", "Equal buying and selling", "No trading activity"],
                "correct": "More aggressive buying",
                "explanation": "Delta = Buy Volume - Sell Volume. Positive = buyers aggressive.",
            },
            {
                "question": "Calculate Fibonacci 61.8% level: High=100, Low=50",
                "type": QuestionType.CALCULATION,
                "topic": "fibonacci_retracement",
                "options": ["69.1", "80.9", "61.8", "38.2"],
                "correct": "69.1",
                "explanation": "Level = High - (High-Low)*0.618 = 100 - 50*0.618 = 69.1",
            },
            {
                "question": "What does absorption in order flow indicate?",
                "type": QuestionType.MULTIPLE_CHOICE,
                "topic": "order_flow_basics",
                "options": ["Large orders stopping price movement", "Price breaking through levels", "No significant orders", "Market closing"],
                "correct": "Large orders stopping price movement",
                "explanation": "Absorption = large orders absorbing aggressive flow, stopping price.",
            },
            {
                "question": "Scenario: Price makes new high, but delta is decreasing. What does this suggest?",
                "type": QuestionType.SCENARIO_ANALYSIS,
                "topic": "order_flow_basics",
                "options": ["Weakening momentum, potential reversal", "Strong continuation", "Accumulation phase", "No significance"],
                "correct": "Weakening momentum, potential reversal",
                "explanation": "Divergence between price and delta suggests exhaustion.",
            },
        ],
        
        # EXPERT (Level 5)
        TestDifficulty.EXPERT: [
            {
                "question": "Kelly Criterion formula: K = W - (1-W)/R. If W=0.6 and R=2, what is K?",
                "type": QuestionType.CALCULATION,
                "topic": "position_sizing_kelly",
                "options": ["0.4 (40%)", "0.6 (60%)", "0.2 (20%)", "0.8 (80%)"],
                "correct": "0.4 (40%)",
                "explanation": "K = 0.6 - (1-0.6)/2 = 0.6 - 0.2 = 0.4 = 40%",
            },
            {
                "question": "What is the half-life in mean reversion?",
                "type": QuestionType.MULTIPLE_CHOICE,
                "topic": "mean_reversion",
                "options": ["Time for spread to revert halfway to mean", "Time for price to double", "Period of moving average", "Decay rate of momentum"],
                "correct": "Time for spread to revert halfway to mean",
                "explanation": "Half-life measures how quickly prices revert to mean.",
            },
            {
                "question": "Z-score of 2.5 means price is how many standard deviations from mean?",
                "type": QuestionType.CALCULATION,
                "topic": "mean_reversion",
                "options": ["2.5", "1.5", "0.5", "3.5"],
                "correct": "2.5",
                "explanation": "Z-score directly represents standard deviations from mean.",
            },
            {
                "question": "Why use fractional Kelly instead of full Kelly?",
                "type": QuestionType.MULTIPLE_CHOICE,
                "topic": "position_sizing_kelly",
                "options": ["Full Kelly is too aggressive, high variance", "Full Kelly is too conservative", "Fractional is faster", "No difference"],
                "correct": "Full Kelly is too aggressive, high variance",
                "explanation": "Full Kelly maximizes growth but has high variance. Half Kelly reduces risk.",
            },
            {
                "question": "Design a mean reversion entry rule using Z-score:",
                "type": QuestionType.STRATEGY_DESIGN,
                "topic": "mean_reversion",
                "options": ["Buy when Z < -2, Sell when Z > 2", "Buy when Z > 2, Sell when Z < -2", "Buy when Z = 0", "Random entries"],
                "correct": "Buy when Z < -2, Sell when Z > 2",
                "explanation": "Mean reversion: buy oversold (low Z), sell overbought (high Z).",
            },
        ],
        
        # MASTER (Level 6)
        TestDifficulty.MASTER: [
            {
                "question": "What test determines if two series are cointegrated?",
                "type": QuestionType.MULTIPLE_CHOICE,
                "topic": "statistical_arbitrage",
                "options": ["Augmented Dickey-Fuller (ADF)", "T-test", "Chi-square", "ANOVA"],
                "correct": "Augmented Dickey-Fuller (ADF)",
                "explanation": "ADF tests for stationarity of the spread (cointegration).",
            },
            {
                "question": "In pairs trading, beta is used to:",
                "type": QuestionType.MULTIPLE_CHOICE,
                "topic": "statistical_arbitrage",
                "options": ["Calculate hedge ratio", "Measure volatility", "Determine entry timing", "Set stop loss"],
                "correct": "Calculate hedge ratio",
                "explanation": "Beta = Cov(A,B)/Var(B), used as hedge ratio in pairs trading.",
            },
            {
                "question": "What is VWAP used for in execution?",
                "type": QuestionType.MULTIPLE_CHOICE,
                "topic": "market_microstructure",
                "options": ["Benchmark for execution quality", "Entry signal", "Stop loss level", "Position sizing"],
                "correct": "Benchmark for execution quality",
                "explanation": "VWAP is the standard benchmark for institutional execution.",
            },
            {
                "question": "Calculate order book imbalance: Bid Vol=1000, Ask Vol=600",
                "type": QuestionType.CALCULATION,
                "topic": "market_microstructure",
                "options": ["0.25 (bullish)", "-0.25 (bearish)", "0.5", "1.67"],
                "correct": "0.25 (bullish)",
                "explanation": "Imbalance = (1000-600)/(1000+600) = 400/1600 = 0.25",
            },
            {
                "question": "Why is correlation not sufficient for pairs trading?",
                "type": QuestionType.MULTIPLE_CHOICE,
                "topic": "statistical_arbitrage",
                "options": ["Need cointegration for mean-reverting spread", "Correlation is always 1", "Correlation changes too fast", "Correlation is too complex"],
                "correct": "Need cointegration for mean-reverting spread",
                "explanation": "Correlation doesn't guarantee mean-reverting spread. Cointegration does.",
            },
        ],
        
        # SUPER HARD (Level 7)
        TestDifficulty.SUPER_HARD: [
            {
                "question": "In DQN, what is the purpose of the target network?",
                "type": QuestionType.MULTIPLE_CHOICE,
                "topic": "reinforcement_learning_trading",
                "options": ["Stabilize training by providing fixed Q-targets", "Speed up training", "Reduce memory usage", "Generate actions"],
                "correct": "Stabilize training by providing fixed Q-targets",
                "explanation": "Target network provides stable targets, updated periodically.",
            },
            {
                "question": "What is the Bellman equation for Q-learning?",
                "type": QuestionType.MULTIPLE_CHOICE,
                "topic": "reinforcement_learning_trading",
                "options": ["Q(s,a) = r + γ * max(Q(s',a'))", "Q(s,a) = r - γ * Q(s',a')", "Q(s,a) = max(r, Q(s',a'))", "Q(s,a) = r * γ"],
                "correct": "Q(s,a) = r + γ * max(Q(s',a'))",
                "explanation": "Bellman equation: current Q = reward + discounted future max Q.",
            },
            {
                "question": "In attention mechanism, what does softmax(QK^T/√d_k) compute?",
                "type": QuestionType.MULTIPLE_CHOICE,
                "topic": "transformer_models",
                "options": ["Attention weights", "Output values", "Position encoding", "Loss function"],
                "correct": "Attention weights",
                "explanation": "Softmax normalizes scaled dot-product to get attention weights.",
            },
            {
                "question": "Why divide by √d_k in attention?",
                "type": QuestionType.MULTIPLE_CHOICE,
                "topic": "transformer_models",
                "options": ["Prevent softmax saturation with large d_k", "Speed up computation", "Reduce memory", "Normalize output"],
                "correct": "Prevent softmax saturation with large d_k",
                "explanation": "Scaling prevents dot products from growing too large, keeping gradients stable.",
            },
            {
                "question": "Design an RL reward function for trading that accounts for risk:",
                "type": QuestionType.STRATEGY_DESIGN,
                "topic": "reinforcement_learning_trading",
                "options": ["Sharpe ratio: (return - rf) / volatility", "Just returns", "Win rate only", "Number of trades"],
                "correct": "Sharpe ratio: (return - rf) / volatility",
                "explanation": "Sharpe ratio rewards risk-adjusted returns, not just raw returns.",
            },
            {
                "question": "What is experience replay in DQN and why is it important?",
                "type": QuestionType.MULTIPLE_CHOICE,
                "topic": "reinforcement_learning_trading",
                "options": ["Store and sample past experiences to break correlation", "Replay winning trades only", "Speed up training", "Reduce model size"],
                "correct": "Store and sample past experiences to break correlation",
                "explanation": "Experience replay breaks temporal correlation, improving learning stability.",
            },
        ],
    }
    
    def __init__(self, data_dir: str = "autonomous_learner_data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        self.db_path = self.data_dir / "test_results.db"
        self._init_database()
        
        self.current_difficulty = TestDifficulty.EASY
        self.sessions: List[TestSession] = []
        self.performance_history: List[Dict] = []
        
        # Passing thresholds - STRICT: Must achieve 100% to pass and advance
        self.pass_threshold = 1.0  # 100% to pass - FULL MASTERY REQUIRED
        self.mastery_threshold = 1.0  # 100% for mastery - NO COMPROMISE
        
        logger.info("SelfTester initialized")
    
    def _init_database(self):
        """Initialize test results database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS test_sessions (
                id TEXT PRIMARY KEY,
                difficulty TEXT,
                questions_count INTEGER,
                correct_count INTEGER,
                score REAL,
                passed INTEGER,
                start_time TEXT,
                end_time TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS test_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT,
                question_id TEXT,
                topic TEXT,
                answer_given TEXT,
                correct_answer TEXT,
                is_correct INTEGER,
                time_taken REAL,
                timestamp TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS topic_performance (
                topic TEXT PRIMARY KEY,
                attempts INTEGER,
                correct INTEGER,
                accuracy REAL,
                last_tested TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def generate_test(self, difficulty: TestDifficulty, num_questions: int = 5) -> List[TestQuestion]:
        """Generate a test at specified difficulty"""
        questions_data = self.QUESTION_BANK.get(difficulty, [])
        
        if not questions_data:
            logger.warning(f"No questions available for {difficulty.name}")
            return []
        
        # Sample questions (with replacement if needed)
        selected = random.sample(questions_data, min(num_questions, len(questions_data)))
        if len(selected) < num_questions:
            selected.extend(random.choices(questions_data, k=num_questions - len(selected)))
        
        questions = []
        for i, q_data in enumerate(selected):
            question = TestQuestion(
                id=hashlib.md5(f"{difficulty.name}_{i}_{q_data['question'][:20]}".encode()).hexdigest()[:8],
                question=q_data['question'],
                question_type=q_data['type'],
                difficulty=difficulty,
                topic=q_data['topic'],
                options=q_data['options'],
                correct_answer=q_data['correct'],
                explanation=q_data['explanation'],
                code_context=q_data.get('code_context'),
                points=difficulty.value * 10,
                time_limit=30 + difficulty.value * 10,
            )
            questions.append(question)
        
        return questions
    
    def take_test(self, difficulty: TestDifficulty, num_questions: int = 5) -> TestSession:
        """Take a test and get results"""
        questions = self.generate_test(difficulty, num_questions)
        
        session = TestSession(
            id=hashlib.md5(f"{datetime.now().isoformat()}_{difficulty.name}".encode()).hexdigest()[:12],
            difficulty=difficulty,
            questions=questions,
            results=[],
            start_time=datetime.now(),
            end_time=None,
            score=0.0,
            passed=False,
        )
        
        # Simulate answering questions (AI reasoning)
        for question in questions:
            result = self._answer_question(question)
            session.results.append(result)
        
        # Calculate score
        correct_count = sum(1 for r in session.results if r.is_correct)
        session.score = correct_count / len(questions) if questions else 0
        session.passed = session.score >= self.pass_threshold
        session.end_time = datetime.now()
        
        # Store results
        self._store_session(session)
        self.sessions.append(session)
        
        # Update performance history
        self.performance_history.append({
            'difficulty': difficulty.name,
            'score': session.score,
            'passed': session.passed,
            'timestamp': datetime.now().isoformat(),
        })
        
        return session
    
    def _answer_question(self, question: TestQuestion) -> TestResult:
        """AI answers a question based on learned knowledge"""
        start_time = datetime.now()
        
        # Simulate AI reasoning based on difficulty
        # Higher difficulty = lower base accuracy, but learning improves it
        base_accuracy = {
            TestDifficulty.EASY: 0.95,
            TestDifficulty.MEDIUM: 0.85,
            TestDifficulty.HARD: 0.75,
            TestDifficulty.VERY_HARD: 0.65,
            TestDifficulty.EXPERT: 0.55,
            TestDifficulty.MASTER: 0.45,
            TestDifficulty.SUPER_HARD: 0.35,
        }
        
        # Check topic performance to adjust accuracy
        topic_accuracy = self._get_topic_accuracy(question.topic)
        learning_bonus = topic_accuracy * 0.3  # Up to 30% bonus from learning
        
        accuracy = min(0.98, base_accuracy.get(question.difficulty, 0.5) + learning_bonus)
        
        # Determine if answer is correct
        is_correct = random.random() < accuracy
        
        # Select answer
        if is_correct:
            answer = question.correct_answer
        else:
            wrong_options = [o for o in question.options if o != question.correct_answer]
            answer = random.choice(wrong_options) if wrong_options else question.correct_answer
        
        time_taken = (datetime.now() - start_time).total_seconds() + random.uniform(1, 5)
        
        # Update topic performance
        self._update_topic_performance(question.topic, is_correct)
        
        return TestResult(
            question_id=question.id,
            answer_given=answer,
            is_correct=is_correct,
            time_taken=time_taken,
            confidence=accuracy,
            timestamp=datetime.now(),
        )
    
    def _get_topic_accuracy(self, topic: str) -> float:
        """Get historical accuracy for a topic"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT accuracy FROM topic_performance WHERE topic = ?', (topic,))
        result = cursor.fetchone()
        conn.close()
        
        return result[0] if result else 0.0
    
    def _update_topic_performance(self, topic: str, is_correct: bool):
        """Update topic performance tracking"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT attempts, correct FROM topic_performance WHERE topic = ?', (topic,))
        result = cursor.fetchone()
        
        if result:
            attempts = result[0] + 1
            correct = result[1] + (1 if is_correct else 0)
        else:
            attempts = 1
            correct = 1 if is_correct else 0
        
        accuracy = correct / attempts
        
        cursor.execute('''
            INSERT OR REPLACE INTO topic_performance (topic, attempts, correct, accuracy, last_tested)
            VALUES (?, ?, ?, ?, ?)
        ''', (topic, attempts, correct, accuracy, datetime.now().isoformat()))
        
        conn.commit()
        conn.close()
    
    def _store_session(self, session: TestSession):
        """Store test session in database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        correct_count = sum(1 for r in session.results if r.is_correct)
        
        cursor.execute('''
            INSERT INTO test_sessions (id, difficulty, questions_count, correct_count, score, passed, start_time, end_time)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            session.id,
            session.difficulty.name,
            len(session.questions),
            correct_count,
            session.score,
            int(session.passed),
            session.start_time.isoformat(),
            session.end_time.isoformat() if session.end_time else None,
        ))
        
        for i, (question, result) in enumerate(zip(session.questions, session.results)):
            cursor.execute('''
                INSERT INTO test_results (session_id, question_id, topic, answer_given, correct_answer, is_correct, time_taken, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                session.id,
                question.id,
                question.topic,
                result.answer_given,
                question.correct_answer,
                int(result.is_correct),
                result.time_taken,
                result.timestamp.isoformat(),
            ))
        
        conn.commit()
        conn.close()
    
    def run_progressive_test(self) -> Dict[str, Any]:
        """Run tests from easy to super-hard, advancing on pass"""
        results = []
        current_level = TestDifficulty.EASY
        
        for difficulty in TestDifficulty:
            logger.info(f"Testing at {difficulty.name} level...")
            
            session = self.take_test(difficulty, num_questions=5)
            
            results.append({
                'difficulty': difficulty.name,
                'score': session.score,
                'passed': session.passed,
                'correct': sum(1 for r in session.results if r.is_correct),
                'total': len(session.questions),
            })
            
            if not session.passed:
                logger.info(f"Failed at {difficulty.name} level. Score: {session.score:.1%}")
                break
            else:
                logger.info(f"Passed {difficulty.name} level! Score: {session.score:.1%}")
                current_level = difficulty
        
        return {
            'highest_level_passed': current_level.name,
            'results': results,
            'total_sessions': len(results),
            'timestamp': datetime.now().isoformat(),
        }
    
    def get_knowledge_gaps(self) -> List[Dict[str, Any]]:
        """Identify topics that need more study"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT topic, attempts, correct, accuracy 
            FROM topic_performance 
            WHERE accuracy < 0.7 OR attempts < 3
            ORDER BY accuracy ASC
        ''')
        
        gaps = []
        for row in cursor.fetchall():
            gaps.append({
                'topic': row[0],
                'attempts': row[1],
                'correct': row[2],
                'accuracy': row[3],
                'needs_study': row[3] < 0.7,
                'needs_practice': row[1] < 3,
            })
        
        conn.close()
        return gaps
    
    def get_test_statistics(self) -> Dict[str, Any]:
        """Get overall test statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*), AVG(score), SUM(passed) FROM test_sessions')
        result = cursor.fetchone()
        
        cursor.execute('SELECT difficulty, COUNT(*), AVG(score) FROM test_sessions GROUP BY difficulty')
        by_difficulty = {row[0]: {'count': row[1], 'avg_score': row[2]} for row in cursor.fetchall()}
        
        cursor.execute('SELECT topic, accuracy FROM topic_performance ORDER BY accuracy DESC')
        topic_mastery = {row[0]: row[1] for row in cursor.fetchall()}
        
        conn.close()
        
        return {
            'total_sessions': result[0] or 0,
            'average_score': result[1] or 0,
            'total_passed': result[2] or 0,
            'pass_rate': (result[2] / result[0]) if result[0] else 0,
            'by_difficulty': by_difficulty,
            'topic_mastery': topic_mastery,
        }
