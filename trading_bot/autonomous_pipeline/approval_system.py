"""
Human Approval System - Requests human approval before deployment

Provides:
- Approval request generation
- Human-readable summaries
- Risk assessment
- Approval tracking
- Notification system

Author: AlphaAlgo Trading System
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any
import json
from pathlib import Path

logger = logging.getLogger(__name__)


class ApprovalStatus(Enum):
    """Status of approval request"""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


@dataclass
class ApprovalDecision:
    """Human decision on approval request"""
    approved: bool
    decision_time: datetime
    approver: str
    comments: Optional[str] = None
    conditions: List[str] = field(default_factory=list)


@dataclass
class ApprovalRequest:
    """Request for human approval"""
    request_id: str
    item_name: str
    item_type: str
    
    # Summary
    summary: str
    description: str
    
    # Test results
    test_score: float
    test_passed: bool
    test_details: Dict[str, Any] = field(default_factory=dict)
    
    # Risk assessment
    risk_level: str = "medium"  # low, medium, high
    risk_factors: List[str] = field(default_factory=list)
    
    # Benefits
    estimated_value: float = 0.0
    benefits: List[str] = field(default_factory=list)
    
    # Status
    status: ApprovalStatus = ApprovalStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None
    
    # Decision
    decision: Optional[ApprovalDecision] = None
    
    def to_dict(self) -> Dict:
        return {
            'request_id': self.request_id,
            'item_name': self.item_name,
            'item_type': self.item_type,
            'summary': self.summary,
            'description': self.description,
            'test_score': self.test_score,
            'test_passed': self.test_passed,
            'test_details': self.test_details,
            'risk_level': self.risk_level,
            'risk_factors': self.risk_factors,
            'estimated_value': self.estimated_value,
            'benefits': self.benefits,
            'status': self.status.value,
            'created_at': self.created_at.isoformat(),
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'decision': {
                'approved': self.decision.approved,
                'decision_time': self.decision.decision_time.isoformat(),
                'approver': self.decision.approver,
                'comments': self.decision.comments,
                'conditions': self.decision.conditions
            } if self.decision else None
        }
    
    def generate_human_readable_summary(self) -> str:
        """Generate human-readable summary"""
        lines = [
            "=" * 80,
            f"APPROVAL REQUEST: {self.item_name}",
            "=" * 80,
            "",
            f"Type: {self.item_type}",
            f"Request ID: {self.request_id}",
            f"Created: {self.created_at.strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "SUMMARY:",
            self.summary,
            "",
            "DESCRIPTION:",
            self.description,
            "",
            "TEST RESULTS:",
            f"  Overall Score: {self.test_score:.1%}",
            f"  Status: {'PASSED' if self.test_passed else 'FAILED'}",
            "",
            "RISK ASSESSMENT:",
            f"  Risk Level: {self.risk_level.upper()}",
        ]
        
        if self.risk_factors:
            lines.append("  Risk Factors:")
            for factor in self.risk_factors:
                lines.append(f"    - {factor}")
        
        lines.extend([
            "",
            "BENEFITS:",
            f"  Estimated Value: {self.estimated_value:.2f}",
        ])
        
        if self.benefits:
            lines.append("  Key Benefits:")
            for benefit in self.benefits:
                lines.append(f"    - {benefit}")
        
        lines.extend([
            "",
            "=" * 80,
            "DECISION REQUIRED:",
            "  [A] APPROVE - Deploy to live trading",
            "  [R] REJECT - Do not deploy",
            "  [D] DEFER - Review later",
            "=" * 80
        ])
        
        return "\n".join(lines)


class HumanApprovalSystem:
    """System for managing human approvals"""
    
    def __init__(self, approval_dir: str = "approvals"):
        self.approval_dir = Path(approval_dir)
        self.approval_dir.mkdir(exist_ok=True)
        
        self.pending_requests: Dict[str, ApprovalRequest] = {}
        self.completed_requests: Dict[str, ApprovalRequest] = {}
        
        # Load existing requests
        self._load_requests()
    
    def create_request(
        self,
        item_name: str,
        item_type: str,
        test_results: Dict[str, Any],
        discovered_item: Optional[Dict] = None
    ) -> ApprovalRequest:
        """Create approval request"""
        
        # Generate request ID
        request_id = f"approval_{item_name}_{int(datetime.now().timestamp())}"
        
        # Extract test info
        test_score = test_results.get('overall_score', 0.0)
        test_passed = test_results.get('status') == 'passed'
        
        # Assess risk
        risk_level, risk_factors = self._assess_risk(item_type, test_score, discovered_item)
        
        # Identify benefits
        benefits = self._identify_benefits(item_type, discovered_item)
        
        # Estimate value
        estimated_value = discovered_item.get('estimated_value', 0.0) if discovered_item else 0.0
        
        # Create request
        request = ApprovalRequest(
            request_id=request_id,
            item_name=item_name,
            item_type=item_type,
            summary=self._generate_summary(item_name, item_type, test_score),
            description=self._generate_description(item_name, item_type, discovered_item),
            test_score=test_score,
            test_passed=test_passed,
            test_details=test_results,
            risk_level=risk_level,
            risk_factors=risk_factors,
            estimated_value=estimated_value,
            benefits=benefits
        )
        
        # Save request
        self.pending_requests[request_id] = request
        self._save_request(request)
        
        # Generate human-readable file
        self._save_human_readable(request)
        
        logger.info(f"Approval request created: {request_id}")
        
        return request
    
    def _assess_risk(
        self,
        item_type: str,
        test_score: float,
        discovered_item: Optional[Dict]
    ) -> tuple[str, List[str]]:
        """Assess risk level and factors"""
        
        risk_factors = []
        
        # Test score risk
        if test_score < 0.7:
            risk_factors.append(f"Low test score: {test_score:.1%}")
        
        # Type-specific risks
        if item_type in ['ml_model', 'strategy']:
            risk_factors.append("Directly affects trading decisions")
        
        if discovered_item:
            if discovered_item.get('requires_api_key'):
                risk_factors.append("Requires API key (security consideration)")
            
            if discovered_item.get('cost') == 'paid':
                risk_factors.append("Paid service (cost consideration)")
        
        # Determine overall risk level
        if len(risk_factors) >= 3 or test_score < 0.6:
            risk_level = "high"
        elif len(risk_factors) >= 1 or test_score < 0.8:
            risk_level = "medium"
        else:
            risk_level = "low"
        
        return risk_level, risk_factors
    
    def _identify_benefits(
        self,
        item_type: str,
        discovered_item: Optional[Dict]
    ) -> List[str]:
        """Identify benefits"""
        
        benefits = []
        
        # Type-specific benefits
        type_benefits = {
            'stock_data': "Access to stock market data",
            'forex_data': "Access to forex market data",
            'crypto_data': "Access to cryptocurrency data",
            'sentiment_data': "Market sentiment analysis",
            'satellite_data': "Alternative data from satellite imagery",
            'ml_model': "Enhanced prediction capabilities",
            'strategy': "New trading strategy",
            'indicator': "New technical indicator"
        }
        
        if item_type in type_benefits:
            benefits.append(type_benefits[item_type])
        
        if discovered_item:
            if discovered_item.get('cost') == 'free':
                benefits.append("Free data source (no cost)")
            
            if discovered_item.get('quality_score', 0) > 0.8:
                benefits.append("High quality data source")
        
        return benefits
    
    def _generate_summary(self, item_name: str, item_type: str, test_score: float) -> str:
        """Generate summary"""
        return f"New {item_type} '{item_name}' passed testing with {test_score:.1%} score and is ready for deployment."
    
    def _generate_description(
        self,
        item_name: str,
        item_type: str,
        discovered_item: Optional[Dict]
    ) -> str:
        """Generate detailed description"""
        
        if discovered_item:
            desc = discovered_item.get('description', f"A {item_type} named {item_name}")
            source = discovered_item.get('source', 'Unknown')
            return f"{desc}\n\nSource: {source}"
        
        return f"A {item_type} named {item_name}"
    
    def approve(
        self,
        request_id: str,
        approver: str = "human",
        comments: Optional[str] = None,
        conditions: Optional[List[str]] = None
    ) -> bool:
        """Approve a request"""
        
        request = self.pending_requests.get(request_id)
        if not request:
            logger.error(f"Request not found: {request_id}")
            return False
        
        # Create decision
        decision = ApprovalDecision(
            approved=True,
            decision_time=datetime.now(),
            approver=approver,
            comments=comments,
            conditions=conditions or []
        )
        
        request.decision = decision
        request.status = ApprovalStatus.APPROVED
        
        # Move to completed
        self.pending_requests.pop(request_id)
        self.completed_requests[request_id] = request
        
        # Save
        self._save_request(request)
        
        logger.info(f"Request approved: {request_id}")
        
        return True
    
    def reject(
        self,
        request_id: str,
        approver: str = "human",
        comments: Optional[str] = None
    ) -> bool:
        """Reject a request"""
        
        request = self.pending_requests.get(request_id)
        if not request:
            logger.error(f"Request not found: {request_id}")
            return False
        
        # Create decision
        decision = ApprovalDecision(
            approved=False,
            decision_time=datetime.now(),
            approver=approver,
            comments=comments
        )
        
        request.decision = decision
        request.status = ApprovalStatus.REJECTED
        
        # Move to completed
        self.pending_requests.pop(request_id)
        self.completed_requests[request_id] = request
        
        # Save
        self._save_request(request)
        
        logger.info(f"Request rejected: {request_id}")
        
        return True
    
    def get_pending_requests(self) -> List[ApprovalRequest]:
        """Get all pending requests"""
        return list(self.pending_requests.values())
    
    def get_request(self, request_id: str) -> Optional[ApprovalRequest]:
        """Get specific request"""
        return self.pending_requests.get(request_id) or self.completed_requests.get(request_id)
    
    def _save_request(self, request: ApprovalRequest):
        """Save request to file"""
        filepath = self.approval_dir / f"{request.request_id}.json"
        with open(filepath, 'w') as f:
            json.dump(request.to_dict(), f, indent=2)
    
    def _save_human_readable(self, request: ApprovalRequest):
        """Save human-readable version"""
        filepath = self.approval_dir / f"{request.request_id}_REVIEW.txt"
        with open(filepath, 'w') as f:
            f.write(request.generate_human_readable_summary())
        
        logger.info(f"Human-readable approval saved: {filepath}")
    
    def _load_requests(self):
        """Load existing requests"""
        if not self.approval_dir.exists():
            return
        
        for filepath in self.approval_dir.glob("*.json"):
            try:
                with open(filepath, 'r') as f:
                    data = json.load(f)
                
                # Reconstruct request (simplified)
                request_id = data['request_id']
                status = ApprovalStatus(data['status'])
                
                # Create minimal request object
                request = ApprovalRequest(
                    request_id=request_id,
                    item_name=data['item_name'],
                    item_type=data['item_type'],
                    summary=data['summary'],
                    description=data['description'],
                    test_score=data['test_score'],
                    test_passed=data['test_passed'],
                    status=status
                )
                
                if status == ApprovalStatus.PENDING:
                    self.pending_requests[request_id] = request
                else:
                    self.completed_requests[request_id] = request
                    
            except Exception as e:
                logger.error(f"Error loading request from {filepath}: {e}")
    
    def get_approval_stats(self) -> Dict[str, Any]:
        """Get approval statistics"""
        total = len(self.pending_requests) + len(self.completed_requests)
        approved = sum(1 for r in self.completed_requests.values() if r.status == ApprovalStatus.APPROVED)
        rejected = sum(1 for r in self.completed_requests.values() if r.status == ApprovalStatus.REJECTED)
        pending = len(self.pending_requests)
        
        return {
            'total_requests': total,
            'approved': approved,
            'rejected': rejected,
            'pending': pending,
            'approval_rate': approved / total if total > 0 else 0.0
        }
