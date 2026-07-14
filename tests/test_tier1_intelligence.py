
import asyncio
import sys
from trading_bot.core.csc.router import SkillRouter, HASPExecutor, SkillArtifact, SkillType

async def test_skill_routing_v5():
    print("Starting Tier 1 Intelligence Verification (SkillRouter/HASP)")

    router = SkillRouter()
    executor = HASPExecutor()

    # 1. Register a HASP Skill Program
    print("Case 1: HASP Skill Program Execution")

    def mock_compliance_logic(state):
        # Deterministic logic node
        if state.get("market", {}).get("volatility", 0) > 0.5:
            return {"allow": False, "reason": "HASP: Volatility Limit"}
        return {"allow": True}

    artifact = SkillArtifact(
        skill_id="compliance_gate_hasp",
        skill_type=SkillType.HASP_PROGRAM,
        executable=mock_compliance_logic
    )
    router.register_skill(artifact)

    # 2. Route and Execute
    skill = router.route_task("risk_check", {"market": {"volatility": 0.6}})
    assert skill is not None
    assert skill.skill_id == "compliance_gate_hasp"

    result = executor.execute(skill, {"market": {"volatility": 0.6}})
    print(f"HASP Result: {result}")
    assert result["result"]["allow"] == False
    assert len(skill.performance_history) == 1
    print("PASS: HASP execution and trace-ledging works")

    # 3. Meta-Harness Optimization (Mapping update)
    print("\nCase 2: Meta-Harness Mapping Optimization")
    router.update_mapping("risk_check", "new_optimized_hasp")
    assert router._mappings["risk_check"] == "new_optimized_hasp"
    print("PASS: Meta-Harness mapping optimization works")

    print("\nTier 1 Intelligence Verification COMPLETE")

if __name__ == "__main__":
    asyncio.run(test_skill_routing_v5())
