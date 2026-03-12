"""
Perplexity Trading Orchestrator
============================================================

The main orchestrator that coordinates all components of the
Perplexity Computer-style trading architecture.

Like Perplexity Computer's orchestration layer, this:
- Decomposes queries into subtasks
- Routes subtasks to specialized agents
- Manages dependencies between subtasks
- Retrieves data from multiple sources
- Assembles results with QA verification
- Handles human approval for high-stakes actions
"""

import logging
import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Callable
import time

from .core_types import (
    TradingQuery,
    TradingDecision,
    SubTask,
    SubTaskResult,
    AgentType,
    RetrievalSource,
    ApprovalStatus,
)
from .task_decomposer import TaskDecomposer, TaskGraph
from .model_router import ModelRouter, RoutingDecision
from .trading_agents import (
    BaseTradingAgent,
    AgentContext,
    create_agent,
)
from .retrieval_pipeline import RetrievalPipeline
from .persistent_memory import PersistentMemory
from .assembly_qa import AssemblyEngine
from .human_approval import HumanApprovalGate

logger = logging.getLogger(__name__)


@dataclass
class OrchestratorConfig:
    """Configuration for the orchestrator"""
    # Execution settings
    max_parallel_tasks: int = 5
    task_timeout_seconds: float = 30.0
    total_timeout_seconds: float = 120.0
    
    # Retry settings
    max_retries: int = 3
    retry_delay_seconds: float = 1.0
    
    # Memory settings
    memory_db_path: str = "perplexity_trading_memory.db"
    
    # Approval settings
    require_approval_for_trades: bool = True
    approval_timeout_seconds: float = 300.0
    
    # Logging
    verbose: bool = False


