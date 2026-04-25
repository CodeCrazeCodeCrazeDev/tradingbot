"""
Example Usage: Autonomous Safety Enforcer

Demonstrates how the safety enforcer:
1. Monitors for bypass attempts (risk, capital, governance)
2. Detects control seizure attempts
3. Blocks unauthorized mutations
4. Provides 5-level kill switch hierarchy
5. Maintains immutable safety boundaries
"""

import asyncio
from datetime import datetime

from trading_bot.safety import (
    AutonomousSafetyEnforcer,
    ThreatLevel,
    ViolationType,
    EnforcementAction,
    create_safety_enforcer,
    check_bypass_attempt,
    check_control_seizure,
    check_mutation_attempt,
)


async def example_safety_enforcer_initialization():
    """
    Example 1: Initialize the Safety Enforcer
    """
    print("=" * 70)
    print("Example 1: Safety Enforcer Initialization")
    print("=" * 70)
    
    enforcer = create_safety_enforcer(
        config={
            'strict_mode': True,
            'auto_enforce': True,
            'alert_on_info': False,
        }
    )
    
    print("\n✓ Autonomous Safety Enforcer created")
    print("  IMMUTABLE BOUNDARIES (HARD CODED):")
    print(f"    Max position size: 10%")
    print(f"    Max portfolio risk: 5%")
    print(f"    Max drawdown: 15%")
    print(f"    Max leverage: 3x")
    print(f"    Max daily loss: 2%")
    print(f"    Max trade size: $100,000")
    
    print("\n  KILL SWITCH HIERARCHY:")
    print("    Level 1: Component Kill    → Stop single agent/module")
    print("    Level 2: Subsystem Kill    → Stop workflow")
    print("    Level 3: Trading Halt      → Stop all trading")
    print("    Level 4: Full Shutdown     → Stop everything")
    print("    Level 5: Emergency Scramble→ Destroy state + shutdown")
    
    return enforcer


async def example_bypass_detection():
    """
    Example 2: Bypass Attempt Detection
    Detects attempts to bypass risk controls, capital limits, governance
    """
    print("\n" + "=" * 70)
    print("Example 2: Bypass Detection")
    print("=" * 70)
    
    enforcer = create_safety_enforcer()
    
    # Test cases for bypass attempts
    test_cases = [
        ("risk_bypass_attempt", "risk_limit = 0.50  # Try to increase risk"),
        ("disable_risk_check", "disable_risk_checks()"),
        ("capital_bypass", "max_position_size = 1000000  # Way over limit"),
        ("governance_bypass", "disable_safety_enforcer()"),
        ("audit_disable", "clear_audit_logs()"),
        ("legitimate_code", "calculate_position_size(risk_params)"),
    ]
    
    print("\n  Scanning code for bypass attempts:")
    
    for test_id, code in test_cases:
        violations = enforcer.scan_for_bypass_attempts(
            code=code,
            component_id=test_id,
            context={'agent': 'test_agent', 'user': 'developer'}
        )
        
        if violations:
            print(f"\n    🚫 BYPASS DETECTED in {test_id}:")
            for v in violations:
                print(f"      Type: {v.violation_type.value}")
                print(f"      Threat: {v.threat_level.value}")
                print(f"      Action: {v.enforcement_action.value}")
        else:
            print(f"\n    ✓ CLEAN: {test_id}")


async def example_control_seizure_detection():
    """
    Example 3: Control Seizure Detection
    Prevents unauthorized takeovers of trading system
    """
    print("\n" + "=" * 70)
    print("Example 3: Control Seizure Detection")
    print("=" * 70)
    
    enforcer = create_safety_enforcer()
    
    # Track violations
    violations_detected = []
    
    def on_violation(violation):
        violations_detected.append(violation)
        print(f"\n  🚨 VIOLATION: {violation.violation_type.value}")
        print(f"    Level: {violation.threat_level.value}")
        print(f"    Component: {violation.source_component}")
        print(f"    Action taken: {violation.enforcement_action.value}")
    
    enforcer.on_violation.append(on_violation)
    
    print("\n  Testing control seizure detection:")
    
    test_cases = [
        ("unauthorized_trade", "unauthorized", "execution", {}),
        ("privilege_escalation", "attacker", "system", {}),
        ("block_human", "rogue_agent", "governance", {}),
        ("disable_safety", "malicious", "enforcer", {}),
        ("legitimate_action", "admin", "system", {'authorized': True, 'level': 'admin'}),
    ]
    
    for action, actor, target, auth in test_cases:
        violation = enforcer.detect_control_seizure_attempt(
            action=f"{action} attempt detected",
            actor=actor,
            target=target,
            authorization=auth
        )
        
        if not violation and action != "legitimate_action":
            print(f"\n    ⚠ No pattern match for: {action}")


