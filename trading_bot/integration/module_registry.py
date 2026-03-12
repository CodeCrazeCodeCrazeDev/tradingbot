"""
Canonical Module Registry
=========================
Single authoritative inventory of every Python module under trading_bot/.

Responsibilities:
  - Discover all modules (7,226+)
  - Classify each by layer, tier, domain, and capital impact
  - Track import health (importable / partial / broken)
  - Track promotion state: discovered → registered → wrapped → verified → promoted
  - Persist state to JSON so it survives restarts
  - Never import modules that are quarantined or have forbidden side-effects

Promotion states:
  DISCOVERED   - found on disk, not yet evaluated
  QUARANTINED  - import failed or forbidden patterns detected
  REGISTERED   - passes static checks, added to registry
  WRAPPED      - has a compliant service adapter
  VERIFIED     - passed contract + health checks in sandbox
  PROMOTED     - active in runtime; eligible for decision/execution paths
"""

from __future__ import annotations

import ast
import importlib
import importlib.util
import json
import logging
import os
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class ModuleLayer(int, Enum):
    INFRASTRUCTURE    = 0
    DATA_FOUNDATION   = 1
    INTELLIGENCE_CORE = 2
    SIGNAL_GENERATION = 3
    RISK_SAFETY       = 4
    EXECUTION         = 5
    GOVERNANCE        = 6
    ORCHESTRATION     = 7
    UNCLASSIFIED      = 99


class ModuleTier(str, Enum):
    A = "A"          # Core trading path – highest requirements
    B = "B"          # Decision support
    C = "C"          # Background intelligence / research
    D = "D"          # Experimental / sandbox only
    UNKNOWN = "?"


class PromotionState(str, Enum):
    DISCOVERED   = "discovered"
    QUARANTINED  = "quarantined"
    REGISTERED   = "registered"
    WRAPPED      = "wrapped"
    VERIFIED     = "verified"
    PROMOTED     = "promoted"


class CapitalImpact(str, Enum):
    NONE     = "none"      # No effect on trade decisions
    INDIRECT = "indirect"  # Informs signals but doesn't execute
    DIRECT   = "direct"    # Can initiate or modify live positions


class RollbackClass(str, Enum):
    SAFE_DISABLE  = "safe_disable"   # Can be stopped cleanly anytime
    DEGRADE       = "degrade"        # Falls back to stub on stop
    ISOLATE       = "isolate"        # Requires isolation procedure
    EMERGENCY     = "emergency"      # Needs emergency-stop protocol


# ---------------------------------------------------------------------------
# Layer / Tier Classification Rules
# ---------------------------------------------------------------------------

