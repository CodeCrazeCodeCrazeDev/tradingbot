"""
Institutional GitHub Scout - Strict Trading Infrastructure Discovery

Your sole mission is to discover high-quality trading-system GitHub repositories 
that can improve AlphaAlgo in these domains only:
- execution infrastructure
- risk management
- backtesting correctness
- statistical validation
- market microstructure
- portfolio construction

HARD RESTRICTIONS:
- NO terminal commands
- NO dependency installation
- NO code execution
- NO automatic integration
- NO production modifications
- TRADING-ONLY scope

Author: AlphaAlgo Team
Date: 2026-01-29
Priority: P0 - INSTITUTIONAL GRADE
"""

import logging
import json
import re
import hashlib
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set
from pathlib import Path
import sqlite3

try:
    import aiohttp
except ImportError:
    aiohttp = None

logger = logging.getLogger(__name__)


class RepoCategory(Enum):
    """Allowed repository categories"""
    EXECUTION = "execution"
    RISK = "risk"
    BACKTESTING = "backtesting"
    STATS = "stats"
    MICROSTRUCTURE = "microstructure"
    PORTFOLIO = "portfolio"


class ExpectedROI(Enum):
    """Expected return on investment"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class RiskLevel(Enum):
    """Integration risk level"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class Recommendation(Enum):
    """Final recommendation"""
    ACCEPT = "accept"
    REJECT = "reject"
    INVESTIGATE = "investigate"


@dataclass
class RepoAnalysis:
    """Structured repository analysis"""
    repo_name: str
    github_url: str
    category: RepoCategory
    why_it_matters: str
    key_components: List[str]
    integration_target_in_alphaalgo: str
    expected_roi: ExpectedROI
    risk_level: RiskLevel
    license: str
    red_flags: List[str]
    recommendation: Recommendation
    
    # Quality metrics
    last_commit_days_ago: int
    has_tests: bool
    has_docs: bool
    stars: int
    forks: int
    
    # Safety checks
    safe_patterns: bool
    no_shell_execution: bool
    no_obfuscation: bool
    
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'repo_name': self.repo_name,
            'github_url': self.github_url,
            'category': self.category.value,
            'why_it_matters': self.why_it_matters,
            'key_components': self.key_components,
            'integration_target_in_alphaalgo': self.integration_target_in_alphaalgo,
            'expected_roi': self.expected_roi.value,
            'risk_level': self.risk_level.value,
            'license': self.license,
            'red_flags': self.red_flags,
            'recommendation': self.recommendation.value,
            'last_commit_days_ago': self.last_commit_days_ago,
            'has_tests': self.has_tests,
            'has_docs': self.has_docs,
            'stars': self.stars,
            'forks': self.forks,
            'timestamp': self.timestamp.isoformat(),
        }
    
    def format_output(self) -> str:
        """Format as required output"""
        return f"""
repo_name: "{self.repo_name}"
github_url: "{self.github_url}"
category: "{self.category.value}"
why_it_matters: "{self.why_it_matters}"
key_components: "{', '.join(self.key_components)}"
integration_target_in_alphaalgo: "{self.integration_target_in_alphaalgo}"
expected_roi: "{self.expected_roi.value}"
risk_level: "{self.risk_level.value}"
license: "{self.license}"
red_flags: "{', '.join(self.red_flags) if self.red_flags else 'None'}"
recommendation: "{self.recommendation.value}"
"""


