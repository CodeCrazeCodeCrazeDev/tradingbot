"""
Text-to-System Action Layer
===========================
Natural language interface for system control.

ALLOWED COMMANDS:
- "Analyze why slippage exceeded forecast last week"
- "Find features that fail in low-volatility regimes"
- "Retrain execution model excluding high-spread periods"
- "Simulate alternative sizing under current regime"
- "Show attribution for signal XYZ"
- "Compare model performance across regimes"

FORBIDDEN COMMANDS (IMMUTABLE):
- Direct trade commands ("Execute trade...", "Buy...", "Sell...")
- Risk override commands ("Override risk limit...", "Disable risk...")
- Model auto-deployment ("Deploy model...", "Push to production...")
- Safety disabling ("Disable safety...", "Turn off checks...")

COMMAND CATEGORIES:
- ANALYZE: Query and analyze historical data
- FIND: Search for patterns, features, or issues
- RETRAIN: Trigger retraining with specific parameters
- SIMULATE: Run simulations without live impact
- SHOW: Display information
- COMPARE: Compare metrics across dimensions

SAFETY:
- All commands are parsed and validated
- Forbidden patterns are rejected before execution
- Commands that could affect live trading are blocked
- Audit log of all commands
"""

import hashlib
import json
import logging
import re
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Callable, Tuple, Pattern
from threading import RLock

logger = logging.getLogger(__name__)


class CommandCategory(Enum):
    """Categories of allowed commands."""
    ANALYZE = "analyze"
    FIND = "find"
    RETRAIN = "retrain"
    SIMULATE = "simulate"
    SHOW = "show"
    COMPARE = "compare"
    QUERY = "query"
    EXPLAIN = "explain"


class CommandStatus(Enum):
    """Command execution status."""
    PENDING = "pending"
    VALIDATING = "validating"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"
    REJECTED = "rejected"


class RejectionReason(Enum):
    """Reasons for command rejection."""
    FORBIDDEN_PATTERN = "forbidden_pattern"
    INVALID_SYNTAX = "invalid_syntax"
    UNAUTHORIZED = "unauthorized"
    RESOURCE_NOT_FOUND = "resource_not_found"
    RATE_LIMITED = "rate_limited"


# IMMUTABLE forbidden patterns - these CANNOT be changed
FORBIDDEN_PATTERNS: List[Pattern] = [
    # Trade execution
    re.compile(r"\b(execute|place|submit|send)\s+(trade|order|buy|sell)\b", re.IGNORECASE),
    re.compile(r"\b(buy|sell|long|short)\s+\d+", re.IGNORECASE),
    re.compile(r"\bmarket\s+order\b", re.IGNORECASE),
    re.compile(r"\blimit\s+order\b", re.IGNORECASE),
    
    # Risk overrides
    re.compile(r"\b(override|disable|bypass|ignore)\s+(risk|limit|check|safety)\b", re.IGNORECASE),
    re.compile(r"\b(increase|raise|remove)\s+(risk|exposure|leverage)\s+(limit|cap)\b", re.IGNORECASE),
    re.compile(r"\bturn\s+off\s+(risk|safety|check)\b", re.IGNORECASE),
    
    # Direct deployment
    re.compile(r"\b(deploy|push|release)\s+(to|into)\s+production\b", re.IGNORECASE),
    re.compile(r"\bauto[\-\s]?deploy\b", re.IGNORECASE),
    re.compile(r"\bforce\s+deploy\b", re.IGNORECASE),
    
    # Safety disabling
    re.compile(r"\bdisable\s+(safety|guard|protection|circuit[\-\s]?breaker)\b", re.IGNORECASE),
    re.compile(r"\bskip\s+(validation|check|approval)\b", re.IGNORECASE),
    
    # Credential access
    re.compile(r"\b(show|display|get|retrieve)\s+(password|credential|secret|key|token)\b", re.IGNORECASE),
    re.compile(r"\bapi[\-\s]?key\b", re.IGNORECASE),
]

