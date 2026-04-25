"""
Tool Registry - Standardized Tool Interface

Implements a unified tool registry inspired by:
- OpenAI's function calling (JSON schema for tools)
- LangChain's tool abstraction
- Anthropic's tool use patterns

Key Features:
- Standardized tool interface
- JSON schema validation
- Permission system
- Usage tracking
- Tool composition
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Callable, Type
from dataclasses import dataclass, field
from enum import Enum
from abc import ABC, abstractmethod
import uuid
import json

logger = logging.getLogger(__name__)


class ToolCategory(Enum):
    """Categories of tools"""
    MARKET_DATA = "market_data"
    EXECUTION = "execution"
    ANALYSIS = "analysis"
    RISK = "risk"
    RESEARCH = "research"
    SYSTEM = "system"
    UTILITY = "utility"


class ToolPermission(Enum):
    """Permission levels for tools"""
    PUBLIC = "public"           # Anyone can use
    RESTRICTED = "restricted"   # Requires approval
    ADMIN = "admin"             # Admin only
    SYSTEM = "system"           # System only


@dataclass
class ToolSchema:
    """
    JSON Schema for tool parameters - OpenAI function calling style.
    
    This follows the OpenAI function calling convention for
    defining tool inputs and outputs.
    """
    name: str
    description: str
    parameters: Dict[str, Any]  # JSON Schema
    required: List[str] = field(default_factory=list)
    
    def to_openai_format(self) -> Dict[str, Any]:
        """Convert to OpenAI function calling format"""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": self.parameters,
                "required": self.required
            }
        }
    
    def validate(self, params: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Validate parameters against schema"""
        errors = []
        
        # Check required parameters
        for req in self.required:
            if req not in params:
                errors.append(f"Missing required parameter: {req}")
        
        # Check parameter types (simplified)
        for param_name, param_value in params.items():
            if param_name in self.parameters:
                expected_type = self.parameters[param_name].get('type', 'any')
                if not self._check_type(param_value, expected_type):
                    errors.append(f"Invalid type for {param_name}: expected {expected_type}")
        
        return len(errors) == 0, errors
    
    def _check_type(self, value: Any, expected_type: str) -> bool:
        """Check if value matches expected type"""
        type_map = {
            'string': str,
            'number': (int, float),
            'integer': int,
            'boolean': bool,
            'array': list,
            'object': dict,
            'any': object
        }
        expected = type_map.get(expected_type, object)
        return isinstance(value, expected)


@dataclass
class ToolMetrics:
    """Usage metrics for a tool"""
    total_calls: int = 0
    successful_calls: int = 0
    failed_calls: int = 0
    total_execution_time: float = 0.0
    average_execution_time: float = 0.0
    last_used: Optional[datetime] = None
    
    def record_call(self, success: bool, execution_time: float):
        """Record a tool call"""
        self.total_calls += 1
        if success:
            self.successful_calls += 1
        else:
            self.failed_calls += 1
        
        self.total_execution_time += execution_time
        self.average_execution_time = self.total_execution_time / self.total_calls
        self.last_used = datetime.now()


from typing import Tuple


