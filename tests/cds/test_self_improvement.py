import unittest
import os
import json
from trading_bot.core_agent_system.cds.self_improvement import CDSSelfImprovement
from trading_bot.core_agent_system.cds.evidence_graph import PersistentEvidenceStore

class TestCDSSelfImprovement(unittest.TestCase):
    def setUp(self):
        self.test_file = "test_cds_history.jsonl"
        self.store = PersistentEvidenceStore(self.test_file)
        self.improver = CDSSelfImprovement(self.test_file)

    def tearDown(self):
        if os.path.exists(self.test_file):
            os.remove(self.test_file)

    def test_calibration_cycle(self):
        # 1. Create Mock Failed Traces
        mock_trace = {
            "decision_id": "d1",
            "final_verdict": {
                "outcome": "REJECTED",
                "reviewer_verdicts": [
                    {"role": "Bear", "verdict": "REJECT", "confidence": 0.9, "reasoning": "Risk"},
                    {"role": "Bull", "verdict": "APPROVE", "confidence": 0.2, "reasoning": "Trend"}
                ]
            }
        }
        self.store.persist_trace(mock_trace)

        # 2. Run Calibration
        report = self.improver.run_calibration_cycle()

        # 3. Assertions
        self.assertEqual(report["status"], "success")
        self.assertEqual(report["num_traces_analyzed"], 1)
        self.assertIn("Bear", report["reviewer_performance"])
        self.assertEqual(report["reviewer_performance"]["Bear"]["rejected_correctly"], 1)

        # Bear accuracy is 100%, should have an increase_weight proposal
        bear_proposal = next(p for p in report["proposals"] if p["target"] == "reviewer.Bear")
        self.assertEqual(bear_proposal["action"], "increase_weight")

if __name__ == "__main__":
    unittest.main()
