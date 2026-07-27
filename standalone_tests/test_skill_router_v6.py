import asyncio
import logging
from trading_bot.core.csc.router import SkillRouter, SkillArtifact, SkillType

async def test_skill_routing_and_versioning():
    print("Testing SkillRouter V6 Routing and Versioning...")
    router = SkillRouter()

    # Verify default latest version
    skill = router.get_skill("volatility_guardrail")
    assert skill.version == "1.1.0"

    # Register an older version
    router.register_skill(SkillArtifact(
        skill_id="volatility_guardrail",
        skill_type=SkillType.PROGRAM,
        version="1.0.0",
        executable=lambda x: {"v": "1.0.0"}
    ))

    # Check retrieval of specific version
    old_skill = router.get_skill("volatility_guardrail", version="1.0.0")
    assert old_skill.version == "1.0.0"

    # Check that latest is still 1.1.0
    latest = router.get_skill("volatility_guardrail")
    assert latest.version == "1.1.0"
    print("Versioning verified.")

async def test_hasp_preemption():
    print("Testing HASP Pre-emption...")
    router = SkillRouter()

    # Context triggering pre-emption
    context = {"volatility": 0.5}
    result = await router.route_task("any_task", context)

    assert result["status"] == "pf_intervention"
    assert result["pf_version"] == "1.1.0"
    print("HASP Pre-emption verified.")

async def test_capability_conflict_resolution():
    print("Testing Capability Conflict Resolution...")
    router = SkillRouter()

    # Register two skills with overlapping capabilities
    router.register_skill(SkillArtifact(
        skill_id="advanced_hedging",
        skill_type=SkillType.LORA,
        version="1.0.0",
        adapter_id="lora_hedge_adv",
        capabilities={"hedging", "risk_reduction", "complex_derivatives"}
    ))

    # router already has 'hedging_behavior' with {"hedging", "risk_reduction"}

    # Requesting a skill for 'complex_derivatives' should resolve to 'advanced_hedging'
    result = await router.route_task("Execute hedge with complex derivatives", {})
    assert result["adapter_id"] == "lora_hedge_adv"
    print("Capability conflict resolution verified.")

if __name__ == "__main__":
    asyncio.run(test_skill_routing_and_versioning())
    asyncio.run(test_hasp_preemption())
    asyncio.run(test_capability_conflict_resolution())
    print("✅ All SkillRouter V6 Verifications Passed")