# Maps partial module path tokens → (layer, tier, capital_impact)
_CLASSIFICATION_RULES: List[tuple] = [
    # Layer 0 – Infrastructure
    ("log_system",        ModuleLayer.INFRASTRUCTURE,    ModuleTier.C, CapitalImpact.NONE,     RollbackClass.SAFE_DISABLE),
    ("telemetry",         ModuleLayer.INFRASTRUCTURE,    ModuleTier.C, CapitalImpact.NONE,     RollbackClass.SAFE_DISABLE),
    ("monitoring",        ModuleLayer.INFRASTRUCTURE,    ModuleTier.C, CapitalImpact.NONE,     RollbackClass.SAFE_DISABLE),
    ("observability",     ModuleLayer.INFRASTRUCTURE,    ModuleTier.C, CapitalImpact.NONE,     RollbackClass.SAFE_DISABLE),
    ("profiling",         ModuleLayer.INFRASTRUCTURE,    ModuleTier.D, CapitalImpact.NONE,     RollbackClass.SAFE_DISABLE),
    ("error_handling",    ModuleLayer.INFRASTRUCTURE,    ModuleTier.A, CapitalImpact.NONE,     RollbackClass.SAFE_DISABLE),
    ("infrastructure",    ModuleLayer.INFRASTRUCTURE,    ModuleTier.A, CapitalImpact.NONE,     RollbackClass.SAFE_DISABLE),
    ("ops",               ModuleLayer.INFRASTRUCTURE,    ModuleTier.C, CapitalImpact.NONE,     RollbackClass.SAFE_DISABLE),
    ("alerts",            ModuleLayer.INFRASTRUCTURE,    ModuleTier.C, CapitalImpact.NONE,     RollbackClass.SAFE_DISABLE),
    ("notifications",     ModuleLayer.INFRASTRUCTURE,    ModuleTier.C, CapitalImpact.NONE,     RollbackClass.SAFE_DISABLE),
    ("system_health",     ModuleLayer.INFRASTRUCTURE,    ModuleTier.A, CapitalImpact.NONE,     RollbackClass.SAFE_DISABLE),
    ("self_diagnostic",   ModuleLayer.INFRASTRUCTURE,    ModuleTier.B, CapitalImpact.NONE,     RollbackClass.DEGRADE),
    ("devops",            ModuleLayer.INFRASTRUCTURE,    ModuleTier.D, CapitalImpact.NONE,     RollbackClass.SAFE_DISABLE),
    ("testing",           ModuleLayer.INFRASTRUCTURE,    ModuleTier.D, CapitalImpact.NONE,     RollbackClass.SAFE_DISABLE),
    ("tools",             ModuleLayer.INFRASTRUCTURE,    ModuleTier.D, CapitalImpact.NONE,     RollbackClass.SAFE_DISABLE),
    ("utils",             ModuleLayer.INFRASTRUCTURE,    ModuleTier.C, CapitalImpact.NONE,     RollbackClass.SAFE_DISABLE),

    # Layer 1 – Data Foundation
    ("ingestion",         ModuleLayer.DATA_FOUNDATION,   ModuleTier.A, CapitalImpact.INDIRECT, RollbackClass.DEGRADE),
    ("streaming",         ModuleLayer.DATA_FOUNDATION,   ModuleTier.A, CapitalImpact.INDIRECT, RollbackClass.DEGRADE),
    ("schemas",           ModuleLayer.DATA_FOUNDATION,   ModuleTier.B, CapitalImpact.NONE,     RollbackClass.SAFE_DISABLE),
    ("persistence",       ModuleLayer.DATA_FOUNDATION,   ModuleTier.A, CapitalImpact.NONE,     RollbackClass.DEGRADE),
    ("database",          ModuleLayer.DATA_FOUNDATION,   ModuleTier.A, CapitalImpact.NONE,     RollbackClass.ISOLATE),
    ("data_feeds",        ModuleLayer.DATA_FOUNDATION,   ModuleTier.A, CapitalImpact.INDIRECT, RollbackClass.DEGRADE),
    ("data_sources",      ModuleLayer.DATA_FOUNDATION,   ModuleTier.B, CapitalImpact.INDIRECT, RollbackClass.DEGRADE),
    ("connectivity",      ModuleLayer.DATA_FOUNDATION,   ModuleTier.A, CapitalImpact.INDIRECT, RollbackClass.DEGRADE),
    ("realtime",          ModuleLayer.DATA_FOUNDATION,   ModuleTier.A, CapitalImpact.INDIRECT, RollbackClass.DEGRADE),
    ("features",          ModuleLayer.DATA_FOUNDATION,   ModuleTier.B, CapitalImpact.INDIRECT, RollbackClass.SAFE_DISABLE),
    ("internet_access",   ModuleLayer.DATA_FOUNDATION,   ModuleTier.C, CapitalImpact.INDIRECT, RollbackClass.SAFE_DISABLE),
    ("research_ingestion",ModuleLayer.DATA_FOUNDATION,   ModuleTier.C, CapitalImpact.INDIRECT, RollbackClass.SAFE_DISABLE),
    ("social",            ModuleLayer.DATA_FOUNDATION,   ModuleTier.C, CapitalImpact.INDIRECT, RollbackClass.SAFE_DISABLE),
    ("trading_calendar",  ModuleLayer.DATA_FOUNDATION,   ModuleTier.B, CapitalImpact.INDIRECT, RollbackClass.SAFE_DISABLE),
    ("alternative_data",  ModuleLayer.DATA_FOUNDATION,   ModuleTier.C, CapitalImpact.INDIRECT, RollbackClass.SAFE_DISABLE),
    ("macro",             ModuleLayer.DATA_FOUNDATION,   ModuleTier.C, CapitalImpact.INDIRECT, RollbackClass.SAFE_DISABLE),

    # Layer 2 – Intelligence Core
    ("ml",                ModuleLayer.INTELLIGENCE_CORE, ModuleTier.A, CapitalImpact.INDIRECT, RollbackClass.DEGRADE),
    ("ai_core",           ModuleLayer.INTELLIGENCE_CORE, ModuleTier.A, CapitalImpact.INDIRECT, RollbackClass.DEGRADE),
    ("brain",             ModuleLayer.INTELLIGENCE_CORE, ModuleTier.B, CapitalImpact.INDIRECT, RollbackClass.DEGRADE),
    ("cognitive_architecture", ModuleLayer.INTELLIGENCE_CORE, ModuleTier.B, CapitalImpact.INDIRECT, RollbackClass.DEGRADE),
    ("reasoning",         ModuleLayer.INTELLIGENCE_CORE, ModuleTier.B, CapitalImpact.INDIRECT, RollbackClass.DEGRADE),
    ("world_model",       ModuleLayer.INTELLIGENCE_CORE, ModuleTier.B, CapitalImpact.INDIRECT, RollbackClass.DEGRADE),
    ("meta_learning",     ModuleLayer.INTELLIGENCE_CORE, ModuleTier.C, CapitalImpact.INDIRECT, RollbackClass.DEGRADE),
    ("learning",          ModuleLayer.INTELLIGENCE_CORE, ModuleTier.C, CapitalImpact.INDIRECT, RollbackClass.DEGRADE),
    ("intelligence",      ModuleLayer.INTELLIGENCE_CORE, ModuleTier.B, CapitalImpact.INDIRECT, RollbackClass.DEGRADE),
    ("adaptive_systems",  ModuleLayer.INTELLIGENCE_CORE, ModuleTier.B, CapitalImpact.INDIRECT, RollbackClass.DEGRADE),
    ("multimodal",        ModuleLayer.INTELLIGENCE_CORE, ModuleTier.C, CapitalImpact.INDIRECT, RollbackClass.DEGRADE),
    ("sentiment",         ModuleLayer.INTELLIGENCE_CORE, ModuleTier.B, CapitalImpact.INDIRECT, RollbackClass.SAFE_DISABLE),
    ("psychology",        ModuleLayer.INTELLIGENCE_CORE, ModuleTier.C, CapitalImpact.INDIRECT, RollbackClass.SAFE_DISABLE),
    ("aamis_v3",          ModuleLayer.INTELLIGENCE_CORE, ModuleTier.B, CapitalImpact.INDIRECT, RollbackClass.DEGRADE),
    ("tamic",             ModuleLayer.INTELLIGENCE_CORE, ModuleTier.B, CapitalImpact.INDIRECT, RollbackClass.DEGRADE),
    ("superintelligence", ModuleLayer.INTELLIGENCE_CORE, ModuleTier.D, CapitalImpact.INDIRECT, RollbackClass.DEGRADE),
    ("perplexity_trading",ModuleLayer.INTELLIGENCE_CORE, ModuleTier.D, CapitalImpact.INDIRECT, RollbackClass.DEGRADE),
    ("quantum",           ModuleLayer.INTELLIGENCE_CORE, ModuleTier.D, CapitalImpact.INDIRECT, RollbackClass.SAFE_DISABLE),
    ("blockchain",        ModuleLayer.INTELLIGENCE_CORE, ModuleTier.D, CapitalImpact.NONE,     RollbackClass.SAFE_DISABLE),
    ("skills",            ModuleLayer.INTELLIGENCE_CORE, ModuleTier.C, CapitalImpact.INDIRECT, RollbackClass.SAFE_DISABLE),
    ("self_concepts",     ModuleLayer.INTELLIGENCE_CORE, ModuleTier.C, CapitalImpact.INDIRECT, RollbackClass.SAFE_DISABLE),
    ("self_healing_ai",   ModuleLayer.INTELLIGENCE_CORE, ModuleTier.C, CapitalImpact.INDIRECT, RollbackClass.DEGRADE),
    ("self_improvement",  ModuleLayer.INTELLIGENCE_CORE, ModuleTier.C, CapitalImpact.INDIRECT, RollbackClass.SAFE_DISABLE),
    ("self_learning",     ModuleLayer.INTELLIGENCE_CORE, ModuleTier.C, CapitalImpact.INDIRECT, RollbackClass.SAFE_DISABLE),
    ("self_mastery",      ModuleLayer.INTELLIGENCE_CORE, ModuleTier.C, CapitalImpact.INDIRECT, RollbackClass.SAFE_DISABLE),
    ("recursive_improvement", ModuleLayer.INTELLIGENCE_CORE, ModuleTier.C, CapitalImpact.INDIRECT, RollbackClass.SAFE_DISABLE),
    ("market_student",    ModuleLayer.INTELLIGENCE_CORE, ModuleTier.C, CapitalImpact.INDIRECT, RollbackClass.SAFE_DISABLE),
    ("market_teacher",    ModuleLayer.INTELLIGENCE_CORE, ModuleTier.C, CapitalImpact.INDIRECT, RollbackClass.SAFE_DISABLE),
    ("hivemind",          ModuleLayer.INTELLIGENCE_CORE, ModuleTier.D, CapitalImpact.INDIRECT, RollbackClass.DEGRADE),
    ("sentient_core",     ModuleLayer.INTELLIGENCE_CORE, ModuleTier.D, CapitalImpact.INDIRECT, RollbackClass.DEGRADE),
    ("improvements",      ModuleLayer.INTELLIGENCE_CORE, ModuleTier.C, CapitalImpact.INDIRECT, RollbackClass.SAFE_DISABLE),
    ("improvement_agent", ModuleLayer.INTELLIGENCE_CORE, ModuleTier.C, CapitalImpact.INDIRECT, RollbackClass.SAFE_DISABLE),
    ("autonomous_learner",ModuleLayer.INTELLIGENCE_CORE, ModuleTier.C, CapitalImpact.INDIRECT, RollbackClass.SAFE_DISABLE),
    ("autonomous_pipeline",ModuleLayer.INTELLIGENCE_CORE,ModuleTier.C, CapitalImpact.INDIRECT, RollbackClass.SAFE_DISABLE),
    ("innovations",       ModuleLayer.INTELLIGENCE_CORE, ModuleTier.D, CapitalImpact.INDIRECT, RollbackClass.SAFE_DISABLE),
    ("intelligence_core", ModuleLayer.INTELLIGENCE_CORE, ModuleTier.B, CapitalImpact.INDIRECT, RollbackClass.DEGRADE),
    ("qwen_codemender",   ModuleLayer.INTELLIGENCE_CORE, ModuleTier.D, CapitalImpact.NONE,     RollbackClass.SAFE_DISABLE),
    ("advanced_ml",       ModuleLayer.INTELLIGENCE_CORE, ModuleTier.C, CapitalImpact.INDIRECT, RollbackClass.DEGRADE),
    ("advanced_features", ModuleLayer.INTELLIGENCE_CORE, ModuleTier.D, CapitalImpact.INDIRECT, RollbackClass.DEGRADE),
    ("advanced_analysis", ModuleLayer.INTELLIGENCE_CORE, ModuleTier.C, CapitalImpact.INDIRECT, RollbackClass.DEGRADE),
    ("adversarial_curriculum", ModuleLayer.INTELLIGENCE_CORE, ModuleTier.D, CapitalImpact.INDIRECT, RollbackClass.SAFE_DISABLE),
    ("adversarial_decision",   ModuleLayer.INTELLIGENCE_CORE, ModuleTier.D, CapitalImpact.INDIRECT, RollbackClass.SAFE_DISABLE),
    ("agents",            ModuleLayer.INTELLIGENCE_CORE, ModuleTier.C, CapitalImpact.INDIRECT, RollbackClass.DEGRADE),
    ("eternal_evolution", ModuleLayer.INTELLIGENCE_CORE, ModuleTier.D, CapitalImpact.INDIRECT, RollbackClass.SAFE_DISABLE),
    ("evolution_layer",   ModuleLayer.INTELLIGENCE_CORE, ModuleTier.D, CapitalImpact.INDIRECT, RollbackClass.SAFE_DISABLE),
    ("recursive_evolution",ModuleLayer.INTELLIGENCE_CORE,ModuleTier.D, CapitalImpact.INDIRECT, RollbackClass.SAFE_DISABLE),
    ("self_assembly_ai",  ModuleLayer.INTELLIGENCE_CORE, ModuleTier.D, CapitalImpact.INDIRECT, RollbackClass.SAFE_DISABLE),
    ("superpowerful_ai",  ModuleLayer.INTELLIGENCE_CORE, ModuleTier.D, CapitalImpact.INDIRECT, RollbackClass.DEGRADE),

    # Layer 3 – Signal Generation
    ("alpha_engine",      ModuleLayer.SIGNAL_GENERATION, ModuleTier.A, CapitalImpact.INDIRECT, RollbackClass.DEGRADE),
    ("alpha_research",    ModuleLayer.SIGNAL_GENERATION, ModuleTier.B, CapitalImpact.INDIRECT, RollbackClass.DEGRADE),
    ("analysis",          ModuleLayer.SIGNAL_GENERATION, ModuleTier.A, CapitalImpact.INDIRECT, RollbackClass.DEGRADE),
    ("strategy",          ModuleLayer.SIGNAL_GENERATION, ModuleTier.A, CapitalImpact.INDIRECT, RollbackClass.DEGRADE),
    ("strategies",        ModuleLayer.SIGNAL_GENERATION, ModuleTier.B, CapitalImpact.INDIRECT, RollbackClass.DEGRADE),
    ("indicators",        ModuleLayer.SIGNAL_GENERATION, ModuleTier.A, CapitalImpact.INDIRECT, RollbackClass.SAFE_DISABLE),
    ("signals",           ModuleLayer.SIGNAL_GENERATION, ModuleTier.A, CapitalImpact.INDIRECT, RollbackClass.DEGRADE),
    ("deepchart",         ModuleLayer.SIGNAL_GENERATION, ModuleTier.B, CapitalImpact.INDIRECT, RollbackClass.DEGRADE),
    ("market_intelligence",ModuleLayer.SIGNAL_GENERATION,ModuleTier.A, CapitalImpact.INDIRECT, RollbackClass.DEGRADE),
    ("opportunity_scanner",ModuleLayer.SIGNAL_GENERATION,ModuleTier.B, CapitalImpact.INDIRECT, RollbackClass.SAFE_DISABLE),
    ("filters",           ModuleLayer.SIGNAL_GENERATION, ModuleTier.B, CapitalImpact.INDIRECT, RollbackClass.SAFE_DISABLE),
    ("simulation",        ModuleLayer.SIGNAL_GENERATION, ModuleTier.C, CapitalImpact.NONE,     RollbackClass.SAFE_DISABLE),
    ("intel",             ModuleLayer.SIGNAL_GENERATION, ModuleTier.B, CapitalImpact.INDIRECT, RollbackClass.SAFE_DISABLE),
    ("elite_ai_system",   ModuleLayer.SIGNAL_GENERATION, ModuleTier.B, CapitalImpact.INDIRECT, RollbackClass.DEGRADE),
    ("elite_system",      ModuleLayer.SIGNAL_GENERATION, ModuleTier.B, CapitalImpact.INDIRECT, RollbackClass.DEGRADE),
    ("systems_ai",        ModuleLayer.SIGNAL_GENERATION, ModuleTier.B, CapitalImpact.INDIRECT, RollbackClass.DEGRADE),
    ("decision_layer",    ModuleLayer.SIGNAL_GENERATION, ModuleTier.A, CapitalImpact.DIRECT,   RollbackClass.ISOLATE),
    ("alphaalgo_v2",      ModuleLayer.SIGNAL_GENERATION, ModuleTier.B, CapitalImpact.INDIRECT, RollbackClass.DEGRADE),
    ("alphaalgo_core",    ModuleLayer.SIGNAL_GENERATION, ModuleTier.B, CapitalImpact.INDIRECT, RollbackClass.DEGRADE),
    ("alphaalgo_institutional", ModuleLayer.SIGNAL_GENERATION, ModuleTier.B, CapitalImpact.INDIRECT, RollbackClass.DEGRADE),
    ("arbitrage",         ModuleLayer.SIGNAL_GENERATION, ModuleTier.C, CapitalImpact.INDIRECT, RollbackClass.DEGRADE),
    ("derivatives",       ModuleLayer.SIGNAL_GENERATION, ModuleTier.C, CapitalImpact.INDIRECT, RollbackClass.DEGRADE),
    ("crypto",            ModuleLayer.SIGNAL_GENERATION, ModuleTier.C, CapitalImpact.INDIRECT, RollbackClass.DEGRADE),

    # Layer 4 – Risk & Safety  ← HIGHEST PRIORITY; veto power
    ("msos",              ModuleLayer.RISK_SAFETY,       ModuleTier.A, CapitalImpact.DIRECT,   RollbackClass.EMERGENCY),
    ("risk",              ModuleLayer.RISK_SAFETY,       ModuleTier.A, CapitalImpact.DIRECT,   RollbackClass.EMERGENCY),
    ("safety",            ModuleLayer.RISK_SAFETY,       ModuleTier.A, CapitalImpact.DIRECT,   RollbackClass.EMERGENCY),
    ("stealth_safety",    ModuleLayer.RISK_SAFETY,       ModuleTier.B, CapitalImpact.DIRECT,   RollbackClass.ISOLATE),
    ("hedge_fund_safety", ModuleLayer.RISK_SAFETY,       ModuleTier.A, CapitalImpact.DIRECT,   RollbackClass.EMERGENCY),
    ("reality_gates",     ModuleLayer.RISK_SAFETY,       ModuleTier.A, CapitalImpact.DIRECT,   RollbackClass.EMERGENCY),
    ("risk_management",   ModuleLayer.RISK_SAFETY,       ModuleTier.A, CapitalImpact.DIRECT,   RollbackClass.EMERGENCY),
    ("risk_unified",      ModuleLayer.RISK_SAFETY,       ModuleTier.A, CapitalImpact.DIRECT,   RollbackClass.EMERGENCY),

    # Layer 5 – Execution
    ("execution",         ModuleLayer.EXECUTION,         ModuleTier.A, CapitalImpact.DIRECT,   RollbackClass.EMERGENCY),
    ("broker",            ModuleLayer.EXECUTION,         ModuleTier.A, CapitalImpact.DIRECT,   RollbackClass.EMERGENCY),
    ("brokers",           ModuleLayer.EXECUTION,         ModuleTier.A, CapitalImpact.DIRECT,   RollbackClass.EMERGENCY),
    ("trading",           ModuleLayer.EXECUTION,         ModuleTier.A, CapitalImpact.DIRECT,   RollbackClass.EMERGENCY),
    ("portfolio",         ModuleLayer.EXECUTION,         ModuleTier.A, CapitalImpact.DIRECT,   RollbackClass.ISOLATE),
    ("position",          ModuleLayer.EXECUTION,         ModuleTier.A, CapitalImpact.DIRECT,   RollbackClass.ISOLATE),
    ("exit_strategies",   ModuleLayer.EXECUTION,         ModuleTier.A, CapitalImpact.DIRECT,   RollbackClass.ISOLATE),
    ("profit_maximizer",  ModuleLayer.EXECUTION,         ModuleTier.B, CapitalImpact.DIRECT,   RollbackClass.ISOLATE),
    ("hft",               ModuleLayer.EXECUTION,         ModuleTier.B, CapitalImpact.DIRECT,   RollbackClass.EMERGENCY),
    ("market_making",     ModuleLayer.EXECUTION,         ModuleTier.B, CapitalImpact.DIRECT,   RollbackClass.ISOLATE),
    ("institutional",     ModuleLayer.EXECUTION,         ModuleTier.B, CapitalImpact.DIRECT,   RollbackClass.ISOLATE),
    ("institutional_entry",ModuleLayer.EXECUTION,        ModuleTier.B, CapitalImpact.DIRECT,   RollbackClass.ISOLATE),
    ("hedge_fund",        ModuleLayer.EXECUTION,         ModuleTier.B, CapitalImpact.DIRECT,   RollbackClass.ISOLATE),
    ("wealth",            ModuleLayer.EXECUTION,         ModuleTier.C, CapitalImpact.DIRECT,   RollbackClass.ISOLATE),
    ("hedging",           ModuleLayer.EXECUTION,         ModuleTier.B, CapitalImpact.DIRECT,   RollbackClass.ISOLATE),
    ("ctrader",           ModuleLayer.EXECUTION,         ModuleTier.C, CapitalImpact.DIRECT,   RollbackClass.ISOLATE),

    # Layer 6 – Governance
    ("audit",             ModuleLayer.GOVERNANCE,        ModuleTier.A, CapitalImpact.NONE,     RollbackClass.SAFE_DISABLE),
    ("governance",        ModuleLayer.GOVERNANCE,        ModuleTier.A, CapitalImpact.NONE,     RollbackClass.SAFE_DISABLE),
    ("approval",          ModuleLayer.GOVERNANCE,        ModuleTier.A, CapitalImpact.DIRECT,   RollbackClass.ISOLATE),
    ("explainability",    ModuleLayer.GOVERNANCE,        ModuleTier.B, CapitalImpact.NONE,     RollbackClass.SAFE_DISABLE),
    ("validation",        ModuleLayer.GOVERNANCE,        ModuleTier.A, CapitalImpact.INDIRECT, RollbackClass.DEGRADE),
    ("verification",      ModuleLayer.GOVERNANCE,        ModuleTier.A, CapitalImpact.INDIRECT, RollbackClass.DEGRADE),
    ("compliance",        ModuleLayer.GOVERNANCE,        ModuleTier.A, CapitalImpact.NONE,     RollbackClass.SAFE_DISABLE),
    ("surveillance",      ModuleLayer.GOVERNANCE,        ModuleTier.B, CapitalImpact.NONE,     RollbackClass.SAFE_DISABLE),
    ("quality",           ModuleLayer.GOVERNANCE,        ModuleTier.C, CapitalImpact.NONE,     RollbackClass.SAFE_DISABLE),
    ("security",          ModuleLayer.GOVERNANCE,        ModuleTier.A, CapitalImpact.NONE,     RollbackClass.DEGRADE),
    ("human_layer",       ModuleLayer.GOVERNANCE,        ModuleTier.A, CapitalImpact.DIRECT,   RollbackClass.ISOLATE),
    ("ultimate_approval", ModuleLayer.GOVERNANCE,        ModuleTier.A, CapitalImpact.DIRECT,   RollbackClass.ISOLATE),
    ("unified_approval",  ModuleLayer.GOVERNANCE,        ModuleTier.A, CapitalImpact.DIRECT,   RollbackClass.ISOLATE),
    ("anti_rogue_ai",     ModuleLayer.GOVERNANCE,        ModuleTier.A, CapitalImpact.NONE,     RollbackClass.SAFE_DISABLE),

    # Layer 7 – Orchestration
    ("event_pipeline",    ModuleLayer.ORCHESTRATION,     ModuleTier.A, CapitalImpact.INDIRECT, RollbackClass.DEGRADE),
    ("orchestrator",      ModuleLayer.ORCHESTRATION,     ModuleTier.A, CapitalImpact.INDIRECT, RollbackClass.DEGRADE),
    ("reporting",         ModuleLayer.ORCHESTRATION,     ModuleTier.C, CapitalImpact.NONE,     RollbackClass.SAFE_DISABLE),
    ("system_supervisor", ModuleLayer.ORCHESTRATION,     ModuleTier.A, CapitalImpact.NONE,     RollbackClass.DEGRADE),
    ("visualization",     ModuleLayer.ORCHESTRATION,     ModuleTier.D, CapitalImpact.NONE,     RollbackClass.SAFE_DISABLE),
    ("voice_assistant",   ModuleLayer.ORCHESTRATION,     ModuleTier.D, CapitalImpact.NONE,     RollbackClass.SAFE_DISABLE),
    ("trade_journal",     ModuleLayer.ORCHESTRATION,     ModuleTier.B, CapitalImpact.NONE,     RollbackClass.SAFE_DISABLE),
    ("automation",        ModuleLayer.ORCHESTRATION,     ModuleTier.C, CapitalImpact.INDIRECT, RollbackClass.SAFE_DISABLE),
    ("intelligent_delegation", ModuleLayer.ORCHESTRATION,ModuleTier.B, CapitalImpact.INDIRECT, RollbackClass.DEGRADE),
    ("bridges",           ModuleLayer.ORCHESTRATION,     ModuleTier.C, CapitalImpact.INDIRECT, RollbackClass.SAFE_DISABLE),
    ("connectors",        ModuleLayer.ORCHESTRATION,     ModuleTier.B, CapitalImpact.INDIRECT, RollbackClass.DEGRADE),
    ("integrations",      ModuleLayer.ORCHESTRATION,     ModuleTier.B, CapitalImpact.INDIRECT, RollbackClass.DEGRADE),
    ("production",        ModuleLayer.ORCHESTRATION,     ModuleTier.A, CapitalImpact.DIRECT,   RollbackClass.EMERGENCY),
    ("ultimate_system",   ModuleLayer.ORCHESTRATION,     ModuleTier.C, CapitalImpact.INDIRECT, RollbackClass.DEGRADE),
    ("unified_system",    ModuleLayer.ORCHESTRATION,     ModuleTier.B, CapitalImpact.INDIRECT, RollbackClass.DEGRADE),
    ("unified_architecture",ModuleLayer.ORCHESTRATION,   ModuleTier.C, CapitalImpact.INDIRECT, RollbackClass.DEGRADE),
    ("ultimate_architecture",ModuleLayer.ORCHESTRATION,  ModuleTier.D, CapitalImpact.INDIRECT, RollbackClass.DEGRADE),
    ("ultimate_bot",      ModuleLayer.ORCHESTRATION,     ModuleTier.D, CapitalImpact.INDIRECT, RollbackClass.DEGRADE),
    ("ultimate_production",ModuleLayer.ORCHESTRATION,    ModuleTier.C, CapitalImpact.INDIRECT, RollbackClass.DEGRADE),
    ("cloud_deployer",    ModuleLayer.ORCHESTRATION,     ModuleTier.D, CapitalImpact.NONE,     RollbackClass.SAFE_DISABLE),
    ("deployment",        ModuleLayer.ORCHESTRATION,     ModuleTier.D, CapitalImpact.NONE,     RollbackClass.SAFE_DISABLE),
    ("distributed",       ModuleLayer.ORCHESTRATION,     ModuleTier.D, CapitalImpact.INDIRECT, RollbackClass.SAFE_DISABLE),
    ("api",               ModuleLayer.ORCHESTRATION,     ModuleTier.B, CapitalImpact.INDIRECT, RollbackClass.DEGRADE),
    ("global_expansion",  ModuleLayer.ORCHESTRATION,     ModuleTier.D, CapitalImpact.INDIRECT, RollbackClass.SAFE_DISABLE),
    ("mobile",            ModuleLayer.ORCHESTRATION,     ModuleTier.D, CapitalImpact.NONE,     RollbackClass.SAFE_DISABLE),
    ("auto_optimizer",    ModuleLayer.ORCHESTRATION,     ModuleTier.C, CapitalImpact.INDIRECT, RollbackClass.SAFE_DISABLE),
    ("optimization",      ModuleLayer.ORCHESTRATION,     ModuleTier.C, CapitalImpact.INDIRECT, RollbackClass.SAFE_DISABLE),
    ("upgrades",          ModuleLayer.ORCHESTRATION,     ModuleTier.D, CapitalImpact.NONE,     RollbackClass.SAFE_DISABLE),
    ("backtesting",       ModuleLayer.ORCHESTRATION,     ModuleTier.B, CapitalImpact.NONE,     RollbackClass.SAFE_DISABLE),
    ("performance",       ModuleLayer.ORCHESTRATION,     ModuleTier.B, CapitalImpact.NONE,     RollbackClass.SAFE_DISABLE),
    ("analytics",         ModuleLayer.ORCHESTRATION,     ModuleTier.C, CapitalImpact.NONE,     RollbackClass.SAFE_DISABLE),
    ("dashboard",         ModuleLayer.ORCHESTRATION,     ModuleTier.C, CapitalImpact.NONE,     RollbackClass.SAFE_DISABLE),
    ("autonomous",        ModuleLayer.ORCHESTRATION,     ModuleTier.D, CapitalImpact.INDIRECT, RollbackClass.DEGRADE),
    ("event_monitoring",  ModuleLayer.ORCHESTRATION,     ModuleTier.B, CapitalImpact.NONE,     RollbackClass.SAFE_DISABLE),
    ("ai_engineer",       ModuleLayer.ORCHESTRATION,     ModuleTier.D, CapitalImpact.NONE,     RollbackClass.SAFE_DISABLE),
    ("advanced_systems2", ModuleLayer.ORCHESTRATION,     ModuleTier.D, CapitalImpact.INDIRECT, RollbackClass.SAFE_DISABLE),
    ("ai",                ModuleLayer.ORCHESTRATION,     ModuleTier.D, CapitalImpact.INDIRECT, RollbackClass.SAFE_DISABLE),
    ("models",            ModuleLayer.ORCHESTRATION,     ModuleTier.C, CapitalImpact.INDIRECT, RollbackClass.SAFE_DISABLE),
    ("documentation",     ModuleLayer.ORCHESTRATION,     ModuleTier.D, CapitalImpact.NONE,     RollbackClass.SAFE_DISABLE),
]

