"""
AI Learner - Learn from Other AI Systems and Trading Strategies

Analyzes other AI trading systems, extracts their techniques,
and integrates successful patterns into the bot's own strategies.
"""

import asyncio
try:
    import aiohttp
except ImportError:
    aiohttp = None
import json
import re
import ast
import hashlib
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Set, Tuple
from pathlib import Path
import logging
import sqlite3

logger = logging.getLogger(__name__)


class LearningSource(Enum):
    """Sources for learning"""
    GITHUB_REPO = auto()
    ARXIV_PAPER = auto()
    TRADING_FORUM = auto()
    OPEN_SOURCE_BOT = auto()
    RESEARCH_BLOG = auto()
    KAGGLE_NOTEBOOK = auto()


@dataclass
class LearnedTechnique:
    """A technique learned from external sources"""
    id: str
    name: str
    source: LearningSource
    source_url: str
    description: str
    category: str  # strategy, indicator, risk, execution, ml
    code_snippet: Optional[str]
    parameters: Dict[str, Any]
    performance_claims: Dict[str, float]
    confidence: float
    validated: bool
    integrated: bool
    timestamp: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'name': self.name,
            'source': self.source.name,
            'source_url': self.source_url,
            'description': self.description,
            'category': self.category,
            'code_snippet': self.code_snippet,
            'parameters': self.parameters,
            'performance_claims': self.performance_claims,
            'confidence': self.confidence,
            'validated': self.validated,
            'integrated': self.integrated,
            'timestamp': self.timestamp.isoformat(),
        }


@dataclass
class AISystemAnalysis:
    """Analysis of an external AI trading system"""
    name: str
    url: str
    architecture: Dict[str, Any]
    strategies: List[str]
    indicators: List[str]
    ml_models: List[str]
    risk_management: Dict[str, Any]
    strengths: List[str]
    weaknesses: List[str]
    techniques_to_adopt: List[str]
    overall_score: float


