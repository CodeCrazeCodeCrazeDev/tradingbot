"""
Elite Trading Bot - Fundamental Analyzer Module

This module gathers and analyzes fundamental data that can impact markets:
1. Macroeconomic indicators (GDP, CPI, unemployment, interest rates)
2. Central bank decisions and statements
3. Geopolitical and global events
4. Company financials for stocks
5. On-chain data for cryptocurrencies
"""

import os
import json
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, field

import pandas as pd
import numpy as np
import aiohttp
import requests
from bs4 import BeautifulSoup
import yfinance as yf
from fredapi import Fred
from web3 import Web3

try:
    from textblob import TextBlob
except ImportError:
    TextBlob = None

# Placeholder ABI for Compound contract
COMPOUND_ABI = []

from trading_bot.database import DatabaseManager
from trading_bot.utils.validation import validate_signal

logger = logging.getLogger(__name__)

@dataclass
class MacroIndicator:
    """Represents a macroeconomic indicator."""
    name: str
    value: float
    previous_value: float
    date: datetime
    frequency: str
    source: str
    country: str
    impact_score: float = 0.0
    trend: str = "neutral"

@dataclass
class CentralBankEvent:
    """Represents a central bank event or decision."""
    bank: str
    event_type: str
    date: datetime
    decision: str
    previous: str
    statement: str
    sentiment_score: float = 0.0
    market_impact: float = 0.0

@dataclass
class GeopoliticalEvent:
    """Represents a significant geopolitical event."""
    title: str
    description: str
    date: datetime
    category: str
    regions: List[str]
    impact_score: float = 0.0
    sentiment_score: float = 0.0

@dataclass
class CompanyFinancials:
    """Represents company financial data."""
    symbol: str
    date: datetime
    revenue: float
    revenue_growth: float
    net_income: float
    eps: float
    pe_ratio: float
    debt_to_equity: float
    quick_ratio: float
    metrics: Dict[str, float] = field(default_factory=dict)

@dataclass
class OnChainData:
    """Represents blockchain/crypto on-chain data."""
    network: str
    date: datetime
    active_addresses: int
    transaction_volume: float
    avg_transaction_fee: float
    total_value_locked: float
    whale_movements: List[Dict[str, Any]]
    defi_metrics: Dict[str, float] = field(default_factory=dict)

@dataclass
class FundamentalSignal:
    """Represents a trading signal based on fundamental analysis."""
    asset: str
    signal_type: str
    direction: str  # bullish, bearish, neutral
    strength: float  # 0.0 to 1.0
    confidence: float  # 0.0 to 1.0
    timeframe: str
    source: str
    date: datetime
    description: str
    supporting_data: Dict[str, Any]
    impact_duration: str  # short_term, medium_term, long_term

