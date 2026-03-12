"""
Elite Trading Bot - Real-Time Data Feed

This module provides real-time data feed capabilities for the Elite Trading Bot,
enabling integration with various market data sources and APIs.
"""

import enum
import asyncio
import logging
import json
import time
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union
from dataclasses import dataclass, field

try:
    import aiohttp
except ImportError:
    aiohttp = None
import pandas as pd
import numpy as np
try:
    import websockets
except ImportError:
    websockets = None

from .event_monitor import EventMonitor, MarketEvent, EventType, EventPriority, EventSource
from enum import Enum
import numpy
import pandas

# Configure logging
logger = logging.getLogger(__name__)


class DataSource(enum.Enum):
    """Types of data sources."""
    ALPHA_VANTAGE = "alpha_vantage"
    POLYGON = "polygon"
    YAHOO_FINANCE = "yahoo_finance"
    TRADERMADE = "tradermade"
    OANDA = "oanda"
    BINANCE = "binance"
    COINBASE = "coinbase"
    CUSTOM = "custom"
    SIMULATED = "simulated"


class DataFeedStatus(enum.Enum):
    """Status of a data feed."""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    RECONNECTING = "reconnecting"
    ERROR = "error"
    PAUSED = "paused"


@dataclass
class DataStreamConfig:
    """Configuration for a data stream."""
    source: DataSource
    symbols: List[str]
    interval: str = "1m"  # 1m, 5m, 15m, 30m, 1h, 4h, 1d
    fields: List[str] = field(default_factory=lambda: ["open", "high", "low", "close", "volume"])
    max_history_bars: int = 1000
    include_extended_hours: bool = False
    use_websocket: bool = True
    api_params: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DataPoint:
    """Single data point from a real-time feed."""
    symbol: str
    timestamp: datetime
    data: Dict[str, Any]
    source: DataSource


@dataclass
class DataValidationRule:
    """Rule for validating data."""
    field: str
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    not_null: bool = True
    custom_validator: Optional[Callable[[Any], bool]] = None
    
    def validate(self, value: Any) -> bool:
        """
        Validate a value against this rule.
        
        Args:
            value: Value to validate
            
        Returns:
            True if valid, False otherwise
        """
        # Check not null
        if self.not_null and (value is None or pd.isna(value)):
            return False
            
        # Skip other checks if value is None
        if value is None or pd.isna(value):
            return True
            
        # Check min value
        if self.min_value is not None and value < self.min_value:
            return False
            
        # Check max value
        if self.max_value is not None and value > self.max_value:
            return False
            
        # Custom validation
        if self.custom_validator is not None:
            return self.custom_validator(value)
            
        return True


class DataValidator:
    """Validates data from real-time feeds."""
    
    def __init__(self):
        """Initialize data validator."""
        # Default validation rules
        self.default_rules = {
            "open": DataValidationRule("open", min_value=0),
            "high": DataValidationRule("high", min_value=0),
            "low": DataValidationRule("low", min_value=0),
            "close": DataValidationRule("close", min_value=0),
            "volume": DataValidationRule("volume", min_value=0)
        }
        
        # Custom rules by symbol
        self.symbol_rules: Dict[str, Dict[str, DataValidationRule]] = {}
        
    def add_rule(self, field: str, rule: DataValidationRule, symbol: Optional[str] = None):
        """
        Add a validation rule.
        
        Args:
            field: Field to validate
            rule: Validation rule
            symbol: Optional symbol to apply rule to (None for all symbols)
        """
        if symbol is None:
            self.default_rules[field] = rule
        else:
            if symbol not in self.symbol_rules:
                self.symbol_rules[symbol] = {}
            self.symbol_rules[symbol][field] = rule
    
    def validate(self, data_point: DataPoint) -> bool:
        """
        Validate a data point.
        
        Args:
            data_point: Data point to validate
            
        Returns:
            True if valid, False otherwise
        """
        # Get rules for this symbol
        symbol_specific_rules = self.symbol_rules.get(data_point.symbol, {})
        
        # Validate each field
        for field, value in data_point.data.items():
            # Use symbol-specific rule if available, otherwise use default
            rule = symbol_specific_rules.get(field, self.default_rules.get(field))
            
            if rule and not rule.validate(value):
                logger.warning(f"Validation failed for {data_point.symbol} {field}: {value}")
                return False
                
        return True


