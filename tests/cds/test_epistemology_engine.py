import unittest
import time
from trading_bot.core_agent_system.cds.evidence_graph import EvidenceGraph, CDSElement, NodeType, RelationType
from trading_bot.core_agent_system.cds.epistemology_engine import EpistemologyEngine

class TestEpistemologyEngine(unittest.TestCase):
    def setUp(self):
        self.eg = EvidenceGraph()
        self.engine = EpistemologyEngine()

    def test_hypothesis_analysis(self):
        # 1. Setup Graph
        h1 = CDSElement(
            id="h1",
            type=NodeType.HYPOTHESIS,
            content={
                "direction": "LONG",
                "assumptions": ["Trend persists", "No news"],
                "required_evidence_types": ["price", "volume"]
            }
        )
        self.eg.add_node(h1)

        # Support
        e1 = CDSElement(
            id="e1",
            type=NodeType.EVIDENCE,
            content={"price": 105},
            confidence=0.9,
            metadata={"evidence_type": "price"}
        )
        self.eg.add_node(e1)
        self.eg.add_relation("e1", "h1", RelationType.SUPPORTS, weight=1.0)

        # Contradiction
        e2 = CDSElement(
            id="e2",
            type=NodeType.EVIDENCE,
            content={"sentiment": "negative"},
            confidence=0.3,
            metadata={"evidence_type": "sentiment"}
        )
        self.eg.add_node(e2)
        self.eg.add_relation("e2", "h1", RelationType.CONTRADICTS, weight=1.0)

        # 2. Analyze
        report = self.engine.analyze_hypothesis("h1", self.eg)

        # 3. Assertions
        # belief_score = 0.9 / (0.9 + 0.3) = 0.75
        self.assertEqual(report.belief_score, 0.75)
        self.assertIn("volume", report.missing_critical_info)
        self.assertEqual(len(report.assumptions_identified), 2)
        self.assertTrue(report.uncertainty > 0)
        self.assertTrue(len(report.counterarguments) >= 1)
        self.assertGreater(report.adversarial_risk_score, 0)

if __name__ == "__main__":
    unittest.main()