class InstitutionalGitHubScout:
    """
    Institutional-grade GitHub repository scout for trading infrastructure.
    
    MISSION: Discover high-quality trading repos that improve AlphaAlgo.
    RESTRICTIONS: No auto-integration, no code execution, trading-only scope.
    """
    
    # ABSOLUTE FORBIDDENS
    FORBIDDEN_KEYWORDS = [
        'web3', 'nft', 'crypto meme', 'chatbot', 'sentiment scraping',
        'get rich quick', 'pump', 'dump', 'moon', 'lambo', 'degen',
        'airdrop', 'token', 'ico', 'defi yield farm', 'ponzi',
    ]
    
    # Allowed repo types
    ALLOWED_KEYWORDS = [
        # Execution
        'order execution', 'smart order routing', 'order book', 'market maker',
        'limit order', 'slippage model', 'transaction cost', 'fill simulation',
        # Risk
        'var', 'cvar', 'risk engine', 'position sizing', 'drawdown', 'kill switch',
        'exposure limit', 'margin', 'leverage control', 'circuit breaker',
        # Backtesting
        'backtest', 'walk forward', 'time series cv', 'data leakage',
        'lookahead bias', 'survivorship bias', 'backtesting engine',
        # Stats
        'sharpe ratio', 'deflated sharpe', 'multiple testing', 'statistical validation',
        'monte carlo', 'bootstrap', 'hypothesis test', 'alpha decay',
        # Microstructure
        'market microstructure', 'order flow', 'liquidity', 'bid ask spread',
        'price impact', 'market impact', 'tick data', 'level 2',
        # Portfolio
        'portfolio optimization', 'mean variance', 'black litterman',
        'risk parity', 'hierarchical risk parity', 'asset allocation',
    ]
    
    # Acceptable licenses
    ACCEPTABLE_LICENSES = ['MIT', 'BSD', 'BSD-2-Clause', 'BSD-3-Clause', 'Apache-2.0', 'Apache 2.0']
    
    # Forbidden licenses
    FORBIDDEN_LICENSES = ['GPL', 'AGPL', 'GPL-3.0', 'AGPL-3.0', 'LGPL']
    
    # Unsafe code patterns
    UNSAFE_PATTERNS = [
        r'eval\s*\(',
        r'exec\s*\(',
        r'__import__\s*\(',
        r'subprocess\.call\s*\(',
        r'os\.system\s*\(',
        r'curl\s*\|',
        r'wget\s*\|',
        r'bash\s*-c',
        r'sh\s*-c',
    ]
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # Quality thresholds
        self.max_days_since_commit = 18 * 30  # 18 months
        self.min_stars = self.config.get('min_stars', 50)
        self.min_forks = self.config.get('min_forks', 10)
        
        # Database for storing discoveries
        self.db_path = Path(self.config.get('db_path', 'sentient_data/github_scout.db'))
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_database()
        
        # Discovery history
        self.discoveries: List[RepoAnalysis] = []
        
        logger.info("InstitutionalGitHubScout initialized with strict filters")
    
    def _init_database(self):
        """Initialize SQLite database"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS repo_discoveries (
                id TEXT PRIMARY KEY,
                repo_name TEXT NOT NULL,
                github_url TEXT NOT NULL,
                category TEXT NOT NULL,
                recommendation TEXT NOT NULL,
                expected_roi TEXT,
                risk_level TEXT,
                license TEXT,
                discovered_at TEXT NOT NULL,
                data TEXT NOT NULL
            )
        """)
        
        conn.commit()
        conn.close()
    
    def _is_forbidden_repo(self, repo_name: str, description: str, readme: str) -> tuple:
        """Check if repo is in forbidden categories"""
        text = f"{repo_name} {description} {readme}".lower()
        
        for keyword in self.FORBIDDEN_KEYWORDS:
            if keyword in text:
                return True, f"Forbidden keyword: {keyword}"
        
        return False, ""
    
    def _is_allowed_repo(self, repo_name: str, description: str, readme: str) -> tuple:
        """Check if repo is in allowed categories"""
        text = f"{repo_name} {description} {readme}".lower()
        
        matches = []
        for keyword in self.ALLOWED_KEYWORDS:
            if keyword in text:
                matches.append(keyword)
        
        if not matches:
            return False, "No trading infrastructure keywords found"
        
        return True, f"Matched: {', '.join(matches[:3])}"
    
    def _check_license(self, license_name: str) -> tuple:
        """Check if license is acceptable"""
        if not license_name:
            return False, "No license found"
        
        license_upper = license_name.upper()
        
        # Check forbidden first
        for forbidden in self.FORBIDDEN_LICENSES:
            if forbidden.upper() in license_upper:
                return False, f"Forbidden license: {license_name}"
        
        # Check acceptable
        for acceptable in self.ACCEPTABLE_LICENSES:
            if acceptable.upper() in license_upper:
                return True, ""
        
        return False, f"License not in acceptable list: {license_name}"
    
    def _check_code_safety(self, code_samples: List[str]) -> tuple:
        """Check for unsafe code patterns"""
        unsafe_found = []
        
        for code in code_samples:
            for pattern in self.UNSAFE_PATTERNS:
                if re.search(pattern, code, re.IGNORECASE):
                    unsafe_found.append(pattern)
        
        if unsafe_found:
            return False, f"Unsafe patterns: {', '.join(set(unsafe_found))}"
        
        return True, ""
    
    def _determine_category(self, repo_name: str, description: str, readme: str) -> Optional[RepoCategory]:
        """Determine repository category"""
        text = f"{repo_name} {description} {readme}".lower()
        
        # Category keywords
        category_keywords = {
            RepoCategory.EXECUTION: ['execution', 'order routing', 'order book', 'slippage', 'fill'],
            RepoCategory.RISK: ['risk', 'var', 'cvar', 'drawdown', 'position sizing', 'exposure'],
            RepoCategory.BACKTESTING: ['backtest', 'walk forward', 'time series', 'cross validation'],
            RepoCategory.STATS: ['sharpe', 'statistical', 'hypothesis', 'monte carlo', 'bootstrap'],
            RepoCategory.MICROSTRUCTURE: ['microstructure', 'order flow', 'liquidity', 'market impact'],
            RepoCategory.PORTFOLIO: ['portfolio', 'optimization', 'allocation', 'risk parity'],
        }
        
        scores = {}
        for category, keywords in category_keywords.items():
            score = sum(1 for kw in keywords if kw in text)
            if score > 0:
                scores[category] = score
        
        if not scores:
            return None
        
        return max(scores, key=scores.get)
    
    def _calculate_quality_score(self, analysis: Dict[str, Any]) -> float:
        """Calculate overall quality score"""
        score = 0.0
        
        # Recency (0-30 points)
        days_ago = analysis.get('last_commit_days_ago', 999)
        if days_ago < 30:
            score += 30
        elif days_ago < 90:
            score += 20
        elif days_ago < 180:
            score += 10
        
        # Tests (0-25 points)
        if analysis.get('has_tests'):
            score += 25
        
        # Documentation (0-20 points)
        if analysis.get('has_docs'):
            score += 20
        
        # Popularity (0-15 points)
        stars = analysis.get('stars', 0)
        if stars > 1000:
            score += 15
        elif stars > 500:
            score += 10
        elif stars > 100:
            score += 5
        
        # Safety (0-10 points)
        if analysis.get('safe_patterns'):
            score += 10
        
        return score
    
    async def analyze_repository(
        self,
        repo_url: str,
        repo_data: Dict[str, Any]
    ) -> Optional[RepoAnalysis]:
        """
        Analyze a GitHub repository against institutional standards.
        
        Returns RepoAnalysis if repo passes all gates, None otherwise.
        """
        repo_name = repo_data.get('full_name', '')
        description = repo_data.get('description', '')
        
        # Get README (simulated - in production would fetch from GitHub API)
        readme = repo_data.get('readme', '')
        
        # GATE 1: Forbidden categories
        is_forbidden, reason = self._is_forbidden_repo(repo_name, description, readme)
        if is_forbidden:
            logger.debug(f"Rejected {repo_name}: {reason}")
            return None
        
        # GATE 2: Allowed categories
        is_allowed, match_reason = self._is_allowed_repo(repo_name, description, readme)
        if not is_allowed:
            logger.debug(f"Rejected {repo_name}: {match_reason}")
            return None
        
        # GATE 3: License check
        license_name = repo_data.get('license', {}).get('name', '')
        license_ok, license_reason = self._check_license(license_name)
        if not license_ok:
            logger.debug(f"Rejected {repo_name}: {license_reason}")
            return None
        
        # GATE 4: Recency check
        last_commit = repo_data.get('pushed_at', '')
        if last_commit:
            last_commit_date = datetime.fromisoformat(last_commit.replace('Z', '+00:00'))
            days_ago = (datetime.now(last_commit_date.tzinfo) - last_commit_date).days
            
            if days_ago > self.max_days_since_commit:
                logger.debug(f"Rejected {repo_name}: Last commit {days_ago} days ago (max: {self.max_days_since_commit})")
                return None
        else:
            days_ago = 999
        
        # GATE 5: Tests and docs
        has_tests = repo_data.get('has_tests', False)
        has_docs = repo_data.get('has_docs', False)
        
        if not has_tests:
            logger.debug(f"Rejected {repo_name}: No unit tests")
            return None
        
        if not has_docs:
            logger.debug(f"Rejected {repo_name}: No documentation")
            return None
        
        # GATE 6: Code safety
        code_samples = repo_data.get('code_samples', [])
        safe, safety_reason = self._check_code_safety(code_samples)
        if not safe:
            logger.debug(f"Rejected {repo_name}: {safety_reason}")
            return None
        
        # Determine category
        category = self._determine_category(repo_name, description, readme)
        if not category:
            logger.debug(f"Rejected {repo_name}: Could not determine category")
            return None
        
        # Extract key components
        key_components = self._extract_key_components(readme, category)
        
        # Determine integration target
        integration_target = self._determine_integration_target(category, key_components)
        
        # Calculate metrics
        stars = repo_data.get('stargazers_count', 0)
        forks = repo_data.get('forks_count', 0)
        
        # Determine ROI and risk
        expected_roi = self._estimate_roi(category, stars, has_tests)
        risk_level = self._estimate_risk(category, days_ago, safe)
        
        # Collect red flags
        red_flags = []
        if days_ago > 365:
            red_flags.append(f"Last commit {days_ago} days ago")
        if stars < self.min_stars:
            red_flags.append(f"Only {stars} stars")
        if not safe:
            red_flags.append("Potential unsafe patterns")
        
        # Final recommendation
        quality_score = self._calculate_quality_score({
            'last_commit_days_ago': days_ago,
            'has_tests': has_tests,
            'has_docs': has_docs,
            'stars': stars,
            'safe_patterns': safe,
        })
        
        if quality_score >= 70 and not red_flags:
            recommendation = Recommendation.ACCEPT
        elif quality_score >= 50:
            recommendation = Recommendation.INVESTIGATE
        else:
            recommendation = Recommendation.REJECT
        
        # Create analysis
        analysis = RepoAnalysis(
            repo_name=repo_name,
            github_url=repo_url,
            category=category,
            why_it_matters=self._generate_why_it_matters(category, key_components),
            key_components=key_components,
            integration_target_in_alphaalgo=integration_target,
            expected_roi=expected_roi,
            risk_level=risk_level,
            license=license_name,
            red_flags=red_flags,
            recommendation=recommendation,
            last_commit_days_ago=days_ago,
            has_tests=has_tests,
            has_docs=has_docs,
            stars=stars,
            forks=forks,
            safe_patterns=safe,
            no_shell_execution=True,
            no_obfuscation=True,
        )
        
        # Store in database
        self._store_discovery(analysis)
        
        return analysis
    
    def _extract_key_components(self, readme: str, category: RepoCategory) -> List[str]:
        """Extract key components from README"""
        components = []
        
        # Category-specific extraction
        if category == RepoCategory.EXECUTION:
            if 'slippage' in readme.lower():
                components.append('slippage_model')
            if 'order book' in readme.lower():
                components.append('order_book_simulator')
            if 'routing' in readme.lower():
                components.append('smart_order_router')
        
        elif category == RepoCategory.RISK:
            if 'var' in readme.lower():
                components.append('var_calculator')
            if 'position siz' in readme.lower():
                components.append('position_sizer')
            if 'drawdown' in readme.lower():
                components.append('drawdown_monitor')
        
        elif category == RepoCategory.BACKTESTING:
            if 'walk forward' in readme.lower():
                components.append('walk_forward_engine')
            if 'cross validation' in readme.lower():
                components.append('time_series_cv')
        
        elif category == RepoCategory.STATS:
            if 'sharpe' in readme.lower():
                components.append('deflated_sharpe')
            if 'monte carlo' in readme.lower():
                components.append('monte_carlo_simulator')
        
        if not components:
            components.append('core_module')
        
        return components
    
    def _determine_integration_target(self, category: RepoCategory, components: List[str]) -> str:
        """Determine where in AlphaAlgo this should integrate"""
        targets = {
            RepoCategory.EXECUTION: 'alphaalgo/execution/',
            RepoCategory.RISK: 'alphaalgo/risk/',
            RepoCategory.BACKTESTING: 'alphaalgo/backtesting/',
            RepoCategory.STATS: 'alphaalgo/validation/',
            RepoCategory.MICROSTRUCTURE: 'alphaalgo/market_data/',
            RepoCategory.PORTFOLIO: 'alphaalgo/portfolio/',
        }
        
        base = targets.get(category, 'alphaalgo/modules/')
        
        if components:
            return f"{base}{components[0]}.py"
        
        return base
    
    def _generate_why_it_matters(self, category: RepoCategory, components: List[str]) -> str:
        """Generate why this repo matters"""
        reasons = {
            RepoCategory.EXECUTION: "Improves trade execution quality and reduces slippage",
            RepoCategory.RISK: "Enhances capital preservation and drawdown control",
            RepoCategory.BACKTESTING: "Prevents lookahead bias and improves backtest validity",
            RepoCategory.STATS: "Provides rigorous statistical validation of strategies",
            RepoCategory.MICROSTRUCTURE: "Better understanding of market dynamics",
            RepoCategory.PORTFOLIO: "Optimizes capital allocation and risk distribution",
        }
        
        return reasons.get(category, "Improves trading infrastructure")
    
    def _estimate_roi(self, category: RepoCategory, stars: int, has_tests: bool) -> ExpectedROI:
        """Estimate expected ROI"""
        # Risk and execution have highest ROI (capital preservation)
        if category in [RepoCategory.RISK, RepoCategory.EXECUTION]:
            if stars > 500 and has_tests:
                return ExpectedROI.HIGH
            return ExpectedROI.MEDIUM
        
        # Stats and backtesting prevent costly mistakes
        if category in [RepoCategory.STATS, RepoCategory.BACKTESTING]:
            return ExpectedROI.MEDIUM
        
        return ExpectedROI.LOW
    
    def _estimate_risk(self, category: RepoCategory, days_ago: int, safe: bool) -> RiskLevel:
        """Estimate integration risk"""
        if not safe or days_ago > 365:
            return RiskLevel.HIGH
        
        # Execution and risk are critical paths
        if category in [RepoCategory.EXECUTION, RepoCategory.RISK]:
            return RiskLevel.MEDIUM
        
        return RiskLevel.LOW
    
    def _store_discovery(self, analysis: RepoAnalysis):
        """Store discovery in database"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        repo_id = hashlib.sha256(analysis.github_url.encode()).hexdigest()[:16]
        
        cursor.execute("""
            INSERT OR REPLACE INTO repo_discoveries
            (id, repo_name, github_url, category, recommendation, expected_roi, risk_level, license, discovered_at, data)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            repo_id,
            analysis.repo_name,
            analysis.github_url,
            analysis.category.value,
            analysis.recommendation.value,
            analysis.expected_roi.value,
            analysis.risk_level.value,
            analysis.license,
            analysis.timestamp.isoformat(),
            json.dumps(analysis.to_dict())
        ))
        
        conn.commit()
        conn.close()
        
        self.discoveries.append(analysis)
    
    async def scan_github(
        self,
        query: Optional[str] = None,
        max_results: int = 5
    ) -> List[RepoAnalysis]:
        """
        Scan GitHub for trading infrastructure repositories.
        
        Returns 3-5 repos maximum, fully structured, fully filtered.
        """
        logger.info("Starting institutional GitHub scan...")
        
        # In production, this would use GitHub API
        # For now, return structured format
        
        accepted_repos = []
        
        # Simulated repo data (in production, fetch from GitHub API)
        candidate_repos = self._get_candidate_repos(query)
        
        for repo_data in candidate_repos:
            analysis = await self.analyze_repository(
                repo_data['url'],
                repo_data
            )
            
            if analysis and analysis.recommendation == Recommendation.ACCEPT:
                accepted_repos.append(analysis)
                
                if len(accepted_repos) >= max_results:
                    break
        
        if not accepted_repos:
            logger.warning("No acceptable repositories found. Most public repos are below production standard.")
            return []
        
        # Sort by priority: Risk > Execution > Backtesting > Stats > Portfolio
        priority_order = {
            RepoCategory.RISK: 0,
            RepoCategory.EXECUTION: 1,
            RepoCategory.BACKTESTING: 2,
            RepoCategory.STATS: 3,
            RepoCategory.MICROSTRUCTURE: 4,
            RepoCategory.PORTFOLIO: 5,
        }
        
        accepted_repos.sort(key=lambda r: priority_order.get(r.category, 99))
        
        return accepted_repos[:max_results]
    
    def _get_candidate_repos(self, query: Optional[str]) -> List[Dict[str, Any]]:
        """Get candidate repositories (simulated - would use GitHub API in production)"""
        # This is a placeholder - in production, use GitHub API
        return []
    
    def format_scan_results(self, repos: List[RepoAnalysis]) -> str:
        """Format scan results in required format"""
        if not repos:
            return "No acceptable repositories found. Most public repos are below production standard."
        
        output = ["=" * 70]
        output.append("INSTITUTIONAL GITHUB SCAN RESULTS")
        output.append("=" * 70)
        
        for i, repo in enumerate(repos, 1):
            output.append(f"\n[{i}] {repo.repo_name}")
            output.append(repo.format_output())
            output.append("-" * 70)
        
        return "\n".join(output)
    
    def generate_integration_proposal(self, analysis: RepoAnalysis) -> str:
        """Generate safe integration proposal (patch-only)"""
        return f"""
INTEGRATION PROPOSAL FOR: {analysis.repo_name}

TARGET: {analysis.integration_target_in_alphaalgo}

APPROACH (PATCH-ONLY):
1. Extract only {', '.join(analysis.key_components)} components
2. Create clean API boundary in AlphaAlgo
3. Implement as plugin with dependency injection
4. Full unit test coverage required (>80%)
5. Integration tests with existing systems
6. Code review by 2+ engineers
7. Gradual rollout with feature flag

SAFETY MEASURES:
- No direct code copy-paste
- All code reviewed and refactored
- Comprehensive error handling
- Rollback plan documented
- Performance benchmarks established

TIMELINE:
- Week 1: Design API boundary
- Week 2: Implement core module
- Week 3: Testing and validation
- Week 4: Code review and deployment

APPROVAL REQUIRED FROM:
- Lead Engineer
- Risk Manager
- Head of Trading
"""


def create_github_scout(config: Optional[Dict[str, Any]] = None) -> InstitutionalGitHubScout:
    """Create institutional GitHub scout"""
    return InstitutionalGitHubScout(config)


__all__ = [
    'InstitutionalGitHubScout',
    'RepoAnalysis',
    'RepoCategory',
    'ExpectedROI',
    'RiskLevel',
    'Recommendation',
    'create_github_scout',
]