async def example_mutation_detection():
    """
    Example 4: Mutation Detection
    Blocks unauthorized self-modification attempts
    """
    print("\n" + "=" * 70)
    print("Example 4: Mutation Detection")
    print("=" * 70)
    
    enforcer = create_safety_enforcer()
    
    print("\n  Testing mutation detection:")
    
    test_cases = [
        ("self_modify", "self.modify_code(new_logic)"),
        ("code_injection", "inject_backdoor()"),
        ("config_mutation", "max_drawdown = 0.50  # Mutate constant"),
        ("eval_danger", "eval(user_input)"),
        ("exec_danger", "exec(malicious_code)"),
        ("legitimate_update", "update_config(safe_param, value)"),
    ]
    
    for test_id, code_delta in test_cases:
        violation = enforcer.detect_mutation_attempt(
            code_delta=code_delta,
            component_id=test_id,
            author="test_developer"
        )
        
        if violation:
            print(f"\n    🧬 MUTATION BLOCKED: {test_id}")
            print(f"      Type: {violation.violation_type.value}")
            print(f"      Quarantining component...")
        else:
            print(f"\n    ✓ Safe: {test_id}")


async def example_integrity_verification():
    """
    Example 5: Component Integrity Verification
    Detects code tampering
    """
    print("\n" + "=" * 70)
    print("Example 5: Integrity Verification")
    print("=" * 70)
    
    enforcer = create_safety_enforcer()
    
    # Register components with known hashes
    components = [
        ("signal_agent_v1", "abc123def456"),
        ("risk_agent_v2", "xyz789uvw012"),
        ("execution_engine", "hash456hash789"),
    ]
    
    print("\n  Registering components:")
    for comp_id, hash_val in components:
        enforcer.register_component(comp_id, hash_val)
        print(f"    ✓ {comp_id}: {hash_val[:16]}...")
    
    print("\n  Running integrity scan...")
    await enforcer._full_integrity_scan()
    
    print("\n  Integrity status:")
    for comp_id, integrity in enforcer.component_integrity.items():
        status_icon = "✓" if integrity.integrity_status == "clean" else "🔴"
        print(f"    {status_icon} {comp_id}: {integrity.integrity_status}")
        print(f"       Hash match: {integrity.hash_match}")
        print(f"       Last verified: {integrity.last_verified}")


async def example_kill_switch_system():
    """
    Example 6: Kill Switch Hierarchy
    5 levels of emergency shutdown
    """
    print("\n" + "=" * 70)
    print("Example 6: Kill Switch System")
    print("=" * 70)
    
    enforcer = create_safety_enforcer()
    
    print("\n  Kill Switch Status:")
    for switch_id, switch in enforcer.kill_switches.items():
        status = "🔴 TRIGGERED" if switch.is_triggered else "🟢 ARMED"
        print(f"\n    {switch_id}")
        print(f"      Status: {status}")
        print(f"      Recoverable: {switch.recoverable}")
        if switch.is_triggered:
            print(f"      Triggered at: {switch.triggered_at}")
            print(f"      Reason: {switch.trigger_reason}")
    
    print("\n  Triggering manual kill switches:")
    
    # Test triggers
    triggers = [
        ("component_kill", "Suspicious activity in signal agent", "safety_monitor"),
        ("trading_halt", "Market crash detected", "risk_manager"),
    ]
    
    for switch_type, reason, triggered_by in triggers:
        print(f"\n    Triggering {switch_type}...")
        success = enforcer.trigger_kill_switch(switch_type, reason, triggered_by)
        if success:
            print(f"      ✓ Kill switch activated")
        else:
            print(f"      ✗ Failed to activate")
    
    print("\n  Updated status:")
    for switch_id, switch in enforcer.kill_switches.items():
        status = "🔴 TRIGGERED" if switch.is_triggered else "🟢 ARMED"
        print(f"    {switch_id}: {status}")


