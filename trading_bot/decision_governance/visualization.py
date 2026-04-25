"""
DGS Visualization Components

Graph visualization, decision tree rendering, and dashboard components.
"""

from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime
import json


@dataclass
class VisualNode:
    """Node for visualization"""
    id: str
    label: str
    type: str
    status: str  # success, warning, error, neutral
    details: Dict[str, Any]
    x: float = 0.0
    y: float = 0.0


@dataclass
class VisualEdge:
    """Edge for visualization"""
    source: str
    target: str
    label: str
    style: str  # solid, dashed, dotted


class DecisionGraphVisualizer:
    """
    Visualizes the decision reasoning graph.
    """
    
    def __init__(self):
        self.layout_engine = ForceDirectedLayout()
    
    def visualize_claim_graph(
        self,
        claims: List[Any],
        relationships: Dict[str, List[str]]
    ) -> Dict[str, Any]:
        """
        Create visualization data for claim graph.
        
        Returns:
            Dictionary with nodes and edges for rendering
        """
        nodes = []
        edges = []
        
        # Create nodes for each claim
        for claim in claims:
            node = VisualNode(
                id=claim.id,
                label=self._truncate(claim.content, 50),
                type=claim.claim_type.value,
                status=self._get_claim_status(claim),
                details={
                    'confidence': claim.confidence,
                    'source': claim.source,
                    'timestamp': claim.timestamp.isoformat()
                }
            )
            nodes.append(node)
        
        # Create edges for relationships
        for source_id, targets in relationships.items():
            for target_id in targets:
                edge = VisualEdge(
                    source=source_id,
                    target=target_id,
                    label="depends on",
                    style="solid"
                )
                edges.append(edge)
        
        # Apply layout
        nodes = self.layout_engine.layout(nodes, edges)
        
        return {
            "nodes": [
                {
                    "id": n.id,
                    "label": n.label,
                    "type": n.type,
                    "status": n.status,
                    "details": n.details,
                    "x": n.x,
                    "y": n.y
                }
                for n in nodes
            ],
            "edges": [
                {
                    "source": e.source,
                    "target": e.target,
                    "label": e.label,
                    "style": e.style
                }
                for e in edges
            ]
        }
    
    def visualize_decision_pipeline(
        self,
        decision_record: Any
    ) -> Dict[str, Any]:
        """
        Create visualization of the complete decision pipeline.
        
        Shows all 7 layers and their outputs.
        """
        stages = [
            {
                "stage": "Signal Input",
                "status": "complete",
                "details": {
                    "symbol": decision_record.symbol,
                    "source": decision_record.signal_source
                }
            },
            {
                "stage": "Layer 1: Claim Graph",
                "status": "complete",
                "details": {
                    "claims_count": len(decision_record.claims)
                }
            },
            {
                "stage": "Layer 2: Evidence Audit",
                "status": "complete" if not decision_record.evidence_gaps else "warning",
                "details": {
                    "gaps": len(decision_record.evidence_gaps),
                    "coverage": decision_record.evidence_coverage
                }
            },
            {
                "stage": "Layer 3: Adversarial",
                "status": "complete",
                "details": {
                    "challenges": len(decision_record.adversarial_challenges)
                }
            },
            {
                "stage": "Layer 4: Regime Fit",
                "status": "complete" if decision_record.regime_applicability_score > 0.5 else "warning",
                "details": {
                    "score": decision_record.regime_applicability_score,
                    "underrepresented": decision_record.regime_underrepresentation_warning
                }
            },
            {
                "stage": "Layer 5: Counterfactuals",
                "status": "complete",
                "details": {
                    "scenarios": len(decision_record.counterfactual_scenarios),
                    "robustness": decision_record.robustness_score
                }
            },
            {
                "stage": "Layer 6: Uncertainty",
                "status": "complete",
                "details": {
                    "confidence": decision_record.uncertainty_profile.overall_confidence if decision_record.uncertainty_profile else 0,
                    "abstention": decision_record.uncertainty_profile.abstention_probability if decision_record.uncertainty_profile else 0
                }
            },
            {
                "stage": "Layer 7: Governance Arbiter",
                "status": decision_record.final_decision.value,
                "details": {
                    "decision": decision_record.final_decision.value,
                    "reasoning": decision_record.decision_reasoning[:100]
                }
            }
        ]
        
        return {
            "decision_id": decision_record.id,
            "timestamp": decision_record.timestamp.isoformat(),
            "pipeline": stages,
            "summary": {
                "decision": decision_record.final_decision.value,
                "confidence": decision_record.uncertainty_profile.overall_confidence if decision_record.uncertainty_profile else 0,
                "robustness": decision_record.robustness_score,
                "regime_fit": decision_record.regime_applicability_score
            }
        }
    
    def _truncate(self, text: str, length: int) -> str:
        """Truncate text to specified length"""
        if len(text) <= length:
            return text
        return text[:length-3] + "..."
    
    def _get_claim_status(self, claim: Any) -> str:
        """Determine visual status for claim"""
        if claim.confidence > 0.8:
            return "success"
        elif claim.confidence > 0.5:
            return "neutral"
        else:
            return "warning"


