"""
AADS OpenClaw Tool Registry

Inspired by OpenClaw's dynamic tool-use framework. Every agent has access to
a live tool registry. New tools can be registered at runtime. Agents
autonomously discover and select the tools they need via semantic search.

Features:
- Dynamic tool registration at runtime
- Semantic search for tool discovery
- Tool versioning and deprecation
- Usage tracking and analytics
- Rate limiting and access control
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Callable, Any, Union
from datetime import datetime
from enum import Enum
import logging
import numpy as np
from abc import ABC, abstractmethod
import hashlib
import json

logger = logging.getLogger(__name__)


class ToolCategory(Enum):
    """Categories of tools in the registry"""
    MARKET_DATA = "market_data"
    RESEARCH = "research"
    VISION = "vision"
    GRAPH = "graph"
    SIMULATION = "simulation"
    EXECUTION = "execution"
    EVOLUTION = "evolution"
    ANALYSIS = "analysis"
    NOTIFICATION = "notification"


class ToolLatency(Enum):
    """Expected latency categories"""
    REALTIME = "realtime"       # < 10ms
    FAST = "fast"               # < 100ms
    SECONDS = "seconds"         # < 10s
    MINUTES = "minutes"         # < 5min
    ASYNC = "async"             # Background processing


@dataclass
class ToolParameter:
    """Definition of a tool parameter"""
    name: str
    param_type: str             # "str", "int", "float", "bool", "list", "dict"
    description: str
    required: bool = True
    default: Any = None
    constraints: Dict[str, Any] = field(default_factory=dict)  # min, max, enum, etc.


@dataclass
class ToolResult:
    """Result from a tool execution"""
    success: bool
    data: Any
    error: Optional[str] = None
    execution_time_ms: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Tool:
    """
    Tool definition for the OpenClaw registry.
    
    Each tool has:
    - A unique name and description
    - A callable function
    - Parameter definitions
    - Latency expectations
    - Usage tracking
    """
    name: str
    description: str
    fn: Callable[..., Any]
    category: ToolCategory
    latency: ToolLatency
    parameters: List[ToolParameter] = field(default_factory=list)
    
    # Metadata
    version: str = "1.0.0"
    deprecated: bool = False
    deprecation_message: Optional[str] = None
    
    # Access control
    requires_auth: bool = False
    rate_limit_per_minute: int = 60
    
    # Usage tracking
    total_calls: int = 0
    successful_calls: int = 0
    failed_calls: int = 0
    avg_latency_ms: float = 0.0
    last_used: Optional[datetime] = None
    
    # Embedding for semantic search
    embedding: Optional[np.ndarray] = None
    
    def __post_init__(self):
        # Generate embedding from description (placeholder - would use actual embedding model)
        self._generate_embedding()
    
    def _generate_embedding(self) -> None:
        """Generate embedding for semantic search"""
        # Placeholder: create a simple hash-based pseudo-embedding
        # In production, use sentence-transformers or similar
        text = f"{self.name} {self.description} {self.category.value}"
        hash_bytes = hashlib.sha256(text.encode()).digest()
        self.embedding = np.frombuffer(hash_bytes, dtype=np.float32)[:8]
        self.embedding = self.embedding / (np.linalg.norm(self.embedding) + 1e-10)
    
    def execute(self, **kwargs) -> ToolResult:
        """Execute the tool with given parameters"""
        import time
        start = time.time()
        
        try:
            # Validate parameters
            self._validate_params(kwargs)
            
            # Execute function
            result = self.fn(**kwargs)
            
            execution_time = (time.time() - start) * 1000
            
            # Update stats
            self.total_calls += 1
            self.successful_calls += 1
            self.avg_latency_ms = (self.avg_latency_ms * (self.total_calls - 1) + execution_time) / self.total_calls
            self.last_used = datetime.now()
            
            return ToolResult(
                success=True,
                data=result,
                execution_time_ms=execution_time
            )
            
        except Exception as e:
            execution_time = (time.time() - start) * 1000
            self.total_calls += 1
            self.failed_calls += 1
            self.last_used = datetime.now()
            
            logger.error(f"Tool {self.name} failed: {e}")
            
            return ToolResult(
                success=False,
                data=None,
                error=str(e),
                execution_time_ms=execution_time
            )
    
    def _validate_params(self, kwargs: Dict[str, Any]) -> None:
        """Validate parameters against definitions"""
        for param in self.parameters:
            if param.required and param.name not in kwargs:
                raise ValueError(f"Missing required parameter: {param.name}")
            
            if param.name in kwargs:
                value = kwargs[param.name]
                
                # Type checking
                type_map = {
                    'str': str, 'int': int, 'float': (int, float),
                    'bool': bool, 'list': list, 'dict': dict
                }
                expected_type = type_map.get(param.param_type)
                if expected_type and not isinstance(value, expected_type):
                    raise TypeError(f"Parameter {param.name} must be {param.param_type}")
                
                # Constraint checking
                if 'min' in param.constraints and value < param.constraints['min']:
                    raise ValueError(f"Parameter {param.name} below minimum {param.constraints['min']}")
                if 'max' in param.constraints and value > param.constraints['max']:
                    raise ValueError(f"Parameter {param.name} above maximum {param.constraints['max']}")
                if 'enum' in param.constraints and value not in param.constraints['enum']:
                    raise ValueError(f"Parameter {param.name} must be one of {param.constraints['enum']}")
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'description': self.description,
            'category': self.category.value,
            'latency': self.latency.value,
            'parameters': [
                {
                    'name': p.name,
                    'type': p.param_type,
                    'description': p.description,
                    'required': p.required
                }
                for p in self.parameters
            ],
            'version': self.version,
            'deprecated': self.deprecated,
            'stats': {
                'total_calls': self.total_calls,
                'success_rate': self.successful_calls / max(1, self.total_calls),
                'avg_latency_ms': self.avg_latency_ms
            }
        }


class OpenClawRegistry:
    """
    Dynamic tool registry with semantic search capabilities.
    
    Agents query this registry to discover available capabilities.
    New tools can be registered at runtime and are immediately
    available to all agents.
    """
    
    def __init__(self):
        self.registry: Dict[str, Tool] = {}
        self.category_index: Dict[ToolCategory, List[str]] = {cat: [] for cat in ToolCategory}
        self.embedding_index: Dict[str, np.ndarray] = {}
        
        # Initialize with core tools
        self._register_core_tools()
        
        logger.info(f"OpenClawRegistry initialized with {len(self.registry)} tools")
    
    def register(self, tool: Tool) -> None:
        """
        Register a new tool. Immediately available to all agents.
        
        Args:
            tool: Tool to register
        """
        if tool.name in self.registry:
            logger.warning(f"Tool {tool.name} already registered, updating")
        
        self.registry[tool.name] = tool
        self.category_index[tool.category].append(tool.name)
        
        if tool.embedding is not None:
            self.embedding_index[tool.name] = tool.embedding
        
        logger.info(f"Tool registered: {tool.name} — now available to all agents")
    
    def unregister(self, tool_name: str) -> bool:
        """Remove a tool from the registry"""
        if tool_name not in self.registry:
            return False
        
        tool = self.registry[tool_name]
        self.category_index[tool.category].remove(tool_name)
        del self.registry[tool_name]
        
        if tool_name in self.embedding_index:
            del self.embedding_index[tool_name]
        
        logger.info(f"Tool unregistered: {tool_name}")
        return True
    
    def get(self, tool_name: str) -> Optional[Tool]:
        """Get a tool by name"""
        return self.registry.get(tool_name)
    
    def discover(self, task_description: str, top_k: int = 5) -> List[Tool]:
        """
        Discover relevant tools via semantic search.
        
        Agent describes its task in natural language.
        Registry returns the most relevant tools.
        
        Args:
            task_description: Natural language task description
            top_k: Number of tools to return
            
        Returns:
            List of most relevant tools
        """
        # Generate query embedding
        query_embedding = self._embed_text(task_description)
        
        # Calculate similarities
        similarities = {}
        for name, embedding in self.embedding_index.items():
            similarity = np.dot(query_embedding, embedding)
            similarities[name] = similarity
        
        # Sort by similarity
        sorted_tools = sorted(similarities.items(), key=lambda x: x[1], reverse=True)
        
        # Return top-k non-deprecated tools
        results = []
        for name, _ in sorted_tools:
            tool = self.registry[name]
            if not tool.deprecated:
                results.append(tool)
                if len(results) >= top_k:
                    break
        
        return results
    
    def get_by_category(self, category: ToolCategory) -> List[Tool]:
        """Get all tools in a category"""
        tool_names = self.category_index.get(category, [])
        return [self.registry[name] for name in tool_names if name in self.registry]
    
    def execute(self, tool_name: str, **kwargs) -> ToolResult:
        """Execute a tool by name"""
        tool = self.get(tool_name)
        if not tool:
            return ToolResult(success=False, data=None, error=f"Tool not found: {tool_name}")
        
        if tool.deprecated:
            logger.warning(f"Using deprecated tool: {tool_name}. {tool.deprecation_message}")
        
        return tool.execute(**kwargs)
    
    def _embed_text(self, text: str) -> np.ndarray:
        """Generate embedding for text (placeholder)"""
        hash_bytes = hashlib.sha256(text.encode()).digest()
        embedding = np.frombuffer(hash_bytes, dtype=np.float32)[:8]
        return embedding / (np.linalg.norm(embedding) + 1e-10)
    
    def _register_core_tools(self) -> None:
        """Register the core AADS tools"""
        
        # Market Data Tools
        self.register(Tool(
            name="get_orderbook",
            description="Fetch real-time order book depth for an asset",
            fn=lambda asset, depth=10: {"bids": [], "asks": [], "asset": asset},
            category=ToolCategory.MARKET_DATA,
            latency=ToolLatency.REALTIME,
            parameters=[
                ToolParameter("asset", "str", "Asset ticker symbol"),
                ToolParameter("depth", "int", "Order book depth", required=False, default=10)
            ]
        ))
        
        self.register(Tool(
            name="get_options_chain",
            description="Fetch options chain for an underlying asset",
            fn=lambda asset, expiry=None: {"calls": [], "puts": [], "asset": asset},
            category=ToolCategory.MARKET_DATA,
            latency=ToolLatency.REALTIME,
            parameters=[
                ToolParameter("asset", "str", "Underlying asset ticker"),
                ToolParameter("expiry", "str", "Expiration date (YYYY-MM-DD)", required=False)
            ]
        ))
        
        self.register(Tool(
            name="get_dark_pool",
            description="Fetch dark pool prints and block trades",
            fn=lambda asset, min_size=1e6: {"prints": [], "asset": asset},
            category=ToolCategory.MARKET_DATA,
            latency=ToolLatency.FAST,
            parameters=[
                ToolParameter("asset", "str", "Asset ticker"),
                ToolParameter("min_size", "float", "Minimum trade size", required=False, default=1e6)
            ]
        ))
        
        # Research Tools
        self.register(Tool(
            name="search_sec",
            description="Search SEC EDGAR filings (10-K, 10-Q, 8-K)",
            fn=lambda query, filing_type=None: {"results": [], "query": query},
            category=ToolCategory.RESEARCH,
            latency=ToolLatency.SECONDS,
            parameters=[
                ToolParameter("query", "str", "Search query"),
                ToolParameter("filing_type", "str", "Filing type filter", required=False)
            ]
        ))
        
        self.register(Tool(
            name="parse_earnings",
            description="Parse earnings call transcript for sentiment and key metrics",
            fn=lambda transcript: {"sentiment": 0.0, "key_phrases": []},
            category=ToolCategory.RESEARCH,
            latency=ToolLatency.SECONDS,
            parameters=[
                ToolParameter("transcript", "str", "Earnings call transcript text")
            ]
        ))
        
        self.register(Tool(
            name="search_patents",
            description="Search patent filings for R&D signals",
            fn=lambda company, keywords=None: {"patents": []},
            category=ToolCategory.RESEARCH,
            latency=ToolLatency.SECONDS,
            parameters=[
                ToolParameter("company", "str", "Company name"),
                ToolParameter("keywords", "list", "Keywords to search", required=False)
            ]
        ))
        
        self.register(Tool(
            name="web_search",
            description="Search the web for relevant information",
            fn=lambda query, num_results=10: {"results": []},
            category=ToolCategory.RESEARCH,
            latency=ToolLatency.SECONDS,
            parameters=[
                ToolParameter("query", "str", "Search query"),
                ToolParameter("num_results", "int", "Number of results", required=False, default=10)
            ]
        ))
        
        # Vision Tools
        self.register(Tool(
            name="analyze_chart",
            description="Analyze chart image for technical patterns using OpenCLIP",
            fn=lambda image_path: {"patterns": [], "sentiment": "neutral"},
            category=ToolCategory.VISION,
            latency=ToolLatency.SECONDS,
            parameters=[
                ToolParameter("image_path", "str", "Path to chart image")
            ]
        ))
        
        self.register(Tool(
            name="analyze_satellite",
            description="Analyze satellite imagery for economic signals",
            fn=lambda image_path, target_type: {"activity_level": 0.5},
            category=ToolCategory.VISION,
            latency=ToolLatency.MINUTES,
            parameters=[
                ToolParameter("image_path", "str", "Path to satellite image"),
                ToolParameter("target_type", "str", "Type of target (parking_lot, factory, port)")
            ]
        ))
        
        self.register(Tool(
            name="analyze_image",
            description="General image analysis for financial signals",
            fn=lambda image_path: {"category": "unknown", "confidence": 0.0},
            category=ToolCategory.VISION,
            latency=ToolLatency.SECONDS,
            parameters=[
                ToolParameter("image_path", "str", "Path to image")
            ]
        ))
        
        # Graph Tools
        self.register(Tool(
            name="query_ontology",
            description="Query the market knowledge graph",
            fn=lambda cypher_query: {"results": []},
            category=ToolCategory.GRAPH,
            latency=ToolLatency.FAST,
            parameters=[
                ToolParameter("cypher_query", "str", "Cypher query string")
            ]
        ))
        
        self.register(Tool(
            name="update_graph",
            description="Update the market knowledge graph with new data",
            fn=lambda node_type, properties: {"success": True},
            category=ToolCategory.GRAPH,
            latency=ToolLatency.FAST,
            parameters=[
                ToolParameter("node_type", "str", "Type of node to create/update"),
                ToolParameter("properties", "dict", "Node properties")
            ]
        ))
        
        self.register(Tool(
            name="find_contagion",
            description="Find contagion paths in the knowledge graph",
            fn=lambda source_asset, max_hops=3: {"paths": []},
            category=ToolCategory.GRAPH,
            latency=ToolLatency.SECONDS,
            parameters=[
                ToolParameter("source_asset", "str", "Starting asset"),
                ToolParameter("max_hops", "int", "Maximum path length", required=False, default=3)
            ]
        ))
        
        # Simulation Tools
        self.register(Tool(
            name="run_monte_carlo",
            description="Run Monte Carlo simulation for price paths",
            fn=lambda asset, scenarios=10000, horizon_days=20: {"paths": [], "stats": {}},
            category=ToolCategory.SIMULATION,
            latency=ToolLatency.SECONDS,
            parameters=[
                ToolParameter("asset", "str", "Asset to simulate"),
                ToolParameter("scenarios", "int", "Number of scenarios", required=False, default=10000),
                ToolParameter("horizon_days", "int", "Simulation horizon", required=False, default=20)
            ]
        ))
        
        self.register(Tool(
            name="run_causal_sim",
            description="Run causal intervention simulation (do-calculus)",
            fn=lambda variable, value, observe: {"results": {}},
            category=ToolCategory.SIMULATION,
            latency=ToolLatency.SECONDS,
            parameters=[
                ToolParameter("variable", "str", "Variable to intervene on"),
                ToolParameter("value", "float", "Intervention value"),
                ToolParameter("observe", "list", "Variables to observe")
            ]
        ))
        
        self.register(Tool(
            name="run_stress_test",
            description="Run historical stress test scenarios",
            fn=lambda portfolio, scenarios: {"results": {}},
            category=ToolCategory.SIMULATION,
            latency=ToolLatency.SECONDS,
            parameters=[
                ToolParameter("portfolio", "dict", "Portfolio positions"),
                ToolParameter("scenarios", "list", "Stress scenarios to run")
            ]
        ))
        
        # Execution Tools
        self.register(Tool(
            name="submit_equity",
            description="Submit equity order via Alpaca/IBKR",
            fn=lambda asset, side, quantity, order_type="market": {"order_id": None},
            category=ToolCategory.EXECUTION,
            latency=ToolLatency.FAST,
            parameters=[
                ToolParameter("asset", "str", "Asset ticker"),
                ToolParameter("side", "str", "buy or sell"),
                ToolParameter("quantity", "float", "Order quantity"),
                ToolParameter("order_type", "str", "Order type", required=False, default="market")
            ]
        ))
        
        self.register(Tool(
            name="submit_crypto",
            description="Submit crypto order via Binance/Coinbase",
            fn=lambda asset, side, quantity, order_type="market": {"order_id": None},
            category=ToolCategory.EXECUTION,
            latency=ToolLatency.FAST,
            parameters=[
                ToolParameter("asset", "str", "Crypto pair"),
                ToolParameter("side", "str", "buy or sell"),
                ToolParameter("quantity", "float", "Order quantity"),
                ToolParameter("order_type", "str", "Order type", required=False, default="market")
            ]
        ))
        
        self.register(Tool(
            name="submit_polymarket",
            description="Submit Polymarket order via CLOB",
            fn=lambda contract_id, side, amount, price: {"order_id": None},
            category=ToolCategory.EXECUTION,
            latency=ToolLatency.SECONDS,
            parameters=[
                ToolParameter("contract_id", "str", "Polymarket contract ID"),
                ToolParameter("side", "str", "YES or NO"),
                ToolParameter("amount", "float", "Order amount in USDC"),
                ToolParameter("price", "float", "Limit price (0-1)")
            ]
        ))
        
        # Evolution Tools
        self.register(Tool(
            name="run_backtest",
            description="Run walk-forward backtest on a strategy genome",
            fn=lambda genome, data_hash: {"sharpe": 0.0, "max_dd": 0.0},
            category=ToolCategory.EVOLUTION,
            latency=ToolLatency.SECONDS,
            parameters=[
                ToolParameter("genome", "dict", "Strategy genome"),
                ToolParameter("data_hash", "str", "Market data hash")
            ]
        ))
        
        self.register(Tool(
            name="evolve_signal",
            description="Run one AlphaEvolve step to generate improved signal code",
            fn=lambda current_code, context: {"new_code": "", "improvement": 0.0},
            category=ToolCategory.EVOLUTION,
            latency=ToolLatency.MINUTES,
            parameters=[
                ToolParameter("current_code", "str", "Current signal code"),
                ToolParameter("context", "dict", "Market context and performance")
            ]
        ))
        
        self.register(Tool(
            name="mutate_genome",
            description="Apply Sakana-style mutation to a strategy genome",
            fn=lambda genome, mutation_rate=0.15: {"mutated_genome": {}},
            category=ToolCategory.EVOLUTION,
            latency=ToolLatency.SECONDS,
            parameters=[
                ToolParameter("genome", "dict", "Strategy genome to mutate"),
                ToolParameter("mutation_rate", "float", "Mutation rate", required=False, default=0.15)
            ]
        ))
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get registry statistics"""
        total_calls = sum(t.total_calls for t in self.registry.values())
        successful_calls = sum(t.successful_calls for t in self.registry.values())
        
        category_stats = {}
        for cat in ToolCategory:
            tools = self.get_by_category(cat)
            category_stats[cat.value] = {
                'count': len(tools),
                'total_calls': sum(t.total_calls for t in tools)
            }
        
        most_used = sorted(
            self.registry.values(),
            key=lambda t: t.total_calls,
            reverse=True
        )[:5]
        
        return {
            'total_tools': len(self.registry),
            'total_calls': total_calls,
            'success_rate': successful_calls / max(1, total_calls),
            'category_stats': category_stats,
            'most_used': [t.name for t in most_used],
            'deprecated_count': sum(1 for t in self.registry.values() if t.deprecated)
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize registry"""
        return {
            'tools': {name: tool.to_dict() for name, tool in self.registry.items()},
            'statistics': self.get_statistics()
        }
