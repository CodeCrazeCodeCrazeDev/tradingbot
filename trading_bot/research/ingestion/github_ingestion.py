"""
GitHub Repository Ingestion Engine

Scans GitHub for quantitative finance repositories, analyzes their code,
extracts trading strategies and techniques, and feeds them into the
research pipeline for evaluation.
"""

import asyncio
import hashlib
import json
import logging
import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum, auto
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class RepoCategory(Enum):
    """Categories of trading-relevant repositories."""
    TRADING_BOT = auto()
    BACKTESTING_FRAMEWORK = auto()
    ML_TRADING = auto()
    RISK_MANAGEMENT = auto()
    DATA_PIPELINE = auto()
    EXECUTION_ENGINE = auto()
    PORTFOLIO_OPTIMIZATION = auto()
    INDICATOR_LIBRARY = auto()
    RESEARCH_NOTEBOOK = auto()
    STRATEGY_IMPLEMENTATION = auto()


@dataclass
class RepoAnalysis:
    """Analysis of a GitHub repository."""
    id: str
    name: str
    full_name: str
    url: str
    description: str
    stars: int
    forks: int
    language: str
    topics: List[str]
    last_updated: Optional[datetime] = None
    categories: List[RepoCategory] = field(default_factory=list)
    key_files: List[str] = field(default_factory=list)
    strategies_found: List[Dict[str, Any]] = field(default_factory=list)
    techniques_found: List[Dict[str, Any]] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    code_quality_score: float = 0.0
    relevance_score: float = 0.0
    novelty_score: float = 0.0
    analyzed_at: datetime = field(default_factory=datetime.utcnow)
    content_hash: str = ""