class FundamentalAnalyzer:
    """
    Core class for gathering and analyzing fundamental data
    that can impact market movements.
    """
    
    def __init__(self,
                 fred_api_key: Optional[str] = None,
                 db_path: str = "./data/fundamentals",
                 cache_duration: int = 3600):
        """Initialize the fundamental analyzer."""
        self.db_path = db_path
        self.cache_duration = cache_duration
        
        # Initialize API clients
        self.fred = Fred(api_key=fred_api_key) if fred_api_key else None
        self.db = DatabaseManager(db_path)
        
        # Initialize Web3 for crypto
        self.w3 = Web3(Web3.HTTPProvider('https://mainnet.infura.io/v3/YOUR-PROJECT-ID'))
        
        # Cache for data
        self.macro_cache: Dict[str, MacroIndicator] = {}
        self.events_cache: Dict[str, List[Union[CentralBankEvent, GeopoliticalEvent]]] = {}
        self.financials_cache: Dict[str, CompanyFinancials] = {}
        self.onchain_cache: Dict[str, OnChainData] = {}
        
        logger.info("Fundamental Analyzer initialized")
    
    async def get_macro_indicators(self, country: str = "US") -> List[MacroIndicator]:
        """
        Fetch macroeconomic indicators from FRED and other sources.
        
        Args:
            country: Country code to fetch indicators for
            
        Returns:
            List of macroeconomic indicators
        """
        indicators = []
        
        if self.fred:
            # Define key indicators to track
            indicator_codes = {
                "GDP": "GDP",
                "CPI": "CPIAUCSL",
                "Unemployment": "UNRATE",
                "Interest Rate": "FEDFUNDS",
                "Industrial Production": "INDPRO",
                "Retail Sales": "RSXFS",
                "Housing Starts": "HOUST"
            }
            
            for name, code in indicator_codes.items():
                try:
                    # Get data from FRED
                    data = self.fred.get_series(code)
                    latest = data.iloc[-1]
                    previous = data.iloc[-2]
                    
                    # Calculate trend
                    trend = "up" if latest > previous else "down" if latest < previous else "neutral"
                    
                    # Calculate impact score based on deviation from mean
                    z_score = (latest - data.mean()) / data.std()
                    impact_score = min(max(abs(z_score) / 3, 0), 1)  # Normalize to 0-1
                    
                    indicator = MacroIndicator(
                        name=name,
                        value=float(latest),
                        previous_value=float(previous),
                        date=data.index[-1].to_pydatetime(),
                        frequency="monthly",
                        source="FRED",
                        country=country,
                        impact_score=impact_score,
                        trend=trend
                    )
                    
                    indicators.append(indicator)
                    
                except Exception as e:
                    logger.error(f"Error fetching {name} from FRED: {e}")
        
        return indicators
    
    async def monitor_central_banks(self) -> List[CentralBankEvent]:
        """Monitor central bank decisions and statements."""
        events = []
        
        # Define central banks to monitor
        banks = {
            "Federal Reserve": "https://www.federalreserve.gov/newsevents/pressreleases.htm",
            "ECB": "https://www.ecb.europa.eu/press/pr/date/html/index.en.html",
            "Bank of England": "https://www.bankofengland.co.uk/news/press-releases"
        }
        
        for bank_name, url in banks.items():
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(url) as response:
                        if response.status == 200:
                            html = await response.text()
                            soup = BeautifulSoup(html, 'html.parser')
                            
                            # Extract latest decision/statement
                            # Note: This is a simplified example, real implementation would need
                            # bank-specific parsing logic
                            latest_release = soup.find("div", class_="press-release")
                            if latest_release:
                                title = latest_release.find("h2").text.strip()
                                content = latest_release.find("div", class_="content").text.strip()
                                date_str = latest_release.find("span", class_="date").text.strip()
                                
                                # Analyze sentiment
                                sentiment = TextBlob(content).sentiment.polarity
                                
                                event = CentralBankEvent(
                                    bank=bank_name,
                                    event_type="rate_decision",
                                    date=datetime.strptime(date_str, "%Y-%m-%d"),
                                    decision=title,
                                    previous="",  # Would need historical data
                                    statement=content,
                                    sentiment_score=sentiment,
                                    market_impact=abs(sentiment)  # Simplified impact calculation
                                )
                                
                                events.append(event)
            
            except Exception as e:
                logger.error(f"Error monitoring {bank_name}: {e}")
        
        return events
    
    async def track_geopolitical_events(self) -> List[GeopoliticalEvent]:
        """Track significant geopolitical events."""
        events = []
        
        # Example sources for geopolitical events
        sources = [
            "https://api.example.com/geopolitical",  # Replace with real API
            "https://www.reuters.com/world",
            "https://www.bloomberg.com/politics"
        ]
        
        for source in sources:
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(source) as response:
                        if response.status == 200:
                            # Parse events (implementation depends on source)
                            data = await response.json()
                            
                            for event_data in data.get("events", []):
                                event = GeopoliticalEvent(
                                    title=event_data["title"],
                                    description=event_data["description"],
                                    date=datetime.fromisoformat(event_data["date"]),
                                    category=event_data["category"],
                                    regions=event_data["regions"],
                                    impact_score=self._calculate_event_impact(event_data),
                                    sentiment_score=self._analyze_event_sentiment(event_data)
                                )
                                
                                events.append(event)
            
            except Exception as e:
                logger.error(f"Error tracking geopolitical events from {source}: {e}")
        
        return events
    
    async def analyze_company_financials(self, symbol: str) -> Optional[CompanyFinancials]:
        """Analyze company financial data for stocks."""
        try:
            # Get data from yfinance
            stock = yf.Ticker(symbol)
            info = stock.info
            financials = stock.financials
            
            if not info or financials.empty:
                return None
            
            # Calculate key metrics
            latest_financials = financials.iloc[:, 0]  # Most recent quarter
            previous_financials = financials.iloc[:, 1]  # Previous quarter
            
            revenue_growth = ((latest_financials["Total Revenue"] - 
                             previous_financials["Total Revenue"]) / 
                            previous_financials["Total Revenue"])
            
            financials = CompanyFinancials(
                symbol=symbol,
                date=datetime.now(),
                revenue=latest_financials["Total Revenue"],
                revenue_growth=revenue_growth,
                net_income=latest_financials["Net Income"],
                eps=info.get("trailingEPS", 0),
                pe_ratio=info.get("trailingPE", 0),
                debt_to_equity=info.get("debtToEquity", 0),
                quick_ratio=info.get("quickRatio", 0),
                metrics={
                    "profit_margin": info.get("profitMargins", 0),
                    "operating_margin": info.get("operatingMargins", 0),
                    "roa": info.get("returnOnAssets", 0),
                    "roe": info.get("returnOnEquity", 0)
                }
            )
            
            return financials
            
        except Exception as e:
            logger.error(f"Error analyzing financials for {symbol}: {e}")
            return None
    
    async def analyze_onchain_data(self, network: str) -> Optional[OnChainData]:
        """Analyze on-chain data for cryptocurrencies."""
        try:
            if network.lower() == "ethereum":
                # Get basic network stats
                block_number = self.w3.eth.block_number
                latest_block = self.w3.eth.get_block(block_number)
                gas_price = self.w3.eth.gas_price
                
                # Get DeFi stats (example using Compound)
                compound_contract = self.w3.eth.contract(
                    address="COMPOUND_ADDRESS",
                    abi=COMPOUND_ABI
                )
                total_supply = compound_contract.functions.totalSupply().call()
                
                # Track large transactions
                whale_threshold = 1000  # ETH
                whale_txs = []
                
                # Scan recent blocks for whale movements
                for i in range(10):  # Last 10 blocks
                    block = self.w3.eth.get_block(block_number - i, True)
                    for tx in block.transactions:
                        if tx.value > whale_threshold * 10**18:  # Convert to Wei
                            whale_txs.append({
                                "hash": tx.hash.hex(),
                                "value": tx.value / 10**18,
                                "from": tx.from_address,
                                "to": tx.to_address,
                                "block": block.number
                            })
                
                onchain_data = OnChainData(
                    network=network,
                    date=datetime.now(),
                    active_addresses=len(set([tx["from"] for tx in whale_txs])),
                    transaction_volume=sum(tx["value"] for tx in whale_txs),
                    avg_transaction_fee=gas_price / 10**9,  # Convert to Gwei
                    total_value_locked=total_supply / 10**18,
                    whale_movements=whale_txs,
                    defi_metrics={
                        "total_supply": total_supply,
                        "utilization_rate": 0.0,  # Would calculate from contract
                        "total_borrowed": 0.0,
                        "total_deposits": 0.0
                    }
                )
                
                return onchain_data
            
        except Exception as e:
            logger.error(f"Error analyzing on-chain data for {network}: {e}")
            return None
    
    def _calculate_event_impact(self, event_data: Dict[str, Any]) -> float:
        """Calculate impact score for a geopolitical event."""
        # Simplified impact calculation - would be more sophisticated in practice
        impact = 0.0
        
        # Check if event affects major economies
        major_regions = {"US", "EU", "China", "Japan", "UK"}
        if any(region in event_data["regions"] for region in major_regions):
            impact += 0.3
        
        # Check event category
        high_impact_categories = {
            "monetary_policy", "trade_war", "military_conflict",
            "election", "natural_disaster"
        }
        if event_data["category"] in high_impact_categories:
            impact += 0.4
        
        # Check for keywords indicating severity
        severity_keywords = {
            "crisis", "emergency", "critical", "urgent", "severe",
            "breakthrough", "historic", "unprecedented"
        }
        if any(kw in event_data["description"].lower() for kw in severity_keywords):
            impact += 0.3
        
        return min(impact, 1.0)
    
    def _analyze_event_sentiment(self, event_data: Dict[str, Any]) -> float:
        """Analyze sentiment of a geopolitical event."""
        
        # Combine title and description for analysis
        text = f"{event_data['title']} {event_data['description']}"
        sentiment = TextBlob(text).sentiment.polarity
        
        return sentiment
    
    async def generate_signals(self, asset: str) -> List[FundamentalSignal]:
        """
        Generate trading signals based on fundamental analysis.
        
        Args:
            asset: Asset symbol to generate signals for
            
        Returns:
            List of fundamental signals
        """
        signals = []
        
        # Get all relevant data
        macro_indicators = await self.get_macro_indicators()
        central_bank_events = await self.monitor_central_banks()
        geopolitical_events = await self.track_geopolitical_events()
        
        # Asset-specific analysis
        if "USD" in asset or "EUR" in asset:
            # Currency pair analysis
            signals.extend(await self._analyze_forex_fundamentals(
                asset, macro_indicators, central_bank_events
            ))
        
        elif asset.endswith("USD"):  # Crypto
            # Cryptocurrency analysis
            onchain_data = await self.analyze_onchain_data(asset.replace("USD", ""))
            if onchain_data:
                signals.extend(self._analyze_crypto_fundamentals(asset, onchain_data))
        
        else:  # Stock
            # Company analysis
            financials = await self.analyze_company_financials(asset)
            if financials:
                signals.extend(self._analyze_stock_fundamentals(asset, financials))
        
        # Add geopolitical signals
        signals.extend(self._analyze_geopolitical_impact(asset, geopolitical_events))
        
        return signals
    
    async def _analyze_forex_fundamentals(self,
                                        pair: str,
                                        indicators: List[MacroIndicator],
                                        bank_events: List[CentralBankEvent]) -> List[FundamentalSignal]:
        """Analyze fundamental factors for forex pairs."""
        signals = []
        base, quote = pair[:3], pair[3:]
        
        # Analyze interest rate differentials
        base_rate = next((i for i in indicators if i.name == "Interest Rate" and i.country == base), None)
        quote_rate = next((i for i in indicators if i.name == "Interest Rate" and i.country == quote), None)
        
        if base_rate and quote_rate:
            differential = base_rate.value - quote_rate.value
            
            signal = FundamentalSignal(
                asset=pair,
                signal_type="interest_rate_differential",
                direction="bullish" if differential > 0 else "bearish",
                strength=min(abs(differential) / 2, 1.0),  # Normalize to 0-1
                confidence=0.8,  # High confidence in central bank data
                timeframe="medium_term",
                source="Central Banks",
                date=datetime.now(),
                description=f"Interest rate differential of {differential:.2f}%",
                supporting_data={
                    "base_rate": base_rate.value,
                    "quote_rate": quote_rate.value,
                    "differential": differential
                },
                impact_duration="medium_term"
            )
            
            signals.append(signal)
        
        return signals
    
    def _analyze_crypto_fundamentals(self,
                                   asset: str,
                                   onchain_data: OnChainData) -> List[FundamentalSignal]:
        """Analyze fundamental factors for cryptocurrencies."""
        signals = []
        
        # Analyze whale movements
        whale_volume = sum(tx["value"] for tx in onchain_data.whale_movements)
        if whale_volume > 0:
            # Calculate net flow (positive = accumulation, negative = distribution)
            whale_flows = pd.DataFrame(onchain_data.whale_movements)
            net_flow = whale_flows.groupby("to")["value"].sum() - whale_flows.groupby("from")["value"].sum()
            
            signal = FundamentalSignal(
                asset=asset,
                signal_type="whale_activity",
                direction="bullish" if net_flow.sum() > 0 else "bearish",
                strength=min(abs(net_flow.sum()) / whale_volume, 1.0),
                confidence=0.7,
                timeframe="short_term",
                source="On-chain Data",
                date=datetime.now(),
                description=f"Whale net flow: {net_flow.sum():.2f} {asset}",
                supporting_data={
                    "whale_volume": whale_volume,
                    "net_flow": net_flow.sum(),
                    "unique_addresses": len(net_flow)
                },
                impact_duration="short_term"
            )
            
            signals.append(signal)
        
        return signals
    
    def _analyze_stock_fundamentals(self,
                                  symbol: str,
                                  financials: CompanyFinancials) -> List[FundamentalSignal]:
        """Analyze fundamental factors for stocks."""
        signals = []
        
        # Analyze growth metrics
        if financials.revenue_growth > 0.2:  # 20% growth threshold
            signal = FundamentalSignal(
                asset=symbol,
                signal_type="revenue_growth",
                direction="bullish",
                strength=min(financials.revenue_growth, 1.0),
                confidence=0.75,
                timeframe="medium_term",
                source="Financial Statements",
                date=datetime.now(),
                description=f"Strong revenue growth: {financials.revenue_growth:.1%}",
                supporting_data={
                    "revenue": financials.revenue,
                    "growth": financials.revenue_growth,
                    "net_income": financials.net_income
                },
                impact_duration="medium_term"
            )
            
            signals.append(signal)
        
        return signals
    
    def _analyze_geopolitical_impact(self,
                                   asset: str,
                                   events: List[GeopoliticalEvent]) -> List[FundamentalSignal]:
        """Analyze impact of geopolitical events on an asset."""
        signals = []
        
        for event in events:
            if event.impact_score > 0.5:  # High impact events only
                # Determine if event affects the asset
                relevant = self._is_event_relevant(asset, event)
                
                if relevant:
                    signal = FundamentalSignal(
                        asset=asset,
                        signal_type="geopolitical",
                        direction="bullish" if event.sentiment_score > 0 else "bearish",
                        strength=event.impact_score,
                        confidence=0.6,  # Lower confidence due to unpredictable nature
                        timeframe="short_term",
                        source=f"Geopolitical Event: {event.category}",
                        date=datetime.now(),
                        description=event.title,
                        supporting_data={
                            "event_category": event.category,
                            "regions": event.regions,
                            "sentiment": event.sentiment_score
                        },
                        impact_duration="short_term"
                    )
                    
                    signals.append(signal)
        
        return signals
    
    def _is_event_relevant(self, asset: str, event: GeopoliticalEvent) -> bool:
        """Determine if a geopolitical event is relevant to an asset."""
        # Check currency pairs
        if len(asset) == 6 and asset.isalpha():
            base, quote = asset[:3], asset[3:]
            return any(self._is_currency_affected(base, event) or 
                      self._is_currency_affected(quote, event))
        
        # Check cryptocurrencies
        elif asset.endswith("USD"):
            return event.category in ["crypto", "technology", "regulation", "cybersecurity"]
        
        # Check stocks
        else:
            # Would need company metadata to check relevance
            return True
    
    def _is_currency_affected(self, currency: str, event: GeopoliticalEvent) -> bool:
        """Check if a currency is affected by an event."""
        currency_regions = {
            "USD": ["US", "North America"],
            "EUR": ["EU", "Europe"],
            "GBP": ["UK", "Britain", "England"],
            "JPY": ["Japan", "Asia"],
            "AUD": ["Australia", "Oceania"],
            "CAD": ["Canada", "North America"]
        }
        
        if currency in currency_regions:
            return any(region in event.regions for region in currency_regions[currency])