class PerplexityTradingOrchestrator:
    """
    Main orchestrator for Perplexity-style trading decisions.
    
    This is the central nervous system that coordinates:
    - Task decomposition
    - Multi-model routing
    - Data retrieval
    - Agent execution
    - Result assembly
    - Human approval
    
    Usage:
    ```python
    orchestrator = PerplexityTradingOrchestrator()
    await orchestrator.initialize()
    
    decision = await orchestrator.analyze("Should I buy EURUSD?")
    print(decision.get_summary())
    ```
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = OrchestratorConfig(**(config or {}))
        
        # Core components
        self.task_decomposer = TaskDecomposer(config)
        self.model_router = ModelRouter(config)
        self.retrieval_pipeline = RetrievalPipeline(config)
        self.memory = PersistentMemory(self.config.memory_db_path, config)
        self.assembly_engine = AssemblyEngine(config)
        self.approval_gate = HumanApprovalGate(config)
        
        # Agent pool
        self.agents: Dict[AgentType, BaseTradingAgent] = {}
        
        # State
        self.initialized = False
        self.current_query: Optional[TradingQuery] = None
        self.current_graph: Optional[TaskGraph] = None
        
        # Metrics
        self.total_queries = 0
        self.successful_queries = 0
        self.total_processing_time_ms = 0.0
    
    async def initialize(self) -> None:
        """Initialize all components"""
        logger.info("Initializing Perplexity Trading Orchestrator...")
        
        # Initialize agents
        for agent_type in AgentType:
            self.agents[agent_type] = create_agent(agent_type, {})
        
        # Load user preferences from memory
        context = self.memory.get_context(['user_preference'])
        logger.info(f"Loaded {len(context.get('user_preferences', {}))} user preferences")
        
        self.initialized = True
        logger.info("Orchestrator initialized successfully")
    
    async def analyze(
        self,
        query: str,
        symbol: Optional[str] = None,
        timeframe: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        require_approval: bool = True,
    ) -> TradingDecision:
        """
        Analyze a trading query and return a decision.
        
        This is the main entry point that orchestrates the entire
        analysis pipeline.
        
        Args:
            query: Natural language trading query
            symbol: Trading symbol (optional, will be extracted from query)
            timeframe: Timeframe for analysis (optional)
            context: Additional context
            require_approval: Whether to require human approval
            
        Returns:
            TradingDecision with action, confidence, reasoning, and citations
        """
        if not self.initialized:
            await self.initialize()
        
        start_time = time.time()
        self.total_queries += 1
        
        logger.info(f"Processing query: {query[:100]}...")
        
        # Create trading query
        trading_query = TradingQuery(
            query=query,
            symbol=symbol,
            timeframe=timeframe,
            context=context or {},
            require_approval=require_approval and self.config.require_approval_for_trades,
        )
        self.current_query = trading_query
        
        try:
            # Step 1: Decompose query into task graph
            logger.info("Step 1: Decomposing query into subtasks...")
            task_graph = self.task_decomposer.decompose(trading_query)
            self.current_graph = task_graph
            
            # Step 2: Route tasks to agents
            logger.info("Step 2: Routing tasks to specialized agents...")
            routing_decisions = self.model_router.route_batch(
                list(task_graph.subtasks.values())
            )
            
            # Step 3: Retrieve data
            logger.info("Step 3: Retrieving data from multiple sources...")
            retrieval_results = await self.retrieval_pipeline.retrieve_all(
                {'symbol': symbol or self.task_decomposer.extract_symbol(query)},
                timeout_seconds=10.0,
            )
            
            # Step 4: Get memory context
            logger.info("Step 4: Loading context from memory...")
            memory_context = self.memory.get_context()
            
            # Step 5: Execute task graph
            logger.info("Step 5: Executing task graph...")
            subtask_results = await self._execute_task_graph(
                task_graph,
                routing_decisions,
                retrieval_results,
                memory_context,
            )
            
            # Step 6: Assemble results
            logger.info("Step 6: Assembling results with QA verification...")
            self.assembly_engine.reset()
            decision = self.assembly_engine.assemble(
                trading_query.id,
                subtask_results,
                symbol=symbol or self.task_decomposer.extract_symbol(query),
            )
            
            # Step 7: Handle approval if needed
            if decision.requires_approval:
                logger.info("Step 7: Requesting human approval...")
                approval = await self.approval_gate.request_approval(
                    decision,
                    timeout_seconds=self.config.approval_timeout_seconds,
                )
                
                if approval.approved:
                    decision.approval_status = ApprovalStatus.APPROVED
                    decision.approval_reason = approval.reason
                    
                    # Apply any modifications
                    if approval.modifications:
                        self._apply_modifications(decision, approval.modifications)
                else:
                    decision.approval_status = ApprovalStatus.REJECTED
                    decision.approval_reason = approval.reason
                    decision.action = "NO_TRADE"
            else:
                decision.approval_status = ApprovalStatus.AUTO_APPROVED
            
            # Step 8: Store in memory
            logger.info("Step 8: Storing decision in memory...")
            self._store_decision_in_memory(decision)
            
            # Update metrics
            processing_time = (time.time() - start_time) * 1000
            decision.processing_time_ms = processing_time
            self.total_processing_time_ms += processing_time
            self.successful_queries += 1
            
            logger.info(f"Query completed in {processing_time:.0f}ms: {decision.action} ({decision.confidence:.0%})")
            
            return decision
            
        except Exception as e:
            logger.error(f"Error processing query: {e}", exc_info=True)
            
            # Return error decision
            return TradingDecision(
                query_id=trading_query.id,
                action="NO_TRADE",
                confidence=0.0,
                reasoning_chain=[f"Error: {str(e)}"],
                requires_approval=False,
                approval_status=ApprovalStatus.REJECTED,
                approval_reason=f"Error during analysis: {str(e)}",
            )
    
    async def _execute_task_graph(
        self,
        graph: TaskGraph,
        routing: Dict[str, RoutingDecision],
        retrieval_results: Dict[RetrievalSource, Any],
        memory_context: Dict[str, Any],
    ) -> Dict[str, SubTaskResult]:
        """Execute all tasks in the graph respecting dependencies"""
        results: Dict[str, SubTaskResult] = {}
        completed: Set[str] = set()
        
        # Prepare initial input data from retrieval
        base_input_data = {}
        for source, result in retrieval_results.items():
            if hasattr(result, 'data'):
                base_input_data[source.value] = result.data
        
        # Execute in batches based on execution order
        for batch in graph.execution_order:
            # Execute batch in parallel
            tasks = []
            for task_id in batch:
                if task_id in completed:
                    continue
                
                subtask = graph.subtasks[task_id]
                routing_decision = routing.get(task_id)
                
                # Gather input data from completed dependencies
                input_data = base_input_data.copy()
                for dep_id in subtask.inputs:
                    if dep_id in results and results[dep_id].success:
                        input_data.update(results[dep_id].output_data)
                
                # Create execution task
                tasks.append(self._execute_subtask(
                    subtask,
                    routing_decision,
                    input_data,
                    memory_context,
                ))
            
            # Wait for batch to complete
            if tasks:
                batch_results = await asyncio.gather(*tasks, return_exceptions=True)
                
                # Process results
                for i, task_id in enumerate(batch):
                    if task_id in completed:
                        continue
                    
                    result = batch_results[i - len([t for t in batch[:i] if t in completed])]
                    
                    if isinstance(result, Exception):
                        results[task_id] = SubTaskResult(
                            subtask_id=task_id,
                            success=False,
                            error=str(result),
                        )
                    else:
                        results[task_id] = result
                    
                    completed.add(task_id)
                    
                    # Release agent
                    if task_id in routing:
                        self.model_router.release_agent(routing[task_id].selected_agent)
        
        return results
    
    async def _execute_subtask(
        self,
        subtask: SubTask,
        routing: Optional[RoutingDecision],
        input_data: Dict[str, Any],
        memory_context: Dict[str, Any],
    ) -> SubTaskResult:
        """Execute a single subtask"""
        start_time = time.time()
        
        # Get agent
        agent_type = routing.selected_agent if routing else subtask.agent_type
        agent = self.agents.get(agent_type)
        
        if not agent:
            return SubTaskResult(
                subtask_id=subtask.id,
                success=False,
                error=f"No agent available for type {agent_type}",
            )
        
        # Create context
        context = AgentContext(
            subtask=subtask,
            input_data=input_data,
            memory_context=memory_context,
            config={
                'symbol': self.current_query.symbol if self.current_query else None,
                'timeframe': self.current_query.timeframe if self.current_query else None,
            },
        )
        
        # Execute with retry
        last_error = None
        for attempt in range(self.config.max_retries):
            try:
                result = await asyncio.wait_for(
                    agent.execute(context),
                    timeout=self.config.task_timeout_seconds,
                )
                
                # Record performance
                latency = (time.time() - start_time) * 1000
                self.model_router.record_result(agent_type, result.success, latency)
                
                if result.success:
                    return result
                
                last_error = result.error
                
            except asyncio.TimeoutError:
                last_error = f"Timeout after {self.config.task_timeout_seconds}s"
            except Exception as e:
                last_error = str(e)
            
            # Wait before retry
            if attempt < self.config.max_retries - 1:
                await asyncio.sleep(self.config.retry_delay_seconds)
        
        # All retries failed
        return SubTaskResult(
            subtask_id=subtask.id,
            success=False,
            error=last_error,
            retry_count=self.config.max_retries,
        )
    
    def _apply_modifications(self, decision: TradingDecision, modifications: Dict[str, Any]) -> None:
        """Apply human modifications to decision"""
        for key, value in modifications.items():
            if hasattr(decision, key):
                setattr(decision, key, value)
                decision.reasoning_chain.append(f"[MODIFIED] {key} changed to {value}")
    
    def _store_decision_in_memory(self, decision: TradingDecision) -> None:
        """Store decision in memory for learning"""
        # Store as trade history
        self.memory.store_trade({
            'query_id': decision.query_id,
            'action': decision.action,
            'symbol': decision.symbol,
            'confidence': decision.confidence,
            'entry_price': decision.entry_price,
            'stop_loss': decision.stop_loss,
            'take_profit': decision.take_profit,
            'position_size': decision.position_size,
            'approval_status': decision.approval_status.value,
            'timestamp': decision.timestamp.isoformat(),
        })
        
        # Store market context
        if decision.symbol:
            self.memory.store_market_context(
                f"last_analysis_{decision.symbol}",
                {
                    'action': decision.action,
                    'confidence': decision.confidence,
                    'timestamp': decision.timestamp.isoformat(),
                }
            )
    
    def get_pending_approvals(self) -> List[Any]:
        """Get pending approval requests"""
        return self.approval_gate.get_pending_requests()
    
    def approve_request(self, request_id: str, reason: Optional[str] = None) -> bool:
        """Approve a pending request"""
        result = self.approval_gate.approve(request_id, reason)
        return result is not None
    
    def reject_request(self, request_id: str, reason: Optional[str] = None) -> bool:
        """Reject a pending request"""
        result = self.approval_gate.reject(request_id, reason)
        return result is not None
    
    def get_stats(self) -> Dict[str, Any]:
        """Get orchestrator statistics"""
        return {
            'total_queries': self.total_queries,
            'successful_queries': self.successful_queries,
            'success_rate': self.successful_queries / self.total_queries if self.total_queries > 0 else 0,
            'avg_processing_time_ms': self.total_processing_time_ms / self.total_queries if self.total_queries > 0 else 0,
            'agent_stats': self.model_router.get_agent_stats(),
            'memory_stats': self.memory.get_stats(),
            'approval_stats': self.approval_gate.get_approval_stats(),
        }
    
    def store_user_preference(self, key: str, value: Any) -> None:
        """Store a user preference"""
        self.memory.store_user_preference(key, value)
    
    def clear_cache(self) -> None:
        """Clear all caches"""
        self.retrieval_pipeline.clear_cache()
        self.memory.clear_short_term()


async def quick_start(config: Optional[Dict[str, Any]] = None) -> PerplexityTradingOrchestrator:
    """Quick start helper to create and initialize orchestrator"""
    orchestrator = PerplexityTradingOrchestrator(config)
    await orchestrator.initialize()
    return orchestrator