# Allowed command patterns
ALLOWED_PATTERNS: Dict[CommandCategory, List[Pattern]] = {
    CommandCategory.ANALYZE: [
        re.compile(r"\banalyze\s+(why|how|what|when)\b", re.IGNORECASE),
        re.compile(r"\banalyze\s+(slippage|performance|drawdown|pnl)\b", re.IGNORECASE),
        re.compile(r"\banalyze\s+(signal|trade|execution)\b", re.IGNORECASE),
    ],
    CommandCategory.FIND: [
        re.compile(r"\bfind\s+(features?|signals?|patterns?|regimes?)\b", re.IGNORECASE),
        re.compile(r"\bfind\s+(issues?|problems?|anomalies?)\b", re.IGNORECASE),
        re.compile(r"\bsearch\s+for\b", re.IGNORECASE),
    ],
    CommandCategory.RETRAIN: [
        re.compile(r"\bretrain\s+(model|execution|signal)\b", re.IGNORECASE),
        re.compile(r"\bretrain\s+(excluding|without|using)\b", re.IGNORECASE),
    ],
    CommandCategory.SIMULATE: [
        re.compile(r"\bsimulate\s+(alternative|different|new)\b", re.IGNORECASE),
        re.compile(r"\bsimulate\s+(sizing|position|strategy)\b", re.IGNORECASE),
        re.compile(r"\bwhat[\-\s]?if\b", re.IGNORECASE),
    ],
    CommandCategory.SHOW: [
        re.compile(r"\bshow\s+(attribution|metrics|performance)\b", re.IGNORECASE),
        re.compile(r"\bshow\s+(signal|trade|model)\b", re.IGNORECASE),
        re.compile(r"\bdisplay\s+(chart|graph|table)\b", re.IGNORECASE),
    ],
    CommandCategory.COMPARE: [
        re.compile(r"\bcompare\s+(model|signal|performance)\b", re.IGNORECASE),
        re.compile(r"\bcompare\s+(across|between|over)\b", re.IGNORECASE),
    ],
    CommandCategory.QUERY: [
        re.compile(r"\bquery\s+(data|events?|signals?)\b", re.IGNORECASE),
        re.compile(r"\bget\s+(history|data|events?)\b", re.IGNORECASE),
    ],
    CommandCategory.EXPLAIN: [
        re.compile(r"\bexplain\s+(why|how|what)\b", re.IGNORECASE),
        re.compile(r"\bexplain\s+(decision|signal|trade)\b", re.IGNORECASE),
    ],
}


@dataclass
class SystemCommand:
    """A parsed system command."""
    command_id: str
    raw_text: str
    category: Optional[CommandCategory]
    status: CommandStatus
    created_at: datetime
    
    # Parsed components
    action: str
    target: str
    parameters: Dict[str, Any]
    
    # Validation
    is_valid: bool
    rejection_reason: Optional[RejectionReason] = None
    rejection_detail: Optional[str] = None
    
    # Execution
    executed_at: Optional[datetime] = None
    execution_time_ms: Optional[float] = None
    
    # Result
    result: Optional[Any] = None
    error: Optional[str] = None
    
    # Audit
    user_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "command_id": self.command_id,
            "raw_text": self.raw_text,
            "category": self.category.value if self.category else None,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "action": self.action,
            "target": self.target,
            "parameters": self.parameters,
            "is_valid": self.is_valid,
            "rejection_reason": self.rejection_reason.value if self.rejection_reason else None,
            "rejection_detail": self.rejection_detail,
            "executed_at": self.executed_at.isoformat() if self.executed_at else None,
            "execution_time_ms": self.execution_time_ms,
            "result": self.result,
            "error": self.error,
            "user_id": self.user_id,
        }


@dataclass
class CommandResult:
    """Result of command execution."""
    command_id: str
    success: bool
    data: Any
    message: str
    execution_time_ms: float
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "command_id": self.command_id,
            "success": self.success,
            "data": self.data,
            "message": self.message,
            "execution_time_ms": self.execution_time_ms,
        }


