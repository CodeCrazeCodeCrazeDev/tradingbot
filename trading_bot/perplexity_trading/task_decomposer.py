"""
Task Decomposer for Perplexity Trading Architecture
============================================================

Decomposes complex trading queries into discrete subtasks,
building a dependency graph for orchestrated execution.

Like Perplexity Computer, this breaks down queries like:
"Research EURUSD fundamentals, analyze the 4H chart, and prepare an entry"

Into a task graph:
1. Research fundamentals (RESEARCH agent)
2. Fetch 4H price data (MARKET_DATA retrieval)
3. Analyze chart patterns (TECHNICAL agent)
4. Calculate risk parameters (RISK agent)
5. Synthesize entry decision (REASONING agent)
6. Verify against sources (VALIDATOR agent)
"""

import re
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Tuple
from enum import Enum

from .core_types import (
    SubTask,
    TaskType,
    AgentType,
    TradingQuery,
)

logger = logging.getLogger(__name__)


class QueryIntent(Enum):
    """Detected intent from the query"""
    RESEARCH = "research"           # Information gathering
    ANALYZE = "analyze"             # Technical/fundamental analysis
    TRADE = "trade"                 # Execute a trade
    POSITION_SIZE = "position_size" # Calculate position size
    RISK_CHECK = "risk_check"       # Check risk parameters
    MONITOR = "monitor"             # Monitor positions/market
    BACKTEST = "backtest"           # Backtest a strategy
    EXPLAIN = "explain"             # Explain a concept/decision
    COMPARE = "compare"             # Compare options
    FORECAST = "forecast"           # Predict future movement


@dataclass
class TaskDependency:
    """Dependency between tasks"""
    from_task_id: str
    to_task_id: str
    output_key: str  # Which output from from_task is needed
    required: bool = True  # If False, can proceed without


@dataclass
class TaskGraph:
    """Directed acyclic graph of subtasks"""
    query_id: str
    subtasks: Dict[str, SubTask] = field(default_factory=dict)
    dependencies: List[TaskDependency] = field(default_factory=list)
    execution_order: List[List[str]] = field(default_factory=list)  # Parallel batches
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    def add_subtask(self, subtask: SubTask) -> None:
        """Add a subtask to the graph"""
        self.subtasks[subtask.id] = subtask
    
    def add_dependency(self, from_id: str, to_id: str, output_key: str, required: bool = True) -> None:
        """Add a dependency between subtasks"""
        self.dependencies.append(TaskDependency(from_id, to_id, output_key, required))
        # Update the to_task's inputs
        if to_id in self.subtasks:
            if from_id not in self.subtasks[to_id].inputs:
                self.subtasks[to_id].inputs.append(from_id)
    
    def compute_execution_order(self) -> List[List[str]]:
        """Compute parallel execution batches using topological sort"""
        # Build adjacency list and in-degree count
        in_degree: Dict[str, int] = {task_id: 0 for task_id in self.subtasks}
        adjacency: Dict[str, List[str]] = {task_id: [] for task_id in self.subtasks}
        
        for dep in self.dependencies:
            if dep.from_task_id in self.subtasks and dep.to_task_id in self.subtasks:
                adjacency[dep.from_task_id].append(dep.to_task_id)
                in_degree[dep.to_task_id] += 1
        
        # Kahn's algorithm with level tracking
        batches: List[List[str]] = []
        current_batch = [task_id for task_id, degree in in_degree.items() if degree == 0]
        
        while current_batch:
            batches.append(sorted(current_batch, key=lambda x: self.subtasks[x].priority, reverse=True))
            next_batch = []
            
            for task_id in current_batch:
                for dependent in adjacency[task_id]:
                    in_degree[dependent] -= 1
                    if in_degree[dependent] == 0:
                        next_batch.append(dependent)
            
            current_batch = next_batch
        
        self.execution_order = batches
        return batches
    
    def get_ready_tasks(self, completed: Set[str]) -> List[str]:
        """Get tasks that are ready to execute (all dependencies satisfied)"""
        ready = []
        for task_id, subtask in self.subtasks.items():
            if task_id in completed:
                continue
            # Check if all required inputs are completed
            all_inputs_ready = all(
                inp in completed 
                for inp in subtask.inputs
            )
            if all_inputs_ready:
                ready.append(task_id)
        return ready
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'query_id': self.query_id,
            'subtasks': {k: v.to_dict() for k, v in self.subtasks.items()},
            'dependencies': [
                {'from': d.from_task_id, 'to': d.to_task_id, 'output': d.output_key}
                for d in self.dependencies
            ],
            'execution_order': self.execution_order,
        }