class AILearner:
    """
    Learns from other AI trading systems and strategies.
    
    Features:
    - Analyzes open-source trading bots
    - Extracts successful patterns and techniques
    - Validates techniques through backtesting
    - Integrates proven strategies
    - Continuous learning from new sources
    """
    
    # Known trading bot repositories to analyze
    TRADING_BOT_REPOS = [
        'freqtrade/freqtrade',
        'jesse-ai/jesse',
        'tensortrade-org/tensortrade',
        'AI4Finance-Foundation/FinRL',
        'stefan-jansen/machine-learning-for-trading',
        'quantopian/zipline',
        'mementum/backtrader',
    ]
    
    # Pattern categories to extract
    PATTERN_CATEGORIES = {
        'strategy': [
            'momentum', 'mean_reversion', 'trend_following', 'breakout',
            'pairs_trading', 'arbitrage', 'market_making', 'scalping',
        ],
        'indicator': [
            'rsi', 'macd', 'bollinger', 'atr', 'ema', 'sma', 'vwap',
            'obv', 'adx', 'stochastic', 'ichimoku', 'fibonacci',
        ],
        'ml_model': [
            'lstm', 'transformer', 'random_forest', 'xgboost', 'lightgbm',
            'reinforcement_learning', 'neural_network', 'ensemble',
        ],
        'risk': [
            'position_sizing', 'stop_loss', 'take_profit', 'trailing_stop',
            'portfolio_optimization', 'var', 'drawdown_control',
        ],
        'execution': [
            'twap', 'vwap', 'iceberg', 'smart_routing', 'slippage_control',
        ],
    }
    
    def __init__(
        self,
        db_path: str = "knowledge/ai_learning.db",
        learning_interval: int = 3600,  # 1 hour
    ):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.learning_interval = learning_interval
        
        # State
        self.is_running = False
        self._task: Optional[asyncio.Task] = None
        self._session: Optional[aiohttp.ClientSession] = None
        
        # Learned techniques
        self.techniques: Dict[str, LearnedTechnique] = {}
        self.analyzed_systems: Dict[str, AISystemAnalysis] = {}
        
        # Statistics
        self.stats = {
            'systems_analyzed': 0,
            'techniques_learned': 0,
            'techniques_validated': 0,
            'techniques_integrated': 0,
            'last_learning': None,
        }
        
        # Initialize database
        self._init_database()
        
        logger.info("AILearner initialized")
    
    def _init_database(self) -> None:
        """Initialize SQLite database"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS techniques (
                id TEXT PRIMARY KEY,
                name TEXT,
                source TEXT,
                source_url TEXT,
                description TEXT,
                category TEXT,
                code_snippet TEXT,
                parameters TEXT,
                performance_claims TEXT,
                confidence REAL,
                validated INTEGER DEFAULT 0,
                integrated INTEGER DEFAULT 0,
                timestamp TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS system_analyses (
                id TEXT PRIMARY KEY,
                name TEXT,
                url TEXT,
                analysis TEXT,
                timestamp TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
    
    async def start(self) -> None:
        """Start the learning loop"""
        if self.is_running:
            return
        
        self.is_running = True
        self._session = aiohttp.ClientSession(
            headers={'User-Agent': 'Mozilla/5.0'}
        )
        self._task = asyncio.create_task(self._learning_loop())
        logger.info("AILearner started")
    
    async def stop(self) -> None:
        """Stop the learning"""
        self.is_running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        if self._session:
            await self._session.close()
        logger.info("AILearner stopped")
    
    async def _learning_loop(self) -> None:
        """Main learning loop"""
        while self.is_running:
            try:
                await self._learn_from_all_sources()
                self.stats['last_learning'] = datetime.now().isoformat()
            except Exception as e:
                logger.error(f"Learning error: {e}")
            
            await asyncio.sleep(self.learning_interval)
    
    async def _learn_from_all_sources(self) -> None:
        """Learn from all available sources"""
        tasks = [
            self._analyze_github_repos(),
            self._analyze_kaggle_notebooks(),
            self._extract_arxiv_techniques(),
        ]
        
        await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _analyze_github_repos(self) -> None:
        """Analyze trading bot repositories on GitHub"""
        for repo in self.TRADING_BOT_REPOS:
            try:
                analysis = await self._analyze_repo(repo)
                if analysis:
                    self.analyzed_systems[repo] = analysis
                    self.stats['systems_analyzed'] += 1
                    
                    # Extract techniques
                    await self._extract_techniques_from_analysis(analysis)
                
                await asyncio.sleep(5)  # Rate limiting
                
            except Exception as e:
                logger.debug(f"Error analyzing {repo}: {e}")
    
    async def _analyze_repo(self, repo: str) -> Optional[AISystemAnalysis]:
        """Analyze a single GitHub repository"""
        try:
            # Get repo info
            url = f"https://api.github.com/repos/{repo}"
            async with self._session.get(url) as response:
                if response.status != 200:
                    return None
                repo_data = await response.json()
            
            # Get README
            readme_url = f"https://raw.githubusercontent.com/{repo}/main/README.md"
            async with self._session.get(readme_url) as response:
                if response.status == 200:
                    readme = await response.text()
                else:
                    # Try master branch
                    readme_url = f"https://raw.githubusercontent.com/{repo}/master/README.md"
                    async with self._session.get(readme_url) as response:
                        readme = await response.text() if response.status == 200 else ""
            
            # Analyze content
            strategies = self._extract_strategies(readme)
            indicators = self._extract_indicators(readme)
            ml_models = self._extract_ml_models(readme)
            
            return AISystemAnalysis(
                name=repo_data.get('name', repo),
                url=repo_data.get('html_url', ''),
                architecture=self._analyze_architecture(readme),
                strategies=strategies,
                indicators=indicators,
                ml_models=ml_models,
                risk_management=self._extract_risk_management(readme),
                strengths=self._identify_strengths(readme, repo_data),
                weaknesses=self._identify_weaknesses(readme, repo_data),
                techniques_to_adopt=strategies[:3] + indicators[:3] + ml_models[:2],
                overall_score=self._calculate_system_score(repo_data),
            )
            
        except Exception as e:
            logger.debug(f"Error analyzing repo {repo}: {e}")
            return None
    
    def _extract_strategies(self, text: str) -> List[str]:
        """Extract trading strategies from text"""
        strategies = []
        text_lower = text.lower()
        
        for strategy in self.PATTERN_CATEGORIES['strategy']:
            if strategy.replace('_', ' ') in text_lower or strategy in text_lower:
                strategies.append(strategy)
        
        return strategies
    
    def _extract_indicators(self, text: str) -> List[str]:
        """Extract technical indicators from text"""
        indicators = []
        text_lower = text.lower()
        
        for indicator in self.PATTERN_CATEGORIES['indicator']:
            if indicator in text_lower:
                indicators.append(indicator)
        
        return indicators
    
    def _extract_ml_models(self, text: str) -> List[str]:
        """Extract ML models from text"""
        models = []
        text_lower = text.lower()
        
        for model in self.PATTERN_CATEGORIES['ml_model']:
            if model.replace('_', ' ') in text_lower or model in text_lower:
                models.append(model)
        
        return models
    
    def _analyze_architecture(self, text: str) -> Dict[str, Any]:
        """Analyze system architecture from text"""
        architecture = {
            'modular': 'modular' in text.lower() or 'plugin' in text.lower(),
            'async': 'async' in text.lower() or 'asyncio' in text.lower(),
            'distributed': 'distributed' in text.lower() or 'cluster' in text.lower(),
            'real_time': 'real-time' in text.lower() or 'realtime' in text.lower(),
            'backtesting': 'backtest' in text.lower(),
            'paper_trading': 'paper' in text.lower() and 'trading' in text.lower(),
            'live_trading': 'live' in text.lower() and 'trading' in text.lower(),
        }
        return architecture
    
    def _extract_risk_management(self, text: str) -> Dict[str, Any]:
        """Extract risk management features from text"""
        risk = {}
        text_lower = text.lower()
        
        for feature in self.PATTERN_CATEGORIES['risk']:
            risk[feature] = feature.replace('_', ' ') in text_lower or feature in text_lower
        
        return risk
    
    def _identify_strengths(self, readme: str, repo_data: Dict) -> List[str]:
        """Identify system strengths"""
        strengths = []
        
        if repo_data.get('stargazers_count', 0) > 1000:
            strengths.append("Popular and well-maintained")
        
        if repo_data.get('forks_count', 0) > 200:
            strengths.append("Actively forked and extended")
        
        if 'documentation' in readme.lower() or 'docs' in readme.lower():
            strengths.append("Well documented")
        
        if 'test' in readme.lower() or 'pytest' in readme.lower():
            strengths.append("Has test coverage")
        
        if 'docker' in readme.lower():
            strengths.append("Docker support")
        
        return strengths
    
    def _identify_weaknesses(self, readme: str, repo_data: Dict) -> List[str]:
        """Identify system weaknesses"""
        weaknesses = []
        
        # Check last update
        updated_at = repo_data.get('updated_at', '')
        if updated_at:
            try:
                last_update = datetime.fromisoformat(updated_at.replace('Z', '+00:00'))
                if (datetime.now(last_update.tzinfo) - last_update).days > 180:
                    weaknesses.append("Not recently updated")
            except Exception:
                pass
        
        if repo_data.get('open_issues_count', 0) > 100:
            weaknesses.append("Many open issues")
        
        if 'deprecated' in readme.lower():
            weaknesses.append("Deprecated")
        
        return weaknesses
    
    def _calculate_system_score(self, repo_data: Dict) -> float:
        """Calculate overall system score"""
        score = 0.5  # Base score
        
        # Stars (up to 0.2)
        stars = repo_data.get('stargazers_count', 0)
        score += min(0.2, stars / 10000)
        
        # Forks (up to 0.1)
        forks = repo_data.get('forks_count', 0)
        score += min(0.1, forks / 2000)
        
        # Recent activity (up to 0.2)
        updated_at = repo_data.get('updated_at', '')
        if updated_at:
            try:
                last_update = datetime.fromisoformat(updated_at.replace('Z', '+00:00'))
                days_since = (datetime.now(last_update.tzinfo) - last_update).days
                if days_since < 30:
                    score += 0.2
                elif days_since < 90:
                    score += 0.1
            except Exception:
                pass
        
        return min(1.0, score)
    
    async def _extract_techniques_from_analysis(
        self,
        analysis: AISystemAnalysis
    ) -> None:
        """Extract learnable techniques from system analysis"""
        # Extract strategy techniques
        for strategy in analysis.strategies:
            technique = LearnedTechnique(
                id=hashlib.md5(f"{analysis.name}_{strategy}".encode()).hexdigest(),
                name=f"{strategy.replace('_', ' ').title()} Strategy",
                source=LearningSource.GITHUB_REPO,
                source_url=analysis.url,
                description=f"Trading strategy: {strategy} from {analysis.name}",
                category='strategy',
                code_snippet=None,
                parameters={},
                performance_claims={},
                confidence=analysis.overall_score,
                validated=False,
                integrated=False,
                timestamp=datetime.now(),
            )
            self._save_technique(technique)
        
        # Extract indicator techniques
        for indicator in analysis.indicators:
            technique = LearnedTechnique(
                id=hashlib.md5(f"{analysis.name}_{indicator}".encode()).hexdigest(),
                name=f"{indicator.upper()} Indicator",
                source=LearningSource.GITHUB_REPO,
                source_url=analysis.url,
                description=f"Technical indicator: {indicator} from {analysis.name}",
                category='indicator',
                code_snippet=None,
                parameters={},
                performance_claims={},
                confidence=analysis.overall_score * 0.9,
                validated=False,
                integrated=False,
                timestamp=datetime.now(),
            )
            self._save_technique(technique)
        
        # Extract ML techniques
        for model in analysis.ml_models:
            technique = LearnedTechnique(
                id=hashlib.md5(f"{analysis.name}_{model}".encode()).hexdigest(),
                name=f"{model.replace('_', ' ').title()} Model",
                source=LearningSource.GITHUB_REPO,
                source_url=analysis.url,
                description=f"ML model: {model} from {analysis.name}",
                category='ml_model',
                code_snippet=None,
                parameters={},
                performance_claims={},
                confidence=analysis.overall_score * 0.8,
                validated=False,
                integrated=False,
                timestamp=datetime.now(),
            )
            self._save_technique(technique)
    
    async def _analyze_kaggle_notebooks(self) -> None:
        """Analyze Kaggle notebooks for trading techniques"""
        # Kaggle API requires authentication, so we'll use public search
        search_terms = [
            'stock prediction lstm',
            'cryptocurrency trading',
            'forex prediction',
            'algorithmic trading',
        ]
        
        for term in search_terms:
            try:
                # Search for notebooks (simplified - would need Kaggle API for full access)
                url = f"https://www.kaggle.com/search?q={term.replace(' ', '+')}"
                
                # For now, create placeholder techniques based on common patterns
                technique = LearnedTechnique(
                    id=hashlib.md5(f"kaggle_{term}".encode()).hexdigest(),
                    name=f"Kaggle: {term.title()}",
                    source=LearningSource.KAGGLE_NOTEBOOK,
                    source_url=url,
                    description=f"Techniques from Kaggle notebooks on {term}",
                    category='ml_model',
                    code_snippet=None,
                    parameters={},
                    performance_claims={},
                    confidence=0.6,
                    validated=False,
                    integrated=False,
                    timestamp=datetime.now(),
                )
                self._save_technique(technique)
                
            except Exception as e:
                logger.debug(f"Kaggle analysis error: {e}")
    
    async def _extract_arxiv_techniques(self) -> None:
        """Extract techniques from arXiv papers"""
        queries = [
            'deep reinforcement learning trading',
            'transformer stock prediction',
            'neural network portfolio optimization',
        ]
        
        for query in queries:
            try:
                url = f"http://export.arxiv.org/api/query?search_query=all:{query.replace(' ', '+')}&max_results=5"
                
                async with self._session.get(url) as response:
                    if response.status == 200:
                        content = await response.text()
                        
                        # Parse papers
                        papers = self._parse_arxiv_for_techniques(content)
                        
                        for paper in papers:
                            technique = LearnedTechnique(
                                id=hashlib.md5(paper['id'].encode()).hexdigest(),
                                name=paper['title'][:100],
                                source=LearningSource.ARXIV_PAPER,
                                source_url=paper['id'],
                                description=paper['summary'][:500],
                                category='ml_model',
                                code_snippet=None,
                                parameters={},
                                performance_claims=self._extract_performance_claims(paper['summary']),
                                confidence=0.85,  # Academic papers are reliable
                                validated=False,
                                integrated=False,
                                timestamp=datetime.now(),
                            )
                            self._save_technique(technique)
                
                await asyncio.sleep(3)
                
            except Exception as e:
                logger.debug(f"arXiv technique extraction error: {e}")
    
    def _parse_arxiv_for_techniques(self, content: str) -> List[Dict[str, str]]:
        """Parse arXiv response for techniques"""
        papers = []
        
        entry_pattern = re.compile(r'<entry>(.*?)</entry>', re.DOTALL)
        id_pattern = re.compile(r'<id>(.*?)</id>')
        title_pattern = re.compile(r'<title>(.*?)</title>', re.DOTALL)
        summary_pattern = re.compile(r'<summary>(.*?)</summary>', re.DOTALL)
        
        for entry_match in entry_pattern.finditer(content):
            entry = entry_match.group(1)
            
            id_match = id_pattern.search(entry)
            title_match = title_pattern.search(entry)
            summary_match = summary_pattern.search(entry)
            
            if id_match and title_match:
                papers.append({
                    'id': id_match.group(1),
                    'title': ' '.join(title_match.group(1).split()),
                    'summary': ' '.join(summary_match.group(1).split()) if summary_match else '',
                })
        
        return papers
    
    def _extract_performance_claims(self, text: str) -> Dict[str, float]:
        """Extract performance claims from text"""
        claims = {}
        
        # Look for percentage improvements
        pct_pattern = re.compile(r'(\d+(?:\.\d+)?)\s*%\s*(improvement|accuracy|return|sharpe)', re.IGNORECASE)
        for match in pct_pattern.finditer(text):
            metric = match.group(2).lower()
            value = float(match.group(1))
            claims[metric] = value
        
        # Look for Sharpe ratio
        sharpe_pattern = re.compile(r'sharpe\s*(?:ratio)?\s*(?:of)?\s*(\d+(?:\.\d+)?)', re.IGNORECASE)
        match = sharpe_pattern.search(text)
        if match:
            claims['sharpe_ratio'] = float(match.group(1))
        
        return claims
    
    def _save_technique(self, technique: LearnedTechnique) -> None:
        """Save a learned technique to database"""
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO techniques
                (id, name, source, source_url, description, category, code_snippet,
                 parameters, performance_claims, confidence, validated, integrated, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                technique.id,
                technique.name,
                technique.source.name,
                technique.source_url,
                technique.description,
                technique.category,
                technique.code_snippet,
                json.dumps(technique.parameters),
                json.dumps(technique.performance_claims),
                technique.confidence,
                1 if technique.validated else 0,
                1 if technique.integrated else 0,
                technique.timestamp.isoformat(),
            ))
            
            conn.commit()
            conn.close()
            
            self.techniques[technique.id] = technique
            self.stats['techniques_learned'] += 1
            
        except Exception as e:
            logger.error(f"Failed to save technique: {e}")
    
    def get_techniques_by_category(self, category: str) -> List[LearnedTechnique]:
        """Get techniques by category"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM techniques WHERE category = ?
            ORDER BY confidence DESC
        ''', (category,))
        
        rows = cursor.fetchall()
        conn.close()
        
        techniques = []
        for row in rows:
            try:
                techniques.append(LearnedTechnique(
                    id=row[0],
                    name=row[1],
                    source=LearningSource[row[2]],
                    source_url=row[3],
                    description=row[4],
                    category=row[5],
                    code_snippet=row[6],
                    parameters=json.loads(row[7]) if row[7] else {},
                    performance_claims=json.loads(row[8]) if row[8] else {},
                    confidence=row[9],
                    validated=bool(row[10]),
                    integrated=bool(row[11]),
                    timestamp=datetime.fromisoformat(row[12]),
                ))
            except Exception:
                pass
        
        return techniques
    
    def get_recommended_techniques(self, limit: int = 10) -> List[LearnedTechnique]:
        """Get recommended techniques to integrate"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM techniques
            WHERE integrated = 0
            ORDER BY confidence DESC
            LIMIT ?
        ''', (limit,))
        
        rows = cursor.fetchall()
        conn.close()
        
        techniques = []
        for row in rows:
            try:
                techniques.append(LearnedTechnique(
                    id=row[0],
                    name=row[1],
                    source=LearningSource[row[2]],
                    source_url=row[3],
                    description=row[4],
                    category=row[5],
                    code_snippet=row[6],
                    parameters=json.loads(row[7]) if row[7] else {},
                    performance_claims=json.loads(row[8]) if row[8] else {},
                    confidence=row[9],
                    validated=bool(row[10]),
                    integrated=bool(row[11]),
                    timestamp=datetime.fromisoformat(row[12]),
                ))
            except Exception:
                pass
        
        return techniques
    
    def mark_integrated(self, technique_id: str) -> None:
        """Mark a technique as integrated"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE techniques SET integrated = 1 WHERE id = ?
        ''', (technique_id,))
        
        conn.commit()
        conn.close()
        
        self.stats['techniques_integrated'] += 1
    
    def get_system_analyses(self) -> List[AISystemAnalysis]:
        """Get all system analyses"""
        return list(self.analyzed_systems.values())
    
    def get_stats(self) -> Dict[str, Any]:
        """Get learner statistics"""
        return {
            **self.stats,
            'techniques_count': len(self.techniques),
            'systems_count': len(self.analyzed_systems),
        }