class BaseTool(ABC):
    """
    Base class for all tools in the system.
    
    Provides standardized interface following OpenAI's function calling pattern.
    """
    
    def __init__(
        self,
        name: str,
        description: str,
        category: ToolCategory = ToolCategory.UTILITY,
        permission: ToolPermission = ToolPermission.PUBLIC
    ):
        self.tool_id = str(uuid.uuid4())
        self.name = name
        self.description = description
        self.category = category
        self.permission = permission
        
        self.schema = self._define_schema()
        self.metrics = ToolMetrics()
        
        self.enabled = True
        self.created_at = datetime.now()
    
    @abstractmethod
    def _define_schema(self) -> ToolSchema:
        """Define the tool's parameter schema - must be implemented"""
        pass
    
    @abstractmethod
    async def _execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the tool - must be implemented"""
        pass
    
    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the tool with validation and metrics tracking.
        
        This is the main entry point for tool execution.
        """
        if not self.enabled:
            return {'success': False, 'error': 'Tool is disabled'}
        
        # Validate parameters
        valid, errors = self.schema.validate(params)
        if not valid:
            return {'success': False, 'error': f'Validation failed: {errors}'}
        
        start_time = datetime.now()
        
        try:
            result = await self._execute(params)
            
            execution_time = (datetime.now() - start_time).total_seconds()
            self.metrics.record_call(True, execution_time)
            
            return result
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            self.metrics.record_call(False, execution_time)
            
            logger.error(f"Tool {self.name} failed: {e}")
            return {'success': False, 'error': str(e)}
    
    def to_openai_function(self) -> Dict[str, Any]:
        """Convert to OpenAI function calling format"""
        return self.schema.to_openai_format()
    
    def get_status(self) -> Dict[str, Any]:
        """Get tool status"""
        return {
            'tool_id': self.tool_id,
            'name': self.name,
            'description': self.description,
            'category': self.category.value,
            'permission': self.permission.value,
            'enabled': self.enabled,
            'metrics': {
                'total_calls': self.metrics.total_calls,
                'success_rate': (
                    self.metrics.successful_calls / self.metrics.total_calls
                    if self.metrics.total_calls > 0 else 1.0
                ),
                'avg_execution_time': self.metrics.average_execution_time
            }
        }


