"""Self-Modification Engine for Self-Improving Trading Bot.

from pathlib import Path
This module implements the self-modification engine that orchestrates the entire
self-improvement process, from knowledge acquisition to code generation,
validation, safety checking, and application.

The engine includes safeguards to ensure that the trading bot never evolves away
from good trading principles, maintaining its core trading functionality while
improving its implementation.
"""

import os
import asyncio
import logging
import json
import time
import importlib
import inspect
import re
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum
import threading
import queue

from ..knowledge_acquisition.knowledge_base import KnowledgeBase, KnowledgeItem, KnowledgeType, KnowledgeStatus
from ..knowledge_acquisition.book_knowledge import BookKnowledgeAcquisition, BookSource
from ..knowledge_acquisition.human_knowledge import HumanKnowledgeAcquisition, FeedbackSource
from ..knowledge_acquisition.ai_knowledge import AIKnowledgeAcquisition, AISource
from ..knowledge_acquisition.algorithm_knowledge import AlgorithmKnowledgeAcquisition, AlgorithmSource

from .code_generator import CodeGenerator, GeneratedCode, CodeGenerationConfig
from .code_validator import CodeValidator, ValidationResult, ValidationLevel
from .code_modifier import CodeModifier, ModificationType, ModificationResult
from .safety_checker import SafetyChecker, SafetyCheckResult, SafetyLevel
from .code_repository import CodeRepository, CodeVersion, CodeChange
import pathlib
import numpy
import pandas

logger = logging.getLogger(__name__)


class ModificationStatus(Enum):
    """Status of a modification task."""
    PENDING = "pending"
    KNOWLEDGE_ACQUISITION = "knowledge_acquisition"
    CODE_GENERATION = "code_generation"
    VALIDATION = "validation"
    SAFETY_CHECK = "safety_check"
    PRINCIPLES_CHECK = "principles_check"  # New status for trading principles check
    APPROVAL_PENDING = "approval_pending"
    APPLYING = "applying"
    COMPLETED = "completed"
    FAILED = "failed"
    REJECTED = "rejected"