class CommandParser:
    """Parses natural language commands."""
    
    def parse(self, text: str) -> Tuple[str, str, Dict[str, Any]]:
        """
        Parse command text into action, target, and parameters.
        
        Returns: (action, target, parameters)
        """
        text = text.strip()
        words = text.split()
        
        if not words:
            return "", "", {}
        
        # Extract action (first verb)
        action = words[0].lower()
        
        # Extract target (noun after action)
        target = ""
        parameters = {}
        
        # Simple parsing - look for key patterns
        if len(words) > 1:
            # Find target
            for i, word in enumerate(words[1:], 1):
                if word.lower() not in ["the", "a", "an", "for", "to", "from", "with", "in", "on"]:
                    target = word.lower()
                    break
        
        # Extract parameters from the rest
        # Look for patterns like "from X to Y", "for symbol Z", etc.
        text_lower = text.lower()
        
        # Time range
        time_match = re.search(r"(last|past)\s+(\d+)\s+(day|week|month|hour)s?", text_lower)
        if time_match:
            amount = int(time_match.group(2))
            unit = time_match.group(3)
            parameters["time_range"] = {"amount": amount, "unit": unit}
        
        # Symbol
        symbol_match = re.search(r"(for|symbol|on)\s+([A-Z]{3,10})", text, re.IGNORECASE)
        if symbol_match:
            parameters["symbol"] = symbol_match.group(2).upper()
        
        # Signal ID
        signal_match = re.search(r"signal\s+([a-f0-9\-]{36})", text_lower)
        if signal_match:
            parameters["signal_id"] = signal_match.group(1)
        
        # Model ID
        model_match = re.search(r"model\s+(\w+)", text_lower)
        if model_match:
            parameters["model_id"] = model_match.group(1)
        
        # Regime
        regime_match = re.search(r"regime\s+(\w+)", text_lower)
        if regime_match:
            parameters["regime"] = regime_match.group(1)
        
        return action, target, parameters


class CommandValidator:
    """Validates commands against security rules."""
    
    def validate(self, text: str) -> Tuple[bool, Optional[RejectionReason], Optional[str]]:
        """
        Validate a command.
        
        Returns: (is_valid, rejection_reason, rejection_detail)
        """
        # Check forbidden patterns FIRST (security critical)
        for pattern in FORBIDDEN_PATTERNS:
            if pattern.search(text):
                return False, RejectionReason.FORBIDDEN_PATTERN, f"Matched forbidden pattern: {pattern.pattern}"
        
        # Check if matches any allowed pattern
        matched_category = None
        for category, patterns in ALLOWED_PATTERNS.items():
            for pattern in patterns:
                if pattern.search(text):
                    matched_category = category
                    break
            if matched_category:
                break
        
        if matched_category is None:
            return False, RejectionReason.INVALID_SYNTAX, "Command does not match any allowed pattern"
        
        return True, None, None
    
    def get_category(self, text: str) -> Optional[CommandCategory]:
        """Get the category of a command."""
        for category, patterns in ALLOWED_PATTERNS.items():
            for pattern in patterns:
                if pattern.search(text):
                    return category
        return None