class GitHubRepoIngestion:
    """
    Ingests and analyzes GitHub repositories for trading ideas.
    
    Searches for quantitative finance repos, analyzes their code structure,
    extracts strategies and techniques, and evaluates their potential.
    """

    SEARCH_QUERIES = [
        "algorithmic trading python",
        "quantitative finance strategy",
        "reinforcement learning trading",
        "pairs trading cointegration",
        "market making bot",
        "portfolio optimization python",
        "backtesting framework",
        "crypto trading bot",
        "forex trading algorithm",
        "machine learning stock prediction",
        "order book analysis",
        "volatility forecasting",
        "sentiment trading nlp",
        "factor investing python",
        "risk parity portfolio",
    ]

    # Files that typically contain strategy logic
    STRATEGY_FILE_PATTERNS = [
        r'strateg', r'signal', r'alpha', r'model', r'predict',
        r'backtest', r'trade', r'execut', r'risk', r'portfolio',
        r'indicator', r'feature', r'agent', r'env',
    ]

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.repos: Dict[str, RepoAnalysis] = {}
        self.analysis_history: List[Dict[str, Any]] = []
        self.storage_dir = Path(self.config.get(
            'storage_dir', 'data/github_repos'
        ))
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        # GitHub API token from env (optional, increases rate limit)
        import os
        self.github_token = os.environ.get('GITHUB_TOKEN', '')
        self.max_repos_per_query = self.config.get('max_repos_per_query', 10)
        logger.info("GitHubRepoIngestion initialized")

    async def discover_repos(self) -> List[RepoAnalysis]:
        """Discover new trading-relevant repositories."""
        all_repos = []

        for query in self.SEARCH_QUERIES:
            try:
                repos = await self._search_github(query)
                all_repos.extend(repos)
                logger.info(f"Found {len(repos)} repos for '{query}'")
            except Exception as e:
                logger.warning(f"GitHub search failed for '{query}': {e}")
            await asyncio.sleep(2)  # Rate limiting

        # Deduplicate
        seen = set()
        unique = []
        for repo in all_repos:
            if repo.full_name not in seen:
                seen.add(repo.full_name)
                unique.append(repo)
                self.repos[repo.id] = repo

        logger.info(f"Discovered {len(unique)} unique repos")
        return unique

    async def _search_github(self, query: str) -> List[RepoAnalysis]:
        """Search GitHub API for repositories."""
        repos = []
        try:
            import urllib.request

            encoded_query = query.replace(' ', '+')
            url = (
                f"https://api.github.com/search/repositories"
                f"?q={encoded_query}+language:python"
                f"&sort=stars&order=desc"
                f"&per_page={self.max_repos_per_query}"
            )

            headers = {'User-Agent': 'AlphaAlgo/1.0', 'Accept': 'application/vnd.github.v3+json'}
            if self.github_token:
                headers['Authorization'] = f'token {self.github_token}'

            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=30) as response:
                data = json.loads(response.read().decode('utf-8'))

            for item in data.get('items', []):
                content_hash = hashlib.sha256(
                    item.get('full_name', '').encode()
                ).hexdigest()[:16]

                updated_at = None
                if item.get('updated_at'):
                    try:
                        updated_at = datetime.fromisoformat(
                            item['updated_at'].replace('Z', '+00:00')
                        )
                    except ValueError:
                        pass

                repo = RepoAnalysis(
                    id=f"gh-{content_hash}",
                    name=item.get('name', ''),
                    full_name=item.get('full_name', ''),
                    url=item.get('html_url', ''),
                    description=item.get('description', '') or '',
                    stars=item.get('stargazers_count', 0),
                    forks=item.get('forks_count', 0),
                    language=item.get('language', 'Python'),
                    topics=item.get('topics', []),
                    last_updated=updated_at,
                    categories=self._categorize_repo(item),
                    content_hash=content_hash,
                )
                repos.append(repo)

        except Exception as e:
            logger.error(f"GitHub API error: {e}")

        return repos

    async def analyze_repo(self, repo: RepoAnalysis) -> RepoAnalysis:
        """Deep-analyze a repository's code for trading strategies."""
        try:
            import urllib.request

            # Get repo file tree
            url = f"https://api.github.com/repos/{repo.full_name}/git/trees/main?recursive=1"
            headers = {'User-Agent': 'AlphaAlgo/1.0', 'Accept': 'application/vnd.github.v3+json'}
            if self.github_token:
                headers['Authorization'] = f'token {self.github_token}'

            try:
                req = urllib.request.Request(url, headers=headers)
                with urllib.request.urlopen(req, timeout=30) as response:
                    tree_data = json.loads(response.read().decode('utf-8'))
            except Exception:
                # Try 'master' branch if 'main' fails
                url = url.replace('/main?', '/master?')
                req = urllib.request.Request(url, headers=headers)
                with urllib.request.urlopen(req, timeout=30) as response:
                    tree_data = json.loads(response.read().decode('utf-8'))

            # Find strategy-relevant files
            strategy_files = []
            for item in tree_data.get('tree', []):
                path = item.get('path', '').lower()
                if path.endswith('.py'):
                    for pattern in self.STRATEGY_FILE_PATTERNS:
                        if re.search(pattern, path):
                            strategy_files.append(item['path'])
                            break

            repo.key_files = strategy_files[:20]  # Limit to top 20

            # Analyze key files for strategies and techniques
            for file_path in strategy_files[:5]:  # Deep-analyze top 5
                try:
                    content = await self._get_file_content(repo.full_name, file_path)
                    if content:
                        strategies = self._extract_strategies_from_code(content, file_path)
                        repo.strategies_found.extend(strategies)
                        techniques = self._extract_techniques_from_code(content, file_path)
                        repo.techniques_found.extend(techniques)
                except Exception as e:
                    logger.debug(f"Error analyzing {file_path}: {e}")

                await asyncio.sleep(1)

            # Extract dependencies from requirements.txt
            try:
                req_content = await self._get_file_content(repo.full_name, 'requirements.txt')
                if req_content:
                    repo.dependencies = [
                        line.strip().split('==')[0].split('>=')[0]
                        for line in req_content.split('\n')
                        if line.strip() and not line.startswith('#')
                    ]
            except Exception:
                pass

            # Score the repo
            repo.code_quality_score = self._score_code_quality(repo)
            repo.relevance_score = self._score_relevance(repo)
            repo.novelty_score = self._score_novelty(repo)

            logger.info(
                f"Analyzed {repo.full_name}: "
                f"{len(repo.strategies_found)} strategies, "
                f"{len(repo.techniques_found)} techniques"
            )

        except Exception as e:
            logger.error(f"Error analyzing repo {repo.full_name}: {e}")

        return repo

    async def _get_file_content(self, full_name: str, file_path: str) -> Optional[str]:
        """Get file content from GitHub."""
        import urllib.request
        import base64

        url = f"https://api.github.com/repos/{full_name}/contents/{file_path}"
        headers = {'User-Agent': 'AlphaAlgo/1.0', 'Accept': 'application/vnd.github.v3+json'}
        if self.github_token:
            headers['Authorization'] = f'token {self.github_token}'

        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=30) as response:
            data = json.loads(response.read().decode('utf-8'))

        content = data.get('content', '')
        if content:
            return base64.b64decode(content).decode('utf-8', errors='replace')
        return None

    def _extract_strategies_from_code(self, code: str, file_path: str) -> List[Dict[str, Any]]:
        """Extract trading strategy patterns from code."""
        strategies = []

        # Look for class definitions that look like strategies
        class_pattern = re.compile(
            r'class\s+(\w*(?:Strategy|Agent|Model|Trader|Bot)\w*)\s*[\(:]',
            re.IGNORECASE
        )
        for match in class_pattern.finditer(code):
            class_name = match.group(1)
            # Extract docstring if present
            start = match.end()
            docstring = ""
            doc_match = re.search(r'"""(.*?)"""', code[start:start+500], re.DOTALL)
            if doc_match:
                docstring = doc_match.group(1).strip()[:200]

            strategies.append({
                'name': class_name,
                'file': file_path,
                'description': docstring,
                'type': 'class',
            })

        # Look for function definitions that compute signals
        func_pattern = re.compile(
            r'def\s+(\w*(?:signal|predict|trade|execute|alpha|score)\w*)\s*\(',
            re.IGNORECASE
        )
        for match in func_pattern.finditer(code):
            func_name = match.group(1)
            strategies.append({
                'name': func_name,
                'file': file_path,
                'description': '',
                'type': 'function',
            })

        return strategies

    def _extract_techniques_from_code(self, code: str, file_path: str) -> List[Dict[str, Any]]:
        """Extract novel techniques from code."""
        techniques = []
        code_lower = code.lower()

        technique_patterns = {
            'attention_mechanism': ['attention', 'self_attention', 'multi_head'],
            'transformer': ['transformer', 'positional_encoding'],
            'gru_lstm': ['lstm', 'gru', 'recurrent'],
            'reinforcement_learning': ['dqn', 'ppo', 'a2c', 'reward', 'q_value'],
            'ensemble': ['ensemble', 'bagging', 'boosting', 'stacking'],
            'bayesian': ['bayesian', 'posterior', 'prior', 'mcmc'],
            'genetic_algorithm': ['genetic', 'mutation', 'crossover', 'fitness'],
            'kalman_filter': ['kalman', 'state_space'],
            'wavelet': ['wavelet', 'dwt', 'cwt'],
            'graph_neural': ['graph_neural', 'gcn', 'gat', 'node_embedding'],
        }

        for technique, keywords in technique_patterns.items():
            if any(kw in code_lower for kw in keywords):
                techniques.append({
                    'name': technique,
                    'file': file_path,
                    'keywords_matched': [kw for kw in keywords if kw in code_lower],
                })

        return techniques

    def _categorize_repo(self, item: Dict) -> List[RepoCategory]:
        """Categorize a repository based on its metadata."""
        text = (
            (item.get('description', '') or '') + ' ' +
            ' '.join(item.get('topics', []))
        ).lower()

        categories = []
        keyword_map = {
            RepoCategory.TRADING_BOT: ['trading bot', 'trade bot', 'auto trade'],
            RepoCategory.BACKTESTING_FRAMEWORK: ['backtest', 'backtesting'],
            RepoCategory.ML_TRADING: ['machine learning', 'deep learning', 'neural'],
            RepoCategory.RISK_MANAGEMENT: ['risk management', 'risk model'],
            RepoCategory.DATA_PIPELINE: ['data pipeline', 'data feed', 'market data'],
            RepoCategory.EXECUTION_ENGINE: ['execution', 'order management'],
            RepoCategory.PORTFOLIO_OPTIMIZATION: ['portfolio', 'optimization', 'allocation'],
            RepoCategory.INDICATOR_LIBRARY: ['indicator', 'technical analysis'],
            RepoCategory.STRATEGY_IMPLEMENTATION: ['strategy', 'alpha', 'signal'],
        }

        for category, keywords in keyword_map.items():
            if any(kw in text for kw in keywords):
                categories.append(category)

        return categories or [RepoCategory.TRADING_BOT]

    def _score_code_quality(self, repo: RepoAnalysis) -> float:
        """Score repository code quality (0-1)."""
        score = 0.0
        if repo.stars > 100:
            score += 0.3
        elif repo.stars > 10:
            score += 0.15
        if repo.forks > 20:
            score += 0.2
        if len(repo.dependencies) > 3:
            score += 0.1
        if len(repo.key_files) > 5:
            score += 0.2
        if repo.description and len(repo.description) > 50:
            score += 0.1
        if repo.topics:
            score += 0.1
        return min(score, 1.0)

    def _score_relevance(self, repo: RepoAnalysis) -> float:
        """Score how relevant the repo is to our trading system."""
        score = 0.0
        if repo.strategies_found:
            score += min(len(repo.strategies_found) * 0.1, 0.4)
        if repo.techniques_found:
            score += min(len(repo.techniques_found) * 0.15, 0.3)
        if RepoCategory.ML_TRADING in repo.categories:
            score += 0.15
        if RepoCategory.STRATEGY_IMPLEMENTATION in repo.categories:
            score += 0.15
        return min(score, 1.0)

    def _score_novelty(self, repo: RepoAnalysis) -> float:
        """Score how novel the repo's techniques are compared to what we have."""
        # Higher novelty for techniques we don't already use
        novel_techniques = [
            t for t in repo.techniques_found
            if t['name'] in ['graph_neural', 'wavelet', 'bayesian', 'genetic_algorithm']
        ]
        if novel_techniques:
            return min(len(novel_techniques) * 0.25, 1.0)
        return 0.2

    def save_analyses(self):
        """Save repo analyses to disk."""
        data = {}
        for rid, repo in self.repos.items():
            data[rid] = {
                'id': repo.id,
                'name': repo.name,
                'full_name': repo.full_name,
                'url': repo.url,
                'stars': repo.stars,
                'strategies_count': len(repo.strategies_found),
                'techniques_count': len(repo.techniques_found),
                'relevance_score': repo.relevance_score,
                'novelty_score': repo.novelty_score,
                'analyzed_at': repo.analyzed_at.isoformat(),
            }

        path = self.storage_dir / 'repos_index.json'
        with open(path, 'w') as f:
            json.dump(data, f, indent=2)
        logger.info(f"Saved {len(data)} repo analyses to {path}")
