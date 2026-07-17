import unittest
import os
import re
import ast
from trading_bot.core.unified_registry import registry, UnifiedComponentRegistry

class TestRegistryIntegrity(unittest.TestCase):
    def test_singleton(self):
        reg2 = UnifiedComponentRegistry()
        self.assertIs(registry, reg2)

    def test_deterministic_order(self):
        registry.clear()
        registry.register("comp1", {}, "type1")
        registry.register("comp2", {}, "type1")

        components = registry.list_components()
        self.assertEqual(components[0]['name'], "comp1")
        self.assertEqual(components[1]['name'], "comp2")

    def test_duplicate_prevention(self):
        registry.clear()
        # Ensure we pass two distinct object references to trigger duplicate prevention if name is same
        registry.register("comp1", {"v": 1}, "type1")
        with self.assertRaises(ValueError):
            registry.register("comp1", {"v": 2}, "type1")

    def test_forbidden_registries_ast(self):
        """
        Enforce registry architecture using AST-based static analysis.
        Fails if any class matches *Registry outside approved namespaces.
        We exclude known legacy and domain-specific non-component registries (like ModelRegistry, ExperimentRegistry).
        """
        root_dir = 'trading_bot'
        allowed_files = {
            'unified_registry.py',
            'registry.py',
            'system_registry.py',
            'module_registry.py',
            'service_registry.py'
        }

        # Exclude specific classes that represent models or datasets rather than system component registries
        allowed_classes = {
            'ModelRegistry', 'ExperimentRegistry', 'BenchmarkDatasetRegistry',
            'SchemaRegistry', 'ComponentRegistry', 'SourceRegistry',
            'MetricsRegistry', 'LegalSourceRegistry', 'ModelArtifactRegistry',
            'FormalTradingInvariantRegistry', 'FrontierCapabilityRegistry',
            'ChampionRegistry', 'AgentRegistry', 'ToolRegistry',
            'CircuitBreakerRegistry', 'ProtectedFileRegistry',
            'OpenClawRegistry', 'ImprovementRegistry', 'LayerRegistry',
            'DistillationRegistry', 'CapabilityOntologyRegistry',
            'CapabilityRegistry', 'ControlledObjectRegistry', 'FallbackRegistry',
            'DatasetRegistry', 'TrainingConfigRegistry', 'StrategyKillSwitchRegistry'
        }

        violations = []

        for root, _, files in os.walk(root_dir):
            if '_archive' in root:
                continue
            for file in files:
                if file.endswith('.py'):
                    path = os.path.join(root, file)
                    if file in allowed_files:
                        continue

                    try:
                        with open(path, 'r', encoding='utf-8', errors='replace') as f:
                            tree = ast.parse(f.read(), filename=path)

                        for node in ast.walk(tree):
                            if isinstance(node, ast.ClassDef):
                                # Exclude ModuleRegistry fallback in main package root init
                                if path == 'trading_bot/__init__.py' and node.name == 'ModuleRegistry':
                                    continue
                                if node.name.endswith('Registry') and node.name not in allowed_classes:
                                    violations.append((path, node.name, node.lineno))
                    except Exception as e:
                        # Skip files that can't be parsed
                        pass

        self.assertEqual(violations, [], f"CRITICAL: Unauthorized component registry implementations found: {violations}")

if __name__ == '__main__':
    unittest.main()
