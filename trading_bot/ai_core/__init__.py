"""AI Core package - minimal orchestration surface."""

try:
    from .orchestrator import AIOrchestrator  # noqa: F401
except ImportError:
    pass
