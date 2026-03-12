"""
Module Scanner - Comprehensive codebase analysis
Scans all 597 modules to identify RL components and integration points
"""

import os
import ast
import logging
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field, asdict
from collections import defaultdict
import re

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class ModuleInfo:
    """Information about a Python module."""
    path: str
    name: str
    classes: List[str] = field(default_factory=list)
    functions: List[str] = field(default_factory=list)
    imports: List[str] = field(default_factory=list)
    has_rl: bool = False
    has_offline_rl: bool = False
    has_policy: bool = False
    has_q_learning: bool = False
    has_evaluation: bool = False
    integration_points: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    size_lines: int = 0
    docstring: Optional[str] = None


@dataclass
class ScanResults:
    """Results from codebase scan."""
    total_modules: int = 0
    rl_modules: List[ModuleInfo] = field(default_factory=list)
    offline_rl_modules: List[ModuleInfo] = field(default_factory=list)
    policy_modules: List[ModuleInfo] = field(default_factory=list)
    evaluation_modules: List[ModuleInfo] = field(default_factory=list)
    integration_candidates: List[ModuleInfo] = field(default_factory=list)
    missing_components: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)


class ModuleScanner:
    """
    Comprehensive module scanner for AlphaAlgo codebase.
    
    Scans all Python modules to identify:
    - Existing RL components
    - Offline RL implementations
    - Policy evaluation systems
    - Integration points
    - Missing components
    """
    
    def __init__(self, root_dir: str = "."):
        """
        Initialize module scanner.
        
        Args:
            root_dir: Root directory to scan
        """
        self.root_dir = Path(root_dir)
        self.results = ScanResults()
        
        # RL-related keywords
        self.rl_keywords = {
            'reinforcement', 'rl', 'q_learning', 'qlearning', 'policy',
            'agent', 'reward', 'state', 'action', 'episode', 'trajectory'
        }
        
        self.offline_rl_keywords = {
            'offline', 'cql', 'bcq', 'iql', 'batch', 'conservative',
            'implicit', 'constrained', 'fqe', 'ope', 'importance_sampling'
        }
        
        self.evaluation_keywords = {
            'evaluation', 'evaluate', 'ope', 'fqe', 'doubly_robust',
            'importance_sampling', 'wis', 'cvar', 'risk_adjusted'
        }
        
        logger.info(f"Module scanner initialized for: {self.root_dir}")
    
    def scan_all_modules(self) -> ScanResults:
        """
        Scan all Python modules in the codebase.
        
        Returns:
            ScanResults with comprehensive analysis
        """
        logger.info("="*80)
        logger.info("STARTING COMPREHENSIVE MODULE SCAN")
        logger.info("="*80)
        
        # Find all Python files
        python_files = list(self.root_dir.rglob("*.py"))
        self.results.total_modules = len(python_files)
        
        logger.info(f"Found {len(python_files)} Python modules")
        
        # Scan each module
        for i, file_path in enumerate(python_files, 1):
            if i % 50 == 0:
                try:
                    logger.info(f"Scanning progress: {i}/{len(python_files)} modules...")

                    module_info = self._scan_module(file_path)
                    self._categorize_module(module_info)
                except Exception as e:
                    logger.warning(f"Failed to scan {file_path}: {e}")

        # Analyze results
        self._analyze_results()
        
        logger.info("="*80)
        logger.info("MODULE SCAN COMPLETE")
        logger.info("="*80)
        
        return self.results
    
    def _scan_module(self, file_path: Path) -> ModuleInfo:
        """Scan a single module."""
        module_info = ModuleInfo(
            path=str(file_path),
            name=file_path.stem
        )
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                module_info.size_lines = len(content.splitlines())
            
            # Parse AST
            tree = ast.parse(content)
            
            # Extract docstring
            if (isinstance(tree.body[0], ast.Expr) and 
                isinstance(tree.body[0].value, ast.Str)):
                module_info.docstring = tree.body[0].value.s
            
            # Extract classes, functions, imports
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    module_info.classes.append(node.name)
                elif isinstance(node, ast.FunctionDef):
                    module_info.functions.append(node.name)
                elif isinstance(node, ast.Import):
                    for alias in node.names:
                        module_info.imports.append(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        module_info.imports.append(node.module)
            
            # Check for RL-related content
            content_lower = content.lower()
            
            module_info.has_rl = any(
                keyword in content_lower for keyword in self.rl_keywords
            )
            
            module_info.has_offline_rl = any(
                keyword in content_lower for keyword in self.offline_rl_keywords
            )
            
            module_info.has_policy = 'policy' in content_lower
            module_info.has_q_learning = 'q' in content_lower and 'learning' in content_lower
            module_info.has_evaluation = any(
                keyword in content_lower for keyword in self.evaluation_keywords
            )
            
            # Identify integration points
            if 'main' in module_info.name.lower():
                module_info.integration_points.append('main_entry')
            if 'orchestrat' in content_lower:
                module_info.integration_points.append('orchestrator')
            if 'trading' in content_lower and 'system' in content_lower:
                module_info.integration_points.append('trading_system')
            if 'alphaalgo' in content_lower:
                module_info.integration_points.append('alphaalgo')
            
        except Exception as e:
            logger.debug(f"Error parsing {file_path}: {e}")
        
        return module_info
    
    def _categorize_module(self, module_info: ModuleInfo):
        """Categorize module based on content."""
        if module_info.has_rl:
            self.results.rl_modules.append(module_info)
        
        if module_info.has_offline_rl:
            self.results.offline_rl_modules.append(module_info)
        
        if module_info.has_policy:
            self.results.policy_modules.append(module_info)
        
        if module_info.has_evaluation:
            self.results.evaluation_modules.append(module_info)
        
        if module_info.integration_points:
            self.results.integration_candidates.append(module_info)
    
    def _analyze_results(self):
        """Analyze scan results and generate recommendations."""
        logger.info("\n" + "="*80)
        logger.info("SCAN ANALYSIS")
        logger.info("="*80)
        
        logger.info(f"Total modules scanned: {self.results.total_modules}")
        logger.info(f"RL-related modules: {len(self.results.rl_modules)}")
        logger.info(f"Offline RL modules: {len(self.results.offline_rl_modules)}")
        logger.info(f"Policy modules: {len(self.results.policy_modules)}")
        logger.info(f"Evaluation modules: {len(self.results.evaluation_modules)}")
        logger.info(f"Integration candidates: {len(self.results.integration_candidates)}")
        
        # Check for missing components
        required_components = {
            'CQL': False,
            'IQL': False,
            'BCQ': False,
            'FQE': False,
            'DoublyRobust': False,
            'ImportanceSampling': False,
            'CVaR': False,
            'ContinuousLearning': False,
            'AutonomousSystem': False
        }
        
        # Check which components exist
        for module in self.results.offline_rl_modules:
            content_str = ' '.join(module.classes + module.functions)
            for component in required_components:
                if component.lower() in content_str.lower():
                    required_components[component] = True
        
        # Identify missing components
        for component, exists in required_components.items():
            if not exists:
                self.results.missing_components.append(component)
        
        # Generate recommendations
        if self.results.missing_components:
            self.results.recommendations.append(
                f"Missing components: {', '.join(self.results.missing_components)}"
            )
        
        if len(self.results.offline_rl_modules) < 5:
            self.results.recommendations.append(
                "Limited Offline RL implementation - recommend full suite"
            )
        
        if len(self.results.evaluation_modules) < 3:
            self.results.recommendations.append(
                "Insufficient evaluation methods - add FQE, DR, WIS"
            )
        
        if not any('autonomous' in m.name.lower() for m in self.results.offline_rl_modules):
            self.results.recommendations.append(
                "No autonomous system detected - implement continuous learning"
            )
        
        # Log recommendations
        if self.results.recommendations:
            logger.info("\n📋 RECOMMENDATIONS:")
            for i, rec in enumerate(self.results.recommendations, 1):
                logger.info(f"   {i}. {rec}")
        
        if self.results.missing_components:
            logger.info("\n❌ MISSING COMPONENTS:")
            for component in self.results.missing_components:
                logger.info(f"   - {component}")
    
    def save_report(self, output_path: str = "module_scan_report.json"):
        """Save scan report to JSON."""
        report = {
            'scan_timestamp': str(Path.cwd()),
            'total_modules': self.results.total_modules,
            'rl_modules_count': len(self.results.rl_modules),
            'offline_rl_modules_count': len(self.results.offline_rl_modules),
            'policy_modules_count': len(self.results.policy_modules),
            'evaluation_modules_count': len(self.results.evaluation_modules),
            'integration_candidates_count': len(self.results.integration_candidates),
            'missing_components': self.results.missing_components,
            'recommendations': self.results.recommendations,
            'rl_modules': [
                {
                    'name': m.name,
                    'path': m.path,
                    'classes': m.classes[:10],  # Limit for readability
                    'size_lines': m.size_lines
                }
                for m in self.results.rl_modules[:20]  # Top 20
            ],
            'offline_rl_modules': [
                {
                    'name': m.name,
                    'path': m.path,
                    'classes': m.classes,
                    'functions': m.functions[:10],
                    'integration_points': m.integration_points
                }
                for m in self.results.offline_rl_modules
            ],
            'integration_candidates': [
                {
                    'name': m.name,
                    'path': m.path,
                    'integration_points': m.integration_points
                }
                for m in self.results.integration_candidates[:10]
            ]
        }
        
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"\n📄 Report saved to: {output_path}")
    
    def get_integration_map(self) -> Dict[str, List[str]]:
        """Get map of integration points."""
        integration_map = defaultdict(list)
        
        for module in self.results.integration_candidates:
            for point in module.integration_points:
                integration_map[point].append(module.path)
        
        return dict(integration_map)
    
    def display_summary(self):
        """Display scan summary."""
        print("\n" + "="*80)
        logger.info("MODULE SCAN SUMMARY")
        print("="*80)
        logger.info(f"Total Modules: {self.results.total_modules}")
        logger.info(f"RL Modules: {len(self.results.rl_modules)}")
        logger.info(f"Offline RL Modules: {len(self.results.offline_rl_modules)}")
        logger.info(f"Policy Modules: {len(self.results.policy_modules)}")
        logger.info(f"Evaluation Modules: {len(self.results.evaluation_modules)}")
        logger.info(f"Integration Candidates: {len(self.results.integration_candidates)}")
        
        if self.results.offline_rl_modules:
            logger.info("\n📦 OFFLINE RL MODULES:")
            for module in self.results.offline_rl_modules[:10]:
                logger.info(f"   - {module.name} ({len(module.classes)} classes)")
        
        if self.results.missing_components:
            logger.info("\n❌ MISSING COMPONENTS:")
            for component in self.results.missing_components:
                logger.info(f"   - {component}")
        
        if self.results.recommendations:
            logger.info("\n💡 RECOMMENDATIONS:")
            for i, rec in enumerate(self.results.recommendations, 1):
                logger.info(f"   {i}. {rec}")
        
        print("="*80)


def main():
    """Run module scanner."""
    scanner = ModuleScanner(root_dir=".")
    results = scanner.scan_all_modules()
    scanner.save_report("logs/module_scan_report.json")
    scanner.display_summary()
    
    return results


if __name__ == '__main__':
    main()
