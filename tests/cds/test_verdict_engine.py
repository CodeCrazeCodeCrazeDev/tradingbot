import unittest
import asyncio
from trading_bot.core_agent_system.cds.verdict_engine import VerdictEngine, FinalVerdictOutcome

class TestVerdictEngine(unittest.TestCase):
    def setUp(self):
        self.engine = VerdictEngine()

    def test_synthesis_logic(self):
        loop = asyncio.get_event_loop()

        # Test Case: LONG hypothesis
        hypothesis = {"direction": "LONG"}
        evidence = []

        verdict = loop.run_until_complete(self.engine.synthesize(hypothesis, evidence))

        # Expected: BearReviewer will REJECT a LONG hypothesis in the current mock
        # Therefore, final verdict should be REJECTED.
        self.assertEqual(verdict.outcome, FinalVerdictOutcome.REJECTED)
        self.assertGreater(len(verdict.reviewer_verdicts), 0)
        self.assertTrue("objections" in verdict.explanation.lower())

if __name__ == "__main__":
    unittest.main()