class DataStreamManager:
    """Manages multiple data streams."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize data stream manager.
        
        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
        self._init_default_config()
        
        # Data streams
        self.streams: Dict[str, RealTimeDataFeed] = {}
        
        # Combined data
        self.latest_data: Dict[str, Dict[str, DataPoint]] = {}
        self.historical_data: Dict[str, pd.DataFrame] = {}
        
        # Status
        self.running = False
        
    def _init_default_config(self):
        """Initialize default configuration if not provided."""
        defaults = {
            "max_streams": 10,
            "update_interval_seconds": 1,
            "max_historical_bars": 1000,
            "auto_reconnect": True,
            "reconnect_delay_seconds": 5,
            "max_reconnect_attempts": 5
        }
        
        for key, value in defaults.items():
            if key not in self.config:
                self.config[key] = value
    
    def add_stream(self, stream_id: str, data_feed: "RealTimeDataFeed"):
        """
        Add a data stream.
        
        Args:
            stream_id: Unique stream identifier
            data_feed: Data feed to add
        """
        if len(self.streams) >= self.config["max_streams"]:
            raise ValueError(f"Maximum number of streams ({self.config['max_streams']}) reached")
            
        self.streams[stream_id] = data_feed
        
        # Initialize data structures
        for symbol in data_feed.config.symbols:
            if symbol not in self.latest_data:
                self.latest_data[symbol] = {}
            if symbol not in self.historical_data:
                self.historical_data[symbol] = pd.DataFrame()
    
    def remove_stream(self, stream_id: str):
        """
        Remove a data stream.
        
        Args:
            stream_id: Stream identifier
        """
        if stream_id in self.streams:
            del self.streams[stream_id]
    
    async def start_all(self):
        """Start all data streams."""
        self.running = True
        
        # Start each stream
        for stream_id, data_feed in self.streams.items():
            await data_feed.connect()
            
        # Start update loop
        asyncio.create_task(self._update_loop())
    
    async def stop_all(self):
        """Stop all data streams."""
        self.running = False
        
        # Stop each stream
        for stream_id, data_feed in self.streams.items():
            await data_feed.disconnect()
    
    async def _update_loop(self):
        """Background task to update combined data."""
        logger.info("Data stream manager update loop started")
        
        while self.running:
            try:
                # Update latest data from each stream
                for stream_id, data_feed in self.streams.items():
                    for symbol, data_point in data_feed.latest_data.items():
                        if data_point:
                            self.latest_data[symbol][stream_id] = data_point
                
                # Update historical data
                for symbol in self.historical_data:
                    # Collect data from all streams
                    symbol_data = []
                    for stream_id, data_feed in self.streams.items():
                        if symbol in data_feed.historical_data:
                            df = data_feed.historical_data[symbol].copy()
                            df["source"] = stream_id
                            symbol_data.append(df)
                    
                    if symbol_data:
                        # Combine data
                        combined = pd.concat(symbol_data)
                        
                        # Remove duplicates (keep latest by source)
                        combined = combined.sort_values("timestamp").drop_duplicates(
                            subset=["timestamp", "source"], keep="last"
                        )
                        
                        # Keep only recent history
                        max_bars = self.config["max_historical_bars"]
                        if len(combined) > max_bars:
                            combined = combined.tail(max_bars)
                            
                        self.historical_data[symbol] = combined
                
            except Exception as e:
                logger.error(f"Error in data stream manager update loop: {e}")
                
            await asyncio.sleep(self.config["update_interval_seconds"])
            
        logger.info("Data stream manager update loop stopped")
    
    def get_latest(self, symbol: str) -> Optional[Dict[str, DataPoint]]:
        """
        Get latest data for a symbol from all streams.
        
        Args:
            symbol: Symbol to get data for
            
        Returns:
            Dictionary of stream_id -> data_point or None if not available
        """
        return self.latest_data.get(symbol)
    
    def get_historical(self, symbol: str) -> pd.DataFrame:
        """
        Get historical data for a symbol.
        
        Args:
            symbol: Symbol to get data for
            
        Returns:
            DataFrame with historical data
        """
        return self.historical_data.get(symbol, pd.DataFrame())
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get status of all streams.
        
        Returns:
            Dictionary with status information
        """
        return {
            stream_id: {
                "status": data_feed.status.value,
                "symbols": data_feed.config.symbols,
                "source": data_feed.config.source.value,
                "last_update": data_feed.last_update.isoformat() if data_feed.last_update else None
            }
            for stream_id, data_feed in self.streams.items()
        }