class ForceDirectedLayout:
    """Simple force-directed layout engine"""
    
    def layout(
        self,
        nodes: List[VisualNode],
        edges: List[VisualEdge],
        iterations: int = 100
    ) -> List[VisualNode]:
        """Apply force-directed layout to nodes"""
        
        # Initialize random positions
        import random
        for node in nodes:
            node.x = random.uniform(-100, 100)
            node.y = random.uniform(-100, 100)
        
        node_map = {n.id: n for n in nodes}
        
        # Simple force simulation
        for _ in range(iterations):
            # Repulsive forces between nodes
            for i, n1 in enumerate(nodes):
                for n2 in nodes[i+1:]:
                    dx = n1.x - n2.x
                    dy = n1.y - n2.y
                    dist = (dx**2 + dy**2) ** 0.5
                    
                    if dist > 0 and dist < 200:
                        force = 1000 / (dist ** 2)
                        n1.x += (dx / dist) * force
                        n1.y += (dy / dist) * force
                        n2.x -= (dx / dist) * force
                        n2.y -= (dy / dist) * force
            
            # Attractive forces along edges
            for edge in edges:
                if edge.source in node_map and edge.target in node_map:
                    n1 = node_map[edge.source]
                    n2 = node_map[edge.target]
                    
                    dx = n2.x - n1.x
                    dy = n2.y - n1.y
                    dist = (dx**2 + dy**2) ** 0.5
                    
                    if dist > 0:
                        force = dist * 0.01  # Spring force
                        n1.x += (dx / dist) * force
                        n1.y += (dy / dist) * force
                        n2.x -= (dx / dist) * force
                        n2.y -= (dy / dist) * force
        
        return nodes


class DashboardRenderer:
    """
    Renders dashboard components for web display.
    """
    
    def render_decision_summary(
        self,
        decisions: List[Any],
        time_range_hours: int = 24
    ) -> Dict[str, Any]:
        """Render decision summary for dashboard"""
        
        from collections import Counter
        
        decisions_by_type = Counter(d.final_decision.value for d in decisions)
        
        # Calculate metrics
        total = len(decisions)
        approved = decisions_by_type.get('approve', 0)
        rejected = decisions_by_type.get('reject', 0) + decisions_by_type.get('abstain', 0)
        
        approval_rate = approved / total if total > 0 else 0
        
        # Average confidence
        avg_confidence = sum(
            d.uncertainty_profile.overall_confidence for d in decisions
            if d.uncertainty_profile
        ) / total if total > 0 else 0
        
        return {
            "period": f"Last {time_range_hours} hours",
            "total_decisions": total,
            "breakdown": dict(decisions_by_type),
            "approval_rate": f"{approval_rate:.1%}",
            "average_confidence": f"{avg_confidence:.1%}",
            "trend": self._calculate_trend(decisions)
        }
    
    def render_risk_gauge(
        self,
        portfolio_value: float,
        var_1d: float,
        max_acceptable_var: float = 0.02
    ) -> Dict[str, Any]:
        """Render risk gauge visualization"""
        
        var_pct = var_1d / portfolio_value if portfolio_value > 0 else 0
        
        # Calculate risk level
        if var_pct < max_acceptable_var * 0.5:
            level = "LOW"
            color = "green"
        elif var_pct < max_acceptable_var:
            level = "MODERATE"
            color = "yellow"
        elif var_pct < max_acceptable_var * 2:
            level = "HIGH"
            color = "orange"
        else:
            level = "CRITICAL"
            color = "red"
        
        return {
            "type": "gauge",
            "value": var_pct,
            "percentage": f"{var_pct:.2%}",
            "level": level,
            "color": color,
            "max_acceptable": max_acceptable_var,
            "description": f"1-day VaR: ${var_1d:,.2f} ({var_pct:.2%})"
        }
    
    def render_latency_chart(
        self,
        latencies: List[float],
        buckets_ms: List[float] = [10, 25, 50, 100, 200, 500]
    ) -> Dict[str, Any]:
        """Render latency distribution histogram"""
        
        buckets = {f"<={b}ms": 0 for b in buckets_ms}
        buckets[">500ms"] = 0
        
        for lat in latencies:
            assigned = False
            for bucket in buckets_ms:
                if lat <= bucket:
                    buckets[f"<={bucket}ms"] += 1
                    assigned = True
                    break
            if not assigned:
                buckets[">500ms"] += 1
        
        total = len(latencies)
        
        return {
            "type": "histogram",
            "title": "Decision Latency Distribution",
            "data": [
                {"bucket": k, "count": v, "percentage": f"{v/total:.1%}"}
                for k, v in buckets.items()
            ],
            "statistics": {
                "count": total,
                "mean": f"{sum(latencies)/total:.1f}ms" if total > 0 else "N/A",
                "p95": f"{sorted(latencies)[int(total*0.95)]:.1f}ms" if total > 20 else "N/A"
            }
        }
    
    def _calculate_trend(self, decisions: List[Any]) -> str:
        """Calculate trend from decisions"""
        
        if len(decisions) < 10:
            return "insufficient_data"
        
        # Split into halves
        mid = len(decisions) // 2
        first_half = decisions[:mid]
        second_half = decisions[mid:]
        
        first_approved = sum(1 for d in first_half if d.final_decision.value == 'approve')
        second_approved = sum(1 for d in second_half if d.final_decision.value == 'approve')
        
        first_rate = first_approved / len(first_half) if first_half else 0
        second_rate = second_approved / len(second_half) if second_half else 0
        
        diff = second_rate - first_rate
        
        if diff > 0.1:
            return "improving"
        elif diff < -0.1:
            return "declining"
        else:
            return "stable"


