import unittest
import time
from trading_bot.core_agent_system.cds.evidence_graph import EvidenceGraph, CDSElement, NodeType, RelationType

class TestEvidenceGraph(unittest.TestCase):
    def setUp(self):
        self.eg = EvidenceGraph()

    def test_basic_graph_construction(self):
        # 1. Create Evidence
        e1 = CDSElement(id="e1", type=NodeType.EVIDENCE, content={"price": 100}, confidence=0.9)
        e2 = CDSElement(id="e2", type=NodeType.EVIDENCE, content={"vol": 0.2}, confidence=0.8)

        # 2. Create Claim
        c1 = CDSElement(id="c1", type=NodeType.CLAIM, content={"statement": "Trend is Up"}, confidence=0.85)

        # 3. Create Hypothesis
        h1 = CDSElement(id="h1", type=NodeType.HYPOTHESIS, content={"direction": "LONG"}, confidence=0.7)

        self.eg.add_node(e1)
        self.eg.add_node(e2)
        self.eg.add_node(c1)
        self.eg.add_node(h1)

        # 4. Link nodes
        self.eg.add_relation("e1", "c1", RelationType.SUPPORTS, weight=0.95)
        self.eg.add_relation("c1", "h1", RelationType.SUPPORTS, weight=0.8)
        self.eg.add_relation("e2", "h1", RelationType.CONTRADICTS, weight=0.3)

        # 5. Verify relations
        supporting = self.eg.get_supporting_evidence("c1")
        self.assertEqual(len(supporting), 1)
        self.assertEqual(supporting[0].id, "e1")

        contradicting = self.eg.get_contradicting_evidence("h1")
        self.assertEqual(len(contradicting), 1)
        self.assertEqual(contradicting[0].id, "e2")

        # 6. Verify confidence path
        conf = self.eg.calculate_path_confidence("e1", "h1")
        # e1.conf(0.9) * edge(0.95) * edge(0.8) = 0.684
        self.assertAlmostEqual(conf, 0.684)

    def test_trace_export(self):
        e1 = CDSElement(id="e_trace", type=NodeType.EVIDENCE, content={"data": 1})
        v1 = CDSElement(id="v_trace", type=NodeType.VERDICT, content={"outcome": "APPROVED"})

        self.eg.add_node(e1)
        self.eg.add_node(v1)
        self.eg.add_relation("e_trace", "v_trace", RelationType.SUPPORTS)

        trace = self.eg.export_trace("v_trace")
        self.assertEqual(trace["decision_id"], "v_trace")
        self.assertIn("e_trace", trace["nodes"])
        self.assertEqual(len(trace["edges"]), 1)

if __name__ == "__main__":
    unittest.main()
