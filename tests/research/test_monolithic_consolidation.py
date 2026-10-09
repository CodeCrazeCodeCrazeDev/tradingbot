"""Monolithic research consolidation contract tests.

The single research monolith lives under ``trading_bot.research``. Legacy
top-level packages and scattered modules (``trading_bot.alpha_research``,
``trading_bot.research_ingestion``, ``trading_bot.core.research_mvp_pipeline``,
``trading_bot.core.aletheia_browser_research``,
``trading_bot.intel.strategy_researcher``,
``trading_bot.services.alpha_research_service``) are compatibility shims that
forward to the canonical package and emit DeprecationWarning.
"""

import importlib
import sys
import warnings

import pytest

pytestmark = pytest.mark.filterwarnings("ignore::DeprecationWarning")


# ---------------------------------------------------------------------------
# Physical location: canonical modules live under trading_bot/research/
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "canonical",
    [
        "trading_bot.research.alpha_research",
        "trading_bot.research.ingestion",
        "trading_bot.research.mvp_pipeline",
        "trading_bot.research.aletheia_browser_research",
        "trading_bot.research.strategy_researcher",
        "trading_bot.research.alpha_research_service",
        "trading_bot.research.orchestration.kernel",
    ],
)
def test_canonical_modules_import(canonical):
    module = importlib.import_module(canonical)
    assert module is not None


# ---------------------------------------------------------------------------
# Legacy shims forward to canonical implementations
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "legacy,canonical",
    [
        ("trading_bot.alpha_research", "trading_bot.research.alpha_research"),
        ("trading_bot.research_ingestion", "trading_bot.research.ingestion"),
        (
            "trading_bot.core.research_mvp_pipeline",
            "trading_bot.research.mvp_pipeline",
        ),
        (
            "trading_bot.core.aletheia_browser_research",
            "trading_bot.research.aletheia_browser_research",
        ),
        (
            "trading_bot.intel.strategy_researcher",
            "trading_bot.research.strategy_researcher",
        ),
        (
            "trading_bot.services.alpha_research_service",
            "trading_bot.research.alpha_research_service",
        ),
    ],
)
def test_legacy_shim_forwards_to_canonical(legacy, canonical):
    legacy_mod = importlib.import_module(legacy)
    canonical_mod = importlib.import_module(canonical)
    shared = [a for a in dir(canonical_mod) if not a.startswith("_")]
    assert shared, f"{canonical} exposes no public attributes"
    for attr in shared[:5]:
        assert getattr(legacy_mod, attr) is getattr(canonical_mod, attr), (
            f"{legacy}.{attr} must resolve to the canonical object"
        )


@pytest.mark.parametrize(
    "legacy",
    [
        "trading_bot.alpha_research",
        "trading_bot.research_ingestion",
        "trading_bot.core.research_mvp_pipeline",
        "trading_bot.core.aletheia_browser_research",
        "trading_bot.intel.strategy_researcher",
        "trading_bot.services.alpha_research_service",
    ],
)
def test_legacy_shim_warns_deprecation(legacy):
    sys.modules.pop(legacy, None)
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        importlib.import_module(legacy)
    assert any(issubclass(w.category, DeprecationWarning) for w in caught), (
        f"{legacy} must emit a DeprecationWarning on import"
    )


# ---------------------------------------------------------------------------
# Single authoritative orchestrator
# ---------------------------------------------------------------------------


def test_sovereign_orchestrator_exported_from_research_root():
    import trading_bot.research as research

    assert research.SovereignResearchOrchestrator.__module__ == (
        "trading_bot.research.orchestration.kernel"
    )


@pytest.mark.parametrize(
    "module_path,cls_name",
    [
        ("trading_bot.research.orchestration.research_os", "ResearchWorkspace"),
        (
            "trading_bot.research.orchestration.research_os_v2",
            "ResearchWorkspaceV2",
        ),
        ("trading_bot.research.orchestration.quant_pipeline", "ResearchLab"),
        (
            "trading_bot.research.orchestration.research_organization",
            "AlphaAlgoResearchOrganization",
        ),
        (
            "trading_bot.research.orchestration.institution",
            "QuantitativeResearchInstitution",
        ),
    ],
)
def test_legacy_orchestrators_warn_on_instantiation(module_path, cls_name):
    cls = getattr(importlib.import_module(module_path), cls_name)
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        try:
            cls()
        except TypeError:
            pytest.skip(f"{cls_name} requires constructor arguments")
    assert any(issubclass(w.category, DeprecationWarning) for w in caught), (
        f"{cls_name}.__init__ must emit a DeprecationWarning"
    )


# ---------------------------------------------------------------------------
# Manifest contract
# ---------------------------------------------------------------------------


def test_manifest_records_consolidated_research_context():
    import json
    import pathlib

    manifest = json.loads(
        pathlib.Path("ARCHITECTURE_COMPONENT_MANIFEST.json").read_text()
    )
    research_ctx = manifest["bounded_contexts"]["research"]
    assert research_ctx["status"] == "consolidated"
    assert manifest["authorities"]["research_orchestration"]["owner"] == (
        "SovereignResearchOrchestrator"
    )
