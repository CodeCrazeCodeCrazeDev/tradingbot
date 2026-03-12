"""
Pipeline Approval System - Redesigned Human Approval for Complete Pipeline

This module provides a streamlined approval interface specifically designed
for the 9-stage trading pipeline with:
- Real-time CLI approval interface
- Web dashboard integration
- Telegram/Discord notifications
- Auto-approval rules
- Batch operations
- Audit trail
"""

import asyncio
import json
import logging
import os
import sys
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple
from queue import Queue

from .approval_hub import UnifiedApprovalHub, ApprovalRequest, ApprovalDecision, get_approval_hub
from .approval_types import ApprovalCategory, ApprovalPriority, ApprovalStatus, RiskLevel

logger = logging.getLogger(__name__)


# =============================================================================
# APPROVAL RULES ENGINE
# =============================================================================

@dataclass
class ApprovalRule:
    """Rule for automatic approval/rejection"""
    name: str
    condition: Callable[[Dict], bool]
    action: str  # 'approve', 'reject', 'escalate'
    reason: str
    priority: int = 0  # Higher priority rules checked first
    enabled: bool = True


class ApprovalRulesEngine:
    """
    Rules engine for automatic approval decisions
    
    Supports:
    - Risk-based rules
    - QwenCodeMender score rules
    - Time-based rules
    - Volume-based rules
    - Custom rules
    """
    
    def __init__(self):
        self.rules: List[ApprovalRule] = []
        self._init_default_rules()
    
    def _init_default_rules(self):
        """Initialize default approval rules"""
        
        # Rule 1: Auto-approve very low risk trades
        self.add_rule(ApprovalRule(
            name="auto_approve_very_low_risk",
            condition=lambda d: d.get('risk_score', 1.0) < 0.2 and d.get('qwen_codemender_score', 0) >= 0.95,
            action='approve',
            reason="Auto-approved: Very low risk (< 0.2) with high QwenCodeMender score (>= 0.95)",
            priority=100,
        ))
        
        # Rule 2: Auto-approve low risk during market hours
        self.add_rule(ApprovalRule(
            name="auto_approve_low_risk_market_hours",
            condition=lambda d: (
                d.get('risk_score', 1.0) < 0.3 and 
                d.get('qwen_codemender_score', 0) >= 0.9 and
                self._is_market_hours()
            ),
            action='approve',
            reason="Auto-approved: Low risk during market hours",
            priority=90,
        ))
        
        # Rule 3: Auto-reject very high risk
        self.add_rule(ApprovalRule(
            name="auto_reject_very_high_risk",
            condition=lambda d: d.get('risk_score', 0) > 0.9,
            action='reject',
            reason="Auto-rejected: Risk score too high (> 0.9)",
            priority=100,
        ))
        
        # Rule 4: Auto-reject low QwenCodeMender score
        self.add_rule(ApprovalRule(
            name="auto_reject_low_qwen_codemender",
            condition=lambda d: d.get('qwen_codemender_score', 1.0) < 0.5,
            action='reject',
            reason="Auto-rejected: QwenCodeMender score too low (< 0.5)",
            priority=95,
        ))
        
        # Rule 5: Escalate medium risk for human review
        self.add_rule(ApprovalRule(
            name="escalate_medium_risk",
            condition=lambda d: 0.3 <= d.get('risk_score', 0) <= 0.7,
            action='escalate',
            reason="Escalated: Medium risk requires human review",
            priority=50,
        ))
    
    def _is_market_hours(self) -> bool:
        """Check if current time is during forex market hours"""
        now = datetime.now()
        # Forex market is open 24/5 (Sunday 5pm to Friday 5pm EST)
        weekday = now.weekday()
        if weekday >= 5:  # Saturday or Sunday
            return False
        return True
    
    def add_rule(self, rule: ApprovalRule):
        """Add a rule to the engine"""
        self.rules.append(rule)
        self.rules.sort(key=lambda r: -r.priority)
    
    def remove_rule(self, name: str):
        """Remove a rule by name"""
        self.rules = [r for r in self.rules if r.name != name]
    
    def evaluate(self, details: Dict) -> Tuple[Optional[str], Optional[str]]:
        """
        Evaluate rules against trade details
        
        Returns: (action, reason) or (None, None) if no rule matches
        """
        for rule in self.rules:
            if not rule.enabled:
                continue
            try:
            
                if rule.condition(details):
                    logger.info(f"Rule matched: {rule.name} -> {rule.action}")
                    return rule.action, rule.reason
            except Exception as e:
                logger.error(f"Rule evaluation error ({rule.name}): {e}")
        
        return None, None