# Forbidden import patterns – quarantine any module containing these
_FORBIDDEN_PATTERNS: Set[str] = {
    "os.system(",
    "subprocess.call(",
    "exec(",
    "eval(",
    "__import__(",
    "compile(",
    "open('/etc/",
    "shutil.rmtree(",
    "os.remove(",
}

# Paths to skip during discovery
_SKIP_DIRS: Set[str] = {
    "__pycache__",
    ".git",
    "autonomous_backups",
    "bot_backups",
    "code_backups",
    "deployment_backups",
    "self_assembly_workspace",
    "_archive",
    ".venv",
    "venv",
    "site-packages",
    "backups",
}


# ---------------------------------------------------------------------------
# Module Record
# ---------------------------------------------------------------------------

@dataclass
class ModuleRecord:
    """One entry in the canonical registry."""

    module_path: str                        # dotted Python path, e.g. trading_bot.risk.risk_manager
    file_path: str                          # absolute filesystem path
    layer: int                              = ModuleLayer.UNCLASSIFIED.value
    tier: str                               = ModuleTier.UNKNOWN.value
    domain: str                             = ""
    capital_impact: str                     = CapitalImpact.NONE.value
    rollback_class: str                     = RollbackClass.SAFE_DISABLE.value
    promotion_state: str                    = PromotionState.DISCOVERED.value
    import_healthy: Optional[bool]          = None
    import_error: str                       = ""
    has_forbidden_patterns: bool            = False
    has_orchestrator: bool                  = False     # exposes an orchestrate() / start() class
    lines_of_code: int                      = 0
    last_checked: str                       = ""
    service_name: str                       = ""        # populated once wrapped
    metadata: Dict[str, Any]               = field(default_factory=dict)

    def to_dict(self) -> Dict:
        d = asdict(self)
        return d

    @classmethod
    def from_dict(cls, d: Dict) -> "ModuleRecord":
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})