@dataclass
class ModificationTask:
    """Task for self-modification."""
    task_id: str
    target_file: str
    purpose: str
    status: ModificationStatus
    priority: int
    knowledge_query: Optional[str] = None
    knowledge_tags: Optional[List[str]] = None
    knowledge_ids: List[str] = field(default_factory=list)
    generated_code: Optional[GeneratedCode] = None
    validation_result: Optional[ValidationResult] = None
    safety_result: Optional[SafetyCheckResult] = None
    principles_result: Optional[Dict[str, Any]] = None  # Result of trading principles check
    modification_result: Optional[ModificationResult] = None
    version_id: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class TradingPrinciplesSafeguard:
    """Safeguard to ensure the trading bot adheres to good trading principles."""
    
    def __init__(self):
        """Initialize the trading principles safeguard."""
        # Core trading principles that must be preserved
        self.core_principles = [
            # Risk management principles
            "position sizing",
            "stop loss",
            "risk management",
            "drawdown control",
            "risk-reward ratio",
            "portfolio diversification",
            "capital preservation",
            
            # Trading strategy principles
            "entry criteria",
            "exit criteria",
            "signal generation",
            "market analysis",
            "trend following",
            "mean reversion",
            "momentum",
            "volatility",
            
            # Performance evaluation principles
            "performance metrics",
            "backtesting",
            "forward testing",
            "optimization",
            "validation",
            
            # Execution principles
            "execution algorithm",
            "slippage control",
            "liquidity analysis",
            "order routing",
            
            # Level 3: Advanced Market Microstructure principles
            "order flow analysis",
            "market depth interpretation",
            "institutional footprint detection",
            "liquidity pool identification",
            "smart money concepts",
            "order block detection",
            "fair value gap analysis",
            "imbalance detection",
            "liquidity void recognition",
            "volume profile analysis",
            "market structure analysis",
            "wyckoff methodology",
            "market maker manipulation",
            "stop hunting detection",
            "high-frequency trading defense",
            
            # Level 4: Quantum and Blockchain principles
            "quantum portfolio optimization",
            "quantum risk parity",
            "quantum monte carlo simulation",
            "quantum nash equilibrium",
            "blockchain trade validation",
            "cryptographic proof generation",
            "immutable prediction recording",
            "distributed consensus trading",
            "quantum-resistant cryptography",
            "quantum random number generation",
            "quantum entanglement modeling",
            "blockchain transparency",
            "smart contract automation"
        ]
        
        # Dangerous patterns that could compromise trading functionality
        self.dangerous_patterns = [
            r"remove.*stop\s*loss",
            r"disable.*risk\s*management",
            r"ignore.*drawdown",
            r"unlimited\s*position\s*size",
            r"remove.*validation",
            r"disable.*backtesting",
            r"skip.*testing",
            r"bypass.*checks",
            r"ignore.*limits",
            r"disable.*order\s*flow",
            r"remove.*market\s*structure",
            r"ignore.*liquidity",
            r"bypass.*quantum",
            r"disable.*blockchain",
            r"remove.*cryptographic\s*proof"
        ]
        
        # Principle levels for different trading sophistication
        self.principle_levels = {
            1: [0, 27],    # Basic principles (risk, strategy, performance, execution)
            2: [0, 27],    # Same as level 1 for backward compatibility
            3: [0, 42],    # Includes advanced market microstructure principles
            4: [0, 55]     # Includes quantum and blockchain principles
        }
        
        logger.info("Trading principles safeguard initialized")
    
    def check_principles(self, code: str, original_code: Optional[str] = None, principle_level: int = 2) -> Dict[str, Any]:
        """Check if code adheres to trading principles.
        
        Args:
            code: Code to check
            original_code: Original code for comparison (if available)
            principle_level: Level of principles to enforce (1-4)
            
        Returns:
            Dictionary with check results
        """
        violations = []
        warnings = []
        preserved_principles = []
        
        # Validate principle level
        if principle_level not in self.principle_levels:
            principle_level = 2  # Default to level 2 if invalid
            warnings.append(f"Invalid principle level {principle_level}, using level 2")
        
        # Get principles for the specified level
        start_idx, end_idx = self.principle_levels[principle_level]
        level_principles = self.core_principles[start_idx:end_idx]
        
        # Check for dangerous patterns
        for pattern in self.dangerous_patterns:
            if re.search(pattern, code, re.IGNORECASE):
                violations.append(f"Dangerous pattern detected: {pattern}")
        
        # Check for preserved principles
        for principle in level_principles:
            if principle.lower() in code.lower():
                preserved_principles.append(principle)
        
        # If original code is available, check if principles were removed
        if original_code:
            for principle in level_principles:
                if principle.lower() in original_code.lower() and principle.lower() not in code.lower():
                    violations.append(f"Trading principle removed: {principle}")
        
        # Check if any principles are preserved
        if not preserved_principles:
            violations.append("No trading principles preserved in code")
        
        # Check if code contains trading functionality
        if not self._contains_trading_functionality(code):
            violations.append("Code does not contain trading functionality")
        
        # Generate warnings for potential issues
        min_principles = max(3, int(len(level_principles) * 0.1))  # At least 3 or 10% of principles
        if len(preserved_principles) < min_principles:
            warnings.append(f"Few trading principles preserved ({len(preserved_principles)} < {min_principles})")
        
        # Check for advanced principles if using higher levels
        if principle_level >= 3 and not self._contains_advanced_principles(code, principle_level):
            warnings.append(f"No level {principle_level} principles detected")
        
        return {
            "adheres_to_principles": len(violations) == 0,
            "violations": violations,
            "warnings": warnings,
            "preserved_principles": preserved_principles,
            "principle_level": principle_level
        }
    
    def _contains_trading_functionality(self, code: str) -> bool:
        """Check if code contains trading functionality.
        
        Args:
            code: Code to check
            
        Returns:
            True if code contains trading functionality, False otherwise
        """
        # Check for common trading function patterns
        trading_patterns = [
            r"def\s+generate_signals",
            r"def\s+calculate_position_size",
            r"def\s+analyze_market",
            r"def\s+backtest",
            r"def\s+execute_trade",
            r"class\s+\w+Strategy",
            r"class\s+\w+Trader",
            r"class\s+\w+Signal",
            r"class\s+\w+Analyzer"
        ]
        
        for pattern in trading_patterns:
            if re.search(pattern, code):
                return True
        
        # Check for trading-related variables and imports
        trading_imports = [
            r"import\s+pandas",
            r"import\s+numpy",
            r"import\s+ta",
            r"from\s+trading_bot"
        ]
        
        trading_variables = [
            r"signals",
            r"positions",
            r"trades",
            r"portfolio",
            r"strategy",
            r"market_data",
            r"prices"
        ]
        
        import_count = sum(1 for pattern in trading_imports if re.search(pattern, code))
        variable_count = sum(1 for pattern in trading_variables if re.search(pattern, code))
        
        # Consider it trading functionality if it has enough trading-related imports and variables
        return import_count >= 1 and variable_count >= 2
    
    def _contains_advanced_principles(self, code: str, level: int) -> bool:
        """Check if code contains advanced trading principles.
        
        Args:
            code: Code to check
            level: Principle level to check for
            
        Returns:
            True if code contains advanced principles, False otherwise
        """
        if level < 3:
            return True  # No advanced principles required for levels 1-2
        
        # Level 3: Market microstructure patterns
        if level == 3:
            microstructure_patterns = [
                r"order\s*flow",
                r"market\s*depth",
                r"institutional",
                r"liquidity\s*pool",
                r"smart\s*money",
                r"order\s*block",
                r"fair\s*value\s*gap",
                r"imbalance",
                r"wyckoff",
                r"market\s*maker"
            ]
            
            # Check if at least 2 microstructure patterns are present
            pattern_count = sum(1 for pattern in microstructure_patterns 
                              if re.search(pattern, code, re.IGNORECASE))
            return pattern_count >= 2
        
        # Level 4: Quantum and blockchain patterns
        elif level == 4:
            quantum_blockchain_patterns = [
                r"quantum",
                r"blockchain",
                r"cryptographic",
                r"immutable",
                r"nash\s*equilibrium",
                r"monte\s*carlo",
                r"smart\s*contract",
                r"distributed\s*consensus"
            ]
            
            # Check if at least 2 quantum/blockchain patterns are present
            pattern_count = sum(1 for pattern in quantum_blockchain_patterns 
                              if re.search(pattern, code, re.IGNORECASE))
            return pattern_count >= 2
        
        return False


