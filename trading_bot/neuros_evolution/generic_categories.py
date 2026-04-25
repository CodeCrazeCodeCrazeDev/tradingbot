"""
Generic Task Categories
=======================

Fully extensible, model-agnostic task category system.
Supports any task type without hardcoded assumptions.
"""

import re
import hashlib
import logging
from typing import Dict, List, Any, Optional, Set, Callable
from dataclasses import dataclass, field
from collections import defaultdict

logger = logging.getLogger(__name__)


@dataclass
class TaskCategory:
    """Definition of a task category"""
    name: str
    description: str
    input_schema: Dict[str, str]  # field_name -> type
    output_schema: Dict[str, str]
    required_tags: List[str] = field(default_factory=list)
    optional_tags: List[str] = field(default_factory=list)
    performance_metrics: List[str] = field(default_factory=list)
    typical_latency_ms: float = 100.0
    
    def matches_input(self, input_data: Dict[str, Any]) -> float:
        """Check if input matches this category's schema (0-1 score)"""
        if not self.input_schema:
            return 1.0
        
        matches = 0
        for field, expected_type in self.input_schema.items():
            if field in input_data:
                actual_value = input_data[field]
                actual_type = type(actual_value).__name__
                
                # Check type compatibility
                if expected_type == actual_type:
                    matches += 1
                elif expected_type == 'str' and isinstance(actual_value, str):
                    matches += 1
                elif expected_type == 'float' and isinstance(actual_value, (int, float)):
                    matches += 1
                elif expected_type == 'int' and isinstance(actual_value, int):
                    matches += 1
        
        return matches / len(self.input_schema)


@dataclass
class TaskPattern:
    """Pattern for auto-detecting task category"""
    name: str
    keywords: List[str]
    regex_patterns: List[str] = field(default_factory=list)
    input_field_hints: Dict[str, str] = field(default_factory=dict)
    priority: int = 0  # Higher = check first