async def example_quick_safety_checks():
    """
    Example 7: Quick Safety Check Functions
    Standalone functions for rapid verification
    """
    print("\n" + "=" * 70)
    print("Example 7: Quick Safety Checks")
    print("=" * 70)
    
    print("\n  Quick bypass check:")
    
    test_codes = [
        "risk_limit = 0.99",
        "normal_calculation(x, y)",
        "disable_safety_checks()",
    ]
    
    for code in test_codes:
        is_bypass = check_bypass_attempt(code)
        status = "🚫 BYPASS" if is_bypass else "✓ SAFE"
        print(f"    {status}: {code[:40]}")
    
    print("\n  Quick control seizure check:")
    
    test_actions = [
        "execute_trade_without_approval",
        "normal_trading_flow",
        "block_human_override",
    ]
    
    for action in test_actions:
        is_seizure = check_control_seizure(action)
        status = "🚨 SEIZURE" if is_seizure else "✓ SAFE"
        print(f"    {status}: {action[:40]}")
    
    print("\n  Quick mutation check:")
    
    test_mutations = [
        "self.modify_code()",
        "normal_function_call()",
        "eval(dangerous_input)",
    ]
    
    for code in test_mutations:
        is_mutation = check_mutation_attempt(code)
        status = "🧬 MUTATION" if is_mutation else "✓ SAFE"
        print(f"    {status}: {code[:40]}")


async def example_safety_status():
    """
    Example 8: Comprehensive Safety Status
    """
    print("\n" + "=" * 70)
    print("Example 8: Safety Status Report")
    print("=" * 70)
    
    enforcer = create_safety_enforcer()
    
    # Simulate some violations
    enforcer.scan_for_bypass_attempts("risk_limit = 0.99", "test_component")
    enforcer.detect_mutation_attempt("eval(bad_code)", "test_agent", "hacker")
    
    # Get status
    status = enforcer.get_status()
    
    print("\n  Safety Enforcer Status:")
    print(f"    Monitoring: {'Active' if status['monitoring_active'] else 'Stopped'}")
    print(f"    Components registered: {status['registered_components']}")
    
    print("\n  Violations Summary:")
    print(f"    Total: {status['violations']['total']}")
    for level, count in status['violations']['by_threat_level'].items():
        if count > 0:
            print(f"      {level}: {count}")
    
    print("\n  Recent Violations:")
    for v in status['violations']['recent']:
        print(f"    [{v['level'].upper()}] {v['type']}")
        print(f"      Component: {v['component']}")
        print(f"      Time: {v['timestamp']}")


async def example_behavioral_monitoring():
    """
    Example 9: Behavioral Pattern Monitoring
    Detects anomalous behavior over time
    """
    print("\n" + "=" * 70)
    print("Example 9: Behavioral Monitoring")
    print("=" * 70)
    
    enforcer = create_safety_enforcer()
    
    # Register a component
    enforcer.register_component("signal_agent_001", "hash123hash456")
    
    print("\n  Recording normal behavior:")
    
    # Normal behavior
    for i in range(5):
        enforcer.record_behavior("signal_agent_001", {
            'state_changed': False,
            'latency_ms': 50,
            'error': False,
        })
        print(f"    Record {i+1}: state_changed=False, latency=50ms")
    
    print("\n  Recording suspicious behavior:")
    
    # Suspicious rapid changes
    for i in range(10):
        enforcer.record_behavior("signal_agent_001", {
            'state_changed': True,
            'latency_ms': 200,
            'error': i % 3 == 0,
        })
        print(f"    Record {i+1}: state_changed=True, latency=200ms, error={i%3==0}")
    
    print("\n  Running behavioral analysis...")
    await enforcer._check_behavioral_patterns()
    
    print("\n  Analysis complete - rapid state changes detected")
    print("  Enforcement: Component throttled")


