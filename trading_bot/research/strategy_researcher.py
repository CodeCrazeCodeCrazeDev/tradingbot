"""
Elite Trading Bot - Strategy Researcher Module

This module enables the trading bot to learn from external sources by:
1. Scraping trading strategies from research papers, blogs, and forums
2. Parsing and summarizing strategies into structured format
3. Backtesting candidate strategies automatically
4. Maintaining a self-improvement loop for strategy evaluation
"""

import os
import json
import re
import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
import hashlib

import numpy as np
import pandas as pd
try:
    from transformers import pipeline
except ImportError:
    pipeline = None

try:
    from scholarly import scholarly
except ImportError:
    scholarly = None

try:
    import arxiv
except ImportError:
    arxiv = None

try:
    from bs4 import BeautifulSoup
except ImportError:
    BeautifulSoup = None
import requests
try:
    import aiohttp
except ImportError:
    aiohttp = None

try:
    from trading_bot.backtesting.strategy_backtester import StrategyBacktester
except ImportError:
    StrategyBacktester = None

try:
    from trading_bot.database import DatabaseManager
except ImportError:
    DatabaseManager = None

try:
    from trading_bot.utils.validation import validate_strategy
except ImportError:
    validate_strategy = None

logger = logging.getLogger(__name__)

@dataclass
class StrategySource:
    """Represents a source of trading strategy information."""
    id: str
    title: str
    url: str
    source_type: str  # paper, blog, forum, repository
    author: str
    published_date: datetime
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class CandidateStrategy:
    """Represents a trading strategy extracted from external sources."""
    id: str
    name: str
    description: str
    source: StrategySource
    parameters: Dict[str, Any]
    entry_rules: List[str]
    exit_rules: List[str]
    risk_management: Dict[str, Any]
    asset_classes: List[str]
    timeframes: List[str]
    performance_metrics: Dict[str, float] = field(default_factory=dict)
    confidence_score: float = 0.0
    implementation_code: Optional[str] = None
    validation_status: str = "pending"
    last_updated: datetime = field(default_factory=datetime.now)

