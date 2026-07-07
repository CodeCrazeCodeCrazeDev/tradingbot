import os

subsystems = [
    "features", "feedback", "filters", "foundation_agents", "gets", "global_expansion",
    "golden_path", "governance", "hedge_fund", "hedge_fund_safety", "hedging", "hft",
    "hivemind", "human_layer", "improvement_agent", "improvements", "indicators",
    "infrastructure", "ingestion", "innovations", "institutional", "institutional_entry",
    "integration", "integrations", "intel", "intelligence", "intelligence_core",
    "intelligent_delegation", "internet_access", "learning", "log_system", "macro",
    "market_intelligence", "market_making", "market_student", "market_teacher",
    "master_system", "meta_governance", "meta_learning", "ml", "mobile", "mobile_app",
    "models", "monitoring", "mosefs", "msos", "multimodal", "neural_integration",
    "neuros_evolution", "neuros_fi", "notifications", "observability",
    "opportunity_scanner", "ops", "optimization", "orchestration", "orchestrator",
    "performance", "perplexity_trading", "persistence", "phce_d", "portfolio",
    "position", "production", "profiling", "profit_maximizer", "psychology",
    "quality", "quant_analysis", "quantum", "qwen_codemender", "radar_ai",
    "reality_gates", "realtime", "realtime_trading_core", "reasoning",
    "recursive_evolution", "recursive_improvement", "recursive_self_improvement",
    "registry", "reporting", "research", "research_ingestion", "research_lab",
    "resilience", "risk", "risk_intelligence", "risk_management", "risk_unified",
    "safety", "schemas", "security", "self_assembly_ai", "self_concepts",
    "self_coordinating_ai", "self_diagnostic", "self_dialogue", "self_healing_ai",
    "self_improvement", "self_learning", "self_mastery", "sentient_core",
    "sentiment", "services", "signal_discovery", "signals", "simulation"
]

# Manual mappings for non-directory or special subsystems
special_mappings = {
    "integrated_agent_system": "trading_bot/core_agent_system/integrated_system.py",
    "memory": "trading_bot/core/hms/memory.py",
    "planning": "trading_bot/core/imaginationplanner.py, trading_bot/agents/planner_agent.py",
}

# Tier assignments based on directive
tiers = {
    "intelligence_core": 0, "intelligence": 0, "reasoning": 0, "learning": 0,
    "self_learning": 0, "self_improvement": 0, "recursive_self_improvement": 0,
    "recursive_evolution": 0, "meta_learning": 0, "world_model": 0, "planning": 0,
    "governance": 0, "risk": 0, "risk_management": 0, "risk_intelligence": 0,
    "safety": 0, "security": 0, "registry": 0, "orchestration": 0, "orchestrator": 0,
    "integrated_agent_system": 0, "memory": 0, "verification": 0, "research": 0,
    "institutional": 0,

    "market_intelligence": 1, "macro": 1, "quant_analysis": 1, "indicators": 1,
    "signal_discovery": 1, "signals": 1, "portfolio": 1, "position": 1,
    "hedge_fund": 1, "hedging": 1, "execution": 1, "realtime": 1,
    "realtime_trading_core": 1, "production": 1,

    "foundation_agents": 2, "hivemind": 2, "intelligent_delegation": 2,
    "self_coordinating_ai": 2, "self_assembly_ai": 2, "improvement_agent": 2,
    "monitoring": 2, "observability": 2, "reporting": 2,

    "infrastructure": 3, "persistence": 3, "services": 3, "integrations": 3,
    "ingestion": 3, "schemas": 3, "log_system": 3, "notifications": 3
}

all_targets = set(subsystems) | set(special_mappings.keys())
root_dir = "trading_bot"

mapping = {}

for sub in all_targets:
    if sub in special_mappings:
        mapping[sub] = [special_mappings[sub]]
        continue

    found = []
    for root, dirs, files in os.walk(root_dir):
        if "_archive" in root: continue # Ignore archive for primary mapping
        if sub in dirs:
            found.append(os.path.join(root, sub))

    # If not found in active dirs, check archive as fallback
    if not found:
        for root, dirs, files in os.walk(root_dir):
            if "_archive" in root and sub in dirs:
                found.append(os.path.join(root, sub))

    mapping[sub] = found

print("# Authoritative Subsystem Mapping")
print("\n| Subsystem | Primary Paths | Tier |")
print("|-----------|---------------|------|")
for sub in sorted(all_targets):
    paths = ", ".join(mapping[sub]) if mapping[sub] else "NOT FOUND"
    tier = tiers.get(sub, 4)
    print(f"| {sub} | {paths} | {tier} |")
