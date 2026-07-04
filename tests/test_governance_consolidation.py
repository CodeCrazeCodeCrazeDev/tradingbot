import unittest
from trading_bot.core.immutable_shield import shield, GovernanceDecision
from trading_bot.core_agent_system.cds.governance_gate import GovernanceGate, GovernanceStatus

class TestGovernanceConsolidation(unittest.TestCase):
    def test_shield_blocking(self):
        # Action that should be blocked: High Drawdown
        context = {"portfolio": {"drawdown": 0.20}}
        report = shield.validate_action("trade", {"exposure": 0.1}, context)
        self.assertEqual(report.decision, GovernanceDecision.BLOCKED)
        self.assertIn("drawdown", report.reason)

    def test_shield_approval(self):
        # Action that should be approved
        context = {"portfolio": {"drawdown": 0.05}, "market": {"volatility": 0.1}}
        report = shield.validate_action("trade", {"exposure": 0.1}, context)
        self.assertEqual(report.decision, GovernanceDecision.APPROVED)

    def test_legacy_gate_parallel_check(self):
        # Verify legacy gate still functions (backward compatibility)
        gate = GovernanceGate()
        context = {"portfolio": {"drawdown": 0.20}, "market": {"volatility": 0.1}}
        report = gate.check(None, context)
        self.assertEqual(report.status, GovernanceStatus.FAILED)

if __name__ == "__main__":
    unittest.main()