class StrategyResearcher:
    """
    Core class for discovering, analyzing, and testing trading strategies
    from external sources.
    """
    
    def __init__(self, 
                 db_path: str = "./data/strategies",
                 min_confidence: float = 0.7,
                 max_strategies: int = 100):
        """Initialize the strategy researcher."""
        self.db_path = db_path
        self.min_confidence = min_confidence
        self.max_strategies = max_strategies
        
        # Initialize components
        self.db = DatabaseManager(db_path)
        self.backtester = StrategyBacktester()
        
        # Load NLP models
        self.summarizer = pipeline("summarization", model="facebook/bart-large-cnn")
        self.classifier = pipeline("zero-shot-classification")
        
        # Load existing strategies
        self.strategies: Dict[str, CandidateStrategy] = {}
        self._load_strategies()
        
        logger.info("Strategy Researcher initialized")
    
    def _load_strategies(self):
        """Load existing strategies from database."""
        try:
            strategies_data = self.db.load_collection("strategies")
            for data in strategies_data:
                strategy = CandidateStrategy(**data)
                self.strategies[strategy.id] = strategy
            logger.info(f"Loaded {len(self.strategies)} existing strategies")
        except Exception as e:
            logger.error(f"Error loading strategies: {e}")
    
    async def research_strategies(self, 
                                asset_classes: List[str] = None,
                                timeframes: List[str] = None) -> List[CandidateStrategy]:
        """
        Research new trading strategies from various sources.
        
        Args:
            asset_classes: List of asset classes to focus on
            timeframes: List of timeframes to consider
            
        Returns:
            List of discovered candidate strategies
        """
        new_strategies = []
        
        # Research academic papers
        paper_strategies = await self._research_papers(asset_classes)
        new_strategies.extend(paper_strategies)
        
        # Research trading blogs
        blog_strategies = await self._research_blogs(asset_classes)
        new_strategies.extend(blog_strategies)
        
        # Research trading forums
        forum_strategies = await self._research_forums(asset_classes)
        new_strategies.extend(forum_strategies)
        
        # Research code repositories
        repo_strategies = await self._research_repositories(asset_classes)
        new_strategies.extend(repo_strategies)
        
        # Filter and validate strategies
        validated_strategies = []
        for strategy in new_strategies:
            if await self._validate_strategy(strategy):
                validated_strategies.append(strategy)
        
        # Save new strategies
        await self._save_strategies(validated_strategies)
        
        return validated_strategies
    
    async def _research_papers(self, asset_classes: List[str]) -> List[CandidateStrategy]:
        """Research trading strategies from academic papers."""
        strategies = []
        
        # Search arXiv
        search_query = " OR ".join([f"trading {asset}" for asset in asset_classes])
        search = arxiv.Search(
            query=search_query,
            max_results=50,
            sort_by=arxiv.SortCriterion.SubmittedDate
        )
        
        for result in search.results():
            try:
                # Create source
                source = StrategySource(
                    id=hashlib.md5(result.entry_id.encode()).hexdigest(),
                    title=result.title,
                    url=result.entry_id,
                    source_type="paper",
                    author=", ".join(result.authors),
                    published_date=result.published,
                    content=result.summary
                )
                
                # Extract strategy details
                strategy = await self._extract_strategy(source)
                if strategy:
                    strategies.append(strategy)
            
            except Exception as e:
                logger.error(f"Error processing paper {result.entry_id}: {e}")
        
        return strategies
    
    async def _research_blogs(self, asset_classes: List[str]) -> List[CandidateStrategy]:
        """Research trading strategies from reputable trading blogs."""
        # Implementation will follow in next part
        return []
    
    async def _research_forums(self, asset_classes: List[str]) -> List[CandidateStrategy]:
        """Research trading strategies from trading forums."""
        # Implementation will follow in next part
        return []
    
    async def _research_repositories(self, asset_classes: List[str]) -> List[CandidateStrategy]:
        """Research trading strategies from code repositories."""
        # Implementation will follow in next part
        return []
    
    async def _extract_strategy(self, source: StrategySource) -> Optional[CandidateStrategy]:
        """Extract trading strategy details from a source."""
        try:
            # Summarize content
            summary = self.summarizer(source.content, max_length=200, min_length=50)[0]["summary_text"]
            
            # Classify strategy type
            strategy_types = ["trend following", "mean reversion", "momentum", "breakout", "statistical arbitrage"]
            classification = self.classifier(summary, strategy_types)
            
            # Extract parameters and rules using NLP
            params = self._extract_parameters(source.content)
            entry_rules = self._extract_rules(source.content, "entry")
            exit_rules = self._extract_rules(source.content, "exit")
            risk_rules = self._extract_risk_rules(source.content)
            
            # Create candidate strategy
            strategy = CandidateStrategy(
                id=hashlib.md5(f"{source.id}_{source.title}".encode()).hexdigest(),
                name=f"{classification['labels'][0].title()} Strategy from {source.title}",
                description=summary,
                source=source,
                parameters=params,
                entry_rules=entry_rules,
                exit_rules=exit_rules,
                risk_management=risk_rules,
                asset_classes=self._extract_asset_classes(source.content),
                timeframes=self._extract_timeframes(source.content),
                confidence_score=classification["scores"][0]
            )
            
            return strategy
            
        except Exception as e:
            logger.error(f"Error extracting strategy from {source.url}: {e}")
            return None
    
    def _extract_parameters(self, content: str) -> Dict[str, Any]:
        """Extract strategy parameters from text."""
        # Basic parameter extraction - will be enhanced
        params = {}
        param_patterns = {
            "period": r"period[:\s]+(\d+)",
            "threshold": r"threshold[:\s]+([\d.]+)",
            "stop_loss": r"stop[- ]loss[:\s]+([\d.]+)",
            "take_profit": r"take[- ]profit[:\s]+([\d.]+)"
        }
        
        for param, pattern in param_patterns.items():
            matches = re.findall(pattern, content.lower())
            if matches:
                try:
                    params[param] = float(matches[0])
                except ValueError:
                    continue
        
        return params
    
    def _extract_rules(self, content: str, rule_type: str) -> List[str]:
        """Extract trading rules from text."""
        # Basic rule extraction - will be enhanced
        rules = []
        sentences = content.split(".")
        
        keywords = {
            "entry": ["enter", "buy", "long", "short", "open position"],
            "exit": ["exit", "sell", "close", "stop", "take profit"]
        }
        
        for sentence in sentences:
            if any(kw in sentence.lower() for kw in keywords[rule_type]):
                rules.append(sentence.strip())
        
        return rules
    
    def _extract_risk_rules(self, content: str) -> Dict[str, Any]:
        """Extract risk management rules from text."""
        risk_rules = {
            "position_size": None,
            "max_loss": None,
            "max_trades": None
        }
        
        # Basic risk rule extraction - will be enhanced
        if "position size" in content.lower():
            risk_rules["position_size"] = "Detected position sizing rules"
        if "stop loss" in content.lower():
            risk_rules["max_loss"] = "Detected stop loss rules"
        if "maximum trades" in content.lower():
            risk_rules["max_trades"] = "Detected trade limit rules"
        
        return risk_rules
    
    def _extract_asset_classes(self, content: str) -> List[str]:
        """Extract mentioned asset classes from text."""
        asset_classes = []
        patterns = {
            "forex": r"forex|fx|currency|currencies",
            "stocks": r"stocks?|equities",
            "crypto": r"crypto|bitcoin|ethereum|digital assets?",
            "commodities": r"commodities|gold|oil|metals",
            "indices": r"indices|index|s&p|nasdaq|dow"
        }
        
        for asset, pattern in patterns.items():
            if re.search(pattern, content.lower()):
                asset_classes.append(asset)
        
        return asset_classes or ["unknown"]
    
    def _extract_timeframes(self, content: str) -> List[str]:
        """Extract mentioned timeframes from text."""
        timeframes = []
        patterns = {
            "M1": r"1[- ]?minute|M1",
            "M5": r"5[- ]?minute|M5",
            "M15": r"15[- ]?minute|M15",
            "H1": r"1[- ]?hour|H1",
            "H4": r"4[- ]?hour|H4",
            "D1": r"daily|D1",
            "W1": r"weekly|W1"
        }
        
        for tf, pattern in patterns.items():
            if re.search(pattern, content.lower()):
                timeframes.append(tf)
        
        return timeframes or ["unknown"]
    
    async def _validate_strategy(self, strategy: CandidateStrategy) -> bool:
        """Validate a candidate strategy."""
        try:
            # Check confidence score
            if strategy.confidence_score < self.min_confidence:
                logger.info(f"Strategy {strategy.name} rejected due to low confidence")
                return False
            
            # Validate strategy structure
            if not validate_strategy(strategy):
                logger.info(f"Strategy {strategy.name} failed validation")
                return False
            
            # Check for duplicates
            if self._is_duplicate(strategy):
                logger.info(f"Strategy {strategy.name} is a duplicate")
                return False
            
            # Basic backtest if possible
            if strategy.implementation_code:
                success = await self._quick_backtest(strategy)
                if not success:
                    logger.info(f"Strategy {strategy.name} failed basic backtest")
                    return False
            
            strategy.validation_status = "validated"
            return True
            
        except Exception as e:
            logger.error(f"Error validating strategy {strategy.name}: {e}")
            return False
    
    def _is_duplicate(self, strategy: CandidateStrategy) -> bool:
        """Check if a strategy is too similar to existing ones."""
        from difflib import SequenceMatcher
        
        for existing in self.strategies.values():
            # Compare descriptions
            desc_ratio = SequenceMatcher(None, 
                                       strategy.description.lower(), 
                                       existing.description.lower()).ratio()
            if desc_ratio > 0.8:  # 80% similarity threshold
                return True
            
            # Compare rules
            rules_ratio = SequenceMatcher(None,
                                        " ".join(strategy.entry_rules + strategy.exit_rules).lower(),
                                        " ".join(existing.entry_rules + existing.exit_rules).lower()).ratio()
            if rules_ratio > 0.8:
                return True
        
        return False
    
    async def _quick_backtest(self, strategy: CandidateStrategy) -> bool:
        """Perform a quick backtest of the strategy."""
        try:
            # Basic backtest on sample data
            results = await self.backtester.quick_test(
                strategy=strategy,
                timeframe="D1",
                period="1M"  # 1 month
            )
            
            # Check basic performance metrics
            if results:
                strategy.performance_metrics = results
                return results.get("sharpe_ratio", 0) > 0.5  # Basic threshold
            
            return False
            
        except Exception as e:
            logger.error(f"Error backtesting strategy {strategy.name}: {e}")
            return False
    
    async def _save_strategies(self, strategies: List[CandidateStrategy]):
        """Save new strategies to database."""
        try:
            for strategy in strategies:
                # Convert to dict for storage
                strategy_dict = {
                    "id": strategy.id,
                    "name": strategy.name,
                    "description": strategy.description,
                    "source": strategy.source.__dict__,
                    "parameters": strategy.parameters,
                    "entry_rules": strategy.entry_rules,
                    "exit_rules": strategy.exit_rules,
                    "risk_management": strategy.risk_management,
                    "asset_classes": strategy.asset_classes,
                    "timeframes": strategy.timeframes,
                    "performance_metrics": strategy.performance_metrics,
                    "confidence_score": strategy.confidence_score,
                    "implementation_code": strategy.implementation_code,
                    "validation_status": strategy.validation_status,
                    "last_updated": strategy.last_updated.isoformat()
                }
                
                # Save to database
                await self.db.upsert_document("strategies", strategy_dict)
                
                # Update local cache
                self.strategies[strategy.id] = strategy
            
            logger.info(f"Saved {len(strategies)} new strategies")
            
        except Exception as e:
            logger.error(f"Error saving strategies: {e}")
    
    async def get_best_strategies(self, 
                                asset_class: str = None,
                                timeframe: str = None,
                                min_sharpe: float = 0.5) -> List[CandidateStrategy]:
        """
        Get the best performing strategies based on criteria.
        
        Args:
            asset_class: Filter by asset class
            timeframe: Filter by timeframe
            min_sharpe: Minimum Sharpe ratio
            
        Returns:
            List of best performing strategies
        """
        strategies = list(self.strategies.values())
        
        # Apply filters
        if asset_class:
            strategies = [s for s in strategies if asset_class in s.asset_classes]
        if timeframe:
            strategies = [s for s in strategies if timeframe in s.timeframes]
        
        # Filter by performance
        strategies = [s for s in strategies if s.performance_metrics.get("sharpe_ratio", 0) >= min_sharpe]
        
        # Sort by Sharpe ratio
        strategies.sort(key=lambda x: x.performance_metrics.get("sharpe_ratio", 0), reverse=True)
        
        return strategies[:self.max_strategies]
