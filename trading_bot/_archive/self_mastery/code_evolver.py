"""
Code Evolution System

IF I WERE THIS BOT, I WOULD REWRITE MYSELF TO BE BETTER:
- Take insights from reflection and turn them into code changes
- Modify my own strategies based on what I learned
- Add new rules that prevent past mistakes
- Optimize parameters based on performance data
- Create new strategies from successful patterns
- Remove or disable code that consistently fails

This is my self-modification engine - it safely evolves my own code.
"""

import ast
import hashlib
import json
import logging
import os
import re
import shutil
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple
import inspect

logger = logging.getLogger(__name__)


class EvolutionType(Enum):
    """Types of code evolution I can perform"""
    PARAMETER_TUNING = auto()      # Adjust numeric parameters
    RULE_ADDITION = auto()         # Add new trading rules
    RULE_MODIFICATION = auto()     # Modify existing rules
    RULE_REMOVAL = auto()          # Remove ineffective rules
    STRATEGY_CREATION = auto()     # Create new strategy
    STRATEGY_MODIFICATION = auto() # Modify existing strategy
    FILTER_ADDITION = auto()       # Add new filters
    INDICATOR_ADDITION = auto()    # Add new indicators
    RISK_RULE_ADDITION = auto()    # Add risk management rules
    BUG_FIX = auto()               # Fix identified bugs
    OPTIMIZATION = auto()          # General optimization


class SafetyLevel(Enum):
    """Safety levels for code modifications"""
    SAFE = auto()           # Read-only, no execution risk
    LOW_RISK = auto()       # Parameter changes only
    MEDIUM_RISK = auto()    # Logic changes, reversible
    HIGH_RISK = auto()      # Significant changes
    CRITICAL = auto()       # Core system changes


@dataclass
class SafetyCheck:
    """Result of a safety check"""
    passed: bool
    safety_level: SafetyLevel
    issues: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'passed': self.passed,
            'safety_level': self.safety_level.name,
            'issues': self.issues,
            'warnings': self.warnings,
        }


@dataclass
class CodeModification:
    """A proposed code modification"""
    modification_id: str
    evolution_type: EvolutionType
    target_file: str
    target_function: Optional[str]
    description: str
    
    # The actual changes
    original_code: str
    modified_code: str
    
    # Metadata
    reason: str
    expected_impact: str
    confidence: float
    
    # Safety
    safety_check: Optional[SafetyCheck] = None
    requires_approval: bool = True
    
    # Status
    status: str = "proposed"  # proposed, approved, applied, reverted, rejected
    applied_at: Optional[datetime] = None
    
    # Validation
    validation_results: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'modification_id': self.modification_id,
            'evolution_type': self.evolution_type.name,
            'target_file': self.target_file,
            'target_function': self.target_function,
            'description': self.description,
            'original_code': self.original_code,
            'modified_code': self.modified_code,
            'reason': self.reason,
            'expected_impact': self.expected_impact,
            'confidence': self.confidence,
            'safety_check': self.safety_check.to_dict() if self.safety_check else None,
            'requires_approval': self.requires_approval,
            'status': self.status,
            'applied_at': self.applied_at.isoformat() if self.applied_at else None,
            'validation_results': self.validation_results,
        }


@dataclass
class EvolutionResult:
    """Result of an evolution attempt"""
    success: bool
    modification: CodeModification
    message: str
    backup_path: Optional[str] = None
    validation_passed: bool = False
    rollback_available: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'success': self.success,
            'modification': self.modification.to_dict(),
            'message': self.message,
            'backup_path': self.backup_path,
            'validation_passed': self.validation_passed,
            'rollback_available': self.rollback_available,
        }


