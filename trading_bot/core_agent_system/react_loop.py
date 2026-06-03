"""
ReAct Loop - OpenAI GPT-4 Agent Pattern

Implements the ReAct (Reasoning + Acting) paradigm from:
"ReAct: Synergizing Reasoning and Acting in Language Models" (Yao et al., 2022)

This is the pattern used by GPT-4 and Claude for agentic tasks:
1. THOUGHT: Reason about the current situation
2. ACTION: Decide what action to take
3. OBSERVATION: Observe the result
4. Repeat until task is complete

Key Features:
- Interleaved reasoning and acting
- Tool use with reflection
- Self-correction on errors
- Interpretable decision traces
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Callable, Union
from dataclasses import dataclass, field
from enum import Enum
from abc import ABC, abstractmethod
import uuid

logger = logging.getLogger(__name__)


class StepType(Enum):
    """Types of steps in the ReAct loop"""
    THOUGHT = "thought"
    ACTION = "action"
    OBSERVATION = "observation"
    REFLECTION = "reflection"  # Added for self-correction
    CONCLUSION = "conclusion"


@dataclass
class Thought:
    """
    A thought in the reasoning chain.
    
    Represents the agent's internal reasoning about:
    - Current situation assessment
    - What needs to be done
    - Why a particular action is chosen
    """
    thought_id: str
    content: str
    reasoning_type: str  # 'assessment', 'planning', 'evaluation', 'reflection'
    confidence: float
    timestamp: datetime = field(default_factory=datetime.now)
    related_observations: List[str] = field(default_factory=list)
    
    def __str__(self):
        return f"THOUGHT [{self.reasoning_type}]: {self.content}"


@dataclass
class Action:
    """
    An action to be executed.
    
    Represents a concrete action the agent wants to take,
    including the tool to use and parameters.
    """
    action_id: str
    action_type: str
    tool_name: str
    parameters: Dict[str, Any]
    expected_outcome: str
    timestamp: datetime = field(default_factory=datetime.now)
    thought_id: Optional[str] = None  # Link to reasoning
    
    def __str__(self):
        return f"ACTION [{self.tool_name}]: {self.parameters}"


@dataclass
class Observation:
    """
    An observation from the environment.
    
    Represents the result of an action or external information
    that the agent perceives.
    """
    observation_id: str
    content: Any
    source: str  # 'tool_result', 'environment', 'memory', 'user'
    success: bool
    error_message: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    action_id: Optional[str] = None  # Link to action that caused this
    
    def __str__(self):
        status = "SUCCESS" if self.success else "FAILED"
        return f"OBSERVATION [{status}]: {self.content}"


@dataclass
class ReActTrace:
    """
    Complete trace of a ReAct reasoning session.
    
    Contains the full chain of thoughts, actions, and observations
    for interpretability and debugging.
    """
    trace_id: str
    task: str
    steps: List[Union[Thought, Action, Observation]]
    start_time: datetime
    end_time: Optional[datetime] = None
    success: bool = False
    final_answer: Optional[Any] = None
    total_tokens: int = 0
    
    def add_step(self, step: Union[Thought, Action, Observation]):
        """Add a step to the trace"""
        self.steps.append(step)
    
    def get_thoughts(self) -> List[Thought]:
        """Get all thoughts in the trace"""
        return [s for s in self.steps if isinstance(s, Thought)]
    
    def get_actions(self) -> List[Action]:
        """Get all actions in the trace"""
        return [s for s in self.steps if isinstance(s, Action)]
    
    def get_observations(self) -> List[Observation]:
        """Get all observations in the trace"""
        return [s for s in self.steps if isinstance(s, Observation)]
    
    def to_string(self) -> str:
        """Convert trace to readable string"""
        lines = [f"=== ReAct Trace: {self.task} ==="]
        for i, step in enumerate(self.steps):
            lines.append(f"Step {i+1}: {step}")
        if self.final_answer:
            lines.append(f"FINAL ANSWER: {self.final_answer}")
        return "\n".join(lines)


class ReActLoop:
    """
    ReAct Loop Implementation - OpenAI/Anthropic Agent Pattern
    
    This implements the core reasoning loop used by modern AI agents:
    
    ┌─────────────────────────────────────────────────────────────┐
    │                      ReAct Loop                              │
    │                                                              │
    │   ┌──────────┐    ┌──────────┐    ┌─────────────┐          │
    │   │ THOUGHT  │───▶│  ACTION  │───▶│ OBSERVATION │          │
    │   │          │    │          │    │             │          │
    │   │ Reason   │    │ Execute  │    │ Perceive    │          │
    │   │ about    │    │ tool or  │    │ result and  │          │
    │   │ situation│    │ action   │    │ environment │          │
    │   └──────────┘    └──────────┘    └──────┬──────┘          │
    │        ▲                                  │                 │
    │        │                                  │                 │
    │        └──────────────────────────────────┘                 │
    │                    (loop until done)                        │
    │                                                              │
    │   ┌─────────────────────────────────────────────────────┐   │
    │   │                   REFLECTION                         │   │
    │   │  Self-correct if observation indicates error         │   │
    │   └─────────────────────────────────────────────────────┘   │
    └─────────────────────────────────────────────────────────────┘
    
    Key innovations over simple action loops:
    1. Explicit reasoning before each action
    2. Reflection and self-correction on errors
    3. Full trace for interpretability
    4. Tool use with structured parameters
    """
    
    def __init__(
        self,
        tool_registry=None,
        memory_system=None,
        max_iterations: int = 10,
        reflection_threshold: float = 0.5
    ):
        self.tool_registry = tool_registry
        self.memory_system = memory_system
        self.max_iterations = max_iterations
        self.reflection_threshold = reflection_threshold
        
        # Trace storage
        self.traces: List[ReActTrace] = []
        self.current_trace: Optional[ReActTrace] = None
        
        # Reasoning templates (inspired by chain-of-thought prompting)
        self.thought_templates = {
            'assessment': "Given the current state: {state}, I observe that {observation}.",
            'planning': "To achieve {goal}, I should {plan}.",
            'evaluation': "The action {action} resulted in {result}. This {assessment}.",
            'reflection': "The previous attempt failed because {reason}. I should try {alternative}."
        }
        
        logger.info("ReAct Loop initialized")
    
    async def initialize(self):
        """Initialize the ReAct loop"""
        logger.info("ReAct Loop ready")
    
    async def run(
        self,
        task: str,
        context: Dict[str, Any],
        available_tools: Optional[List[str]] = None
    ) -> ReActTrace:
        """
        Run the ReAct loop for a given task.
        
        Args:
            task: The task to accomplish
            context: Current context/state
            available_tools: List of tool names that can be used
            
        Returns:
            Complete ReActTrace with all reasoning steps
        """
        # Initialize trace
        trace = ReActTrace(
            trace_id=str(uuid.uuid4()),
            task=task,
            steps=[],
            start_time=datetime.now()
        )
        self.current_trace = trace
        
        logger.info(f"Starting ReAct loop for task: {task}")
        
        iteration = 0
        done = False
        last_observation = None
        
        while not done and iteration < self.max_iterations:
            iteration += 1
            logger.debug(f"ReAct iteration {iteration}")
            
            # Step 1: THOUGHT - Reason about current situation
            thought = await self._generate_thought(
                task, context, last_observation, iteration
            )
            trace.add_step(thought)
            
            # Check if we should conclude
            if thought.reasoning_type == 'conclusion':
                done = True
                trace.final_answer = thought.content
                break
            
            # Step 2: ACTION - Decide and execute action
            action = await self._generate_action(
                thought, context, available_tools
            )
            trace.add_step(action)
            
            # Step 3: Execute action and get OBSERVATION
            observation = await self._execute_action(action)
            trace.add_step(observation)
            last_observation = observation
            
            # Step 4: REFLECTION - Self-correct if needed
            if not observation.success:
                reflection = await self._reflect_on_failure(
                    thought, action, observation, context
                )
                trace.add_step(reflection)
                
                # Update context with reflection
                context['last_error'] = observation.error_message
                context['reflection'] = reflection.content
            else:
                # Update context with successful observation
                context['last_result'] = observation.content
            
            # Check if task is complete
            done = await self._check_completion(task, context, observation)
        
        # Finalize trace
        trace.end_time = datetime.now()
        trace.success = done and (last_observation is None or last_observation.success)
        
        self.traces.append(trace)
        self.current_trace = None
        
        logger.info(f"ReAct loop completed: success={trace.success}, iterations={iteration}")
        
        return trace
    
    async def _generate_thought(
        self,
        task: str,
        context: Dict[str, Any],
        last_observation: Optional[Observation],
        iteration: int
    ) -> Thought:
        """
        Generate a thought based on current situation.
        
        This is where the agent reasons about:
        - What is the current state?
        - What has been tried?
        - What should be done next?
        """
        thought_id = str(uuid.uuid4())
        
        # Determine reasoning type based on context
        if iteration == 1:
            reasoning_type = 'assessment'
            content = self._assess_situation(task, context)
        elif last_observation and not last_observation.success:
            reasoning_type = 'reflection'
            content = self._reflect_on_error(last_observation, context)
        elif self._is_task_complete(task, context):
            reasoning_type = 'conclusion'
            content = self._generate_conclusion(task, context)
        else:
            reasoning_type = 'planning'
            content = self._plan_next_step(task, context, last_observation)
        
        # Calculate confidence based on context
        confidence = self._calculate_thought_confidence(
            reasoning_type, context, last_observation
        )
        
        thought = Thought(
            thought_id=thought_id,
            content=content,
            reasoning_type=reasoning_type,
            confidence=confidence,
            related_observations=[last_observation.observation_id] if last_observation else []
        )
        
        logger.debug(f"Generated thought: {thought}")
        
        return thought
    
    def _assess_situation(self, task: str, context: Dict[str, Any]) -> str:
        """Generate initial situation assessment"""
        market_state = context.get('market_state', {})
        portfolio_state = context.get('portfolio_state', {})
        
        return (
            f"Task: {task}. "
            f"Current market shows price={market_state.get('price', 'unknown')}, "
            f"volatility={market_state.get('volatility', 'unknown')}. "
            f"Portfolio has equity={portfolio_state.get('equity', 'unknown')}, "
            f"exposure={portfolio_state.get('exposure', 'unknown')}. "
            f"I need to analyze the situation and determine the best course of action."
        )
    
    def _reflect_on_error(
        self, 
        observation: Observation, 
        context: Dict[str, Any]
    ) -> str:
        """Generate reflection on error"""
        return (
            f"The previous action failed with error: {observation.error_message}. "
            f"I need to reconsider my approach. "
            f"Possible issues: incorrect parameters, wrong tool, or invalid state. "
            f"I will try an alternative approach."
        )
    
    def _plan_next_step(
        self,
        task: str,
        context: Dict[str, Any],
        last_observation: Optional[Observation]
    ) -> str:
        """Generate plan for next step"""
        if last_observation and last_observation.success:
            return (
                f"Previous action succeeded with result: {last_observation.content}. "
                f"Based on this, I should proceed with the next step towards: {task}."
            )
        else:
            return (
                f"To accomplish '{task}', I need to take the next logical step. "
                f"Based on current context, I will select an appropriate action."
            )
    
    def _generate_conclusion(self, task: str, context: Dict[str, Any]) -> str:
        """Generate conclusion when task is complete"""
        result = context.get('last_result', 'completed')
        return f"Task '{task}' has been completed. Final result: {result}"
    
    def _is_task_complete(self, task: str, context: Dict[str, Any]) -> bool:
        """Check if task is complete based on context"""
        # Check for explicit completion flag
        if context.get('task_complete', False):
            return True
        
        # Check for successful result
        if context.get('last_result') and context.get('goal_achieved', False):
            return True
        
        # Research Lab Grade: Check for signals or recommendations
        if 'signal' in context or 'recommendation' in context:
            return True

        return False
    
    def _calculate_thought_confidence(
        self,
        reasoning_type: str,
        context: Dict[str, Any],
        last_observation: Optional[Observation]
    ) -> float:
        """Calculate confidence in the thought"""
        base_confidence = 0.7
        
        # Reduce confidence after errors
        if last_observation and not last_observation.success:
            base_confidence -= 0.2
        
        # Increase confidence with more context
        if context.get('last_result'):
            base_confidence += 0.1
        
        # Conclusions have higher confidence
        if reasoning_type == 'conclusion':
            base_confidence += 0.1
        
        return min(max(base_confidence, 0.1), 1.0)
    
    async def _generate_action(
        self,
        thought: Thought,
        context: Dict[str, Any],
        available_tools: Optional[List[str]]
    ) -> Action:
        """
        Generate an action based on the thought.
        
        This selects the appropriate tool and parameters
        to execute the plan from the thought.
        """
        action_id = str(uuid.uuid4())
        
        # Determine action based on thought content and context
        action_spec = await self._select_action(thought, context, available_tools)
        
        action = Action(
            action_id=action_id,
            action_type=action_spec['type'],
            tool_name=action_spec['tool'],
            parameters=action_spec['parameters'],
            expected_outcome=action_spec['expected_outcome'],
            thought_id=thought.thought_id
        )
        
        logger.debug(f"Generated action: {action}")
        
        return action
    
    async def _select_action(
        self,
        thought: Thought,
        context: Dict[str, Any],
        available_tools: Optional[List[str]]
    ) -> Dict[str, Any]:
        """Select appropriate action based on thought"""
        # Default action selection logic
        # In production, this would use an LLM or learned policy
        
        reasoning_type = thought.reasoning_type
        
        if reasoning_type == 'assessment':
            # Initial assessment -> gather more information
            return {
                'type': 'information_gathering',
                'tool': 'market_data',
                'parameters': {'symbol': context.get('symbol', 'EURUSD'), 'data_type': 'state'},
                'parameters': {'symbol': context.get('market_state', {}).get('symbol', 'EURUSD')},
                'expected_outcome': 'Comprehensive market analysis'
            }
        
        elif reasoning_type == 'planning':
            # Planning -> execute planned action
            if 'trade' in thought.content.lower() and 'planned_trade' in context:
                return {
                    'type': 'trade_execution',
                    'tool': 'trade_executor',
                    'parameters': context.get('planned_trade', {'operation': 'buy', 'symbol': context.get('symbol', 'EURUSD')}),
                    'expected_outcome': 'Trade executed successfully'
                }
            else:
                return {
                    'type': 'analysis',
                    'tool': 'strategy_analyzer',
                    'parameters': {'analysis_type': 'signal', 'market_data': context.get('market_state', {})},
                    'expected_outcome': 'Strategy analysis complete'
                }
        
        elif reasoning_type == 'reflection':
            # Reflection -> try alternative approach
            return {
                'type': 'alternative_action',
                'tool': 'fallback_handler',
                'parameters': {
                    'previous_error': context.get('last_error'),
                    'context': context
                },
                'expected_outcome': 'Alternative approach executed'
            }
        
        else:
            # Default action
            return {
                'type': 'default',
                'tool': 'status_checker',
                'parameters': {},
                'expected_outcome': 'Status check complete'
            }
    
    async def _execute_action(self, action: Action) -> Observation:
        """
        Execute an action and return observation.
        
        This calls the appropriate tool and captures the result.
        """
        observation_id = str(uuid.uuid4())
        
        try:
            # Get tool from registry
            if self.tool_registry:
                tool = await self.tool_registry.get_tool(action.tool_name)
                if tool:
                    result = await tool.execute(action.parameters)
                    return Observation(
                        observation_id=observation_id,
                        content=result,
                        source='tool_result',
                        success=result.get('success', True) if isinstance(result, dict) else True,
                        action_id=action.action_id
                    )
            
            # Fallback: simulate execution
            return Observation(
                observation_id=observation_id,
                content={'status': 'simulated', 'action': action.action_type},
                source='simulation',
                success=True,
                action_id=action.action_id
            )
            
        except Exception as e:
            logger.error(f"Action execution failed: {e}")
            return Observation(
                observation_id=observation_id,
                content=None,
                source='tool_result',
                success=False,
                error_message=str(e),
                action_id=action.action_id
            )
    
    async def _reflect_on_failure(
        self,
        thought: Thought,
        action: Action,
        observation: Observation,
        context: Dict[str, Any]
    ) -> Thought:
        """
        Generate reflection on failure - Self-correction mechanism.
        
        This is a key feature that allows the agent to learn from
        mistakes within a single session.
        """
        reflection_id = str(uuid.uuid4())
        
        # Analyze the failure
        error = observation.error_message or "Unknown error"
        
        # Generate reflection content
        content = (
            f"Action '{action.action_type}' using tool '{action.tool_name}' failed. "
            f"Error: {error}. "
            f"Original reasoning: {thought.content}. "
            f"I need to reconsider: "
            f"1) Were the parameters correct? "
            f"2) Was this the right tool? "
            f"3) Is the current state valid for this action? "
            f"I will adjust my approach accordingly."
        )
        
        reflection = Thought(
            thought_id=reflection_id,
            content=content,
            reasoning_type='reflection',
            confidence=0.5,  # Lower confidence after failure
            related_observations=[observation.observation_id]
        )
        
        logger.debug(f"Generated reflection: {reflection}")
        
        return reflection
    
    async def _check_completion(
        self,
        task: str,
        context: Dict[str, Any],
        observation: Observation
    ) -> bool:
        """Check if the task is complete"""
        # Check explicit completion
        if context.get('task_complete', False):
            return True
        
        # Check if observation indicates completion
        if observation.success:
            content = observation.content
            if isinstance(content, dict):
                if content.get('complete', False):
                    return True
                if content.get('status') == 'completed':
                    return True
                if 'signal' in content or 'recommendation' in content or 'order_id' in content or 'status' in content:
                # Heuristic for rule-based completion
                if 'signal' in content or 'recommendation' in content or 'order_id' in content:
                    return True
        
        return False
    
    def get_trace(self, trace_id: str) -> Optional[ReActTrace]:
        """Get a specific trace by ID"""
        for trace in self.traces:
            if trace.trace_id == trace_id:
                return trace
        return None
    
    def get_recent_traces(self, n: int = 10) -> List[ReActTrace]:
        """Get n most recent traces"""
        return self.traces[-n:]
    
    async def shutdown(self):
        """Shutdown the ReAct loop"""
        logger.info("ReAct Loop shutdown")


class ReActAgent:
    """
    A complete ReAct-based agent that combines:
    - ReAct loop for reasoning
    - Tool use for actions
    - Memory for context
    
    This is the pattern used by GPT-4 and Claude for complex tasks.
    """
    
    def __init__(
        self,
        name: str,
        react_loop: ReActLoop,
        tools: List[str],
        system_prompt: str = ""
    ):
        self.name = name
        self.react_loop = react_loop
        self.tools = tools
        self.system_prompt = system_prompt
        
        self.task_history: List[ReActTrace] = []
    
    async def execute_task(
        self,
        task: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute a task using ReAct reasoning.
        
        Args:
            task: The task to accomplish
            context: Optional context/state
            
        Returns:
            Result of task execution
        """
        context = context or {}
        
        # Add system prompt to context
        context['system_prompt'] = self.system_prompt
        context['agent_name'] = self.name
        
        # Run ReAct loop
        trace = await self.react_loop.run(
            task=task,
            context=context,
            available_tools=self.tools
        )
        
        self.task_history.append(trace)
        
        return {
            'success': trace.success,
            'answer': trace.final_answer,
            'trace_id': trace.trace_id,
            'iterations': len(trace.steps),
            'reasoning': trace.to_string()
        }
    
    def get_capabilities(self) -> Dict[str, Any]:
        """Get agent capabilities"""
        return {
            'name': self.name,
            'tools': self.tools,
            'max_iterations': self.react_loop.max_iterations,
            'tasks_completed': len(self.task_history)
        }