class TaskDecomposer:
    """
    Decomposes trading queries into task graphs.
    
    Uses pattern matching and NLP-like heuristics to identify:
    1. Query intent (research, analyze, trade, etc.)
    2. Required data sources
    3. Required agents
    4. Task dependencies
    """
    
    # Intent patterns (regex-based for simplicity)
    INTENT_PATTERNS = {
        QueryIntent.RESEARCH: [
            r'\bresearch\b', r'\bfind\b', r'\blook up\b', r'\bwhat is\b',
            r'\bfundamentals\b', r'\bnews\b', r'\bsentiment\b',
        ],
        QueryIntent.ANALYZE: [
            r'\banalyze\b', r'\banalysis\b', r'\bchart\b', r'\bpattern\b',
            r'\btechnical\b', r'\bindicator\b', r'\btrend\b',
        ],
        QueryIntent.TRADE: [
            r'\bbuy\b', r'\bsell\b', r'\benter\b', r'\bexit\b', r'\bopen\b',
            r'\bclose\b', r'\bexecute\b', r'\bplace order\b',
        ],
        QueryIntent.POSITION_SIZE: [
            r'\bposition size\b', r'\bhow much\b', r'\blot size\b',
            r'\brisk per trade\b', r'\bcalculate size\b',
        ],
        QueryIntent.RISK_CHECK: [
            r'\brisk\b', r'\bdrawdown\b', r'\bexposure\b', r'\bstop loss\b',
            r'\btake profit\b', r'\brisk reward\b',
        ],
        QueryIntent.MONITOR: [
            r'\bmonitor\b', r'\bwatch\b', r'\btrack\b', r'\balert\b',
            r'\bnotify\b',
        ],
        QueryIntent.BACKTEST: [
            r'\bbacktest\b', r'\bhistorical\b', r'\btest strategy\b',
            r'\bsimulate\b',
        ],
        QueryIntent.EXPLAIN: [
            r'\bexplain\b', r'\bwhy\b', r'\bhow does\b', r'\bwhat does\b',
        ],
        QueryIntent.COMPARE: [
            r'\bcompare\b', r'\bvs\b', r'\bversus\b', r'\bwhich is better\b',
        ],
        QueryIntent.FORECAST: [
            r'\bpredict\b', r'\bforecast\b', r'\bwill\b', r'\bexpect\b',
            r'\bprojection\b',
        ],
    }
    
    # Symbol patterns
    SYMBOL_PATTERNS = [
        r'\b([A-Z]{3}[A-Z]{3})\b',  # EURUSD, GBPJPY
        r'\b([A-Z]{3}/[A-Z]{3})\b',  # EUR/USD
        r'\b(BTC|ETH|XRP|SOL|ADA)[A-Z]{3,4}\b',  # Crypto pairs
        r'\b([A-Z]{1,5})\b',  # Stock symbols
    ]
    
    # Timeframe patterns
    TIMEFRAME_PATTERNS = [
        (r'\b1[- ]?min(ute)?\b', 'M1'),
        (r'\b5[- ]?min(ute)?\b', 'M5'),
        (r'\b15[- ]?min(ute)?\b', 'M15'),
        (r'\b30[- ]?min(ute)?\b', 'M30'),
        (r'\b1[- ]?h(our)?\b', 'H1'),
        (r'\b4[- ]?h(our)?\b', 'H4'),
        (r'\bdaily\b', 'D1'),
        (r'\bweekly\b', 'W1'),
        (r'\bmonthly\b', 'MN'),
    ]
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self._task_counter = 0
    
    def _generate_task_id(self, prefix: str = "task") -> str:
        """Generate unique task ID"""
        self._task_counter += 1
        return f"{prefix}_{self._task_counter}"
    
    def detect_intents(self, query: str) -> List[QueryIntent]:
        """Detect all intents in the query"""
        query_lower = query.lower()
        intents = []
        
        for intent, patterns in self.INTENT_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, query_lower):
                    if intent not in intents:
                        intents.append(intent)
                    break
        
        # Default to ANALYZE if no intent detected
        if not intents:
            intents = [QueryIntent.ANALYZE]
        
        return intents
    
    def extract_symbol(self, query: str) -> Optional[str]:
        """Extract trading symbol from query"""
        query_upper = query.upper()
        
        for pattern in self.SYMBOL_PATTERNS:
            match = re.search(pattern, query_upper)
            if match:
                symbol = match.group(1).replace('/', '')
                # Validate it looks like a real symbol
                if len(symbol) >= 3 and symbol.isalpha():
                    return symbol
        
        return None
    
    def extract_timeframe(self, query: str) -> Optional[str]:
        """Extract timeframe from query"""
        query_lower = query.lower()
        
        for pattern, timeframe in self.TIMEFRAME_PATTERNS:
            if re.search(pattern, query_lower):
                return timeframe
        
        return None
    
    def decompose(self, query: TradingQuery) -> TaskGraph:
        """
        Decompose a trading query into a task graph.
        
        This is the main entry point that:
        1. Detects query intents
        2. Creates appropriate subtasks
        3. Builds dependency graph
        4. Computes execution order
        """
        logger.info(f"Decomposing query: {query.query[:100]}...")
        
        # Create task graph
        graph = TaskGraph(query_id=query.id)
        
        # Detect intents and extract metadata
        intents = self.detect_intents(query.query)
        symbol = query.symbol or self.extract_symbol(query.query)
        timeframe = query.timeframe or self.extract_timeframe(query.query)
        
        logger.info(f"Detected intents: {[i.value for i in intents]}, symbol: {symbol}, timeframe: {timeframe}")
        
        # Build subtasks based on intents
        created_tasks: Dict[str, SubTask] = {}
        
        # Always start with context retrieval from memory
        memory_task = SubTask(
            id=self._generate_task_id("memory"),
            task_type=TaskType.RESEARCH,
            agent_type=AgentType.RESEARCH,
            description="Retrieve relevant context from persistent memory",
            action="Query memory for user preferences, recent trades, and market context",
            outputs=["memory_context"],
            tool="memory_query",
            priority=10,
        )
        graph.add_subtask(memory_task)
        created_tasks["memory"] = memory_task
        
        # Research tasks
        if QueryIntent.RESEARCH in intents or QueryIntent.ANALYZE in intents:
            # Fundamentals research
            fundamentals_task = SubTask(
                id=self._generate_task_id("fundamentals"),
                task_type=TaskType.RESEARCH,
                agent_type=AgentType.RESEARCH,
                description=f"Research fundamentals for {symbol or 'the asset'}",
                action="Gather economic data, news, and fundamental factors",
                inputs=[memory_task.id],
                outputs=["fundamentals_data", "news_summary"],
                tool="web_research",
                priority=8,
            )
            graph.add_subtask(fundamentals_task)
            graph.add_dependency(memory_task.id, fundamentals_task.id, "memory_context")
            created_tasks["fundamentals"] = fundamentals_task
            
            # Sentiment analysis
            sentiment_task = SubTask(
                id=self._generate_task_id("sentiment"),
                task_type=TaskType.ANALYSIS,
                agent_type=AgentType.SENTIMENT,
                description=f"Analyze market sentiment for {symbol or 'the asset'}",
                action="Analyze social media, news sentiment, and positioning data",
                inputs=[memory_task.id],
                outputs=["sentiment_score", "sentiment_breakdown"],
                tool="sentiment_analysis",
                priority=7,
            )
            graph.add_subtask(sentiment_task)
            graph.add_dependency(memory_task.id, sentiment_task.id, "memory_context")
            created_tasks["sentiment"] = sentiment_task
        
        # Technical analysis tasks
        if QueryIntent.ANALYZE in intents or QueryIntent.TRADE in intents:
            # Market data retrieval
            market_data_task = SubTask(
                id=self._generate_task_id("market_data"),
                task_type=TaskType.EXTRACTION,
                agent_type=AgentType.TECHNICAL,
                description=f"Fetch market data for {symbol or 'the asset'} on {timeframe or 'multiple timeframes'}",
                action="Retrieve OHLCV data, order book, and recent trades",
                outputs=["ohlcv_data", "order_book", "recent_trades"],
                tool="market_data_fetch",
                priority=9,
            )
            graph.add_subtask(market_data_task)
            created_tasks["market_data"] = market_data_task
            
            # Technical analysis
            technical_task = SubTask(
                id=self._generate_task_id("technical"),
                task_type=TaskType.ANALYSIS,
                agent_type=AgentType.TECHNICAL,
                description=f"Perform technical analysis on {symbol or 'the asset'}",
                action="Analyze chart patterns, indicators, support/resistance, trend",
                inputs=[market_data_task.id],
                outputs=["technical_signals", "patterns", "key_levels"],
                tool="technical_analysis",
                priority=8,
            )
            graph.add_subtask(technical_task)
            graph.add_dependency(market_data_task.id, technical_task.id, "ohlcv_data")
            created_tasks["technical"] = technical_task
            
            # Microstructure analysis
            microstructure_task = SubTask(
                id=self._generate_task_id("microstructure"),
                task_type=TaskType.ANALYSIS,
                agent_type=AgentType.MICROSTRUCTURE,
                description="Analyze market microstructure",
                action="Analyze order flow, liquidity, and market depth",
                inputs=[market_data_task.id],
                outputs=["order_flow", "liquidity_score", "market_depth"],
                tool="microstructure_analysis",
                priority=6,
            )
            graph.add_subtask(microstructure_task)
            graph.add_dependency(market_data_task.id, microstructure_task.id, "order_book")
            created_tasks["microstructure"] = microstructure_task
        
        # Risk analysis tasks
        if QueryIntent.RISK_CHECK in intents or QueryIntent.POSITION_SIZE in intents or QueryIntent.TRADE in intents:
            risk_task = SubTask(
                id=self._generate_task_id("risk"),
                task_type=TaskType.CALCULATION,
                agent_type=AgentType.RISK,
                description="Calculate risk parameters and position sizing",
                action="Calculate position size, stop loss, take profit, risk/reward",
                inputs=[memory_task.id] + ([created_tasks["technical"].id] if "technical" in created_tasks else []),
                outputs=["position_size", "stop_loss", "take_profit", "risk_reward"],
                tool="risk_calculation",
                priority=7,
            )
            graph.add_subtask(risk_task)
            graph.add_dependency(memory_task.id, risk_task.id, "memory_context")
            if "technical" in created_tasks:
                graph.add_dependency(created_tasks["technical"].id, risk_task.id, "key_levels")
            created_tasks["risk"] = risk_task
        
        # Macro analysis for context
        if QueryIntent.RESEARCH in intents or QueryIntent.FORECAST in intents:
            macro_task = SubTask(
                id=self._generate_task_id("macro"),
                task_type=TaskType.ANALYSIS,
                agent_type=AgentType.MACRO,
                description="Analyze macroeconomic context",
                action="Analyze economic indicators, central bank policy, global factors",
                inputs=[memory_task.id],
                outputs=["macro_outlook", "economic_calendar", "policy_stance"],
                tool="macro_analysis",
                priority=6,
            )
            graph.add_subtask(macro_task)
            graph.add_dependency(memory_task.id, macro_task.id, "memory_context")
            created_tasks["macro"] = macro_task
        
        # Synthesis/Reasoning task - combines all analysis
        synthesis_inputs = [t.id for t in created_tasks.values()]
        synthesis_task = SubTask(
            id=self._generate_task_id("synthesis"),
            task_type=TaskType.SYNTHESIS,
            agent_type=AgentType.REASONING,
            description="Synthesize all analysis into a trading decision",
            action="Combine technical, fundamental, sentiment, and risk analysis into a coherent decision",
            inputs=synthesis_inputs,
            outputs=["trading_signal", "confidence", "reasoning_chain"],
            priority=5,
        )
        graph.add_subtask(synthesis_task)
        for task_id in synthesis_inputs:
            graph.add_dependency(task_id, synthesis_task.id, "output")
        created_tasks["synthesis"] = synthesis_task
        
        # Verification task - cross-reference and validate
        verification_task = SubTask(
            id=self._generate_task_id("verification"),
            task_type=TaskType.VERIFICATION,
            agent_type=AgentType.VALIDATOR,
            description="Verify and cross-reference the analysis",
            action="Cross-reference data sources, check for inconsistencies, validate reasoning",
            inputs=[synthesis_task.id],
            outputs=["verification_result", "confidence_adjustment", "issues"],
            priority=4,
        )
        graph.add_subtask(verification_task)
        graph.add_dependency(synthesis_task.id, verification_task.id, "trading_signal")
        created_tasks["verification"] = verification_task
        
        # Final summary task
        summary_task = SubTask(
            id=self._generate_task_id("summary"),
            task_type=TaskType.SUMMARY,
            agent_type=AgentType.SUMMARIZER,
            description="Generate final trading decision with explanation",
            action="Produce final decision with full reasoning chain and citations",
            inputs=[synthesis_task.id, verification_task.id],
            outputs=["final_decision", "explanation", "citations"],
            priority=3,
        )
        graph.add_subtask(summary_task)
        graph.add_dependency(synthesis_task.id, summary_task.id, "trading_signal")
        graph.add_dependency(verification_task.id, summary_task.id, "verification_result")
        created_tasks["summary"] = summary_task
        
        # Execution task (if trade intent)
        if QueryIntent.TRADE in intents:
            execution_task = SubTask(
                id=self._generate_task_id("execution"),
                task_type=TaskType.EXECUTION,
                agent_type=AgentType.EXECUTION,
                description="Prepare order execution",
                action="Prepare order with optimal routing and timing",
                inputs=[summary_task.id, created_tasks.get("risk", summary_task).id],
                outputs=["order_details", "execution_plan"],
                tool="order_execution",
                priority=2,
            )
            graph.add_subtask(execution_task)
            graph.add_dependency(summary_task.id, execution_task.id, "final_decision")
            if "risk" in created_tasks:
                graph.add_dependency(created_tasks["risk"].id, execution_task.id, "position_size")
            created_tasks["execution"] = execution_task
        
        # Compute execution order
        graph.compute_execution_order()
        
        logger.info(f"Created task graph with {len(graph.subtasks)} subtasks in {len(graph.execution_order)} batches")
        
        return graph
    
    def decompose_simple(self, query_text: str, symbol: Optional[str] = None) -> TaskGraph:
        """Convenience method for simple query decomposition"""
        query = TradingQuery(
            query=query_text,
            symbol=symbol,
        )
        return self.decompose(query)
