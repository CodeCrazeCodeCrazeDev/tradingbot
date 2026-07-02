import unittest
import asyncio
from trading_bot.core_agent_system.cds.orchestrator import CDSOrchestrator

class TestCDSOrchestrator(unittest.TestCase):
    def setUp(self):
        self.orchestrator = CDSOrchestrator()

    def test_full_cds_pipeline(self):
        loop = asyncio.get_event_loop()

        hypothesis = {
            "direction": "LONG",
            "required_evidence_types": ["price"]
        }
        evidence = [
            {"type": "price", "direction": "LONG", "confidence": 0.9, "weight": 1.0}
        ]

        result = loop.run_until_complete(
            self.orchestrator.decide("AAPL", hypothesis, evidence)
        )

        self.assertIn("decision_id", result)
        self.assertEqual(result["symbol"], "AAPL")
        self.assertIn("outcome", result)
        self.assertIn("trace", result)
        self.assertGreater(result["latency_ms"], 0)

if __name__ == "__main__":
    unittest.main()