class ToolRegistry:
    """
    Centralized Tool Registry
    
    Manages all tools in the system:
    - Registration and discovery
    - Permission checking
    - Usage tracking
    - Tool composition
    
    ┌─────────────────────────────────────────────────────────────┐
    │                    TOOL REGISTRY                             │
    │                                                              │
    │  ┌─────────────────────────────────────────────────────┐    │
    │  │              Tool Catalog                            │    │
    │  │  - market_data: Get market prices, indicators       │    │
    │  │  - trade_executor: Execute trades                   │    │
    │  │  - risk_calculator: Calculate risk metrics          │    │
    │  │  - strategy_analyzer: Analyze strategies            │    │
    │  │  - backtester: Run backtests                        │    │
    │  └─────────────────────────────────────────────────────┘    │
    │                          │                                   │
    │  ┌─────────────────────────────────────────────────────┐    │
    │  │           Category Index                             │    │
    │  │  MARKET_DATA → [market_data, price_feed]            │    │
    │  │  EXECUTION → [trade_executor, order_manager]        │    │
    │  │  ANALYSIS → [strategy_analyzer, pattern_detector]   │    │
    │  │  RISK → [risk_calculator, position_sizer]           │    │
    │  └─────────────────────────────────────────────────────┘    │
    │                          │                                   │
    │  ┌─────────────────────────────────────────────────────┐    │
    │  │           OpenAI Function Format                     │    │
    │  │  Export tools as OpenAI function definitions        │    │
    │  │  for use with LLM-based agents                      │    │
    │  └─────────────────────────────────────────────────────┘    │
    └─────────────────────────────────────────────────────────────┘
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # Tool storage
        self.tools: Dict[str, BaseTool] = {}
        
        # Category index
        self.category_index: Dict[ToolCategory, List[str]] = {
            cat: [] for cat in ToolCategory
        }
        
        # Tool factories for dynamic creation
        self.tool_factories: Dict[str, Type[BaseTool]] = {}
        
        logger.info("Tool Registry initialized")
    
    async def initialize(self):
        """Initialize the registry with default tools"""
        logger.info("Initializing Tool Registry")
        
        # Register default tools
        await self._register_default_tools()
        
        logger.info(f"Tool Registry ready with {len(self.tools)} tools")
    
    async def _register_default_tools(self):
        """Register default tools"""
        default_tools = [
            MarketDataTool(),
            TradeExecutorTool(),
            RiskCalculatorTool(),
            StrategyAnalyzerTool(),
            BacktesterTool(),
            PortfolioTool(),
            StatusCheckerTool(),
        ]
        
        for tool in default_tools:
            await self.register_tool(tool)
    
    async def register_tool(self, tool: BaseTool) -> str:
        """Register a tool"""
        self.tools[tool.name] = tool
        self.category_index[tool.category].append(tool.name)
        
        logger.info(f"Registered tool: {tool.name} ({tool.category.value})")
        
        return tool.tool_id
    
    async def unregister_tool(self, tool_name: str):
        """Unregister a tool"""
        if tool_name not in self.tools:
            return
        
        tool = self.tools[tool_name]
        
        if tool_name in self.category_index[tool.category]:
            self.category_index[tool.category].remove(tool_name)
        
        del self.tools[tool_name]
        
        logger.info(f"Unregistered tool: {tool_name}")
    
    async def get_tool(self, tool_name: str) -> Optional[BaseTool]:
        """Get a tool by name"""
        return self.tools.get(tool_name)
    
    def get_tools_by_category(self, category: ToolCategory) -> List[BaseTool]:
        """Get all tools in a category"""
        return [
            self.tools[name]
            for name in self.category_index[category]
            if name in self.tools
        ]
    
    def get_all_tools(self) -> List[BaseTool]:
        """Get all registered tools"""
        return list(self.tools.values())
    
    def to_openai_functions(self) -> List[Dict[str, Any]]:
        """
        Export all tools as OpenAI function definitions.
        
        This allows using the tools with OpenAI's function calling API.
        """
        return [
            tool.to_openai_function()
            for tool in self.tools.values()
            if tool.enabled
        ]
    
    async def execute_tool(
        self, 
        tool_name: str, 
        params: Dict[str, Any],
        caller_permission: ToolPermission = ToolPermission.PUBLIC
    ) -> Dict[str, Any]:
        """
        Execute a tool by name.
        
        Args:
            tool_name: Name of the tool to execute
            params: Parameters for the tool
            caller_permission: Permission level of the caller
            
        Returns:
            Tool execution result
        """
        tool = self.tools.get(tool_name)
        
        if not tool:
            return {'success': False, 'error': f'Tool not found: {tool_name}'}
        
        # Check permission
        if not self._check_permission(tool, caller_permission):
            return {'success': False, 'error': 'Permission denied'}
        
        return await tool.execute(params)
    
    def _check_permission(
        self, 
        tool: BaseTool, 
        caller_permission: ToolPermission
    ) -> bool:
        """Check if caller has permission to use tool"""
        permission_hierarchy = {
            ToolPermission.PUBLIC: 0,
            ToolPermission.RESTRICTED: 1,
            ToolPermission.ADMIN: 2,
            ToolPermission.SYSTEM: 3
        }
        
        caller_level = permission_hierarchy.get(caller_permission, 0)
        tool_level = permission_hierarchy.get(tool.permission, 0)
        
        return caller_level >= tool_level
    
    def get_status(self) -> Dict[str, Any]:
        """Get registry status"""
        category_counts = {}
        for cat in ToolCategory:
            count = len(self.category_index[cat])
            if count > 0:
                category_counts[cat.value] = count
        
        return {
            'total_tools': len(self.tools),
            'enabled_tools': sum(1 for t in self.tools.values() if t.enabled),
            'category_distribution': category_counts,
            'tools': [t.get_status() for t in self.tools.values()]
        }
    
    async def shutdown(self):
        """Shutdown the registry"""
        logger.info("Tool Registry shutdown")


# ==================== CONCRETE TOOL IMPLEMENTATIONS ====================

class MarketDataTool(BaseTool):
    """Tool for getting market data"""
    
    def __init__(self):
        super().__init__(
            name="market_data",
            description="Get current market data including prices, indicators, and market state",
            category=ToolCategory.MARKET_DATA,
            permission=ToolPermission.PUBLIC
        )
    
    def _define_schema(self) -> ToolSchema:
        return ToolSchema(
            name="market_data",
            description="Get market data for a symbol",
            parameters={
                "symbol": {"type": "string", "description": "Trading symbol (e.g., EURUSD)"},
                "data_type": {"type": "string", "description": "Type of data: price, indicators, state"},
                "timeframe": {"type": "string", "description": "Timeframe: 1m, 5m, 1h, 1d"}
            },
            required=["symbol"]
        )
    
    async def _execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        symbol = params.get('symbol', 'EURUSD')
        data_type = params.get('data_type', 'state')
        
        # Simulated market data (would connect to real data source)
        return {
            'success': True,
            'symbol': symbol,
            'price': 1.0850,
            'bid': 1.0849,
            'ask': 1.0851,
            'volatility': 0.012,
            'trend': 'bullish',
            'momentum': 0.3,
            'rsi': 55,
            'macd': 0.0002,
            'timestamp': datetime.now().isoformat()
        }


class TradeExecutorTool(BaseTool):
    """Tool for executing trades"""
    
    def __init__(self):
        super().__init__(
            name="trade_executor",
            description="Execute trading operations: buy, sell, modify, cancel orders",
            category=ToolCategory.EXECUTION,
            permission=ToolPermission.RESTRICTED
        )
    
    def _define_schema(self) -> ToolSchema:
        return ToolSchema(
            name="trade_executor",
            description="Execute a trade",
            parameters={
                "operation": {"type": "string", "description": "Operation: buy, sell, modify, cancel"},
                "symbol": {"type": "string", "description": "Trading symbol"},
                "size": {"type": "number", "description": "Position size (lots)"},
                "order_type": {"type": "string", "description": "Order type: market, limit, stop"},
                "price": {"type": "number", "description": "Price for limit/stop orders"},
                "stop_loss": {"type": "number", "description": "Stop loss price"},
                "take_profit": {"type": "number", "description": "Take profit price"}
            },
            required=["operation", "symbol"]
        )
    
    async def _execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        operation = params.get('operation')
        symbol = params.get('symbol')
        size = params.get('size', 0.01)
        
        # Simulated execution (would connect to broker)
        order_id = str(uuid.uuid4())
        
        return {
            'success': True,
            'order_id': order_id,
            'operation': operation,
            'symbol': symbol,
            'size': size,
            'executed_price': 1.0850,
            'executed_at': datetime.now().isoformat(),
            'status': 'filled'
        }


class RiskCalculatorTool(BaseTool):
    """Tool for calculating risk metrics"""
    
    def __init__(self):
        super().__init__(
            name="risk_calculator",
            description="Calculate risk metrics: VaR, position sizing, exposure",
            category=ToolCategory.RISK,
            permission=ToolPermission.PUBLIC
        )
    
    def _define_schema(self) -> ToolSchema:
        return ToolSchema(
            name="risk_calculator",
            description="Calculate risk metrics",
            parameters={
                "operation": {"type": "string", "description": "Operation: get_metrics, calculate_var, position_size"},
                "portfolio": {"type": "object", "description": "Current portfolio state"},
                "proposed_trade": {"type": "object", "description": "Proposed trade for risk assessment"}
            },
            required=["operation"]
        )
    
    async def _execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        operation = params.get('operation', 'get_metrics')
        
        if operation == 'get_metrics':
            return {
                'success': True,
                'var': 0.02,
                'sharpe': 1.5,
                'exposure': 0.3,
                'max_drawdown': 0.05,
                'risk_score': 0.4
            }
        elif operation == 'position_size':
            return {
                'success': True,
                'recommended_size': 0.02,
                'max_size': 0.05,
                'risk_per_trade': 0.01
            }
        
        return {'success': True, 'operation': operation}


class StrategyAnalyzerTool(BaseTool):
    """Tool for analyzing trading strategies"""
    
    def __init__(self):
        super().__init__(
            name="strategy_analyzer",
            description="Analyze trading strategies and market conditions",
            category=ToolCategory.ANALYSIS,
            permission=ToolPermission.PUBLIC
        )
    
    def _define_schema(self) -> ToolSchema:
        return ToolSchema(
            name="strategy_analyzer",
            description="Analyze a trading strategy",
            parameters={
                "strategy": {"type": "object", "description": "Strategy definition"},
                "market_data": {"type": "object", "description": "Current market data"},
                "analysis_type": {"type": "string", "description": "Type: signal, performance, optimization"}
            },
            required=["analysis_type"]
        )
    
    async def _execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        analysis_type = params.get('analysis_type', 'signal')
        
        if analysis_type == 'signal':
            return {
                'success': True,
                'signal': 'buy',
                'confidence': 0.7,
                'reasoning': 'Bullish trend with momentum confirmation'
            }
        elif analysis_type == 'performance':
            return {
                'success': True,
                'win_rate': 0.6,
                'profit_factor': 1.8,
                'sharpe': 1.5
            }
        
        return {'success': True, 'analysis_type': analysis_type}


class BacktesterTool(BaseTool):
    """Tool for backtesting strategies"""
    
    def __init__(self):
        super().__init__(
            name="backtester",
            description="Backtest trading strategies on historical data",
            category=ToolCategory.RESEARCH,
            permission=ToolPermission.PUBLIC
        )
    
    def _define_schema(self) -> ToolSchema:
        return ToolSchema(
            name="backtester",
            description="Run a backtest",
            parameters={
                "strategy": {"type": "object", "description": "Strategy to backtest"},
                "start_date": {"type": "string", "description": "Start date (YYYY-MM-DD)"},
                "end_date": {"type": "string", "description": "End date (YYYY-MM-DD)"},
                "symbol": {"type": "string", "description": "Symbol to backtest on"},
                "initial_capital": {"type": "number", "description": "Initial capital"}
            },
            required=["strategy"]
        )
    
    async def _execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        # Simulated backtest results
        return {
            'success': True,
            'total_return': 0.15,
            'sharpe_ratio': 1.8,
            'max_drawdown': 0.08,
            'win_rate': 0.58,
            'profit_factor': 1.6,
            'total_trades': 150,
            'winning_trades': 87,
            'losing_trades': 63
        }


class PortfolioTool(BaseTool):
    """Tool for portfolio management"""
    
    def __init__(self):
        super().__init__(
            name="portfolio",
            description="Get and manage portfolio state",
            category=ToolCategory.EXECUTION,
            permission=ToolPermission.PUBLIC
        )
    
    def _define_schema(self) -> ToolSchema:
        return ToolSchema(
            name="portfolio",
            description="Portfolio operations",
            parameters={
                "operation": {"type": "string", "description": "Operation: get_state, get_positions, get_history"}
            },
            required=["operation"]
        )
    
    async def _execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        operation = params.get('operation', 'get_state')
        
        if operation == 'get_state':
            return {
                'success': True,
                'equity': 10000,
                'balance': 9500,
                'margin_used': 500,
                'margin_free': 9000,
                'exposure': 0.05,
                'pnl': 150,
                'drawdown': 0.02
            }
        elif operation == 'get_positions':
            return {
                'success': True,
                'positions': [
                    {'symbol': 'EURUSD', 'size': 0.1, 'pnl': 50},
                    {'symbol': 'GBPUSD', 'size': 0.05, 'pnl': -20}
                ]
            }
        
        return {'success': True, 'operation': operation}


class StatusCheckerTool(BaseTool):
    """Tool for checking system status"""
    
    def __init__(self):
        super().__init__(
            name="status_checker",
            description="Check system and component status",
            category=ToolCategory.SYSTEM,
            permission=ToolPermission.PUBLIC
        )
    
    def _define_schema(self) -> ToolSchema:
        return ToolSchema(
            name="status_checker",
            description="Check status",
            parameters={
                "component": {"type": "string", "description": "Component to check: system, agents, tools, all"}
            },
            required=[]
        )
    
    async def _execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        component = params.get('component', 'system')
        
        return {
            'success': True,
            'component': component,
            'status': 'healthy',
            'uptime': 3600,
            'timestamp': datetime.now().isoformat()
        }