class GenericCategoryManager:
    """
    Manages any task categories without hardcoded assumptions.
    
    Supports:
    - Dynamic category registration
    - Auto-detection from task content
    - Schema validation
    - Category hierarchies
    """
    
    def __init__(self):
        # Registry of categories
        self._categories: Dict[str, TaskCategory] = {}
        
        # Auto-detection patterns
        self._patterns: List[TaskPattern] = []
        
        # Category hierarchy (parent -> children)
        self._hierarchy: Dict[str, List[str]] = defaultdict(list)
        
        # Statistics
        self._usage_counts: Dict[str, int] = defaultdict(int)
        
        # Built-in generic patterns
        self._init_generic_patterns()
        
        logger.info("GenericCategoryManager initialized")
    
    def _init_generic_patterns(self):
        """Initialize generic detection patterns"""
        # Generic analysis pattern
        self.add_pattern(TaskPattern(
            name="analysis",
            keywords=["analyze", "assess", "evaluate", "examine", "inspect", "review", "check"],
            input_field_hints={"data": "any", "target": "str"},
            priority=10
        ))
        
        # Generic generation pattern
        self.add_pattern(TaskPattern(
            name="generation",
            keywords=["generate", "create", "produce", "make", "build", "construct", "synthesize"],
            input_field_hints={"prompt": "str", "parameters": "dict"},
            priority=10
        ))
        
        # Generic prediction pattern
        self.add_pattern(TaskPattern(
            name="prediction",
            keywords=["predict", "forecast", "estimate", "project", "anticipate", "expect"],
            input_field_hints={"historical_data": "list", "horizon": "str"},
            priority=10
        ))
        
        # Generic classification pattern
        self.add_pattern(TaskPattern(
            name="classification",
            keywords=["classify", "categorize", "label", "tag", "identify", "recognize"],
            input_field_hints={"item": "any", "options": "list"},
            priority=10
        ))
        
        # Generic optimization pattern
        self.add_pattern(TaskPattern(
            name="optimization",
            keywords=["optimize", "improve", "enhance", "maximize", "minimize", "tune"],
            input_field_hints={"objective": "str", "constraints": "list"},
            priority=10
        ))
        
        # Generic transformation pattern
        self.add_pattern(TaskPattern(
            name="transformation",
            keywords=["transform", "convert", "translate", "map", "process"],
            input_field_hints={"input": "any", "target_format": "str"},
            priority=10
        ))
        
        # Generic decision pattern
        self.add_pattern(TaskPattern(
            name="decision",
            keywords=["decide", "choose", "select", "pick", "determine", "judge"],
            input_field_hints={"options": "list", "criteria": "dict"},
            priority=10
        ))
    
    def register_category(self, category: TaskCategory, parent: Optional[str] = None):
        """
        Register a new task category.
        
        Args:
            category: The category definition
            parent: Optional parent category for hierarchy
        """
        self._categories[category.name] = category
        
        if parent:
            self._hierarchy[parent].append(category.name)
        
        logger.info(f"Registered category: {category.name}")
    
    def add_pattern(self, pattern: TaskPattern):
        """Add a detection pattern"""
        self._patterns.append(pattern)
        # Sort by priority
        self._patterns.sort(key=lambda p: p.priority, reverse=True)
    
    def detect_category(self, 
                       task_type: str,
                       input_data: Dict[str, Any],
                       description: Optional[str] = None) -> List[Tuple[str, float]]:
        """
        Auto-detect category from task content.
        
        Returns: List of (category_name, confidence_score) sorted by confidence
        """
        scores: Dict[str, float] = defaultdict(float)
        
        text = f"{task_type} {description or ''}".lower()
        
        # Pattern matching
        for pattern in self._patterns:
            # Keyword matching
            keyword_matches = sum(1 for kw in pattern.keywords if kw in text)
            if keyword_matches > 0:
                scores[pattern.name] += keyword_matches * 0.3
            
            # Regex matching
            for regex in pattern.regex_patterns:
                try:
                    if re.search(regex, text, re.IGNORECASE):
                        scores[pattern.name] += 0.5
                except:
                    pass
            
            # Input field hints
            if pattern.input_field_hints:
                hint_matches = sum(
                    1 for hint in pattern.input_field_hints
                    if hint in input_data
                )
                scores[pattern.name] += hint_matches * 0.2
        
        # Check explicit categories
        for name, category in self._categories.items():
            if name.lower() in text:
                scores[name] += 0.8
            
            # Schema matching
            schema_match = category.matches_input(input_data)
            if schema_match > 0.5:
                scores[name] += schema_match * 0.5
        
        # Sort by score
        sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        
        # If no matches, return 'general' with low confidence
        if not sorted_scores or sorted_scores[0][1] < 0.1:
            return [("general", 0.1)]
        
        return sorted_scores
    
    def get_category(self, name: str) -> Optional[TaskCategory]:
        """Get a registered category"""
        return self._categories.get(name)
    
    def get_all_categories(self) -> List[str]:
        """Get all registered category names"""
        return list(self._categories.keys())
    
    def get_children(self, parent: str) -> List[str]:
        """Get child categories"""
        return self._hierarchy.get(parent, [])
    
    def record_usage(self, category: str):
        """Record category usage"""
        self._usage_counts[category] += 1
    
    def get_popular_categories(self, n: int = 10) -> List[Tuple[str, int]]:
        """Get most frequently used categories"""
        return sorted(
            self._usage_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )[:n]
    
    def validate_task_against_category(self, 
                                      category_name: str,
                                      input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate task input against category schema.
        
        Returns validation report.
        """
        category = self._categories.get(category_name)
        if not category:
            return {'valid': False, 'error': f'Unknown category: {category_name}'}
        
        missing = []
        type_mismatches = []
        
        for field, expected_type in category.input_schema.items():
            if field not in input_data:
                missing.append(field)
            else:
                actual_value = input_data[field]
                actual_type = type(actual_value).__name__
                
                # Check type
                if expected_type != actual_type:
                    # Allow int->float
                    if not (expected_type == 'float' and isinstance(actual_value, (int, float))):
                        type_mismatches.append({
                            'field': field,
                            'expected': expected_type,
                            'actual': actual_type
                        })
        
        return {
            'valid': len(missing) == 0 and len(type_mismatches) == 0,
            'missing_fields': missing,
            'type_mismatches': type_mismatches,
            'category': category_name
        }
    
    def suggest_improvements(self, 
                            category_name: str,
                            current_performance: float) -> List[str]:
        """
        Suggest improvements for a category based on performance.
        """
        suggestions = []
        
        category = self._categories.get(category_name)
        if not category:
            return suggestions
        
        # Low performance suggestions
        if current_performance < 0.6:
            suggestions.append(f"Consider decomposing {category_name} into smaller sub-tasks")
            suggestions.append(f"Review input schema for {category_name}")
        
        # High latency suggestions
        if category.typical_latency_ms > 100:
            suggestions.append(f"Consider caching for {category_name}")
            suggestions.append(f"Optimize {category_name} implementation for latency")
        
        # Usage-based suggestions
        usage = self._usage_counts.get(category_name, 0)
        if usage > 1000:
            suggestions.append(f"Consider creating specialized sub-categories for {category_name}")
        
        return suggestions


class DynamicCategoryDiscoverer:
    """
    Dynamically discovers new categories from task patterns.
    """
    
    def __init__(self, manager: GenericCategoryManager):
        self.manager = manager
        self._task_clusters: Dict[str, List[Dict]] = defaultdict(list)
        self._similarity_threshold = 0.7
    
    def add_task_sample(self, 
                       task_type: str,
                       input_data: Dict[str, Any],
                       description: Optional[str] = None):
        """Add a task sample for clustering"""
        sample = {
            'task_type': task_type,
            'input_fields': list(input_data.keys()),
            'input_types': {k: type(v).__name__ for k, v in input_data.items()},
            'description': description
        }
        
        # Find or create cluster
        cluster_key = self._get_cluster_key(sample)
        self._task_clusters[cluster_key].append(sample)
    
    def _get_cluster_key(self, sample: Dict) -> str:
        """Generate cluster key from sample"""
        # Use input field signature
        fields = sorted(sample['input_fields'])
        return f"fields:{','.join(fields)}"
    
    def discover_new_categories(self, min_samples: int = 10) -> List[TaskCategory]:
        """
        Discover new categories from task clusters.
        
        Returns: List of proposed new categories
        """
        discovered = []
        
        for cluster_key, samples in self._task_clusters.items():
            if len(samples) < min_samples:
                continue
            
            # Check if this cluster represents a known category
            first_sample = samples[0]
            detected = self.manager.detect_category(
                first_sample['task_type'],
                {},
                first_sample.get('description')
            )
            
            # If low confidence in existing categories, propose new one
            if not detected or detected[0][1] < 0.3:
                # Generate category from cluster
                category = self._generate_category_from_cluster(cluster_key, samples)
                if category:
                    discovered.append(category)
        
        return discovered
    
    def _generate_category_from_cluster(self, 
                                       cluster_key: str,
                                       samples: List[Dict]) -> Optional[TaskCategory]:
        """Generate a category definition from cluster samples"""
        if not samples:
            return None
        
        # Infer name from common patterns
        task_types = [s['task_type'] for s in samples]
        common_prefix = self._get_common_prefix(task_types)
        
        if common_prefix:
            name = common_prefix.strip('_').lower()
        else:
            name = f"auto_{cluster_key.replace(':', '_')}"
        
        # Infer input schema
        all_fields = defaultdict(lambda: defaultdict(int))
        for sample in samples:
            for field, field_type in sample['input_types'].items():
                all_fields[field][field_type] += 1
        
        input_schema = {}
        for field, type_counts in all_fields.items():
            # Most common type
            most_common = max(type_counts, key=type_counts.get)
            input_schema[field] = most_common
        
        return TaskCategory(
            name=name,
            description=f"Auto-discovered category: {name}",
            input_schema=input_schema,
            output_schema={},  # Unknown
            typical_latency_ms=100.0
        )
    
    def _get_common_prefix(self, strings: List[str]) -> str:
        """Find common prefix of strings"""
        if not strings:
            return ""
        
        prefix = strings[0]
        for s in strings[1:]:
            while not s.startswith(prefix):
                prefix = prefix[:-1]
                if not prefix:
                    return ""
        
        return prefix


# Global category manager instance
_category_manager: Optional[GenericCategoryManager] = None


def get_category_manager() -> GenericCategoryManager:
    """Get or create global category manager"""
    global _category_manager
    if _category_manager is None:
        _category_manager = GenericCategoryManager()
    return _category_manager


def register_category(category: TaskCategory, parent: Optional[str] = None):
    """Convenience function to register a category"""
    return get_category_manager().register_category(category, parent)


def detect_category(task_type: str, 
                   input_data: Dict[str, Any],
                   description: Optional[str] = None) -> List[Tuple[str, float]]:
    """Convenience function to detect category"""
    return get_category_manager().detect_category(task_type, input_data, description)
