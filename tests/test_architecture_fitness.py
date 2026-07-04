"""
Architecture Fitness Tests - UCA-2026 Verification
================================================

Continuous verification of architectural constraints.
"""

import unittest
import sys
from trading_bot.core.unified_registry import registry, UnifiedComponentRegistry
from trading_bot.core.unified_event_bus import decision_bus, UnifiedDecisionBus
from trading_bot.core.immutable_shield import shield, ImmutableShield

class TestArchitectureFitness(unittest.TestCase):
    """
    Continuous Architecture Fitness Tests.
    """

    def test_singleton_registry(self):
        """
        Rule 3: Ensure exactly one registry instance exists.
        """
        r1 = registry
        r2 = UnifiedComponentRegistry()
        self.assertIs(r1, r2, "UnifiedComponentRegistry must be a singleton")

    def test_singleton_event_bus(self):
        """
        Rule 3: Ensure exactly one event bus instance exists.
        """
        b1 = decision_bus
        b2 = UnifiedDecisionBus()
        self.assertIs(b1, b2, "UnifiedDecisionBus must be a singleton")

    def test_singleton_shield(self):
        """
        Rule 3: Ensure exactly one governance shield instance exists.
        """
        s1 = shield
        s2 = ImmutableShield()
        self.assertIs(s1, s2, "ImmutableShield must be a singleton")

    def test_no_redundant_registries(self):
        """
        Rule 3: Check for legacy registry files (monitored during Phase 1-5).
        """
        # This will be expanded as we decommission legacy registries
        pass

    def test_no_governance_bypass_structure(self):
        """
        Rule 6: Verify no direct execution access without governance.
        (Placeholder until ImmutableShield is implemented)
        """
        pass

if __name__ == "__main__":
    unittest.main()