# =============================================================================
# REAL-TIME CLI APPROVAL INTERFACE
# =============================================================================

class CLIApprovalInterface:
    """
    Real-time CLI interface for approving trades
    
    Features:
    - Live queue display
    - Keyboard shortcuts
    - Batch operations
    - Color-coded output
    - Sound alerts
    """
    
    def __init__(self, approval_hub: UnifiedApprovalHub):
        self.hub = approval_hub
        self.running = False
        self.input_queue = Queue()
        self.rules_engine = ApprovalRulesEngine()
        
    def _clear_screen(self):
        """Clear terminal screen"""
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def _print_header(self):
        """Print header"""
        print("\n" + "=" * 80)
        print("           ALPHAALGO TRADING APPROVAL SYSTEM")
        print("=" * 80)
        print(f"  Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"  Pending: {len(self.hub.pending_requests)} requests")
        print("=" * 80)
    
    def _print_request(self, request: ApprovalRequest, index: int):
        """Print a single request"""
        # Color codes
        COLORS = {
            'red': '\033[91m',
            'green': '\033[92m',
            'yellow': '\033[93m',
            'blue': '\033[94m',
            'reset': '\033[0m',
            'bold': '\033[1m',
        }
        
        # Determine color based on risk
        if request.risk_level == RiskLevel.CRITICAL:
            color = COLORS['red']
        elif request.risk_level == RiskLevel.HIGH:
            color = COLORS['yellow']
        else:
            color = COLORS['green']
        
        details = request.details
        
        print(f"\n{color}[{index}] {COLORS['bold']}{request.title}{COLORS['reset']}")
        print(f"    ID: {request.request_id}")
        print(f"    Symbol: {details.get('symbol', 'N/A')}")
        print(f"    Direction: {details.get('direction', 'N/A')}")
        print(f"    Entry: {details.get('entry_price', 'N/A')}")
        print(f"    Stop Loss: {details.get('stop_loss', 'N/A')}")
        print(f"    Take Profit: {details.get('take_profit', 'N/A')}")
        print(f"    Position Size: {details.get('position_size', 'N/A')}")
        print(f"    Confidence: {details.get('confidence', 0):.1%}")
        print(f"    QwenCodeMender Score: {color}{details.get('qwen_codemender_score', 0):.1%}{COLORS['reset']}")
        print(f"    Risk Score: {color}{details.get('risk_score', 0):.1%}{COLORS['reset']}")
        print(f"    Reasoning: {details.get('reasoning', 'N/A')[:60]}...")
        
        if request.expires_at:
            remaining = request.time_remaining()
            if remaining:
                mins = remaining.total_seconds() / 60
                print(f"    Expires in: {mins:.1f} minutes")
    
    def _print_menu(self):
        """Print action menu"""
        print("\n" + "-" * 80)
        print("ACTIONS:")
        print("  [A <n>] Approve request #n      [R <n>] Reject request #n")
        print("  [AA]    Approve ALL             [RA]    Reject ALL")
        print("  [AL]    Approve Low-Risk        [S]     Show details")
        print("  [Q]     Quit                    [H]     Help")
        print("-" * 80)
    
    async def run(self):
        """Run the CLI interface"""
        self.running = True
        
        print("\n" + "=" * 80)
        print("ALPHAALGO APPROVAL SYSTEM - STARTING")
        print("=" * 80)
        print("\nWaiting for approval requests...")
        print("Press Ctrl+C to exit\n")
        
        try:
            while self.running:
                # Check for expired requests
                await self.hub.check_expired()
                
                # Get pending requests
                pending = self.hub.get_pending_requests()
                
                if pending:
                    self._clear_screen()
                    self._print_header()
                    
                    # Print each request
                    for i, request in enumerate(pending[:10], 1):  # Show max 10
                        self._print_request(request, i)
                    
                    if len(pending) > 10:
                        print(f"\n... and {len(pending) - 10} more requests")
                    
                    self._print_menu()
                    
                    # Get user input with timeout
                    user_input = await self._get_input_async(timeout=5.0)
                    
                    if user_input:
                        await self._process_input(user_input, pending)
                else:
                    # No pending requests - show waiting message
                    print(f"\r[{datetime.now().strftime('%H:%M:%S')}] Waiting for approval requests... (0 pending)", end='', flush=True)
                    await asyncio.sleep(1)
                    
        except KeyboardInterrupt:
            print("\n\nApproval system stopped by user")
        finally:
            self.running = False
    
    async def _get_input_async(self, timeout: float = 5.0) -> Optional[str]:
        """Get user input with timeout"""
        try:
            # Use threading for non-blocking input on Windows
            import select
            if os.name == 'nt':
                # Windows - use msvcrt
                import msvcrt
                start = time.time()
                chars = []
                while time.time() - start < timeout:
                    if msvcrt.kbhit():
                        char = msvcrt.getwch()
                        if char == '\r':
                            print()
                            return ''.join(chars)
                        elif char == '\x03':  # Ctrl+C
                            raise KeyboardInterrupt
                        else:
                            chars.append(char)
                            print(char, end='', flush=True)
                    await asyncio.sleep(0.05)
                return None
            else:
                # Unix - use select
                print("\nCommand: ", end='', flush=True)
                rlist, _, _ = select.select([sys.stdin], [], [], timeout)
                if rlist:
                    return sys.stdin.readline().strip()
                return None
        except Exception:
            return None
    
    async def _process_input(self, user_input: str, pending: List[ApprovalRequest]):
        """Process user input"""
        parts = user_input.upper().split()
        if not parts:
            return
        
        cmd = parts[0]
        
        if cmd == 'Q':
            self.running = False
            
        elif cmd == 'H':
            self._print_help()
            input("Press Enter to continue...")
            
        elif cmd == 'A' and len(parts) > 1:
            try:
                # Approve specific request
                idx = int(parts[1]) - 1
                if 0 <= idx < len(pending):
                    request = pending[idx]
                    await self.hub.approve(request.request_id, "human", "Approved via CLI")
                    print(f"\n✓ Approved: {request.title}")
                    await asyncio.sleep(1)
            except ValueError:
                print("Invalid request number")
                
        elif cmd == 'R' and len(parts) > 1:
            try:
                # Reject specific request
                idx = int(parts[1]) - 1
                if 0 <= idx < len(pending):
                    request = pending[idx]
                    reason = ' '.join(parts[2:]) if len(parts) > 2 else "Rejected via CLI"
                    await self.hub.reject(request.request_id, "human", reason)
                    print(f"\n✗ Rejected: {request.title}")
                    await asyncio.sleep(1)
            except ValueError:
                print("Invalid request number")
                
        elif cmd == 'AA':
            # Approve all
            confirm = input("Approve ALL pending requests? (yes/no): ")
            if confirm.lower() == 'yes':
                for request in pending:
                    await self.hub.approve(request.request_id, "human", "Batch approved via CLI")
                print(f"\n✓ Approved {len(pending)} requests")
                await asyncio.sleep(1)
                
        elif cmd == 'RA':
            # Reject all
            confirm = input("Reject ALL pending requests? (yes/no): ")
            if confirm.lower() == 'yes':
                for request in pending:
                    await self.hub.reject(request.request_id, "human", "Batch rejected via CLI")
                print(f"\n✗ Rejected {len(pending)} requests")
                await asyncio.sleep(1)
                
        elif cmd == 'AL':
            # Approve low-risk only
            low_risk = [r for r in pending if r.details.get('risk_score', 1.0) < 0.3]
            for request in low_risk:
                await self.hub.approve(request.request_id, "human", "Approved (low risk)")
            print(f"\n✓ Approved {len(low_risk)} low-risk requests")
            await asyncio.sleep(1)
            
        elif cmd == 'S' and len(parts) > 1:
            try:
                # Show details
                idx = int(parts[1]) - 1
                if 0 <= idx < len(pending):
                    request = pending[idx]
                    print("\n" + request.generate_summary())
                    input("Press Enter to continue...")
            except ValueError:
                print("Invalid request number")
    
    def _print_help(self):
        """Print help message"""
        print("\n" + "=" * 80)
        print("HELP - APPROVAL COMMANDS")
        print("=" * 80)
        print("""
SINGLE ACTIONS:
  A <n>     - Approve request number n
  R <n>     - Reject request number n
  S <n>     - Show full details of request n

BATCH ACTIONS:
  AA        - Approve ALL pending requests
  RA        - Reject ALL pending requests
  AL        - Approve all LOW-RISK requests (risk_score < 0.3)

NAVIGATION:
  Q         - Quit the approval system
  H         - Show this help

AUTO-APPROVAL RULES:
  - Very low risk (< 0.2) + QwenCodeMender >= 0.95 -> Auto-approve
  - Low risk (< 0.3) + QwenCodeMender >= 0.9 during market hours -> Auto-approve
  - Very high risk (> 0.9) -> Auto-reject
  - Low QwenCodeMender (< 0.5) -> Auto-reject

KEYBOARD SHORTCUTS:
  Ctrl+C    - Exit immediately
""")
        print("=" * 80)


# =============================================================================
# PIPELINE APPROVAL MANAGER
# =============================================================================

class PipelineApprovalManager:
    """
    Main approval manager for the trading pipeline
    
    Integrates:
    - Unified Approval Hub
    - Rules Engine
    - CLI Interface
    - Notifications
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # Initialize components
        self.hub = get_approval_hub(self.config.get('hub_config'))
        self.rules_engine = ApprovalRulesEngine()
        self.cli = CLIApprovalInterface(self.hub)
        
        # Callbacks for pipeline integration
        self.on_approved: List[Callable] = []
        self.on_rejected: List[Callable] = []
        
        # Register decision callback
        self.hub.add_decision_callback(self._on_decision)
        
        logger.info("Pipeline Approval Manager initialized")
    
    async def request_trade_approval(
        self,
        signal_id: str,
        symbol: str,
        direction: str,
        entry_price: float,
        stop_loss: float,
        take_profit: float,
        position_size: float,
        confidence: float,
        qwen_codemender_score: float,
        risk_score: float,
        reasoning: str,
    ) -> Tuple[bool, str]:
        """
        Request approval for a trade signal
        
        Returns: (approved, reason)
        """
        details = {
            'signal_id': signal_id,
            'symbol': symbol,
            'direction': direction,
            'entry_price': entry_price,
            'stop_loss': stop_loss,
            'take_profit': take_profit,
            'position_size': position_size,
            'confidence': confidence,
            'qwen_codemender_score': qwen_codemender_score,
            'risk_score': risk_score,
            'reasoning': reasoning,
        }
        
        # Check rules engine first
        action, reason = self.rules_engine.evaluate(details)
        
        if action == 'approve':
            logger.info(f"Trade {signal_id} auto-approved: {reason}")
            return True, reason
        
        if action == 'reject':
            logger.info(f"Trade {signal_id} auto-rejected: {reason}")
            return False, reason
        
        # Escalate to human approval
        request = await self.hub.request_approval(
            category=ApprovalCategory.TRADE_EXECUTION,
            title=f"Trade: {direction} {symbol}",
            description=f"Entry: {entry_price:.5f}, SL: {stop_loss:.5f}, TP: {take_profit:.5f}",
            details=details,
            requester='pipeline',
            source_system='complete_pipeline_orchestrator',
            value=risk_score,
            test_score=qwen_codemender_score,
        )
        
        # Wait for decision
        timeout = self.config.get('approval_timeout', 300)
        approved = await self._wait_for_decision(request.request_id, timeout)
        
        if approved:
            return True, "Approved by human"
        else:
            return False, "Rejected or timed out"
    
    async def _wait_for_decision(self, request_id: str, timeout: int) -> bool:
        """Wait for approval decision"""
        start = datetime.now()
        
        while (datetime.now() - start).total_seconds() < timeout:
            request = self.hub.get_request(request_id)
            
            if request and request.status != ApprovalStatus.PENDING:
                return request.status == ApprovalStatus.APPROVED
            
            await asyncio.sleep(0.5)
        
        return False
    
    async def _on_decision(self, request: ApprovalRequest):
        """Handle decision callback"""
        if request.status == ApprovalStatus.APPROVED:
            for callback in self.on_approved:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(request)
                    else:
                        callback(request)
                except Exception as e:
                    logger.error(f"Approval callback error: {e}")
                    
        elif request.status == ApprovalStatus.REJECTED:
            for callback in self.on_rejected:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(request)
                    else:
                        callback(request)
                except Exception as e:
                    logger.error(f"Rejection callback error: {e}")
    
    def add_approval_rule(self, rule: ApprovalRule):
        """Add custom approval rule"""
        self.rules_engine.add_rule(rule)
    
    def get_pending_count(self) -> int:
        """Get number of pending approvals"""
        return len(self.hub.pending_requests)
    
    def get_stats(self) -> Dict:
        """Get approval statistics"""
        return self.hub.get_stats()
    
    async def run_cli(self):
        """Run CLI approval interface"""
        await self.cli.run()


# =============================================================================
# STANDALONE APPROVAL RUNNER
# =============================================================================

async def run_approval_system():
    """Run the approval system standalone"""
    manager = PipelineApprovalManager()
    await manager.run_cli()


def main():
    """Main entry point"""
    print("\n" + "=" * 80)
    print("ALPHAALGO PIPELINE APPROVAL SYSTEM")
    print("=" * 80)
    print("\nStarting approval interface...")
    print("This will monitor and approve/reject trade signals from the pipeline.")
    print("\nPress Ctrl+C to exit\n")
    
    asyncio.run(run_approval_system())


if __name__ == '__main__':
    main()