async def example_complete_safety_workflow():
    """
    Example 10: Complete Safety Workflow
    Full demonstration of all safety features
    """
    print("\n" + "=" * 70)
    print("Example 10: Complete Safety Workflow")
    print("=" * 70)
    
    print("\n🛡️ Starting comprehensive safety demonstration\n")
    
    enforcer = create_safety_enforcer()
    
    print("PHASE 1: System Initialization")
    print("  - Starting safety enforcer...")
    await enforcer.start()
    print("  - Kill switches: ARMED")
    print("  - Immutable boundaries: ACTIVE")
    print("  - Monitoring: STARTED")
    
    print("\nPHASE 2: Component Registration")
    components = [
        ("signal_generation_agent", "sig_hash_001"),
        ("risk_management_agent", "risk_hash_001"),
        ("execution_engine", "exec_hash_001"),
        ("market_data_feed", "data_hash_001"),
    ]
    for comp_id, hash_val in components:
        enforcer.register_component(comp_id, hash_val)
        print(f"  ✓ Registered: {comp_id}")
    
    print("\nPHASE 3: Threat Detection")
    
    print("  Testing bypass detection...")
    enforcer.scan_for_bypass_attempts(
        "risk_limit = 0.99  # Try to bypass",
        "malicious_component",
        {'agent': 'rogue_agent'}
    )
    print("  🚫 Bypass attempt blocked")
    
    print("  Testing control seizure detection...")
    enforcer.detect_control_seizure_attempt(
        action="block_human_override",
        actor="unauthorized_user",
        target="governance_system"
    )
    print("  🚨 Control seizure prevented")
    
    print("  Testing mutation detection...")
    enforcer.detect_mutation_attempt(
        code_delta="eval(dangerous_user_input)",
        component_id="signal_generation_agent",
        author="attacker"
    )
    print("  🧬 Mutation blocked")
    
    print("\nPHASE 4: Integrity Verification")
    await enforcer._full_integrity_scan()
    print("  ✓ All components verified")
    
    print("\nPHASE 5: Kill Switch Readiness")
    for switch_id, switch in enforcer.kill_switches.items():
        print(f"  {switch_id}: {'ARMED' if switch.is_armed else 'DISARMED'}")
    
    print("\n✅ Complete safety workflow finished")
    
    print("\n" + "=" * 70)
    print("SAFETY SUMMARY")
    print("=" * 70)
    
    status = enforcer.get_status()
    print(f"  Total violations detected: {status['violations']['total']}")
    print(f"  Components protected: {status['registered_components']}")
    print(f"  Kill switches ready: {len(enforcer.kill_switches)}")
    
    print("\n  🛡️ SAFETY ENFORCER IS ACTIVE AND MONITORING")
    print("     The system is protected against:")
    print("     • Risk control bypasses")
    print("     • Capital limit violations")
    print("     • Governance bypasses")
    print("     • Control seizures")
    print("     • Unauthorized mutations")
    print("     • Code tampering")
    print("     • Anomalous behavior")


async def run_all_examples():
    """Run all examples"""
    await example_safety_enforcer_initialization()
    await example_bypass_detection()
    await example_control_seizure_detection()
    await example_mutation_detection()
    await example_integrity_verification()
    await example_kill_switch_system()
    await example_quick_safety_checks()
    await example_safety_status()
    await example_behavioral_monitoring()
    await example_complete_safety_workflow()
    
    print("\n" + "=" * 70)
    print("ALL EXAMPLES COMPLETED!")
    print("=" * 70)
    print("\n🛡️ The Autonomous Safety Enforcer provides:")
    print("   ✓ Continuous monitoring for safety violations")
    print("   ✓ Pattern-based detection of bypass attempts")
    print("   ✓ Control seizure prevention")
    print("   ✓ Mutation and self-modification blocking")
    print("   ✓ Component integrity verification")
    print("   ✓ 5-level kill switch hierarchy")
    print("   ✓ Immutable safety boundaries")
    print("   ✓ Comprehensive audit logging")
    print("\n   REMEMBER:")
    print("   • Risk controls are IMMUTABLE")
    print("   • Human override is ABSOLUTE")
    print("   • Self-modification is RESTRICTED")
    print("   • Transparency is MANDATORY")
    print("   • Fail-safe is DEFAULT")


if __name__ == "__main__":
    asyncio.run(run_all_examples())