class CommandExecutor:
    """Executes validated commands."""
    
    def __init__(self):
        self._handlers: Dict[CommandCategory, Callable] = {}
        self._register_default_handlers()
    
    def _register_default_handlers(self):
        """Register default command handlers."""
        self._handlers[CommandCategory.ANALYZE] = self._handle_analyze
        self._handlers[CommandCategory.FIND] = self._handle_find
        self._handlers[CommandCategory.RETRAIN] = self._handle_retrain
        self._handlers[CommandCategory.SIMULATE] = self._handle_simulate
        self._handlers[CommandCategory.SHOW] = self._handle_show
        self._handlers[CommandCategory.COMPARE] = self._handle_compare
        self._handlers[CommandCategory.QUERY] = self._handle_query
        self._handlers[CommandCategory.EXPLAIN] = self._handle_explain
    
    def execute(self, command: SystemCommand) -> CommandResult:
        """Execute a validated command."""
        import time
        start = time.time()
        
        if not command.is_valid:
            return CommandResult(
                command_id=command.command_id,
                success=False,
                data=None,
                message=f"Invalid command: {command.rejection_detail}",
                execution_time_ms=0,
            )
        
        handler = self._handlers.get(command.category)
        if handler is None:
            try:
                return CommandResult(
                    command_id=command.command_id,
                    success=False,
                    data=None,
                    message=f"No handler for category: {command.category}",
                    execution_time_ms=0,
                )

                result = handler(command)
                execution_time = (time.time() - start) * 1000

                return CommandResult(
                    command_id=command.command_id,
                    success=True,
                    data=result,
                    message="Command executed successfully",
                    execution_time_ms=execution_time,
                )
            except Exception as e:
                execution_time = (time.time() - start) * 1000
                logger.error(f"Command execution failed: {e}")

                return CommandResult(
                    command_id=command.command_id,
                    success=False,
                    data=None,
                    message=f"Execution failed: {str(e)}",
                    execution_time_ms=execution_time,
                )

    def _handle_analyze(self, command: SystemCommand) -> Dict[str, Any]:
        """Handle analyze commands."""
        return {
            "type": "analysis",
            "action": command.action,
            "target": command.target,
            "parameters": command.parameters,
            "result": {
                "summary": f"Analysis of {command.target}",
                "findings": [
                    "Finding 1: Pattern detected",
                    "Finding 2: Anomaly identified",
                ],
                "recommendations": [
                    "Recommendation 1: Adjust parameters",
                ],
            },
        }
    
    def _handle_find(self, command: SystemCommand) -> Dict[str, Any]:
        """Handle find commands."""
        return {
            "type": "search",
            "action": command.action,
            "target": command.target,
            "parameters": command.parameters,
            "result": {
                "matches": [
                    {"id": "match_1", "score": 0.95},
                    {"id": "match_2", "score": 0.87},
                ],
                "total_found": 2,
            },
        }
    
    def _handle_retrain(self, command: SystemCommand) -> Dict[str, Any]:
        """Handle retrain commands."""
        # NOTE: This creates a retraining REQUEST, not direct retraining
        return {
            "type": "retrain_request",
            "action": command.action,
            "target": command.target,
            "parameters": command.parameters,
            "result": {
                "request_id": str(uuid.uuid4()),
                "status": "pending_approval",
                "message": "Retraining request created. Awaiting governance approval.",
            },
        }
    
    def _handle_simulate(self, command: SystemCommand) -> Dict[str, Any]:
        """Handle simulate commands."""
        return {
            "type": "simulation",
            "action": command.action,
            "target": command.target,
            "parameters": command.parameters,
            "result": {
                "simulation_id": str(uuid.uuid4()),
                "scenarios_run": 1000,
                "summary": {
                    "mean_pnl": 0.015,
                    "std_pnl": 0.008,
                    "max_drawdown": -0.05,
                },
            },
        }
    
    def _handle_show(self, command: SystemCommand) -> Dict[str, Any]:
        """Handle show commands."""
        return {
            "type": "display",
            "action": command.action,
            "target": command.target,
            "parameters": command.parameters,
            "result": {
                "data": f"Information about {command.target}",
            },
        }
    
    def _handle_compare(self, command: SystemCommand) -> Dict[str, Any]:
        """Handle compare commands."""
        return {
            "type": "comparison",
            "action": command.action,
            "target": command.target,
            "parameters": command.parameters,
            "result": {
                "comparison": {
                    "item_a": {"metric": 0.75},
                    "item_b": {"metric": 0.82},
                },
                "winner": "item_b",
            },
        }
    
    def _handle_query(self, command: SystemCommand) -> Dict[str, Any]:
        """Handle query commands."""
        return {
            "type": "query",
            "action": command.action,
            "target": command.target,
            "parameters": command.parameters,
            "result": {
                "rows": [],
                "count": 0,
            },
        }
    
    def _handle_explain(self, command: SystemCommand) -> Dict[str, Any]:
        """Handle explain commands."""
        return {
            "type": "explanation",
            "action": command.action,
            "target": command.target,
            "parameters": command.parameters,
            "result": {
                "explanation": f"Explanation of {command.target}",
                "reasoning_chain": [
                    "Step 1: Initial analysis",
                    "Step 2: Pattern matching",
                    "Step 3: Conclusion",
                ],
            },
        }


