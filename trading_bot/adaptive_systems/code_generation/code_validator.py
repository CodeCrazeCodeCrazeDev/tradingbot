"""Code Validator for Self-Improving Trading Bot.

This module implements a code validator that checks generated code for
correctness, safety, and adherence to coding standards.
"""

import os
import ast
import logging
import tempfile
import subprocess
import importlib.util
import inspect
from typing import Any, Dict, List, Optional, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum

from .code_generator import GeneratedCode

logger = logging.getLogger(__name__)


class ValidationLevel(Enum):
    """Validation levels for code validation."""
    BASIC = "basic"  # Syntax check only
    STANDARD = "standard"  # Syntax + imports + basic static analysis
    STRICT = "strict"  # Standard + linting + type checking
    COMPREHENSIVE = "comprehensive"  # Strict + test execution


@dataclass
class ValidationResult:
    """Result of code validation."""
    valid: bool
    errors: List[str]
    warnings: List[str]
    level: ValidationLevel
    validation_time: float  # seconds
    metadata: Dict[str, Any] = field(default_factory=dict)


class CodeValidator:
    """Validator for checking generated code."""
    
    def __init__(self, default_level: ValidationLevel = ValidationLevel.STANDARD):
        """Initialize the code validator.
        
        Args:
            default_level: Default validation level
        """
        self.default_level = default_level
        self.validation_history = []
        
        logger.info(f"Code validator initialized with default level: {default_level.value}")
    
    def validate(self, code: Union[str, GeneratedCode], 
               level: Optional[ValidationLevel] = None) -> ValidationResult:
        """Validate code.
        
        Args:
            code: Code to validate (string or GeneratedCode object)
            level: Validation level
            
        Returns:
            Validation result
        """
        import time
        start_time = time.time()
        
        # Extract code string if GeneratedCode object
        code_str = code.code if isinstance(code, GeneratedCode) else code
        
        # Use default level if not specified
        validation_level = level or self.default_level
        
        logger.info(f"Validating code with level: {validation_level.value}")
        
        errors = []
        warnings = []
        
        # Basic validation (syntax check)
        syntax_errors = self._check_syntax(code_str)
        errors.extend(syntax_errors)
        
        # Stop if basic validation fails
        if errors:
            validation_time = time.time() - start_time
            result = ValidationResult(
                valid=False,
                errors=errors,
                warnings=warnings,
                level=validation_level,
                validation_time=validation_time
            )
            
            self._record_validation(result)
            return result
        
        # Standard validation
        if validation_level.value in ["standard", "strict", "comprehensive"]:
            import_errors, import_warnings = self._check_imports(code_str)
            errors.extend(import_errors)
            warnings.extend(import_warnings)
            
            static_errors, static_warnings = self._static_analysis(code_str)
            errors.extend(static_errors)
            warnings.extend(static_warnings)
        
        # Strict validation
        if validation_level.value in ["strict", "comprehensive"]:
            lint_errors, lint_warnings = self._lint_code(code_str)
            errors.extend(lint_errors)
            warnings.extend(lint_warnings)
            
            type_errors, type_warnings = self._type_check(code_str)
            errors.extend(type_errors)
            warnings.extend(type_warnings)
        
        # Comprehensive validation
        if validation_level.value == "comprehensive":
            test_errors, test_warnings = self._run_tests(code_str)
            errors.extend(test_errors)
            warnings.extend(test_warnings)
        
        validation_time = time.time() - start_time
        result = ValidationResult(
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            level=validation_level,
            validation_time=validation_time
        )
        
        self._record_validation(result)
        return result
    
    def _check_syntax(self, code: str) -> List[str]:
        """Check code syntax.
        
        Args:
            code: Code to check
            
        Returns:
            List of syntax errors
        """
        errors = []
        
        try:
            ast.parse(code)
        except SyntaxError as e:
            errors.append(f"Syntax error: {e}")
        
        return errors
    
    def _check_imports(self, code: str) -> Tuple[List[str], List[str]]:
        """Check imports in code.
        
        Args:
            code: Code to check
            
        Returns:
            Tuple of (errors, warnings)
        """
        errors = []
        warnings = []
        
        try:
            tree = ast.parse(code)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for name in node.names:
                        try:
                            importlib.util.find_spec(name.name)
                        except ImportError:
                            errors.append(f"Import error: Module '{name.name}' not found")
                        except Exception as e:
                            warnings.append(f"Import warning: {e}")
                
                elif isinstance(node, ast.ImportFrom):
                    try:
                        importlib.util.find_spec(node.module)
                    except ImportError:
                        errors.append(f"Import error: Module '{node.module}' not found")
                    except Exception as e:
                        warnings.append(f"Import warning: {e}")
        
        except Exception as e:
            errors.append(f"Import check error: {e}")
        
        return errors, warnings
    
    def _static_analysis(self, code: str) -> Tuple[List[str], List[str]]:
        """Perform static analysis on code.
        
        Args:
            code: Code to analyze
            
        Returns:
            Tuple of (errors, warnings)
        """
        errors = []
        warnings = []
        
        try:
            tree = ast.parse(code)
            
            # Check for undefined variables
            defined_vars = set()
            for node in ast.walk(tree):
                if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
                    defined_vars.add(node.id)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
                    if node.id not in defined_vars and node.id not in __builtins__:
                        warnings.append(f"Potential undefined variable: {node.id}")
            
            # Check for unused variables
            used_vars = set()
            for node in ast.walk(tree):
                if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
                    used_vars.add(node.id)
            
            for var in defined_vars:
                if var not in used_vars and not var.startswith('_'):
                    warnings.append(f"Unused variable: {var}")
            
            # Check for potentially dangerous functions
            dangerous_functions = ['eval', 'exec', 'os.system', 'subprocess.call', 
                                 'subprocess.Popen', 'subprocess.run']
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    if isinstance(node.func, ast.Name) and node.func.id in ['eval', 'exec']:
                        errors.append(f"Dangerous function call: {node.func.id}")
                    elif isinstance(node.func, ast.Attribute):
                        if isinstance(node.func.value, ast.Name):
                            call = f"{node.func.value.id}.{node.func.attr}"
                            if call in dangerous_functions:
                                errors.append(f"Dangerous function call: {call}")
        
        except Exception as e:
            errors.append(f"Static analysis error: {e}")
        
        return errors, warnings
    
    def _lint_code(self, code: str) -> Tuple[List[str], List[str]]:
        """Lint code using flake8.
        
        Args:
            code: Code to lint
            
        Returns:
            Tuple of (errors, warnings)
        """
        errors = []
        warnings = []
        
        try:
            # Write code to temporary file
            with tempfile.NamedTemporaryFile(suffix='.py', delete=False) as temp_file:
                pass
            try:
                temp_file_path = temp_file.name
                temp_file.write(code.encode('utf-8'))
            
                # Run flake8
                result = subprocess.run(
                    ['flake8', temp_file_path],
                    capture_output=True,
                    text=True
                )
                
                if result.returncode != 0:
                    for line in result.stdout.splitlines():
                        if 'E' in line:  # Error
                            errors.append(f"Linting error: {line}")
                        else:  # Warning
                            warnings.append(f"Linting warning: {line}")
            
            finally:
                # Clean up temporary file
                os.unlink(temp_file_path)
        
        except FileNotFoundError:
            warnings.append("Linting skipped: flake8 not installed")
        except Exception as e:
            warnings.append(f"Linting error: {e}")
        
        return errors, warnings
    
    def _type_check(self, code: str) -> Tuple[List[str], List[str]]:
        """Type check code using mypy.
        
        Args:
            code: Code to type check
            
        Returns:
            Tuple of (errors, warnings)
        """
        errors = []
        warnings = []
        
        try:
            # Write code to temporary file
            with tempfile.NamedTemporaryFile(suffix='.py', delete=False) as temp_file:
                pass
            try:
                temp_file_path = temp_file.name
                temp_file.write(code.encode('utf-8'))
            
                # Run mypy
                result = subprocess.run(
                    ['mypy', '--ignore-missing-imports', temp_file_path],
                    capture_output=True,
                    text=True
                )
                
                if result.returncode != 0:
                    for line in result.stdout.splitlines():
                        if 'error' in line.lower():
                            errors.append(f"Type error: {line}")
                        else:
                            warnings.append(f"Type warning: {line}")
            
            finally:
                # Clean up temporary file
                os.unlink(temp_file_path)
        
        except FileNotFoundError:
            warnings.append("Type checking skipped: mypy not installed")
        except Exception as e:
            warnings.append(f"Type checking error: {e}")
        
        return errors, warnings
    
    def _run_tests(self, code: str) -> Tuple[List[str], List[str]]:
        """Run tests in code.
        
        Args:
            code: Code to test
            
        Returns:
            Tuple of (errors, warnings)
        """
        errors = []
        warnings = []
        
        try:
            # Check if code contains test functions
            tree = ast.parse(code)
            has_tests = False
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef) and node.name.startswith('test_'):
                    has_tests = True
                    break
            
            if not has_tests:
                warnings.append("No test functions found in code")
                return errors, warnings
            
            # Write code to temporary file
            with tempfile.NamedTemporaryFile(suffix='.py', delete=False) as temp_file:
                pass
            try:
                temp_file_path = temp_file.name
                temp_file.write(code.encode('utf-8'))
            
                # Run pytest
                result = subprocess.run(
                    ['pytest', temp_file_path, '-v'],
                    capture_output=True,
                    text=True
                )
                
                if result.returncode != 0:
                    for line in result.stdout.splitlines():
                        if 'FAILED' in line:
                            errors.append(f"Test error: {line}")
                        elif 'warning' in line.lower():
                            warnings.append(f"Test warning: {line}")
            
            finally:
                # Clean up temporary file
                os.unlink(temp_file_path)
        
        except FileNotFoundError:
            warnings.append("Testing skipped: pytest not installed")
        except Exception as e:
            warnings.append(f"Testing error: {e}")
        
        return errors, warnings
    
    def _record_validation(self, result: ValidationResult):
        """Record validation result in history.
        
        Args:
            result: Validation result
        """
        self.validation_history.append({
            "timestamp": result.metadata.get("timestamp", None),
            "level": result.level.value,
            "valid": result.valid,
            "error_count": len(result.errors),
            "warning_count": len(result.warnings),
            "validation_time": result.validation_time
        })
    
    def get_validation_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get validation history.
        
        Args:
            limit: Maximum number of entries to return
            
        Returns:
            List of validation history entries
        """
        return self.validation_history[-limit:]
    
    def get_validation_stats(self) -> Dict[str, Any]:
        """Get statistics about validation.
        
        Returns:
            Dictionary of statistics
        """
        stats = {
            "total_validations": len(self.validation_history),
            "valid_count": sum(1 for v in self.validation_history if v["valid"]),
            "invalid_count": sum(1 for v in self.validation_history if not v["valid"]),
            "by_level": {},
            "avg_validation_time": sum(v["validation_time"] for v in self.validation_history) / len(self.validation_history) if self.validation_history else 0
        }
        
        # Count by level
        for validation in self.validation_history:
            level = validation["level"]
            if level not in stats["by_level"]:
                stats["by_level"][level] = {
                    "count": 0,
                    "valid_count": 0,
                    "invalid_count": 0
                }
            
            stats["by_level"][level]["count"] += 1
            if validation["valid"]:
                stats["by_level"][level]["valid_count"] += 1
            else:
                stats["by_level"][level]["invalid_count"] += 1
        
        return stats
