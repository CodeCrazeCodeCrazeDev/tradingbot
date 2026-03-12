"""Code Modifier for Self-Improving Trading Bot.

from pathlib import Path
This module implements a code modifier that can safely modify existing code
files based on generated code.
"""

import os
import ast
import re
import logging
import tempfile
import shutil
import difflib
import time
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum
# Git functionality removed for compatibility
# Using direct file operations instead

from .code_generator import GeneratedCode
import pathlib

logger = logging.getLogger(__name__)


class ModificationType(Enum):
    """Types of code modifications."""
    REPLACE = "replace"  # Replace entire file
    INSERT = "insert"  # Insert new code
    UPDATE = "update"  # Update existing code
    DELETE = "delete"  # Delete code
    REFACTOR = "refactor"  # Refactor code


@dataclass
class ModificationResult:
    """Result of code modification."""
    success: bool
    file_path: str
    modification_type: ModificationType
    errors: List[str]
    warnings: List[str]
    diff: str
    backup_path: Optional[str]
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


class CodeModifier:
    """Modifier for safely modifying code files."""
    
    def __init__(self, backup_dir: Optional[str] = None):
        """Initialize the code modifier.
        
        Args:
            backup_dir: Directory to store backups
        """
        self.backup_dir = backup_dir or os.path.join(os.getcwd(), "code_backups")
        os.makedirs(self.backup_dir, exist_ok=True)
        
        self.modification_history = []
        
        logger.info(f"Code modifier initialized with backup directory: {self.backup_dir}")
    
    def modify_file(self, file_path: str, generated_code: GeneratedCode,
                  modification_type: ModificationType = ModificationType.REPLACE,
                  create_backup: bool = True) -> ModificationResult:
        """Modify a code file.
        
        Args:
            file_path: Path to the file to modify
            generated_code: Generated code to use for modification
            modification_type: Type of modification to perform
            create_backup: Whether to create a backup of the original file
            
        Returns:
            Modification result
        """
        logger.info(f"Modifying file: {file_path} with {modification_type.value}")
        
        errors = []
        warnings = []
        diff = ""
        backup_path = None
        
        # Check if file exists
        file_exists = os.path.exists(file_path)
        
        if not file_exists and modification_type != ModificationType.REPLACE:
            try:
                errors.append(f"File does not exist: {file_path}")
                return ModificationResult(
                    success=False,
                    file_path=file_path,
                    modification_type=modification_type,
                    errors=errors,
                    warnings=warnings,
                    diff="",
                    backup_path=None
                )

                # Create backup if requested
                if file_exists and create_backup:
                    backup_path = self._create_backup(file_path)
                    logger.info(f"Created backup: {backup_path}")

                # Read original file if it exists
                original_code = ""
                if file_exists:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        original_code = f.read()

                # Perform modification based on type
                if modification_type == ModificationType.REPLACE:
                    new_code = generated_code.code

                    # Create directory if it doesn't exist
                    os.makedirs(os.path.dirname(file_path), exist_ok=True)

                    # Write new code to file
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(new_code)

                    # Generate diff
                    if file_exists:
                        diff = self._generate_diff(original_code, new_code, file_path)
                    else:
                        diff = f"Created new file: {file_path}"

                elif modification_type == ModificationType.INSERT:
                    new_code = self._insert_code(original_code, generated_code.code)

                    # Write new code to file
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(new_code)

                    # Generate diff
                    diff = self._generate_diff(original_code, new_code, file_path)

                elif modification_type == ModificationType.UPDATE:
                    new_code = self._update_code(original_code, generated_code.code)

                    # Write new code to file
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(new_code)

                    # Generate diff
                    diff = self._generate_diff(original_code, new_code, file_path)

                elif modification_type == ModificationType.DELETE:
                    new_code = self._delete_code(original_code, generated_code.code)

                    # Write new code to file
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(new_code)

                    # Generate diff
                    diff = self._generate_diff(original_code, new_code, file_path)

                elif modification_type == ModificationType.REFACTOR:
                    new_code = self._refactor_code(original_code, generated_code.code)

                    # Write new code to file
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(new_code)

                    # Generate diff
                    diff = self._generate_diff(original_code, new_code, file_path)

                # Record modification
                result = ModificationResult(
                    success=True,
                    file_path=file_path,
                    modification_type=modification_type,
                    errors=errors,
                    warnings=warnings,
                    diff=diff,
                    backup_path=backup_path
                )

                self._record_modification(result)
                return result

            except Exception as e:
                errors.append(f"Modification error: {e}")

                # Restore from backup if available
                if backup_path and os.path.exists(backup_path):
                    try:
                        shutil.copy2(backup_path, file_path)
                        warnings.append(f"Restored from backup: {backup_path}")
                    except Exception as restore_error:
                        errors.append(f"Restore error: {restore_error}")

                result = ModificationResult(
                    success=False,
                    file_path=file_path,
                    modification_type=modification_type,
                    errors=errors,
                    warnings=warnings,
                    diff="",
                    backup_path=backup_path
                )

                self._record_modification(result)
                return result

    def _create_backup(self, file_path: str) -> str:
        """Create a backup of a file.
        
        Args:
            file_path: Path to the file to back up
            
        Returns:
            Path to the backup file
        """
        # Create timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Create backup filename
        file_name = os.path.basename(file_path)
        backup_name = f"{file_name}.{timestamp}.bak"
        backup_path = os.path.join(self.backup_dir, backup_name)
        
        # Copy file to backup
        shutil.copy2(file_path, backup_path)
        
        return backup_path
    
    def _generate_diff(self, original_code: str, new_code: str, file_path: str) -> str:
        """Generate a diff between original and new code.
        
        Args:
            original_code: Original code
            new_code: New code
            file_path: Path to the file
            
        Returns:
            Diff string
        """
        original_lines = original_code.splitlines()
        new_lines = new_code.splitlines()
        
        diff = difflib.unified_diff(
            original_lines,
            new_lines,
            fromfile=f"a/{file_path}",
            tofile=f"b/{file_path}",
            lineterm=""
        )
        
        return "\n".join(diff)
    
    def _insert_code(self, original_code: str, new_code: str) -> str:
        """Insert new code into original code.
        
        Args:
            original_code: Original code
            new_code: New code to insert
            
        Returns:
            Modified code
        """
        try:
            # Parse original code
            original_tree = ast.parse(original_code)
        except SyntaxError:
            pass
        try:
            # If original code has syntax errors, append new code
            return original_code + "\n\n" + new_code
        
        # Parse new code
            new_tree = ast.parse(new_code)
        except SyntaxError:
            # If new code has syntax errors, append as comment
            return original_code + "\n\n# Generated code (syntax error):\n# " + new_code.replace("\n", "\n# ")
        
        # Extract imports, classes, and functions from new code
        new_imports = []
        new_classes = []
        new_functions = []
        
        for node in new_tree.body:
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                new_imports.append(ast.unparse(node))
            elif isinstance(node, ast.ClassDef):
                new_classes.append(ast.unparse(node))
            elif isinstance(node, ast.FunctionDef):
                new_functions.append(ast.unparse(node))
        
        # Find insertion points in original code
        original_lines = original_code.splitlines()
        
        # Find last import
        last_import_line = 0
        for i, node in enumerate(original_tree.body):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                last_import_line = node.end_lineno
        
        # Insert imports after last import
        if new_imports:
            original_lines.insert(last_import_line, "\n" + "\n".join(new_imports))
        
        # Append classes and functions at the end
        if new_classes or new_functions:
            original_lines.append("\n\n# Generated code:")
            original_lines.append("\n".join(new_classes + new_functions))
        
        return "\n".join(original_lines)
    
    def _update_code(self, original_code: str, new_code: str) -> str:
        """Update original code with new code.
        
        Args:
            original_code: Original code
            new_code: New code to use for update
            
        Returns:
            Modified code
        """
        try:
            # Parse original code
            original_tree = ast.parse(original_code)
        except SyntaxError:
            pass
        try:
            # If original code has syntax errors, replace with new code
            return new_code
        
        # Parse new code
            new_tree = ast.parse(new_code)
        except SyntaxError:
            # If new code has syntax errors, keep original code
            return original_code
        
        # Extract classes and functions from both code bases
        original_classes = {}
        original_functions = {}
        
        for node in original_tree.body:
            if isinstance(node, ast.ClassDef):
                original_classes[node.name] = node
            elif isinstance(node, ast.FunctionDef):
                original_functions[node.name] = node
        
        new_classes = {}
        new_functions = {}
        
        for node in new_tree.body:
            if isinstance(node, ast.ClassDef):
                new_classes[node.name] = node
            elif isinstance(node, ast.FunctionDef):
                new_functions[node.name] = node
        
        # Update classes and functions
        updated_code = original_code
        
        for name, node in new_classes.items():
            if name in original_classes:
                # Replace existing class
                class_str = ast.unparse(node)
                pattern = rf"class\s+{name}\s*\(.*?\):.*?(?=\n\S|\Z)"
                updated_code = re.sub(pattern, class_str, updated_code, flags=re.DOTALL)
            else:
                # Add new class
                class_str = ast.unparse(node)
                updated_code += f"\n\n{class_str}"
        
        for name, node in new_functions.items():
            if name in original_functions:
                # Replace existing function
                func_str = ast.unparse(node)
                pattern = rf"def\s+{name}\s*\(.*?\):.*?(?=\n\S|\Z)"
                updated_code = re.sub(pattern, func_str, updated_code, flags=re.DOTALL)
            else:
                # Add new function
                func_str = ast.unparse(node)
                updated_code += f"\n\n{func_str}"
        
        return updated_code
    
    def _delete_code(self, original_code: str, code_to_delete: str) -> str:
        """Delete code from original code.
        
        Args:
            original_code: Original code
            code_to_delete: Code to delete (can be function/class names or code snippets)
            
        Returns:
            Modified code
        """
        try:
            # Parse original code
            original_tree = ast.parse(original_code)
        except SyntaxError:
            # If original code has syntax errors, return as is
            return original_code
        
        # Check if code_to_delete contains function or class names
        lines = code_to_delete.strip().splitlines()
        names_to_delete = []
        
        for line in lines:
            line = line.strip()
            if line:
                # Check for function or class names
                func_match = re.match(r"def\s+(\w+)", line)
                class_match = re.match(r"class\s+(\w+)", line)
                
                if func_match:
                    names_to_delete.append(func_match.group(1))
                elif class_match:
                    names_to_delete.append(class_match.group(1))
                else:
                    # Check for just names
                    name_match = re.match(r"(\w+)", line)
                    if name_match:
                        names_to_delete.append(name_match.group(1))
        
        # Delete functions and classes by name
        if names_to_delete:
            updated_code = original_code
            
            for name in names_to_delete:
                # Delete class
                class_pattern = rf"class\s+{name}\s*\(.*?\):.*?(?=\n\S|\Z)"
                updated_code = re.sub(class_pattern, "", updated_code, flags=re.DOTALL)
                
                # Delete function
                func_pattern = rf"def\s+{name}\s*\(.*?\):.*?(?=\n\S|\Z)"
                updated_code = re.sub(func_pattern, "", updated_code, flags=re.DOTALL)
            
            # Clean up extra newlines
            updated_code = re.sub(r"\n{3,}", "\n\n", updated_code)
            
            return updated_code
        
        # If no names found, try to delete code snippet directly
        return original_code.replace(code_to_delete, "")
    
    def _refactor_code(self, original_code: str, refactored_code: str) -> str:
        """Refactor original code using refactored code.
        
        Args:
            original_code: Original code
            refactored_code: Refactored code
            
        Returns:
            Modified code
        """
        try:
            # For refactoring, we use a more sophisticated approach
        # that tries to preserve imports and module-level variables
        
        # Parse original code
            original_tree = ast.parse(original_code)
        except SyntaxError:
            pass
        try:
            # If original code has syntax errors, replace with refactored code
            return refactored_code
        
        # Parse refactored code
            refactored_tree = ast.parse(refactored_code)
        except SyntaxError:
            # If refactored code has syntax errors, keep original code
            return original_code
        
        # Extract imports and module-level variables from original code
        original_imports = []
        original_variables = []
        original_classes = {}
        original_functions = {}
        
        for node in original_tree.body:
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                original_imports.append(ast.unparse(node))
            elif isinstance(node, ast.Assign) and all(isinstance(target, ast.Name) for target in node.targets):
                original_variables.append(ast.unparse(node))
            elif isinstance(node, ast.ClassDef):
                original_classes[node.name] = node
            elif isinstance(node, ast.FunctionDef):
                original_functions[node.name] = node
        
        # Extract imports, classes, and functions from refactored code
        refactored_imports = []
        refactored_variables = []
        refactored_classes = {}
        refactored_functions = {}
        
        for node in refactored_tree.body:
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                refactored_imports.append(ast.unparse(node))
            elif isinstance(node, ast.Assign) and all(isinstance(target, ast.Name) for target in node.targets):
                refactored_variables.append(ast.unparse(node))
            elif isinstance(node, ast.ClassDef):
                refactored_classes[node.name] = node
            elif isinstance(node, ast.FunctionDef):
                refactored_functions[node.name] = node
        
        # Merge imports (keep all imports from both)
        merged_imports = list(set(original_imports + refactored_imports))
        
        # Merge variables (prefer refactored variables)
        merged_variables = []
        original_var_names = set()
        
        for var in original_variables:
            name = var.split("=")[0].strip()
            original_var_names.add(name)
            merged_variables.append(var)
        
        for var in refactored_variables:
            name = var.split("=")[0].strip()
            if name not in original_var_names:
                merged_variables.append(var)
        
        # Use refactored classes and functions
        merged_classes = []
        for name, node in refactored_classes.items():
            merged_classes.append(ast.unparse(node))
        
        merged_functions = []
        for name, node in refactored_functions.items():
            merged_functions.append(ast.unparse(node))
        
        # Build refactored code
        result = []
        
        # Add docstring if present
        if (len(original_tree.body) > 0 and 
            isinstance(original_tree.body[0], ast.Expr) and 
            isinstance(original_tree.body[0].value, ast.Constant) and 
            isinstance(original_tree.body[0].value.value, str)):
            result.append(ast.unparse(original_tree.body[0]))
        
        # Add imports
        result.extend(merged_imports)
        
        # Add variables
        if merged_variables:
            result.append("")  # Empty line
            result.extend(merged_variables)
        
        # Add classes
        if merged_classes:
            result.append("")  # Empty line
            result.extend(merged_classes)
        
        # Add functions
        if merged_functions:
            result.append("")  # Empty line
            result.extend(merged_functions)
        
        return "\n".join(result)
    
    def restore_from_backup(self, backup_path: str) -> bool:
        """Restore a file from backup.
        
        Args:
            backup_path: Path to the backup file
            
        Returns:
            True if successful, False otherwise
        """
        if not os.path.exists(backup_path):
            logger.error(f"Backup file not found: {backup_path}")
            return False
        try:
        
            # Extract original file path from backup name
            backup_name = os.path.basename(backup_path)
            original_name = backup_name.split(".")[0]
            
            # Determine original file path
            original_path = None
            for result in self.modification_history:
                if result.get("backup_path") == backup_path:
                    original_path = result.get("file_path")
                    break
            
            if not original_path:
                logger.warning(f"Original file path not found for backup: {backup_path}")
                # Try to guess original path
                original_path = os.path.join(os.getcwd(), original_name)
            
            # Copy backup to original file
            shutil.copy2(backup_path, original_path)
            logger.info(f"Restored file from backup: {backup_path} -> {original_path}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error restoring from backup: {e}")
            return False
    
    def _record_modification(self, result: ModificationResult):
        """Record modification result in history.
        
        Args:
            result: Modification result
        """
        self.modification_history.append({
            "timestamp": result.timestamp,
            "file_path": result.file_path,
            "modification_type": result.modification_type.value,
            "success": result.success,
            "error_count": len(result.errors),
            "warning_count": len(result.warnings),
            "backup_path": result.backup_path
        })
    
    def get_modification_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get modification history.
        
        Args:
            limit: Maximum number of entries to return
            
        Returns:
            List of modification history entries
        """
        return self.modification_history[-limit:]
    
    def get_modification_stats(self) -> Dict[str, Any]:
        """Get statistics about modifications.
        
        Returns:
            Dictionary of statistics
        """
        stats = {
            "total_modifications": len(self.modification_history),
            "successful_count": sum(1 for m in self.modification_history if m["success"]),
            "failed_count": sum(1 for m in self.modification_history if not m["success"]),
            "by_type": {},
            "by_file": {}
        }
        
        # Count by type
        for mod in self.modification_history:
            mod_type = mod["modification_type"]
            if mod_type not in stats["by_type"]:
                stats["by_type"][mod_type] = {
                    "count": 0,
                    "successful_count": 0,
                    "failed_count": 0
                }
            
            stats["by_type"][mod_type]["count"] += 1
            if mod["success"]:
                stats["by_type"][mod_type]["successful_count"] += 1
            else:
                stats["by_type"][mod_type]["failed_count"] += 1
        
        # Count by file
        for mod in self.modification_history:
            file_path = mod["file_path"]
            if file_path not in stats["by_file"]:
                stats["by_file"][file_path] = {
                    "count": 0,
                    "successful_count": 0,
                    "failed_count": 0
                }
            
            stats["by_file"][file_path]["count"] += 1
            if mod["success"]:
                stats["by_file"][file_path]["successful_count"] += 1
            else:
                stats["by_file"][file_path]["failed_count"] += 1
        
        return stats