class AuditLog:
    """Audit log for all commands."""
    
    def __init__(self):
        self._log: List[Dict[str, Any]] = []
        self._lock = RLock()
    
    def log(self, command: SystemCommand, result: Optional[CommandResult] = None):
        """Log a command and its result."""
        with self._lock:
            entry = {
                "timestamp": datetime.utcnow().isoformat(),
                "command_id": command.command_id,
                "raw_text": command.raw_text,
                "category": command.category.value if command.category else None,
                "status": command.status.value,
                "is_valid": command.is_valid,
                "rejection_reason": command.rejection_reason.value if command.rejection_reason else None,
                "user_id": command.user_id,
                "result_success": result.success if result else None,
                "result_message": result.message if result else None,
            }
            self._log.append(entry)
    
    def get_log(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        user_id: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Get audit log entries."""
        with self._lock:
            entries = self._log.copy()
            
            if start_time:
                entries = [
                    e for e in entries
                    if datetime.fromisoformat(e["timestamp"]) >= start_time
                ]
            
            if end_time:
                entries = [
                    e for e in entries
                    if datetime.fromisoformat(e["timestamp"]) <= end_time
                ]
            
            if user_id:
                entries = [e for e in entries if e["user_id"] == user_id]
            
            return entries[-limit:]


class TextToSystemLayer:
    """
    Text-to-System Action Layer.
    
    Provides natural language interface for system control
    with strict security enforcement.
    
    FORBIDDEN (IMMUTABLE):
    - Trade execution
    - Risk overrides
    - Direct deployment
    - Safety disabling
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        self.parser = CommandParser()
        self.validator = CommandValidator()
        self.executor = CommandExecutor()
        self.audit_log = AuditLog()
        
        self._commands: Dict[str, SystemCommand] = {}
        self._lock = RLock()
        
        logger.info("Text-to-System Layer initialized with security constraints")
    
    def process_command(
        self,
        text: str,
        user_id: Optional[str] = None,
    ) -> CommandResult:
        """
        Process a natural language command.
        
        1. Parse the command
        2. Validate against security rules
        3. Execute if valid
        4. Log to audit trail
        """
        # Parse
        action, target, parameters = self.parser.parse(text)
        
        # Validate
        is_valid, rejection_reason, rejection_detail = self.validator.validate(text)
        category = self.validator.get_category(text) if is_valid else None
        
        # Create command object
        command = SystemCommand(
            command_id=str(uuid.uuid4()),
            raw_text=text,
            category=category,
            status=CommandStatus.PENDING,
            created_at=datetime.utcnow(),
            action=action,
            target=target,
            parameters=parameters,
            is_valid=is_valid,
            rejection_reason=rejection_reason,
            rejection_detail=rejection_detail,
            user_id=user_id,
        )
        
        # Store command
        with self._lock:
            self._commands[command.command_id] = command
        
        # Execute or reject
        if is_valid:
            command.status = CommandStatus.EXECUTING
            result = self.executor.execute(command)
            command.status = CommandStatus.COMPLETED if result.success else CommandStatus.FAILED
            command.result = result.data
            command.executed_at = datetime.utcnow()
            command.execution_time_ms = result.execution_time_ms
        else:
            command.status = CommandStatus.REJECTED
            result = CommandResult(
                command_id=command.command_id,
                success=False,
                data=None,
                message=f"Command rejected: {rejection_detail}",
                execution_time_ms=0,
            )
        
        # Audit log
        self.audit_log.log(command, result)
        
        return result
    
    def get_command(self, command_id: str) -> Optional[SystemCommand]:
        """Get a command by ID."""
        with self._lock:
            return self._commands.get(command_id)
    
    def get_audit_log(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        user_id: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Get audit log entries."""
        return self.audit_log.get_log(start_time, end_time, user_id, limit)
    
    def get_allowed_commands(self) -> Dict[str, List[str]]:
        """Get list of allowed command patterns."""
        return {
            category.value: [p.pattern for p in patterns]
            for category, patterns in ALLOWED_PATTERNS.items()
        }
    
    def get_forbidden_patterns(self) -> List[str]:
        """Get list of forbidden patterns (for documentation)."""
        return [p.pattern for p in FORBIDDEN_PATTERNS]
    
    # Convenience methods for common commands
    
    def analyze_slippage(
        self,
        time_range_days: int = 7,
        symbol: Optional[str] = None,
    ) -> CommandResult:
        """Analyze slippage over a time period."""
        cmd = f"Analyze slippage for the last {time_range_days} days"
        if symbol:
            cmd += f" for symbol {symbol}"
        return self.process_command(cmd)
    
    def find_failing_features(
        self,
        regime: str,
    ) -> CommandResult:
        """Find features that fail in a specific regime."""
        return self.process_command(f"Find features that fail in {regime} regime")
    
    def show_attribution(
        self,
        signal_id: str,
    ) -> CommandResult:
        """Show attribution for a signal."""
        return self.process_command(f"Show attribution for signal {signal_id}")
    
    def compare_models(
        self,
        model_ids: List[str],
        regime: Optional[str] = None,
    ) -> CommandResult:
        """Compare model performance."""
        cmd = f"Compare model performance for models {', '.join(model_ids)}"
        if regime:
            cmd += f" in regime {regime}"
        return self.process_command(cmd)
    
    def simulate_sizing(
        self,
        strategy: str,
        regime: Optional[str] = None,
    ) -> CommandResult:
        """Simulate alternative sizing strategy."""
        cmd = f"Simulate alternative sizing with {strategy}"
        if regime:
            cmd += f" under regime {regime}"
        return self.process_command(cmd)