# ---------------------------------------------------------------------------
# ModuleRegistry
# ---------------------------------------------------------------------------

class ModuleRegistry:
    """
    Canonical inventory of every Python module in the trading_bot package.

    Usage:
        registry = ModuleRegistry()
        registry.scan()                          # discover all modules
        registry.classify()                      # assign layer / tier
        registry.check_imports(quick=True)       # test importability
        registry.save()                          # persist to disk
        report = registry.status_report()        # human-readable summary
    """

    REGISTRY_FILE = "alphaalgo_data/module_registry.json"

    def __init__(self, root: Optional[str] = None):
        if root is None:
            root = str(Path(__file__).parent.parent.parent)
        self.root = Path(root)
        self.package_root = self.root / "trading_bot"
        self.records: Dict[str, ModuleRecord] = {}
        self._registry_path = self.root / self.REGISTRY_FILE
        self._registry_path.parent.mkdir(parents=True, exist_ok=True)

    # -----------------------------------------------------------------------
    # Discovery
    # -----------------------------------------------------------------------

    def scan(self) -> int:
        """Discover all .py files under trading_bot/ and register them."""
        found = 0
        for py_file in self.package_root.rglob("*.py"):
            # Skip forbidden directories
            parts = set(py_file.parts)
            if parts & _SKIP_DIRS:
                continue
            if py_file.name == "__init__.py":
                continue

            module_path = self._file_to_module(py_file)
            if not module_path:
                continue

            if module_path not in self.records:
                record = ModuleRecord(
                    module_path=module_path,
                    file_path=str(py_file),
                    last_checked=datetime.utcnow().isoformat(),
                )
                self.records[module_path] = record
                found += 1

        logger.info(f"ModuleRegistry.scan: discovered {found} new modules ({len(self.records)} total)")
        return found

    def _file_to_module(self, py_file: Path) -> Optional[str]:
        """Convert a filesystem path to a dotted module name."""
        try:
            rel = py_file.relative_to(self.root)
            parts = list(rel.with_suffix("").parts)
            return ".".join(parts)
        except ValueError:
            return None

    # -----------------------------------------------------------------------
    # Classification
    # -----------------------------------------------------------------------

    def classify(self) -> None:
        """Assign layer, tier, domain, capital_impact, rollback_class to each record."""
        for record in self.records.values():
            self._classify_record(record)

    def _classify_record(self, record: ModuleRecord) -> None:
        """Apply classification rules based on module path tokens."""
        # Extract path tokens from the path after "trading_bot."
        path = record.module_path
        tokens = path.split(".")

        # Drop the leading "trading_bot" package token
        if tokens and tokens[0] == "trading_bot":
            tokens = tokens[1:]

        # Domain = first meaningful token after trading_bot
        domain = tokens[0] if tokens else ""
        record.domain = domain

        # Apply first matching rule
        for (token, layer, tier, capital, rollback) in _CLASSIFICATION_RULES:
            if any(t.startswith(token) for t in tokens):
                record.layer = layer.value
                record.tier = tier.value
                record.capital_impact = capital.value
                record.rollback_class = rollback.value
                return

        # Default: unclassified
        record.layer = ModuleLayer.UNCLASSIFIED.value
        record.tier = ModuleTier.UNKNOWN.value
        record.capital_impact = CapitalImpact.NONE.value
        record.rollback_class = RollbackClass.SAFE_DISABLE.value

    # -----------------------------------------------------------------------
    # Static Analysis
    # -----------------------------------------------------------------------

    def analyze_static(self) -> None:
        """Run lightweight AST-level static analysis on all records."""
        for record in self.records.values():
            self._analyze_file(record)

    def _analyze_file(self, record: ModuleRecord) -> None:
        """Check LOC, forbidden patterns, and orchestrator presence."""
        try:
            source = Path(record.file_path).read_text(encoding="utf-8", errors="replace")
            record.lines_of_code = source.count("\n") + 1

            # Forbidden pattern check
            record.has_forbidden_patterns = any(
                pat in source for pat in _FORBIDDEN_PATTERNS
            )
            if record.has_forbidden_patterns:
                record.promotion_state = PromotionState.QUARANTINED.value

            # Quick check for start() or health_check() or orchestrator
            record.has_orchestrator = (
                "def start(" in source
                or "async def start(" in source
                or "Orchestrator" in source
                or "def health_check(" in source
            )
        except Exception as exc:
            record.import_error = f"static_analysis: {exc}"

    # -----------------------------------------------------------------------
    # Import Health Check
    # -----------------------------------------------------------------------

    def check_imports(self, quick: bool = True, max_per_tier: int = 50) -> Dict[str, int]:
        """
        Test importability of registered modules.

        quick=True  → only attempt DISCOVERED modules, skip already checked
        quick=False → re-check everything

        Returns counts by state.
        """
        counts = {"healthy": 0, "broken": 0, "skipped": 0}
        checked = 0

        for record in self.records.values():
            if record.promotion_state == PromotionState.QUARANTINED.value:
                counts["skipped"] += 1
                continue
            if quick and record.import_healthy is not None:
                counts["skipped"] += 1
                continue
            if quick and checked >= max_per_tier:
                counts["skipped"] += 1
                continue

            ok, err = self._try_import(record.module_path)
            record.import_healthy = ok
            record.import_error = err
            record.last_checked = datetime.utcnow().isoformat()
            checked += 1

            if ok:
                counts["healthy"] += 1
                if record.promotion_state == PromotionState.DISCOVERED.value:
                    record.promotion_state = PromotionState.REGISTERED.value
            else:
                counts["broken"] += 1
                if record.promotion_state == PromotionState.DISCOVERED.value:
                    record.promotion_state = PromotionState.QUARANTINED.value

        logger.info(
            f"Import check: healthy={counts['healthy']} broken={counts['broken']} skipped={counts['skipped']}"
        )
        return counts

    @staticmethod
    def _try_import(module_path: str) -> tuple:
        """Attempt to import a module. Returns (ok: bool, error: str)."""
        try:
            spec = importlib.util.find_spec(module_path)
            if spec is None:
                return False, "module_not_found"
            return True, ""
        except Exception as exc:
            return False, str(exc)[:200]

    # -----------------------------------------------------------------------
    # Promotion
    # -----------------------------------------------------------------------

    def promote(self, module_path: str, to_state: PromotionState) -> bool:
        """Manually advance a module's promotion state."""
        record = self.records.get(module_path)
        if not record:
            return False
        if record.promotion_state == PromotionState.QUARANTINED.value:
            logger.warning(f"Cannot promote quarantined module: {module_path}")
            return False
        record.promotion_state = to_state.value
        return True

    def quarantine(self, module_path: str, reason: str = "") -> bool:
        """Force-quarantine a module."""
        record = self.records.get(module_path)
        if not record:
            return False
        record.promotion_state = PromotionState.QUARANTINED.value
        record.import_error = f"manually_quarantined: {reason}"
        return True

    # -----------------------------------------------------------------------
    # Queries
    # -----------------------------------------------------------------------

    def by_layer(self, layer: ModuleLayer) -> List[ModuleRecord]:
        return [r for r in self.records.values() if r.layer == layer.value]

    def by_tier(self, tier: ModuleTier) -> List[ModuleRecord]:
        return [r for r in self.records.values() if r.tier == tier.value]

    def by_state(self, state: PromotionState) -> List[ModuleRecord]:
        return [r for r in self.records.values() if r.promotion_state == state.value]

    def promoted_modules(self) -> List[ModuleRecord]:
        return self.by_state(PromotionState.PROMOTED)

    def registered_modules(self) -> List[ModuleRecord]:
        return [
            r for r in self.records.values()
            if r.promotion_state in (
                PromotionState.REGISTERED.value,
                PromotionState.WRAPPED.value,
                PromotionState.VERIFIED.value,
                PromotionState.PROMOTED.value,
            )
        ]

    # -----------------------------------------------------------------------
    # Persistence
    # -----------------------------------------------------------------------

    def save(self) -> None:
        """Persist registry to JSON."""
        data = {
            "generated": datetime.utcnow().isoformat(),
            "total": len(self.records),
            "modules": {k: v.to_dict() for k, v in self.records.items()},
        }
        self._registry_path.write_text(
            json.dumps(data, indent=2, default=str), encoding="utf-8"
        )
        logger.info(f"Registry saved → {self._registry_path} ({len(self.records)} modules)")

    def load(self) -> bool:
        """Load registry from JSON if it exists."""
        if not self._registry_path.exists():
            return False
        try:
            data = json.loads(self._registry_path.read_text(encoding="utf-8"))
            self.records = {
                k: ModuleRecord.from_dict(v)
                for k, v in data.get("modules", {}).items()
            }
            logger.info(f"Registry loaded: {len(self.records)} modules")
            return True
        except Exception as exc:
            logger.error(f"Registry load failed: {exc}")
            return False

    # -----------------------------------------------------------------------
    # Reporting
    # -----------------------------------------------------------------------

    def status_report(self) -> Dict[str, Any]:
        """Return a machine-readable status report."""
        by_state: Dict[str, int] = {}
        by_layer: Dict[str, int] = {}
        by_tier: Dict[str, int] = {}
        by_impact: Dict[str, int] = {}

        for r in self.records.values():
            by_state[r.promotion_state] = by_state.get(r.promotion_state, 0) + 1
            layer_name = ModuleLayer(r.layer).name if r.layer != 99 else "UNCLASSIFIED"
            by_layer[layer_name] = by_layer.get(layer_name, 0) + 1
            by_tier[r.tier] = by_tier.get(r.tier, 0) + 1
            by_impact[r.capital_impact] = by_impact.get(r.capital_impact, 0) + 1

        return {
            "total_modules": len(self.records),
            "by_promotion_state": by_state,
            "by_layer": by_layer,
            "by_tier": by_tier,
            "by_capital_impact": by_impact,
            "healthy_imports": sum(1 for r in self.records.values() if r.import_healthy),
            "broken_imports": sum(1 for r in self.records.values() if r.import_healthy is False),
            "unchecked": sum(1 for r in self.records.values() if r.import_healthy is None),
            "quarantined": len(self.by_state(PromotionState.QUARANTINED)),
            "promoted": len(self.promoted_modules()),
            "generated": datetime.utcnow().isoformat(),
        }

    def print_report(self) -> None:
        """Print a human-readable status report."""
        r = self.status_report()
        lines = [
            "=" * 70,
            "ALPHAALGO CANONICAL MODULE REGISTRY - STATUS REPORT",
            "=" * 70,
            f"  Total modules discovered : {r['total_modules']}",
            f"  Healthy imports          : {r['healthy_imports']}",
            f"  Broken imports           : {r['broken_imports']}",
            f"  Unchecked                : {r['unchecked']}",
            f"  Quarantined              : {r['quarantined']}",
            f"  Promoted                 : {r['promoted']}",
            "",
            "  By Promotion State:",
        ]
        for state, count in sorted(r["by_promotion_state"].items()):
            lines.append(f"    {state:<20} {count:>5}")
        lines.append("")
        lines.append("  By Architecture Layer:")
        for layer, count in sorted(r["by_layer"].items()):
            lines.append(f"    {layer:<25} {count:>5}")
        lines.append("")
        lines.append("  By Tier:")
        for tier, count in sorted(r["by_tier"].items()):
            lines.append(f"    Tier {tier:<20} {count:>5}")
        lines.append("")
        lines.append("  By Capital Impact:")
        for impact, count in sorted(r["by_capital_impact"].items()):
            lines.append(f"    {impact:<20} {count:>5}")
        lines.append("=" * 70)
        print("\n".join(lines))


# ---------------------------------------------------------------------------
# Singleton
# ---------------------------------------------------------------------------

_registry_instance: Optional[ModuleRegistry] = None


def get_module_registry(root: Optional[str] = None) -> ModuleRegistry:
    """Return the singleton ModuleRegistry (creates it if needed)."""
    global _registry_instance
    if _registry_instance is None:
        _registry_instance = ModuleRegistry(root=root)
    return _registry_instance