class RealTimeDataFeed:
    """
    Real-time data feed that connects to various market data sources
    and provides streaming price data.
    """
    
    def __init__(self, 
                 event_monitor: Optional[EventMonitor] = None,
                 config: Optional[DataStreamConfig] = None):
        """
        Initialize real-time data feed.
        
        Args:
            event_monitor: Optional event monitoring system
            config: Data stream configuration
        """
        self.event_monitor = event_monitor
        self.config = config or DataStreamConfig(
            source=DataSource.SIMULATED,
            symbols=["EURUSD", "GBPUSD"]
        )
        
        # API client
        self.api_client: Dict[str, Any] = {}
        
        # Data storage
        self.latest_data: Dict[str, DataPoint] = {}
        self.historical_data: Dict[str, pd.DataFrame] = {}
        
        # Websocket connection
        self.ws_connection = None
        self.ws_task = None
        
        # Status
        self.status = DataFeedStatus.DISCONNECTED
        self.last_update: Optional[datetime] = None
        self.connection_attempts = 0
        
        # Data validator
        self.validator = DataValidator()
        
        # Callbacks
        self.on_data_callbacks: List[Callable[[DataPoint], None]] = []
        self.on_status_change_callbacks: List[Callable[[DataFeedStatus], None]] = []
        
        logger.info(f"RealTimeDataFeed initialized for {self.config.source.value}")
    
    async def configure_api(self, api_key: str, **kwargs):
        """
        Configure API client.
        
        Args:
            api_key: API key
            **kwargs: Additional configuration parameters
        """
        self.api_client = {
            "api_key": api_key,
            "base_url": kwargs.get("base_url"),
            "ws_url": kwargs.get("ws_url"),
            "session": None,
            "config": kwargs
        }
        logger.info(f"Configured API client for {self.config.source.value}")
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create an aiohttp session."""
        if not self.api_client:
            raise ValueError(f"API client for {self.config.source.value} not configured")
            
        if "session" not in self.api_client or self.api_client["session"] is None or self.api_client["session"].closed:
            self.api_client["session"] = aiohttp.ClientSession()
            
        return self.api_client["session"]
    
    async def connect(self):
        """Connect to the data source."""
        if self.status in (DataFeedStatus.CONNECTED, DataFeedStatus.CONNECTING):
            logger.warning(f"Already connected to {self.config.source.value}")
            return
            
        self._set_status(DataFeedStatus.CONNECTING)
        self.connection_attempts += 1
        
        try:
            # Initialize historical data
            await self._initialize_historical_data()
            
            # Connect to real-time feed
            if self.config.use_websocket:
                await self._connect_websocket()
            else:
                # Start polling loop for REST API
                self.ws_task = asyncio.create_task(self._polling_loop())
                
            self._set_status(DataFeedStatus.CONNECTED)
            logger.info(f"Connected to {self.config.source.value}")
            
        except Exception as e:
            logger.error(f"Error connecting to {self.config.source.value}: {e}")
            self._set_status(DataFeedStatus.ERROR)
            
            # Auto-reconnect
            if self.connection_attempts < self.api_client.get("config", {}).get("max_reconnect_attempts", 5):
                delay = self.api_client.get("config", {}).get("reconnect_delay_seconds", 5)
                logger.info(f"Reconnecting to {self.config.source.value} in {delay} seconds...")
                await asyncio.sleep(delay)
                await self.connect()
    
    async def disconnect(self):
        """Disconnect from the data source."""
        if self.status == DataFeedStatus.DISCONNECTED:
            return
            
        # Cancel websocket task
        if self.ws_task:
            self.ws_task.cancel()
            self.ws_task = None
            
        # Close websocket connection
        if self.ws_connection:
            await self.ws_connection.close()
            self.ws_connection = None
            
        self._set_status(DataFeedStatus.DISCONNECTED)
        logger.info(f"Disconnected from {self.config.source.value}")
    
    async def _initialize_historical_data(self):
        """Initialize historical data."""
        for symbol in self.config.symbols:
            # Fetch historical data
            df = await self._fetch_historical_data(symbol)
            
            if df is not None and not df.empty:
                # Store historical data
                self.historical_data[symbol] = df
                
                # Set latest data point
                latest_row = df.iloc[-1]
                self.latest_data[symbol] = DataPoint(
                    symbol=symbol,
                    timestamp=latest_row.name if isinstance(df.index, pd.DatetimeIndex) else datetime.now(),
                    data={col: latest_row[col] for col in df.columns},
                    source=self.config.source
                )
                
                logger.info(f"Initialized historical data for {symbol}: {len(df)} bars")
    
    async def _fetch_historical_data(self, symbol: str) -> Optional[pd.DataFrame]:
        """
        Fetch historical data for a symbol.
        
        Args:
            symbol: Symbol to fetch data for
            
        Returns:
            DataFrame with historical data or None on error
        """
        if not self.api_client:
            # Use simulated data
            return self._generate_simulated_data(symbol)
        try:
            
            session = await self._get_session()
            
            # Build request based on source
            if self.config.source == DataSource.ALPHA_VANTAGE:
                url = f"{self.api_client['base_url']}/query"
                params = {
                    "function": "TIME_SERIES_INTRADAY",
                    "symbol": symbol,
                    "interval": self.config.interval,
                    "outputsize": "full",
                    "apikey": self.api_client["api_key"]
                }
                
                async with session.get(url, params=params) as response:
                    response.raise_for_status()
                    data = await response.json()
                    
                    # Parse Alpha Vantage response
                    time_series_key = f"Time Series ({self.config.interval})"
                    if time_series_key in data:
                        time_series = data[time_series_key]
                        df = pd.DataFrame.from_dict(time_series, orient="index")
                        
                        # Rename columns
                        df.columns = [col.split(". ")[1] for col in df.columns]
                        df.columns = [col.lower() for col in df.columns]
                        
                        # Convert to numeric
                        for col in df.columns:
                            df[col] = pd.to_numeric(df[col])
                            
                        # Convert index to datetime
                        df.index = pd.to_datetime(df.index)
                        
                        # Sort by date
                        df = df.sort_index()
                        
                        # Limit to max bars
                        if len(df) > self.config.max_history_bars:
                            df = df.tail(self.config.max_history_bars)
                            
                        return df
                    
                    return None
                    
            elif self.config.source == DataSource.POLYGON:
                # Convert interval to Polygon format
                interval_mapping = {
                    "1m": "minute",
                    "5m": "minute",
                    "15m": "minute",
                    "30m": "minute",
                    "1h": "hour",
                    "4h": "hour",
                    "1d": "day"
                }
                
                interval_value = int(self.config.interval[:-1])
                interval_unit = interval_mapping.get(self.config.interval, "minute")
                
                url = f"{self.api_client['base_url']}/v2/aggs/ticker/{symbol}/range/{interval_value}/{interval_unit}/2020-01-01/{datetime.now().strftime('%Y-%m-%d')}"
                params = {
                    "apiKey": self.api_client["api_key"],
                    "limit": self.config.max_history_bars
                }
                
                async with session.get(url, params=params) as response:
                    response.raise_for_status()
                    data = await response.json()
                    
                    # Parse Polygon response
                    if data.get("results"):
                        df = pd.DataFrame(data["results"])
                        
                        # Rename columns
                        column_mapping = {
                            "o": "open",
                            "h": "high",
                            "l": "low",
                            "c": "close",
                            "v": "volume",
                            "t": "timestamp"
                        }
                        df = df.rename(columns=column_mapping)
                        
                        # Convert timestamp to datetime
                        df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
                        
                        # Set index
                        df = df.set_index("timestamp")
                        
                        # Sort by date
                        df = df.sort_index()
                        
                        return df
                    
                    return None
                    
            elif self.config.source == DataSource.TRADERMADE:
                # Convert interval to TraderMade format
                interval_mapping = {
                    "1m": "minute",
                    "5m": "minute",
                    "15m": "minute",
                    "30m": "minute",
                    "1h": "hour",
                    "4h": "hour",
                    "1d": "daily"
                }
                
                interval_unit = interval_mapping.get(self.config.interval, "minute")
                
                url = f"{self.api_client['base_url']}/v1/timeseries"
                params = {
                    "currency": symbol,
                    "api_key": self.api_client["api_key"],
                    "format": "json",
                    "start_date": (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d-%H:%M"),
                    "end_date": datetime.now().strftime("%Y-%m-%d-%H:%M"),
                    "interval": interval_unit
                }
                
                async with session.get(url, params=params) as response:
                    response.raise_for_status()
                    data = await response.json()
                    
                    # Parse TraderMade response
                    if data.get("quotes"):
                        df = pd.DataFrame(data["quotes"])
                        
                        # Rename columns
                        df.columns = [col.lower() for col in df.columns]
                        
                        # Convert timestamp to datetime
                        df["timestamp"] = pd.to_datetime(df["timestamp"])
                        
                        # Set index
                        df = df.set_index("timestamp")
                        
                        # Sort by date
                        df = df.sort_index()
                        
                        # Limit to max bars
                        if len(df) > self.config.max_history_bars:
                            df = df.tail(self.config.max_history_bars)
                            
                        return df
                    
                    return None
            
            else:
                # Use simulated data for unsupported sources
                return self._generate_simulated_data(symbol)
                
        except Exception as e:
            logger.error(f"Error fetching historical data for {symbol}: {e}")
            return self._generate_simulated_data(symbol)
    
    def _generate_simulated_data(self, symbol: str) -> pd.DataFrame:
        """
        Generate simulated historical data.
        
        Args:
            symbol: Symbol to generate data for
            
        Returns:
            DataFrame with simulated data
        """
        # Use symbol as seed for reproducibility
        seed = sum(ord(c) for c in symbol)
        np.random.seed(seed)
        
        # Generate dates
        end_date = datetime.now()
        
        # Determine time delta based on interval
        if self.config.interval == "1m":
            delta = timedelta(minutes=1)
        elif self.config.interval == "5m":
            delta = timedelta(minutes=5)
        elif self.config.interval == "15m":
            delta = timedelta(minutes=15)
        elif self.config.interval == "30m":
            delta = timedelta(minutes=30)
        elif self.config.interval == "1h":
            delta = timedelta(hours=1)
        elif self.config.interval == "4h":
            delta = timedelta(hours=4)
        else:  # 1d
            delta = timedelta(days=1)
            
        dates = [end_date - delta * i for i in range(self.config.max_history_bars)]
        dates.reverse()
        
        # Base price varies by symbol
        if symbol.startswith("BTC") or symbol.endswith("BTC"):
            base_price = 50000
        elif symbol.startswith("ETH") or symbol.endswith("ETH"):
            base_price = 3000
        elif "USD" in symbol:
            base_price = 1.1
        else:
            base_price = 100
        
        # Generate OHLCV data
        data = pd.DataFrame({
            'open': np.random.randn(len(dates)).cumsum() + base_price,
            'high': np.random.randn(len(dates)).cumsum() + base_price + 0.02 * base_price,
            'low': np.random.randn(len(dates)).cumsum() + base_price - 0.02 * base_price,
            'close': np.random.randn(len(dates)).cumsum() + base_price,
            'volume': np.random.randint(1000, 10000, len(dates))
        }, index=dates)
        
        # Ensure high is always highest and low is always lowest
        for i in range(len(data)):
            values = [data.iloc[i]['open'], data.iloc[i]['close']]
            data.iloc[i, data.columns.get_loc('high')] = max(values) + abs(np.random.randn()) * 0.01 * base_price
            data.iloc[i, data.columns.get_loc('low')] = min(values) - abs(np.random.randn()) * 0.01 * base_price
        
        return data
    
    async def _connect_websocket(self):
        """Connect to websocket API."""
        if not self.api_client or "ws_url" not in self.api_client:
            raise ValueError(f"Websocket URL not configured for {self.config.source.value}")
            
        # Build websocket URL and parameters based on source
        ws_url = self.api_client["ws_url"]
        
        if self.config.source == DataSource.POLYGON:
            # Add API key to URL
            ws_url = f"{ws_url}?apiKey={self.api_client['api_key']}"
            
        elif self.config.source == DataSource.BINANCE:
            # Build stream name for each symbol
            streams = [f"{symbol.lower()}@kline_{self.config.interval}" for symbol in self.config.symbols]
            ws_url = f"{ws_url}/stream?streams={'/'.join(streams)}"
            
        # Connect to websocket
        self.ws_connection = await websockets.connect(ws_url)
        
        # Subscribe to symbols
        await self._subscribe_symbols()
        
        # Start websocket task
        self.ws_task = asyncio.create_task(self._websocket_loop())
    
    async def _subscribe_symbols(self):
        """Subscribe to symbols on websocket."""
        if not self.ws_connection:
            return
        try:
            
            if self.config.source == DataSource.POLYGON:
                # Subscribe to each symbol
                for symbol in self.config.symbols:
                    subscribe_msg = {
                        "action": "subscribe",
                        "params": f"AM.{symbol}"  # Aggregate minute data
                    }
                    await self.ws_connection.send(json.dumps(subscribe_msg))
                    
            elif self.config.source == DataSource.BINANCE:
                # Already subscribed in URL
                pass
                
            elif self.config.source == DataSource.TRADERMADE:
                # Subscribe to each symbol
                symbols = ",".join(self.config.symbols)
                subscribe_msg = {
                    "userKey": self.api_client["api_key"],
                    "symbol": symbols
                }
                await self.ws_connection.send(json.dumps(subscribe_msg))
                
        except Exception as e:
            logger.error(f"Error subscribing to symbols: {e}")
    
    async def _websocket_loop(self):
        """Background task to process websocket messages."""
        logger.info(f"Websocket loop started for {self.config.source.value}")
        
        try:
            while True:
                # Receive message
                message = await self.ws_connection.recv()
                
                try:
                    # Parse message
                    data = json.loads(message)
                    
                    # Process based on source
                    if self.config.source == DataSource.POLYGON:
                        await self._process_polygon_message(data)
                    elif self.config.source == DataSource.BINANCE:
                        await self._process_binance_message(data)
                    elif self.config.source == DataSource.TRADERMADE:
                        await self._process_tradermade_message(data)
                        
                except json.JSONDecodeError:
                    logger.warning(f"Invalid JSON message: {message}")
                except Exception as e:
                    logger.error(f"Error processing websocket message: {e}")
                    
        except asyncio.CancelledError:
            logger.info(f"Websocket loop cancelled for {self.config.source.value}")
        except websockets.exceptions.ConnectionClosed:
            logger.warning(f"Websocket connection closed for {self.config.source.value}")
            
            # Auto-reconnect
            if self.status != DataFeedStatus.DISCONNECTED:
                self._set_status(DataFeedStatus.RECONNECTING)
                await asyncio.sleep(self.api_client.get("config", {}).get("reconnect_delay_seconds", 5))
                await self.connect()
        except Exception as e:
            logger.error(f"Error in websocket loop: {e}")
            self._set_status(DataFeedStatus.ERROR)
    
    async def _polling_loop(self):
        """Background task to poll REST API for updates."""
        logger.info(f"Polling loop started for {self.config.source.value}")
        
        try:
            while True:
                try:
                    # Poll for each symbol
                    for symbol in self.config.symbols:
                        await self._poll_symbol(symbol)
                        
                    # Update status
                    self._set_status(DataFeedStatus.CONNECTED)
                    self.last_update = datetime.now()
                    
                except Exception as e:
                    logger.error(f"Error polling data: {e}")
                    
                # Wait for next poll
                interval_seconds = self._get_interval_seconds()
                await asyncio.sleep(interval_seconds)
                
        except asyncio.CancelledError:
            logger.info(f"Polling loop cancelled for {self.config.source.value}")
    
    def _get_interval_seconds(self) -> int:
        """Get polling interval in seconds based on configured interval."""
        if self.config.interval == "1m":
            return 60
        elif self.config.interval == "5m":
            return 60 * 5
        elif self.config.interval == "15m":
            return 60 * 15
        elif self.config.interval == "30m":
            return 60 * 30
        elif self.config.interval == "1h":
            return 60 * 60
        elif self.config.interval == "4h":
            return 60 * 60 * 4
        else:  # 1d
            return 60 * 60 * 24
    
    async def _poll_symbol(self, symbol: str):
        """
        Poll for updates for a symbol.
        
        Args:
            symbol: Symbol to poll for
        """
        if not self.api_client:
            # Use simulated data
            self._update_simulated_data(symbol)
            return
        try:
            
            session = await self._get_session()
            
            # Build request based on source
            if self.config.source == DataSource.ALPHA_VANTAGE:
                url = f"{self.api_client['base_url']}/query"
                params = {
                    "function": "GLOBAL_QUOTE",
                    "symbol": symbol,
                    "apikey": self.api_client["api_key"]
                }
                
                async with session.get(url, params=params) as response:
                    response.raise_for_status()
                    data = await response.json()
                    
                    # Parse Alpha Vantage response
                    if "Global Quote" in data:
                        quote = data["Global Quote"]
                        
                        # Create data point
                        data_point = DataPoint(
                            symbol=symbol,
                            timestamp=datetime.now(),
                            data={
                                "open": float(quote.get("02. open", 0)),
                                "high": float(quote.get("03. high", 0)),
                                "low": float(quote.get("04. low", 0)),
                                "close": float(quote.get("05. price", 0)),
                                "volume": float(quote.get("06. volume", 0))
                            },
                            source=self.config.source
                        )
                        
                        # Update data
                        await self._update_data(data_point)
                        
            elif self.config.source == DataSource.POLYGON:
                url = f"{self.api_client['base_url']}/v2/aggs/ticker/{symbol}/prev"
                params = {
                    "apiKey": self.api_client["api_key"]
                }
                
                async with session.get(url, params=params) as response:
                    response.raise_for_status()
                    data = await response.json()
                    
                    # Parse Polygon response
                    if data.get("results"):
                        result = data["results"][0]
                        
                        # Create data point
                        data_point = DataPoint(
                            symbol=symbol,
                            timestamp=datetime.now(),
                            data={
                                "open": result.get("o", 0),
                                "high": result.get("h", 0),
                                "low": result.get("l", 0),
                                "close": result.get("c", 0),
                                "volume": result.get("v", 0)
                            },
                            source=self.config.source
                        )
                        
                        # Update data
                        await self._update_data(data_point)
                        
            else:
                # Use simulated data for unsupported sources
                self._update_simulated_data(symbol)
                
        except Exception as e:
            logger.error(f"Error polling data for {symbol}: {e}")
            self._update_simulated_data(symbol)
    
    def _update_simulated_data(self, symbol: str):
        """
        Update with simulated data.
        
        Args:
            symbol: Symbol to update
        """
        # Get last data point
        last_data = self.latest_data.get(symbol)
        
        if last_data:
            # Generate new data point based on last data
            last_close = last_data.data.get("close", 100)
            
            # Random price change
            price_change = np.random.normal(0, last_close * 0.005)
            new_close = max(0.001, last_close + price_change)
            
            # Generate OHLC
            new_high = max(new_close, last_close) + abs(np.random.normal(0, new_close * 0.002))
            new_low = min(new_close, last_close) - abs(np.random.normal(0, new_close * 0.002))
            new_open = last_close
            
            # Generate volume
            new_volume = max(100, np.random.normal(last_data.data.get("volume", 1000), 500))
            
            # Create data point
            data_point = DataPoint(
                symbol=symbol,
                timestamp=datetime.now(),
                data={
                    "open": new_open,
                    "high": new_high,
                    "low": new_low,
                    "close": new_close,
                    "volume": new_volume
                },
                source=DataSource.SIMULATED
            )
            
            # Update data
            asyncio.create_task(self._update_data(data_point))
        else:
            # No previous data, generate new data frame
            df = self._generate_simulated_data(symbol)
            
            if not df.empty:
                # Get latest row
                latest_row = df.iloc[-1]
                
                # Create data point
                data_point = DataPoint(
                    symbol=symbol,
                    timestamp=latest_row.name if isinstance(df.index, pd.DatetimeIndex) else datetime.now(),
                    data={col: latest_row[col] for col in df.columns},
                    source=DataSource.SIMULATED
                )
                
                # Update data
                asyncio.create_task(self._update_data(data_point))
    
    async def _process_polygon_message(self, data: Dict[str, Any]):
        """
        Process Polygon websocket message.
        
        Args:
            data: Message data
        """
        if isinstance(data, list):
            for item in data:
                if item.get("ev") == "AM" and item.get("sym") in self.config.symbols:
                    symbol = item.get("sym")
                    
                    # Create data point
                    data_point = DataPoint(
                        symbol=symbol,
                        timestamp=datetime.fromtimestamp(item.get("s") / 1000),
                        data={
                            "open": item.get("o", 0),
                            "high": item.get("h", 0),
                            "low": item.get("l", 0),
                            "close": item.get("c", 0),
                            "volume": item.get("v", 0)
                        },
                        source=self.config.source
                    )
                    
                    # Update data
                    await self._update_data(data_point)
    
    async def _process_binance_message(self, data: Dict[str, Any]):
        """
        Process Binance websocket message.
        
        Args:
            data: Message data
        """
        if "data" in data and "k" in data["data"]:
            kline = data["data"]["k"]
            symbol = data["data"]["s"]
            
            if symbol in self.config.symbols:
                # Create data point
                data_point = DataPoint(
                    symbol=symbol,
                    timestamp=datetime.fromtimestamp(kline.get("t") / 1000),
                    data={
                        "open": float(kline.get("o", 0)),
                        "high": float(kline.get("h", 0)),
                        "low": float(kline.get("l", 0)),
                        "close": float(kline.get("c", 0)),
                        "volume": float(kline.get("v", 0))
                    },
                    source=self.config.source
                )
                
                # Update data
                await self._update_data(data_point)
    
    async def _process_tradermade_message(self, data: Dict[str, Any]):
        """
        Process TraderMade websocket message.
        
        Args:
            data: Message data
        """
        if "symbol" in data and "bid" in data and "ask" in data:
            symbol = data["symbol"]
            
            if symbol in self.config.symbols:
                # Create data point
                bid = float(data.get("bid", 0))
                ask = float(data.get("ask", 0))
                
                data_point = DataPoint(
                    symbol=symbol,
                    timestamp=datetime.now(),
                    data={
                        "open": (bid + ask) / 2,
                        "high": ask,
                        "low": bid,
                        "close": (bid + ask) / 2,
                        "volume": 0,  # TraderMade doesn't provide volume
                        "bid": bid,
                        "ask": ask,
                        "spread": ask - bid
                    },
                    source=self.config.source
                )
                
                # Update data
                await self._update_data(data_point)
    
    async def _update_data(self, data_point: DataPoint):
        """
        Update data with a new data point.
        
        Args:
            data_point: New data point
        """
        # Validate data
        if not self.validator.validate(data_point):
            logger.warning(f"Invalid data point for {data_point.symbol}: {data_point.data}")
            return
            
        # Update latest data
        self.latest_data[data_point.symbol] = data_point
        self.last_update = datetime.now()
        
        # Update historical data
        if data_point.symbol in self.historical_data:
            # Create new row
            new_row = pd.Series(data_point.data, name=data_point.timestamp)
            
            # Append to dataframe
            self.historical_data[data_point.symbol] = pd.concat([
                self.historical_data[data_point.symbol],
                pd.DataFrame([new_row])
            ])
            
            # Remove duplicates
            self.historical_data[data_point.symbol] = self.historical_data[data_point.symbol].loc[
                ~self.historical_data[data_point.symbol].index.duplicated(keep='last')
            ]
            
            # Sort by timestamp
            self.historical_data[data_point.symbol] = self.historical_data[data_point.symbol].sort_index()
            
            # Limit to max bars
            if len(self.historical_data[data_point.symbol]) > self.config.max_history_bars:
                self.historical_data[data_point.symbol] = self.historical_data[data_point.symbol].tail(
                    self.config.max_history_bars
                )
        else:
            # Create new dataframe
            self.historical_data[data_point.symbol] = pd.DataFrame([pd.Series(
                data_point.data, name=data_point.timestamp
            )])
        
        # Call callbacks
        for callback in self.on_data_callbacks:
            try:
                callback(data_point)
            except Exception as e:
                logger.error(f"Error in data callback: {e}")
        
        # Generate event if event monitor is available
        if self.event_monitor:
            await self._generate_market_event(data_point)
    
    async def _generate_market_event(self, data_point: DataPoint):
        """
        Generate market event from data point.
        
        Args:
            data_point: Data point
        """
        # Only generate events for significant price changes
        last_data = self.latest_data.get(data_point.symbol)
        if not last_data or last_data == data_point:
            return
            
        # Calculate price change
        last_close = last_data.data.get("close", 0)
        current_close = data_point.data.get("close", 0)
        
        if last_close > 0:
            price_change_pct = (current_close - last_close) / last_close * 100
        else:
            price_change_pct = 0
            
        # Only generate events for significant changes
        if abs(price_change_pct) < 0.1:  # Less than 0.1% change
            return
            
        # Create event
        event_id = f"market_{data_point.symbol}_{int(time.time())}"
        
        # Determine priority based on price change
        if abs(price_change_pct) >= 1.0:
            priority = EventPriority.HIGH
        elif abs(price_change_pct) >= 0.5:
            priority = EventPriority.MEDIUM
        else:
            priority = EventPriority.LOW
            
        # Create event
        event = MarketEvent(
            id=event_id,
            type=EventType.MARKET,
            priority=priority,
            source=EventSource.PRICE_ACTION,
            timestamp=data_point.timestamp,
            description=f"{data_point.symbol} price {price_change_pct:.2f}% {'up' if price_change_pct > 0 else 'down'}",
            symbol=data_point.symbol,
            price=current_close,
            volume=data_point.data.get("volume"),
            timeframe=self.config.interval,
            previous_price=last_close,
            price_change_pct=price_change_pct
        )
        
        await self.event_monitor.add_event(event)
    
    def _set_status(self, status: DataFeedStatus):
        """
        Set data feed status.
        
        Args:
            status: New status
        """
        if self.status != status:
            self.status = status
            
            # Call callbacks
            for callback in self.on_status_change_callbacks:
                try:
                    callback(status)
                except Exception as e:
                    logger.error(f"Error in status change callback: {e}")
    
    def register_data_callback(self, callback: Callable[[DataPoint], None]):
        """
        Register callback for new data.
        
        Args:
            callback: Function to call when new data arrives
        """
        self.on_data_callbacks.append(callback)
    
    def register_status_callback(self, callback: Callable[[DataFeedStatus], None]):
        """
        Register callback for status changes.
        
        Args:
            callback: Function to call when status changes
        """
        self.on_status_change_callbacks.append(callback)
    
    def get_latest(self, symbol: str) -> Optional[DataPoint]:
        """
        Get latest data for a symbol.
        
        Args:
            symbol: Symbol to get data for
            
        Returns:
            Latest data point or None if not available
        """
        return self.latest_data.get(symbol)
    
    def get_historical(self, symbol: str) -> pd.DataFrame:
        """
        Get historical data for a symbol.
        
        Args:
            symbol: Symbol to get data for
            
        Returns:
            DataFrame with historical data
        """
        return self.historical_data.get(symbol, pd.DataFrame())
    
    async def close(self):
        """Close data feed and release resources."""
        await self.disconnect()
        
        # Close API session
        if self.api_client and "session" in self.api_client and self.api_client["session"]:
            await self.api_client["session"].close()