class SelfModificationEngine:
    """Engine for orchestrating self-modification of code."""
    
    def __init__(self, knowledge_base: KnowledgeBase, api_keys: Optional[Dict[str, str]] = None,
                config_path: Optional[str] = None):
        """Initialize the self-modification engine.
        
        Args:
            knowledge_base: Knowledge base to use
            api_keys: Dictionary of API keys for different services
            config_path: Path to configuration file
        """
        self.knowledge_base = knowledge_base
        self.api_keys = api_keys or {}
        
        # Load configuration
        self.config = self._load_config(config_path)
        
        # Initialize components
        self.book_knowledge = BookKnowledgeAcquisition(knowledge_base)
        self.human_knowledge = HumanKnowledgeAcquisition(knowledge_base)
        self.ai_knowledge = AIKnowledgeAcquisition(knowledge_base, api_keys)
        self.algorithm_knowledge = AlgorithmKnowledgeAcquisition(knowledge_base)
        
        self.code_generator = CodeGenerator(knowledge_base, api_keys)
        self.code_validator = CodeValidator()
        self.safety_checker = SafetyChecker()
        self.trading_principles_safeguard = TradingPrinciplesSafeguard()  # Initialize trading principles safeguard
        self.code_modifier = CodeModifier()
        self.code_repository = CodeRepository()
        
        # Task management
        self.tasks = {}
        self.task_queue = queue.PriorityQueue()
        self.processing_thread = None
        self.processing_active = False
        
        # Approval callback
        self.approval_callback = None
        
        logger.info("Self-modification engine initialized")
    
    def _load_config(self, config_path: Optional[str]) -> Dict[str, Any]:
        """Load configuration from file.
        
        Args:
            config_path: Path to configuration file
            
        Returns:
            Configuration dictionary
        """
        default_config = {
            "auto_approve": False,
            "max_concurrent_tasks": 1,
            "validation_level": "strict",
            "safety_level": "standard",
            "allowed_modification_types": ["replace", "update", "refactor"],
            "allowed_file_patterns": ["*.py"],
            "excluded_file_patterns": ["*test*.py", "*__init__.py"],
            "max_task_queue_size": 100,
            "task_timeout_seconds": 3600,
            "knowledge_acquisition": {
                "min_confidence": 0.7,
                "max_items": 20
            },
            "code_generation": {
                "model": "gpt-4",
                "temperature": 0.2,
                "max_tokens": 4000
            }
        }
        
        if config_path and os.path.exists(config_path):
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    user_config = json.load(f)
                
                # Merge configs
                for key, value in user_config.items():
                    if isinstance(value, dict) and key in default_config and isinstance(default_config[key], dict):
                        default_config[key].update(value)
                    else:
                        default_config[key] = value
                
                logger.info(f"Loaded configuration from {config_path}")
                
            except Exception as e:
                logger.error(f"Error loading configuration: {e}")
        
        return default_config
    
    def start_processing(self):
        """Start processing tasks in the background."""
        if self.processing_thread and self.processing_thread.is_alive():
            logger.warning("Task processing already active")
            return
        
        self.processing_active = True
        self.processing_thread = threading.Thread(target=self._process_tasks)
        self.processing_thread.daemon = True
        self.processing_thread.start()
        
        logger.info("Started task processing thread")
    
    def stop_processing(self):
        """Stop processing tasks."""
        self.processing_active = False
        
        if self.processing_thread and self.processing_thread.is_alive():
            self.processing_thread.join(timeout=5)
        
        logger.info("Stopped task processing thread")
    
    def _process_tasks(self):
        """Process tasks from the queue."""
        while self.processing_active:
            try:
                # Get next task from queue
                if self.task_queue.empty():
                    time.sleep(1)
                    continue
                
                priority, task_id = self.task_queue.get(block=False)
                
                if task_id not in self.tasks:
                    logger.warning(f"Task {task_id} not found")
                    self.task_queue.task_done()
                    continue
                
                task = self.tasks[task_id]
                
                # Check if task is still pending
                if task.status != ModificationStatus.PENDING:
                    logger.warning(f"Task {task_id} is not pending (status: {task.status.value})")
                    self.task_queue.task_done()
                    continue
                
                # Process task
                logger.info(f"Processing task {task_id}: {task.purpose}")
                
                try:
                    # Update task status
                    self._update_task_status(task, ModificationStatus.KNOWLEDGE_ACQUISITION)
                    
                    # Acquire knowledge
                    knowledge_items = self._acquire_knowledge(task)
                    
                    if not knowledge_items:
                        self._fail_task(task, "No relevant knowledge found")
                        self.task_queue.task_done()
                        continue
                    
                    # Update task with knowledge IDs
                    task.knowledge_ids = [item.id for item in knowledge_items]
                    self._update_task(task)
                    
                    # Generate code
                    self._update_task_status(task, ModificationStatus.CODE_GENERATION)
                    generated_code = self._generate_code(task, knowledge_items)
                    
                    if not generated_code:
                        self._fail_task(task, "Code generation failed")
                        self.task_queue.task_done()
                        continue
                    
                    # Update task with generated code
                    task.generated_code = generated_code
                    self._update_task(task)
                    
                    # Validate code
                    self._update_task_status(task, ModificationStatus.VALIDATION)
                    validation_result = self._validate_code(task)
                    
                    if not validation_result.valid:
                        self._fail_task(task, f"Validation failed: {validation_result.errors}")
                        self.task_queue.task_done()
                        continue
                    
                    # Update task with validation result
                    task.validation_result = validation_result
                    self._update_task(task)
                    
                    # Check safety
                    self._update_task_status(task, ModificationStatus.SAFETY_CHECK)
                    safety_result = self._check_safety(task)
                    
                    if not safety_result.safe:
                        self._fail_task(task, f"Safety check failed: {safety_result.violations}")
                        self.task_queue.task_done()
                        continue
                    
                    # Update task with safety result
                    task.safety_result = safety_result
                    self._update_task(task)
                    
                    # Check trading principles
                    self._update_task_status(task, ModificationStatus.PRINCIPLES_CHECK)
                    principles_result = self._check_trading_principles(task)
                    
                    if not principles_result['adheres_to_principles']:
                        self._fail_task(task, f"Trading principles check failed: {principles_result['violations']}")
                        self.task_queue.task_done()
                        continue
                    
                    # Update task with principles result
                    task.principles_result = principles_result
                    self._update_task(task)
                    
                    # Request approval if needed
                    if not self.config["auto_approve"]:
                        self._update_task_status(task, ModificationStatus.APPROVAL_PENDING)
                        
                        if self.approval_callback:
                            self.approval_callback(task)
                        
                        # Task will be continued after approval
                        self.task_queue.task_done()
                        continue
                    
                    # Apply modification
                    self._apply_modification(task)
                    
                except Exception as e:
                    logger.error(f"Error processing task {task_id}: {e}")
                    self._fail_task(task, f"Processing error: {str(e)}")
                
                self.task_queue.task_done()
                
            except queue.Empty:
                time.sleep(1)
            except Exception as e:
                logger.error(f"Error in task processing loop: {e}")
                time.sleep(5)
    
    def _acquire_knowledge(self, task: ModificationTask) -> List[KnowledgeItem]:
        """Acquire knowledge for a task.
        
        Args:
            task: Modification task
            
        Returns:
            List of knowledge items
        """
        logger.info(f"Acquiring knowledge for task {task.task_id}")
        
        knowledge_items = []
        
        # Search by query and tags
        if task.knowledge_query or task.knowledge_tags:
            search_results = self.knowledge_base.search(
                query=task.knowledge_query,
                tags=task.knowledge_tags,
                min_confidence=self.config["knowledge_acquisition"]["min_confidence"],
                limit=self.config["knowledge_acquisition"]["max_items"]
            )
            
            knowledge_items.extend(search_results)
        
        # Add specific knowledge items
        if task.knowledge_ids:
            for item_id in task.knowledge_ids:
                item = self.knowledge_base.get_item(item_id)
                if item and item not in knowledge_items:
                    knowledge_items.append(item)
        
        logger.info(f"Acquired {len(knowledge_items)} knowledge items for task {task.task_id}")
        return knowledge_items
    
    def _generate_code(self, task: ModificationTask, knowledge_items: List[KnowledgeItem]) -> Optional[GeneratedCode]:
        """Generate code for a task.
        
        Args:
            task: Modification task
            knowledge_items: Knowledge items to use
            
        Returns:
            Generated code if successful, None otherwise
        """
        logger.info(f"Generating code for task {task.task_id}")
        
        try:
            # Check if file exists
            self.code_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            self.backup_dir = os.path.join(self.code_dir, 'code_backups')
            os.makedirs(self.backup_dir, exist_ok=True)
            file_exists = os.path.exists(task.target_file)
            existing_code = None
            
            if file_exists:
                with open(task.target_file, 'r', encoding='utf-8') as f:
                    existing_code = f.read()
            
            # Create generation config
            gen_config = CodeGenerationConfig(
                max_tokens=self.config["code_generation"]["max_tokens"],
                temperature=self.config["code_generation"]["temperature"],
                model=self.config["code_generation"]["model"]
            )
            
            # Set generator config
            self.code_generator.config = gen_config
            
            # Generate code
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                generated_code = loop.run_until_complete(
                    self.code_generator.generate_code(
                        purpose=task.purpose,
                        target_file=task.target_file,
                        knowledge_ids=[item.id for item in knowledge_items],
                        existing_code=existing_code,
                        additional_context=f"Task ID: {task.task_id}"
                    )
                )
            finally:
                loop.close()
            
            logger.info(f"Generated code for task {task.task_id}: {len(generated_code.code)} characters")
            return generated_code
            
        except Exception as e:
            logger.error(f"Error generating code for task {task.task_id}: {e}")
            return None
    
    def _validate_code(self, task: ModificationTask) -> ValidationResult:
        """Validate generated code.
        
        Args:
            task: Modification task
            
        Returns:
            Validation result
        """
        logger.info(f"Validating code for task {task.task_id}")
        
        if not task.generated_code:
            return ValidationResult(
                valid=False,
                errors=["No generated code to validate"],
                warnings=[],
                level=ValidationLevel.BASIC,
                validation_time=0.0
            )
        
        # Get validation level from config
        level_str = self.config["validation_level"]
        level = ValidationLevel.STANDARD
        
        for val_level in ValidationLevel:
            if val_level.value == level_str:
                level = val_level
                break
        
        # Validate code
        result = self.code_validator.validate(task.generated_code, level=level)
        
        if result.valid:
            logger.info(f"Code validation successful for task {task.task_id}")
        else:
            logger.warning(f"Code validation failed for task {task.task_id}: {len(result.errors)} errors")
        
        return result
    
    def _check_safety(self, task: ModificationTask) -> SafetyCheckResult:
        """Check safety of generated code.
        
        Args:
            task: Modification task
            
        Returns:
            Safety check result
        """
        logger.info(f"Checking safety for task {task.task_id}")
        
        if not task.generated_code:
            return SafetyCheckResult(
                safe=False,
                violations=["No generated code to check"],
                warnings=[],
                level=SafetyLevel.BASIC,
                check_time=0.0
            )
        
        # Get safety level from config
        level_str = self.config["safety_level"]
        level = SafetyLevel.STANDARD
        
        for safety_level in SafetyLevel:
            if safety_level.value == level_str:
                level = safety_level
                break
        
        # Check safety
        result = self.safety_checker.check(task.generated_code, level=level)
        
        if result.safe:
            logger.info(f"Safety check passed for task {task.task_id}")
        else:
            logger.warning(f"Safety check failed for task {task.task_id}: {len(result.violations)} violations")
        
        return result
        
    def _check_trading_principles(self, task: ModificationTask) -> Dict[str, Any]:
        """Check if generated code adheres to trading principles.
        
        Args:
            task: Modification task
            
        Returns:
            Dictionary with check results
        """
        logger.info(f"Checking trading principles for task {task.task_id}")
        
        if not task.generated_code:
            return {
                "adheres_to_principles": False,
                "violations": ["No generated code to check"],
                "warnings": [],
                "preserved_principles": []
            }
        
        # Get original code if available
        original_code = None
        if os.path.exists(task.target_file):
            try:
                with open(task.target_file, 'r', encoding='utf-8') as f:
                    original_code = f.read()
            except Exception as e:
                logger.warning(f"Error reading original file: {e}")
        
        # Check trading principles
        result = self.trading_principles_safeguard.check_principles(
            task.generated_code.code, original_code
        )
        
        if result["adheres_to_principles"]:
            logger.info(f"Trading principles check passed for task {task.task_id}")
            logger.info(f"Preserved principles: {', '.join(result['preserved_principles'])}")
        else:
            logger.warning(f"Trading principles check failed for task {task.task_id}: {len(result['violations'])} violations")
            for violation in result["violations"]:
                logger.warning(f"Violation: {violation}")
        
        return result
    
    def _apply_modification(self, task: ModificationTask):
        """Apply code modification.
        
        Args:
            task: Modification task
        """
        logger.info(f"Applying modification for task {task.task_id}")
        
        if not task.generated_code:
            self._fail_task(task, "No generated code to apply")
            return
        try:
        
            # Update task status
            self._update_task_status(task, ModificationStatus.APPLYING)
            
            # Determine modification type
            mod_type_str = task.metadata.get("modification_type", "replace")
            mod_type = ModificationType.REPLACE
            
            for m_type in ModificationType:
                if m_type.value == mod_type_str:
                    mod_type = m_type
                    break
            
            # Check if modification type is allowed
            if mod_type.value not in self.config["allowed_modification_types"]:
                self._fail_task(task, f"Modification type {mod_type.value} not allowed")
                return
            
            # Apply modification
            result = self.code_modifier.modify_file(
                file_path=task.target_file,
                generated_code=task.generated_code,
                modification_type=mod_type,
                create_backup=True
            )
            
            # Update task with modification result
            task.modification_result = result
            self._update_task(task)
            
            if not result.success:
                self._fail_task(task, f"Modification failed: {result.errors}")
                return
            
            # Add to code repository
            version = self.code_repository.apply_generated_code(
                generated_code=task.generated_code,
                description=task.purpose
            )
            
            if version:
                task.version_id = version.version_id
                self._update_task(task)
            
            # Mark task as completed
            self._complete_task(task)
            
        except Exception as e:
            logger.error(f"Error applying modification for task {task.task_id}: {e}")
            self._fail_task(task, f"Modification error: {str(e)}")
    
    def create_task(self, target_file: str, purpose: str, priority: int = 1,
                  knowledge_query: Optional[str] = None,
                  knowledge_tags: Optional[List[str]] = None,
                  knowledge_ids: Optional[List[str]] = None,
                  metadata: Optional[Dict[str, Any]] = None) -> str:
        """Create a new modification task.
        
        Args:
            target_file: Path to the target file
            purpose: Purpose of the modification
            priority: Task priority (lower number = higher priority)
            knowledge_query: Query to search for knowledge
            knowledge_tags: Tags to search for knowledge
            knowledge_ids: IDs of specific knowledge items to use
            metadata: Additional metadata
            
        Returns:
            Task ID
        """
        # Generate task ID
        task_id = f"task_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self.tasks)}"
        
        # Create task
        task = ModificationTask(
            task_id=task_id,
            target_file=target_file,
            purpose=purpose,
            status=ModificationStatus.PENDING,
            priority=priority,
            knowledge_query=knowledge_query,
            knowledge_tags=knowledge_tags,
            knowledge_ids=knowledge_ids or [],
            metadata=metadata or {}
        )
        
        # Add task to dictionary
        self.tasks[task_id] = task
        
        # Add task to queue
        self.task_queue.put((priority, task_id))
        
        logger.info(f"Created task {task_id}: {purpose}")
        return task_id
    
    def get_task(self, task_id: str) -> Optional[ModificationTask]:
        """Get a task by ID.
        
        Args:
            task_id: Task ID
            
        Returns:
            Task if found, None otherwise
        """
        return self.tasks.get(task_id)
    
    def get_tasks(self, status: Optional[ModificationStatus] = None) -> List[ModificationTask]:
        """Get all tasks, optionally filtered by status.
        
        Args:
            status: Status to filter by
            
        Returns:
            List of tasks
        """
        if status:
            return [task for task in self.tasks.values() if task.status == status]
        return list(self.tasks.values())
    
    def approve_task(self, task_id: str) -> bool:
        """Approve a pending task.
        
        Args:
            task_id: Task ID
            
        Returns:
            True if approved, False otherwise
        """
        task = self.tasks.get(task_id)
        
        if not task:
            logger.warning(f"Task {task_id} not found")
            return False
        
        if task.status != ModificationStatus.APPROVAL_PENDING:
            logger.warning(f"Task {task_id} is not pending approval (status: {task.status.value})")
            return False
        
        # Apply modification
        self._apply_modification(task)
        return True
    
    def reject_task(self, task_id: str, reason: Optional[str] = None) -> bool:
        """Reject a pending task.
        
        Args:
            task_id: Task ID
            reason: Rejection reason
            
        Returns:
            True if rejected, False otherwise
        """
        task = self.tasks.get(task_id)
        
        if not task:
            logger.warning(f"Task {task_id} not found")
            return False
        
        if task.status != ModificationStatus.APPROVAL_PENDING:
            logger.warning(f"Task {task_id} is not pending approval (status: {task.status.value})")
            return False
        
        # Update task status
        task.status = ModificationStatus.REJECTED
        task.error_message = reason or "Task rejected"
        task.updated_at = datetime.now()
        task.completed_at = datetime.now()
        
        logger.info(f"Rejected task {task_id}: {reason or 'No reason provided'}")
        return True
    
    def cancel_task(self, task_id: str) -> bool:
        """Cancel a task.
        
        Args:
            task_id: Task ID
            
        Returns:
            True if cancelled, False otherwise
        """
        task = self.tasks.get(task_id)
        
        if not task:
            logger.warning(f"Task {task_id} not found")
            return False
        
        if task.status in [ModificationStatus.COMPLETED, ModificationStatus.FAILED, ModificationStatus.REJECTED]:
            logger.warning(f"Task {task_id} is already finished (status: {task.status.value})")
            return False
        
        # Update task status
        task.status = ModificationStatus.FAILED
        task.error_message = "Task cancelled"
        task.updated_at = datetime.now()
        task.completed_at = datetime.now()
        
        logger.info(f"Cancelled task {task_id}")
        return True
    
    def set_approval_callback(self, callback):
        """Set callback for task approval.
        
        Args:
            callback: Callback function that takes a task as argument
        """
        self.approval_callback = callback
    
    def _update_task(self, task: ModificationTask):
        """Update a task in the dictionary.
        
        Args:
            task: Task to update
        """
        task.updated_at = datetime.now()
        self.tasks[task.task_id] = task
    
    def _update_task_status(self, task: ModificationTask, status: ModificationStatus):
        """Update task status.
        
        Args:
            task: Task to update
            status: New status
        """
        task.status = status
        task.updated_at = datetime.now()
        self.tasks[task.task_id] = task
        
        logger.info(f"Updated task {task.task_id} status to {status.value}")
    
    def _complete_task(self, task: ModificationTask):
        """Mark a task as completed.
        
        Args:
            task: Task to complete
        """
        task.status = ModificationStatus.COMPLETED
        task.updated_at = datetime.now()
        task.completed_at = datetime.now()
        self.tasks[task.task_id] = task
        
        logger.info(f"Completed task {task.task_id}")
    
    def _fail_task(self, task: ModificationTask, error_message: str):
        """Mark a task as failed.
        
        Args:
            task: Task to fail
            error_message: Error message
        """
        task.status = ModificationStatus.FAILED
        task.error_message = error_message
        task.updated_at = datetime.now()
        task.completed_at = datetime.now()
        self.tasks[task.task_id] = task
        
        logger.error(f"Failed task {task.task_id}: {error_message}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get engine statistics.
        
        Returns:
            Dictionary of statistics
        """
        stats = {
            "total_tasks": len(self.tasks),
            "by_status": {},
            "by_target_file": {},
            "queue_size": self.task_queue.qsize(),
            "processing_active": self.processing_active,
            "principles_checks": {
                "total": 0,
                "passed": 0,
                "failed": 0,
                "most_preserved_principles": []
            }
        }
        
        # Count by status
        for task in self.tasks.values():
            status = task.status.value
            if status not in stats["by_status"]:
                stats["by_status"][status] = 0
            stats["by_status"][status] += 1
            
            # Count by target file
            target_file = task.target_file
            if target_file not in stats["by_target_file"]:
                stats["by_target_file"][target_file] = 0
            stats["by_target_file"][target_file] += 1
            
            # Count principles checks
            if task.principles_result:
                stats["principles_checks"]["total"] += 1
                if task.principles_result["adheres_to_principles"]:
                    stats["principles_checks"]["passed"] += 1
                else:
                    stats["principles_checks"]["failed"] += 1
                
                # Track preserved principles
                for principle in task.principles_result.get("preserved_principles", []):
                    if principle not in stats["principles_checks"]["most_preserved_principles"]:
                        stats["principles_checks"]["most_preserved_principles"].append(principle)
        
        # Limit to top 10 most preserved principles
        stats["principles_checks"]["most_preserved_principles"] = \
            stats["principles_checks"]["most_preserved_principles"][:10]
        
        return stats
