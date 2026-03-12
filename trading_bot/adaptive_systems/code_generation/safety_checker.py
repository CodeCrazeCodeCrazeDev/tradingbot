"""Safety Checker for Self-Improving Trading Bot.

import asyncio
import json
from datetime import datetime
This module implements a safety checker that ensures generated code is safe
to execute and won't cause harm to the system or data.
"""

import os
import ast
import re
import logging
import tempfile
import subprocess
from typing import Any, Dict, List, Optional, Set, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum

from .code_generator import GeneratedCode

logger = logging.getLogger(__name__)


class SafetyLevel(Enum):
    """Safety levels for code checking."""
    BASIC = "basic"  # Check for obvious dangerous operations
    STANDARD = "standard"  # Basic + check for file operations and network access
    STRICT = "strict"  # Standard + check for resource usage and dependencies
    PARANOID = "paranoid"  # Strict + whitelist approach for all operations


@dataclass
class SafetyCheckResult:
    """Result of safety check."""
    safe: bool
    violations: List[str]
    warnings: List[str]
    level: SafetyLevel
    check_time: float  # seconds
    metadata: Dict[str, Any] = field(default_factory=dict)


class SafetyChecker:
    """Checker for ensuring code safety."""
    
    def __init__(self, default_level: SafetyLevel = SafetyLevel.STANDARD):
        """Initialize the safety checker.
        
        Args:
            default_level: Default safety level
        """
        self.default_level = default_level
        self.check_history = []
        
        # Define dangerous operations
        self.dangerous_functions = {
            'eval': 'Arbitrary code execution',
            'exec': 'Arbitrary code execution',
            'os.system': 'Shell command execution',
            'os.popen': 'Shell command execution',
            'os.spawn': 'Process spawning',
            'os.execl': 'Process execution',
            'os.execle': 'Process execution',
            'os.execlp': 'Process execution',
            'os.execlpe': 'Process execution',
            'os.execv': 'Process execution',
            'os.execve': 'Process execution',
            'os.execvp': 'Process execution',
            'os.execvpe': 'Process execution',
            'subprocess.call': 'Shell command execution',
            'subprocess.check_call': 'Shell command execution',
            'subprocess.check_output': 'Shell command execution',
            'subprocess.Popen': 'Shell command execution',
            'subprocess.run': 'Shell command execution',
            'pickle.loads': 'Arbitrary object deserialization',
            'pickle.load': 'Arbitrary object deserialization',
            'marshal.loads': 'Arbitrary object deserialization',
            'marshal.load': 'Arbitrary object deserialization',
            'yaml.load': 'Potentially unsafe YAML deserialization',
            'builtins.compile': 'Code compilation',
            '__import__': 'Dynamic module import'
        }
        
        # File operations to check
        self.file_operations = {
            'open': 'File opening',
            'file': 'File opening',
            'os.open': 'File opening',
            'os.remove': 'File deletion',
            'os.unlink': 'File deletion',
            'os.rmdir': 'Directory deletion',
            'os.removedirs': 'Directory deletion',
            'shutil.rmtree': 'Directory tree deletion',
            'os.rename': 'File renaming',
            'os.renames': 'File renaming',
            'os.replace': 'File replacement',
            'os.truncate': 'File truncation',
            'os.chmod': 'File permission modification',
            'os.chown': 'File ownership modification',
            'os.link': 'File linking',
            'os.symlink': 'Symbolic link creation'
        }
        
        # Network operations to check
        self.network_operations = {
            'socket.socket': 'Socket creation',
            'urllib.request.urlopen': 'URL opening',
            'urllib.request.Request': 'URL request',
            'http.client.HTTPConnection': 'HTTP connection',
            'http.client.HTTPSConnection': 'HTTPS connection',
            'ftplib.FTP': 'FTP connection',
            'smtplib.SMTP': 'SMTP connection',
            'telnetlib.Telnet': 'Telnet connection',
            'paramiko.SSHClient': 'SSH connection',
            'requests.get': 'HTTP GET request',
            'requests.post': 'HTTP POST request',
            'requests.put': 'HTTP PUT request',
            'requests.delete': 'HTTP DELETE request',
            'requests.head': 'HTTP HEAD request',
            'requests.options': 'HTTP OPTIONS request',
            'aiohttp.ClientSession': 'Async HTTP session'
        }
        
        # Resource usage operations to check
        self.resource_operations = {
            'multiprocessing.Process': 'Process creation',
            'threading.Thread': 'Thread creation',
            'concurrent.futures.ProcessPoolExecutor': 'Process pool creation',
            'concurrent.futures.ThreadPoolExecutor': 'Thread pool creation',
            'asyncio.create_subprocess_exec': 'Subprocess creation',
            'asyncio.create_subprocess_shell': 'Shell subprocess creation'
        }
        
        # Allowed modules for paranoid mode
        self.allowed_modules = {
            'numpy', 'pandas', 'scipy', 'sklearn', 'torch', 'tensorflow',
            'matplotlib', 'seaborn', 'plotly', 'statsmodels', 'nltk',
            'datetime', 'time', 'math', 'random', 're', 'json',
            'collections', 'itertools', 'functools', 'operator', 'typing',
            'dataclasses', 'enum', 'abc', 'logging', 'warnings', 'traceback'
        }
        
        logger.info(f"Safety checker initialized with default level: {default_level.value}")
    
    def check(self, code: Union[str, GeneratedCode], 
            level: Optional[SafetyLevel] = None) -> SafetyCheckResult:
        """Check code for safety.
        
        Args:
            code: Code to check (string or GeneratedCode object)
            level: Safety level
            
        Returns:
            Safety check result
        """
        import time
        start_time = time.time()
        
        # Extract code string if GeneratedCode object
        code_str = code.code if isinstance(code, GeneratedCode) else code
        
        # Use default level if not specified
        safety_level = level or self.default_level
        
        logger.info(f"Checking code safety with level: {safety_level.value}")
        
        violations = []
        warnings = []
        
        # Basic safety checks
        basic_violations, basic_warnings = self._basic_safety_check(code_str)
        violations.extend(basic_violations)
        warnings.extend(basic_warnings)
        
        # Standard safety checks
        if safety_level.value in ["standard", "strict", "paranoid"]:
            std_violations, std_warnings = self._standard_safety_check(code_str)
            violations.extend(std_violations)
            warnings.extend(std_warnings)
        
        # Strict safety checks
        if safety_level.value in ["strict", "paranoid"]:
            strict_violations, strict_warnings = self._strict_safety_check(code_str)
            violations.extend(strict_violations)
            warnings.extend(strict_warnings)
        
        # Paranoid safety checks
        if safety_level.value == "paranoid":
            paranoid_violations, paranoid_warnings = self._paranoid_safety_check(code_str)
            violations.extend(paranoid_violations)
            warnings.extend(paranoid_warnings)
        
        check_time = time.time() - start_time
        result = SafetyCheckResult(
            safe=len(violations) == 0,
            violations=violations,
            warnings=warnings,
            level=safety_level,
            check_time=check_time
        )
        
        self._record_check(result)
        return result
    
    def _basic_safety_check(self, code: str) -> Tuple[List[str], List[str]]:
        """Perform basic safety checks.
        
        Args:
            code: Code to check
            
        Returns:
            Tuple of (violations, warnings)
        """
        violations = []
        warnings = []
        
        try:
            tree = ast.parse(code)
            
            # Check for dangerous function calls
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    # Check direct function calls (e.g., eval(), exec())
                    if isinstance(node.func, ast.Name):
                        func_name = node.func.id
                        if func_name in self.dangerous_functions:
                            violations.append(f"Dangerous function call: {func_name} - {self.dangerous_functions[func_name]}")
                    
                    # Check attribute function calls (e.g., os.system())
                    elif isinstance(node.func, ast.Attribute):
                        if isinstance(node.func.value, ast.Name):
                            call = f"{node.func.value.id}.{node.func.attr}"
                            if call in self.dangerous_functions:
                                violations.append(f"Dangerous function call: {call} - {self.dangerous_functions[call]}")
            
            # Check for potentially dangerous imports
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for name in node.names:
                        if name.name in ['os', 'subprocess', 'pickle', 'marshal']:
                            warnings.append(f"Potentially dangerous module import: {name.name}")
                
                elif isinstance(node, ast.ImportFrom):
                    if node.module in ['os', 'subprocess', 'pickle', 'marshal']:
                        warnings.append(f"Potentially dangerous module import: {node.module}")
        
        except Exception as e:
            violations.append(f"Safety check error: {e}")
        
        return violations, warnings
    
    def _standard_safety_check(self, code: str) -> Tuple[List[str], List[str]]:
        """Perform standard safety checks.
        
        Args:
            code: Code to check
            
        Returns:
            Tuple of (violations, warnings)
        """
        violations = []
        warnings = []
        
        try:
            tree = ast.parse(code)
            
            # Check for file operations
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    # Check direct function calls (e.g., open(, encoding='utf-8'), encoding='utf-8')
                    if isinstance(node.func, ast.Name):
                        func_name = node.func.id
                        if func_name in self.file_operations:
                            warnings.append(f"File operation: {func_name} - {self.file_operations[func_name]}")
                    
                    # Check attribute function calls (e.g., os.remove())
                    elif isinstance(node.func, ast.Attribute):
                        if isinstance(node.func.value, ast.Name):
                            call = f"{node.func.value.id}.{node.func.attr}"
                            if call in self.file_operations:
                                warnings.append(f"File operation: {call} - {self.file_operations[call]}")
            
            # Check for network operations
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    # Check attribute function calls (e.g., socket.socket())
                    if isinstance(node.func, ast.Attribute):
                        if isinstance(node.func.value, ast.Name):
                            call = f"{node.func.value.id}.{node.func.attr}"
                            if call in self.network_operations:
                                warnings.append(f"Network operation: {call} - {self.network_operations[call]}")
            
            # Check for imports of network modules
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for name in node.names:
                        if name.name in ['socket', 'urllib', 'http', 'ftplib', 'smtplib', 'telnetlib', 'paramiko', 'requests', 'aiohttp']:
                            warnings.append(f"Network module import: {name.name}")
                
                elif isinstance(node, ast.ImportFrom):
                    if node.module in ['socket', 'urllib', 'http', 'ftplib', 'smtplib', 'telnetlib', 'paramiko', 'requests', 'aiohttp']:
                        warnings.append(f"Network module import: {node.module}")
        
        except Exception as e:
            violations.append(f"Safety check error: {e}")
        
        return violations, warnings
    
    def _strict_safety_check(self, code: str) -> Tuple[List[str], List[str]]:
        """Perform strict safety checks.
        
        Args:
            code: Code to check
            
        Returns:
            Tuple of (violations, warnings)
        """
        violations = []
        warnings = []
        
        try:
            tree = ast.parse(code)
            
            # Check for resource usage operations
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    # Check attribute function calls (e.g., multiprocessing.Process())
                    if isinstance(node.func, ast.Attribute):
                        if isinstance(node.func.value, ast.Name):
                            call = f"{node.func.value.id}.{node.func.attr}"
                            if call in self.resource_operations:
                                warnings.append(f"Resource operation: {call} - {self.resource_operations[call]}")
            
            # Check for imports of resource modules
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for name in node.names:
                        if name.name in ['multiprocessing', 'threading', 'concurrent']:
                            warnings.append(f"Resource module import: {name.name}")
                
                elif isinstance(node, ast.ImportFrom):
                    if node.module in ['multiprocessing', 'threading', 'concurrent']:
                        warnings.append(f"Resource module import: {node.module}")
            
            # Check for infinite loops
            for node in ast.walk(tree):
                if isinstance(node, ast.While):
                    if isinstance(node.test, ast.Constant) and node.test.value is True:
                        violations.append("Potential infinite loop: while True")
                    elif isinstance(node.test, ast.Name) and node.test.id == 'True':
                        violations.append("Potential infinite loop: while True")
            
            # Check for large memory allocations
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    if isinstance(node.func, ast.Attribute):
                        if isinstance(node.func.value, ast.Name):
                            if node.func.value.id in ['numpy', 'np'] and node.func.attr in ['zeros', 'ones', 'empty', 'full']:
                                # Check if shape is a large constant
                                for arg in node.args:
                                    if isinstance(arg, ast.Tuple):
                                        for elt in arg.elts:
                                            if isinstance(elt, ast.Constant) and isinstance(elt.value, int) and elt.value > 10000:
                                                warnings.append(f"Large memory allocation: {node.func.value.id}.{node.func.attr} with size {elt.value}")
        
        except Exception as e:
            violations.append(f"Safety check error: {e}")
        
        return violations, warnings
    
    def _paranoid_safety_check(self, code: str) -> Tuple[List[str], List[str]]:
        """Perform paranoid safety checks.
        
        Args:
            code: Code to check
            
        Returns:
            Tuple of (violations, warnings)
        """
        violations = []
        warnings = []
        
        try:
            tree = ast.parse(code)
            
            # Check all imports against whitelist
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for name in node.names:
                        base_module = name.name.split('.')[0]
                        if base_module not in self.allowed_modules:
                            violations.append(f"Non-whitelisted module import: {base_module}")
                
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        base_module = node.module.split('.')[0]
                        if base_module not in self.allowed_modules:
                            violations.append(f"Non-whitelisted module import: {base_module}")
            
            # Check for any file operations
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    # Check for open() calls
                    if isinstance(node.func, ast.Name) and node.func.id == 'open':
                        violations.append("File operation not allowed in paranoid mode: open(, encoding='utf-8')", encoding='utf-8')
                    
                    # Check for any os module calls
                    elif isinstance(node.func, ast.Attribute):
                        if isinstance(node.func.value, ast.Name) and node.func.value.id == 'os':
                            violations.append(f"OS operation not allowed in paranoid mode: os.{node.func.attr}()")
            
            # Check for any network operations
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    if isinstance(node.func, ast.Attribute):
                        if isinstance(node.func.value, ast.Name):
                            module = node.func.value.id
                            if module in ['socket', 'urllib', 'http', 'requests', 'aiohttp']:
                                violations.append(f"Network operation not allowed in paranoid mode: {module}.{node.func.attr}()")
        
        except Exception as e:
            violations.append(f"Safety check error: {e}")
        
        return violations, warnings
    
    def _record_check(self, result: SafetyCheckResult):
        """Record safety check result in history.
        
        Args:
            result: Safety check result
        """
        self.check_history.append({
            "timestamp": result.metadata.get("timestamp", None),
            "level": result.level.value,
            "safe": result.safe,
            "violation_count": len(result.violations),
            "warning_count": len(result.warnings),
            "check_time": result.check_time
        })
    
    def get_check_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get safety check history.
        
        Args:
            limit: Maximum number of entries to return
            
        Returns:
            List of safety check history entries
        """
        return self.check_history[-limit:]
    
    def get_check_stats(self) -> Dict[str, Any]:
        """Get statistics about safety checks.
        
        Returns:
            Dictionary of statistics
        """
        stats = {
            "total_checks": len(self.check_history),
            "safe_count": sum(1 for c in self.check_history if c["safe"]),
            "unsafe_count": sum(1 for c in self.check_history if not c["safe"]),
            "by_level": {},
            "avg_check_time": sum(c["check_time"] for c in self.check_history) / len(self.check_history) if self.check_history else 0
        }
        
        # Count by level
        for check in self.check_history:
            level = check["level"]
            if level not in stats["by_level"]:
                stats["by_level"][level] = {
                    "count": 0,
                    "safe_count": 0,
                    "unsafe_count": 0
                }
            
            stats["by_level"][level]["count"] += 1
            if check["safe"]:
                stats["by_level"][level]["safe_count"] += 1
            else:
                stats["by_level"][level]["unsafe_count"] += 1
        
        return stats