class ReportGenerator:
    """
    Generates comprehensive reports in multiple formats.
    """
    
    def generate_html_report(
        self,
        decision_record: Any,
        audit_trail: List[Any]
    ) -> str:
        """Generate HTML report for a decision"""
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>DGS Decision Report - {decision_record.id}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .header {{ background: #f0f0f0; padding: 20px; border-radius: 5px; }}
                .section {{ margin: 20px 0; }}
                .decision {{ font-size: 24px; font-weight: bold; padding: 10px; border-radius: 5px; }}
                .approve {{ background: #d4edda; color: #155724; }}
                .reject {{ background: #f8d7da; color: #721c24; }}
                .defer {{ background: #fff3cd; color: #856404; }}
                table {{ border-collapse: collapse; width: 100%; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background: #f2f2f2; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Decision Governance Report</h1>
                <p>ID: {decision_record.id}</p>
                <p>Time: {decision_record.timestamp.isoformat()}</p>
                <p>Symbol: {decision_record.symbol}</p>
            </div>
            
            <div class="section">
                <div class="decision {decision_record.final_decision.value}">
                    Decision: {decision_record.final_decision.value.upper()}
                </div>
            </div>
            
            <div class="section">
                <h2>Scores</h2>
                <table>
                    <tr><th>Metric</th><th>Value</th></tr>
                    <tr><td>Confidence</td><td>{decision_record.uncertainty_profile.overall_confidence:.2%}</td></tr>
                    <tr><td>Robustness</td><td>{decision_record.robustness_score:.2%}</td></tr>
                    <tr><td>Regime Fit</td><td>{decision_record.regime_applicability_score:.2%}</td></tr>
                </table>
            </div>
            
            <div class="section">
                <h2>Reasoning</h2>
                <p>{decision_record.decision_reasoning}</p>
            </div>
        </body>
        </html>
        """
        
        return html
    
    def generate_json_report(
        self,
        start_date: datetime,
        end_date: datetime,
        decisions: List[Any]
    ) -> Dict[str, Any]:
        """Generate JSON report for date range"""
        
        from collections import Counter
        
        decision_counts = Counter(d.final_decision.value for d in decisions)
        
        return {
            "report_period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            },
            "summary": {
                "total_decisions": len(decisions),
                "decision_breakdown": dict(decision_counts),
                "approval_rate": decision_counts.get('approve', 0) / len(decisions) if decisions else 0
            },
            "performance": {
                "avg_confidence": sum(d.uncertainty_profile.overall_confidence for d in decisions if d.uncertainty_profile) / len(decisions) if decisions else 0,
                "avg_robustness": sum(d.robustness_score for d in decisions) / len(decisions) if decisions else 0
            },
            "decisions": [
                {
                    "id": d.id,
                    "timestamp": d.timestamp.isoformat(),
                    "symbol": d.symbol,
                    "decision": d.final_decision.value,
                    "confidence": d.uncertainty_profile.overall_confidence if d.uncertainty_profile else 0
                }
                for d in decisions
            ]
        }
