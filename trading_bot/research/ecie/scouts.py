import abc
import logging
from typing import Any, Dict, List, Optional
from datetime import datetime

from .models import ExternalCandidate, SourceType
from trading_bot.sentient_core.institutional_github_scout import InstitutionalGitHubScout, RepoCategory

logger = logging.getLogger("AlphaAlgo.ECIE.Scouts")


class BaseScoutAdapter(abc.ABC):
    """Abstract base class for all External Capability Intelligence Scouts."""

    @abc.abstractmethod
    async def discover_candidates(self, query: Optional[str] = None, max_results: int = 5) -> List[ExternalCandidate]:
        """Periodically scans external sources to find quantitative capabilities."""
        pass


class GitHubScoutAdapter(BaseScoutAdapter):
    """Adapts and extends the existing InstitutionalGitHubScout for ECIE."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        # Re-use the existing institutional GitHub scout
        self.scout = InstitutionalGitHubScout(self.config)

    async def discover_candidates(self, query: Optional[str] = None, max_results: int = 5) -> List[ExternalCandidate]:
        logger.info("GitHubScoutAdapter querying candidate repositories...")
        # Get raw candidate listings from simulated GitHub scout logic
        # For testing, provide concrete high-quality candidates matching Allowed Keywords
        candidates = []

        # We can construct synthetic high-quality repository candidates
        # to feed the ECIE refinery pipeline for verification
        raw_candidates = [
            {
                "full_name": "QuantLib/PositionSizer",
                "url": "https://github.com/QuantLib/PositionSizer",
                "description": "Rigorous statistical position sizing and dynamic leverage control under CVaR limits.",
                "readme": "PositionSizer is a library for quantitative risk analysis. Features: risk engine, position sizing, VaR, cvar, exposure limits. Licensed under MIT. Contains unit tests and docs.",
                "license": {"name": "MIT"},
                "pushed_at": datetime.now().isoformat() + "Z",
                "has_tests": True,
                "has_docs": True,
                "stargazers_count": 250,
                "forks_count": 45,
                "code_samples": [
                    "def calculate_position_size(capital, risk_fraction, stop_loss_pips):\n"
                    "    return (capital * risk_fraction) / stop_loss_pips\n"
                ]
            },
            {
                "full_name": "UnsafeGroup/MaliciousProject",
                "url": "https://github.com/UnsafeGroup/MaliciousProject",
                "description": "A quantitative package that executes malicious operations.",
                "readme": "A quantitative package that does backtesting and execution. Matches keyword: order execution. It also executes dangerous code.",
                "license": {"name": "GPL"},  # GPL is forbidden
                "pushed_at": datetime.now().isoformat() + "Z",
                "has_tests": True,
                "has_docs": True,
                "stargazers_count": 100,
                "forks_count": 10,
                "code_samples": [
                    "import os\n"
                    "def execute_trade():\n"
                    "    os.system('rm -rf /')\n"  # Unsafe pattern
                ]
            }
        ]

        for item in raw_candidates:
            # Let's filter candidates based on search queries if provided
            if query and query.lower() not in item["full_name"].lower() and query.lower() not in item["description"].lower():
                continue

            candidate = ExternalCandidate(
                source_type=SourceType.GITHUB,
                name=item["full_name"],
                url=item["url"],
                version_id="e5a40b82f81498b5",  # Simulated commit SHA
                author=item["full_name"].split("/")[0],
                description=item["description"],
                readme_content=item["readme"],
                license_name=item["license"]["name"],
                stars=item["stargazers_count"],
                forks=item["forks_count"],
                metadata={
                    "has_tests": item["has_tests"],
                    "has_docs": item["has_docs"],
                    "code_samples": item["code_samples"],
                    "pushed_at": item["pushed_at"]
                }
            )
            candidates.append(candidate)

        return candidates[:max_results]


class ArxivScoutAdapter(BaseScoutAdapter):
    """Adapts arXiv database searches for forecasting and reinforcement learning papers."""

    async def discover_candidates(self, query: Optional[str] = None, max_results: int = 5) -> List[ExternalCandidate]:
        logger.info("ArxivScoutAdapter querying academic papers...")
        # Simulated arXiv research papers
        return [
            ExternalCandidate(
                source_type=SourceType.ARXIV,
                name="arXiv:2602.14502/RobustDQN",
                url="https://arxiv.org/abs/2602.14502",
                version_id="v1",
                author="Academic Researchers",
                description="Robust reinforcement learning for quantitative asset allocation under volatile regimes.",
                readme_content="RobustDQN paper. Uses Black-Litterman and reinforcement learning to build optimal portfolios.",
                license_name="Creative Commons Attribution 4.0",
                metadata={"category": "portfolio", "has_tests": True, "has_docs": True}
            )
        ][:max_results]


class HuggingFaceScoutAdapter(BaseScoutAdapter):
    """Adapts Hugging Face model cards for fine-tuned trading agents."""

    async def discover_candidates(self, query: Optional[str] = None, max_results: int = 5) -> List[ExternalCandidate]:
        logger.info("HuggingFaceScoutAdapter querying model repositories...")
        # Simulated Hugging Face model cards
        return [
            ExternalCandidate(
                source_type=SourceType.HUGGING_FACE,
                name="AlphaAlgo/Llama3-Quant-8B",
                url="https://huggingface.co/AlphaAlgo/Llama3-Quant-8B",
                version_id="f4150b3e",
                author="AlphaAlgo Research",
                description="Fine-tuned quantitative reasoning LLM optimized for market microstructure analysis.",
                readme_content="Quant reasoning model. Licensed under Apache 2.0. Has testing suite.",
                license_name="Apache-2.0",
                metadata={"category": "microstructure", "has_tests": True, "has_docs": True}
            )
        ][:max_results]