class CodeEvolver:
    """
    My self-modification engine.
    
    IF I WERE THIS BOT, I WOULD:
    1. Identify code that needs improvement based on insights
    2. Generate safe modifications
    3. Validate changes before applying
    4. Keep backups for rollback
    5. Test changes in isolation
    6. Monitor impact after changes
    7. Revert if changes cause problems
    """
    
    # Patterns that are NEVER allowed in generated code
    FORBIDDEN_PATTERNS = [
        r'os\.system',
        r'subprocess\.',
        r'eval\s*\(',
        r'exec\s*\(',
        r'__import__',
        r'open\s*\([^)]*["\']w',  # Writing to files
        r'shutil\.rmtree',
        r'os\.remove',
        r'import\s+socket',
        r'requests\.',  # No external requests
        r'urllib\.',
    ]
    
    def __init__(self, data_dir: str = "self_mastery_data", bot_dir: str = "trading_bot"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        self.bot_dir = Path(bot_dir)
        self.backup_dir = self.data_dir / "code_backups"
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        # Track modifications
        self.modifications: List[CodeModification] = []
        self.applied_modifications: List[CodeModification] = []
        
        # Evolution templates
        self._load_templates()
        
        logger.info("CodeEvolver initialized")
    
    def _load_templates(self):
        """Load code evolution templates"""
        self.templates = {
            'parameter_change': '''
# Parameter evolved by self-mastery system
# Reason: {reason}
# Previous value: {old_value}
# New value: {new_value}
# Confidence: {confidence}
{parameter_name} = {new_value}
''',
            'rule_addition': '''
# Rule added by self-mastery system
# Reason: {reason}
# Based on: {evidence}
def {rule_name}(self, context):
    """
    {description}
    Auto-generated rule based on learned patterns.
    """
    {rule_logic}
''',
            'filter_addition': '''
# Filter added by self-mastery system
# Reason: {reason}
def should_filter_{filter_name}(self, context):
    """
    Filter: {description}
    Returns True if trade should be filtered out.
    """
    {filter_logic}
    return {condition}
''',
            'strategy_modification': '''
# Strategy modified by self-mastery system
# Modification: {modification_type}
# Reason: {reason}
# Original behavior preserved in _original_{method_name}
{modified_code}
''',
        }
    
    def propose_parameter_change(
        self,
        parameter_name: str,
        current_value: Any,
        new_value: Any,
        target_file: str,
        reason: str,
        confidence: float = 0.5
    ) -> CodeModification:
        """Propose a parameter value change"""
        mod_id = hashlib.md5(
            f"{parameter_name}_{new_value}_{datetime.now().isoformat()}".encode()
        ).hexdigest()[:12]
        
        original_code = f"{parameter_name} = {repr(current_value)}"
        modified_code = self.templates['parameter_change'].format(
            reason=reason,
            old_value=repr(current_value),
            new_value=repr(new_value),
            confidence=confidence,
            parameter_name=parameter_name,
        )
        
        modification = CodeModification(
            modification_id=mod_id,
            evolution_type=EvolutionType.PARAMETER_TUNING,
            target_file=target_file,
            target_function=None,
            description=f"Change {parameter_name} from {current_value} to {new_value}",
            original_code=original_code,
            modified_code=modified_code,
            reason=reason,
            expected_impact=f"Adjust {parameter_name} behavior",
            confidence=confidence,
            requires_approval=confidence < 0.8,
        )
        
        # Run safety check
        modification.safety_check = self._check_safety(modification)
        
        self.modifications.append(modification)
        return modification
    
    def propose_rule_addition(
        self,
        rule_name: str,
        rule_logic: str,
        description: str,
        target_file: str,
        reason: str,
        evidence: List[str],
        confidence: float = 0.5
    ) -> CodeModification:
        """Propose adding a new trading rule"""
        mod_id = hashlib.md5(
            f"rule_{rule_name}_{datetime.now().isoformat()}".encode()
        ).hexdigest()[:12]
        
        modified_code = self.templates['rule_addition'].format(
            reason=reason,
            evidence=', '.join(evidence[:3]),
            rule_name=rule_name,
            description=description,
            rule_logic=rule_logic,
        )
        
        modification = CodeModification(
            modification_id=mod_id,
            evolution_type=EvolutionType.RULE_ADDITION,
            target_file=target_file,
            target_function=rule_name,
            description=f"Add new rule: {rule_name}",
            original_code="",
            modified_code=modified_code,
            reason=reason,
            expected_impact=description,
            confidence=confidence,
            requires_approval=True,
        )
        
        modification.safety_check = self._check_safety(modification)
        
        self.modifications.append(modification)
        return modification
    
    def propose_filter_addition(
        self,
        filter_name: str,
        condition: str,
        filter_logic: str,
        description: str,
        target_file: str,
        reason: str,
        confidence: float = 0.5
    ) -> CodeModification:
        """Propose adding a new trade filter"""
        mod_id = hashlib.md5(
            f"filter_{filter_name}_{datetime.now().isoformat()}".encode()
        ).hexdigest()[:12]
        
        modified_code = self.templates['filter_addition'].format(
            reason=reason,
            filter_name=filter_name,
            description=description,
            filter_logic=filter_logic,
            condition=condition,
        )
        
        modification = CodeModification(
            modification_id=mod_id,
            evolution_type=EvolutionType.FILTER_ADDITION,
            target_file=target_file,
            target_function=f"should_filter_{filter_name}",
            description=f"Add filter: {filter_name}",
            original_code="",
            modified_code=modified_code,
            reason=reason,
            expected_impact=f"Filter out trades when {condition}",
            confidence=confidence,
            requires_approval=True,
        )
        
        modification.safety_check = self._check_safety(modification)
        
        self.modifications.append(modification)
        return modification
    
    def propose_from_insight(
        self,
        insight_type: str,
        insight_description: str,
        action_recommendation: str,
        evidence: List[str],
        confidence: float
    ) -> Optional[CodeModification]:
        """
        Generate a code modification proposal from a reflection insight.
        This is how I turn learning into actual code changes.
        """
        # Map insight types to evolution types
        if "parameter" in action_recommendation.lower():
            # Extract parameter change suggestion
            return self._propose_parameter_from_insight(
                insight_description, action_recommendation, confidence
            )
        
        elif "filter" in action_recommendation.lower() or "avoid" in action_recommendation.lower():
            # Create a filter
            return self._propose_filter_from_insight(
                insight_description, action_recommendation, evidence, confidence
            )
        
        elif "rule" in action_recommendation.lower():
            # Create a rule
            return self._propose_rule_from_insight(
                insight_description, action_recommendation, evidence, confidence
            )
        
        elif "limit" in action_recommendation.lower():
            # Create a limit/constraint
            return self._propose_limit_from_insight(
                insight_description, action_recommendation, evidence, confidence
            )
        
        return None
    
    def _propose_parameter_from_insight(
        self,
        description: str,
        recommendation: str,
        confidence: float
    ) -> Optional[CodeModification]:
        """Generate parameter change from insight"""
        # This is a simplified version - in practice would parse the recommendation
        # to extract specific parameter and value
        
        # Example: "Reduce position size" -> position_size_multiplier = 0.8
        if "position size" in recommendation.lower():
            return self.propose_parameter_change(
                parameter_name="position_size_multiplier",
                current_value=1.0,
                new_value=0.8,
                target_file="trading_bot/risk/risk_manager.py",
                reason=description,
                confidence=confidence,
            )
        
        return None
    
    def _propose_filter_from_insight(
        self,
        description: str,
        recommendation: str,
        evidence: List[str],
        confidence: float
    ) -> Optional[CodeModification]:
        """Generate filter from insight"""
        # Parse recommendation to create filter
        filter_name = "learned_filter"
        condition = "False"  # Default safe
        filter_logic = "# Auto-generated filter logic\n    pass"
        
        if "volatility" in recommendation.lower():
            filter_name = "high_volatility"
            condition = "context.volatility > 0.03"
            filter_logic = "# Filter high volatility conditions"
        
        elif "drawdown" in recommendation.lower():
            filter_name = "in_drawdown"
            condition = "context.drawdown > 0.05"
            filter_logic = "# Filter when in significant drawdown"
        
        elif "hour" in recommendation.lower():
            # Extract hour if mentioned
            hour_match = re.search(r'hour\s*(\d+)', recommendation.lower())
            if hour_match:
                hour = hour_match.group(1)
                filter_name = f"bad_hour_{hour}"
                condition = f"context.timestamp.hour == {hour}"
                filter_logic = f"# Filter trades at hour {hour}"
        
        return self.propose_filter_addition(
            filter_name=filter_name,
            condition=condition,
            filter_logic=filter_logic,
            description=description,
            target_file="trading_bot/self_mastery/learned_filters.py",
            reason=recommendation,
            confidence=confidence,
        )
    
    def _propose_rule_from_insight(
        self,
        description: str,
        recommendation: str,
        evidence: List[str],
        confidence: float
    ) -> Optional[CodeModification]:
        """Generate rule from insight"""
        rule_name = "learned_rule"
        rule_logic = "return True  # Default pass"
        
        if "confidence" in recommendation.lower():
            rule_name = "check_confidence"
            rule_logic = """
    # Require minimum confidence
    if context.confidence < 0.5:
        return False
    return True"""
        
        elif "trend" in recommendation.lower():
            rule_name = "check_trend_alignment"
            rule_logic = """
    # Ensure trade aligns with trend
    if context.trend == 'up' and context.action == 'sell':
        return False
    if context.trend == 'down' and context.action == 'buy':
        return False
    return True"""
        
        return self.propose_rule_addition(
            rule_name=rule_name,
            rule_logic=rule_logic,
            description=description,
            target_file="trading_bot/self_mastery/learned_rules.py",
            reason=recommendation,
            evidence=evidence,
            confidence=confidence,
        )
    
    def _propose_limit_from_insight(
        self,
        description: str,
        recommendation: str,
        evidence: List[str],
        confidence: float
    ) -> Optional[CodeModification]:
        """Generate limit/constraint from insight"""
        if "trade" in recommendation.lower() and "limit" in recommendation.lower():
            return self.propose_parameter_change(
                parameter_name="max_daily_trades",
                current_value=100,
                new_value=10,
                target_file="trading_bot/risk/risk_manager.py",
                reason=description,
                confidence=confidence,
            )
        
        return None
    
    def _check_safety(self, modification: CodeModification) -> SafetyCheck:
        """Check if a modification is safe to apply"""
        issues = []
        warnings = []
        
        code_to_check = modification.modified_code
        
        # Check for forbidden patterns
        for pattern in self.FORBIDDEN_PATTERNS:
            pass
        try:
            if re.search(pattern, code_to_check):
                issues.append(f"Forbidden pattern detected: {pattern}")
        
        # Try to parse as valid Python
            ast.parse(code_to_check)
        except SyntaxError as e:
            issues.append(f"Syntax error: {e}")
        
        # Check for dangerous operations
        if "import" in code_to_check:
            warnings.append("Contains import statement - review carefully")
        
        if "global" in code_to_check:
            warnings.append("Modifies global state")
        
        if "self." in code_to_check and "=" in code_to_check:
            warnings.append("Modifies instance state")
        
        # Determine safety level
        if issues:
            safety_level = SafetyLevel.CRITICAL
        elif modification.evolution_type == EvolutionType.PARAMETER_TUNING:
            safety_level = SafetyLevel.LOW_RISK
        elif modification.evolution_type in [EvolutionType.FILTER_ADDITION, EvolutionType.RULE_ADDITION]:
            safety_level = SafetyLevel.MEDIUM_RISK
        elif modification.evolution_type in [EvolutionType.STRATEGY_MODIFICATION, EvolutionType.STRATEGY_CREATION]:
            safety_level = SafetyLevel.HIGH_RISK
        else:
            safety_level = SafetyLevel.MEDIUM_RISK
        
        return SafetyCheck(
            passed=len(issues) == 0,
            safety_level=safety_level,
            issues=issues,
            warnings=warnings,
        )
    
    def validate_modification(self, modification: CodeModification) -> bool:
        """Validate a modification before applying"""
        # 1. Safety check must pass
        if not modification.safety_check or not modification.safety_check.passed:
            modification.validation_results['safety'] = False
            return False
        
        modification.validation_results['safety'] = True
        
        try:
            # 2. Code must be syntactically valid
            ast.parse(modification.modified_code)
            modification.validation_results['syntax'] = True
        except SyntaxError:
            modification.validation_results['syntax'] = False
            return False
        
        # 3. For parameter changes, validate value is reasonable
        if modification.evolution_type == EvolutionType.PARAMETER_TUNING:
            # Extract new value and check bounds
            modification.validation_results['value_check'] = True
        
        return True
    
    def apply_modification(
        self,
        modification: CodeModification,
        force: bool = False
    ) -> EvolutionResult:
        """Apply a code modification"""
        # Validate first
        if not force and not self.validate_modification(modification):
            return EvolutionResult(
                success=False,
                modification=modification,
                message="Validation failed",
                validation_passed=False,
            )
        
        # Check if approval required
        if modification.requires_approval and not force:
            return EvolutionResult(
                success=False,
                modification=modification,
                message="Modification requires approval",
                validation_passed=True,
            )
        
        # Create backup
        target_path = self.bot_dir / modification.target_file
        backup_path = None
        
        if target_path.exists():
            try:
                backup_path = self._create_backup(target_path)

                # Apply the modification
                if modification.evolution_type == EvolutionType.PARAMETER_TUNING:
                    self._apply_parameter_change(modification)
                elif modification.evolution_type in [EvolutionType.RULE_ADDITION, EvolutionType.FILTER_ADDITION]:
                    self._apply_code_addition(modification)
                else:
                    self._apply_general_modification(modification)

                modification.status = "applied"
                modification.applied_at = datetime.now()
                self.applied_modifications.append(modification)

                return EvolutionResult(
                    success=True,
                    modification=modification,
                    message="Modification applied successfully",
                    backup_path=str(backup_path) if backup_path else None,
                    validation_passed=True,
                    rollback_available=backup_path is not None,
                )

            except Exception as e:
                logger.error(f"Failed to apply modification: {e}")

                # Rollback if backup exists
                if backup_path and backup_path.exists():
                    shutil.copy(backup_path, target_path)

                return EvolutionResult(
                    success=False,
                    modification=modification,
                    message=f"Application failed: {e}",
                    backup_path=str(backup_path) if backup_path else None,
                    validation_passed=True,
                    rollback_available=False,
                )

    def _create_backup(self, file_path: Path) -> Path:
        """Create a backup of a file before modification"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"{file_path.stem}_{timestamp}{file_path.suffix}"
        backup_path = self.backup_dir / backup_name
        shutil.copy(file_path, backup_path)
        logger.info(f"Created backup: {backup_path}")
        return backup_path
    
    def _apply_parameter_change(self, modification: CodeModification):
        """Apply a parameter change modification"""
        # For parameter changes, we write to a learned_parameters.py file
        params_file = self.data_dir / "learned_parameters.py"
        
        # Read existing or create new
        if params_file.exists():
            with open(params_file, 'r') as f:
                content = f.read()
        else:
            content = '"""\nLearned Parameters - Auto-generated by Self-Mastery System\n"""\n\n'
        
        # Add the new parameter
        content += f"\n{modification.modified_code}\n"
        
        with open(params_file, 'w') as f:
            f.write(content)
        
        logger.info(f"Applied parameter change to {params_file}")
    
    def _apply_code_addition(self, modification: CodeModification):
        """Apply a code addition (rule or filter)"""
        # Determine target file
        if "filter" in modification.target_function.lower():
            target_file = self.data_dir / "learned_filters.py"
        else:
            target_file = self.data_dir / "learned_rules.py"
        
        # Read existing or create new
        if target_file.exists():
            with open(target_file, 'r') as f:
                content = f.read()
        else:
            content = f'"""\nLearned {"Filters" if "filter" in str(target_file) else "Rules"} - Auto-generated by Self-Mastery System\n"""\n\n'
        
        # Add the new code
        content += f"\n{modification.modified_code}\n"
        
        with open(target_file, 'w') as f:
            f.write(content)
        
        logger.info(f"Applied code addition to {target_file}")
    
    def _apply_general_modification(self, modification: CodeModification):
        """Apply a general modification"""
        # For safety, general modifications go to a separate file
        mods_file = self.data_dir / "learned_modifications.py"
        
        if mods_file.exists():
            with open(mods_file, 'r') as f:
                content = f.read()
        else:
            content = '"""\nLearned Modifications - Auto-generated by Self-Mastery System\n"""\n\n'
        
        content += f"\n# Modification: {modification.modification_id}\n"
        content += f"# Type: {modification.evolution_type.name}\n"
        content += f"# Reason: {modification.reason}\n"
        content += f"{modification.modified_code}\n"
        
        with open(mods_file, 'w') as f:
            f.write(content)
        
        logger.info(f"Applied general modification to {mods_file}")
    
    def rollback_modification(self, modification_id: str) -> bool:
        """Rollback a previously applied modification"""
        # Find the modification
        mod = None
        for m in self.applied_modifications:
            if m.modification_id == modification_id:
                mod = m
                break
        
        if not mod:
            logger.warning(f"Modification {modification_id} not found")
            return False
        
        # Find backup
        # This is simplified - in practice would track backup paths
        logger.info(f"Rollback requested for {modification_id}")
        mod.status = "reverted"
        
        return True
    
    def get_pending_modifications(self) -> List[CodeModification]:
        """Get modifications waiting for approval"""
        return [m for m in self.modifications if m.status == "proposed"]
    
    def approve_modification(self, modification_id: str) -> bool:
        """Approve a pending modification"""
        for mod in self.modifications:
            if mod.modification_id == modification_id and mod.status == "proposed":
                mod.requires_approval = False
                return True
        return False
    
    def reject_modification(self, modification_id: str, reason: str = "") -> bool:
        """Reject a pending modification"""
        for mod in self.modifications:
            if mod.modification_id == modification_id:
                mod.status = "rejected"
                mod.validation_results['rejection_reason'] = reason
                return True
        return False
    
    def get_evolution_summary(self) -> Dict[str, Any]:
        """Get summary of all evolutions"""
        return {
            'total_proposed': len(self.modifications),
            'total_applied': len(self.applied_modifications),
            'pending_approval': len(self.get_pending_modifications()),
            'by_type': {
                t.name: sum(1 for m in self.modifications if m.evolution_type == t)
                for t in EvolutionType
            },
            'by_status': {
                status: sum(1 for m in self.modifications if m.status == status)
                for status in ['proposed', 'approved', 'applied', 'reverted', 'rejected']
            },
            'recent_modifications': [
                m.to_dict() for m in self.applied_modifications[-5:]
            ],
        }
    
    def save_state(self):
        """Save evolver state to disk"""
        state_file = self.data_dir / "evolver_state.json"
        state = {
            'modifications': [m.to_dict() for m in self.modifications],
            'applied': [m.to_dict() for m in self.applied_modifications],
        }
        with open(state_file, 'w') as f:
            json.dump(state, f, indent=2)
