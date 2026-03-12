"""
Bloomberg Terminal Data Bridge
Institutional-grade market data integration
"""

import asyncio
import logging
import numpy as np
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
import pandas as pd

logger = logging.getLogger(__name__)


@dataclass
class BloombergSecurity:
    """Bloomberg security identifier"""
    ticker: str
    yellow_key: str  # Equity, Curncy, Comdty, etc.
    exchange: Optional[str] = None
    

class BloombergBridge:
    """
    Bloomberg Terminal data bridge for institutional-grade data
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.connected = False
        
        try:
            # Try to import Bloomberg API
            import blpapi
            self.blpapi = blpapi
            self.session = None
            logger.info("Bloomberg API available")
        except ImportError:
            self.blpapi = None
            logger.warning("Bloomberg API not available. Using mock data.")
            
        # Connection settings
        self.host = self.config.get('host', 'localhost')
        self.port = self.config.get('port', 8194)
        
    async def connect(self) -> bool:
        """Connect to Bloomberg Terminal"""
        if self.blpapi is None:
            logger.warning("Bloomberg API not available")
            return False
        try:
            
            session_options = self.blpapi.SessionOptions()
            session_options.setServerHost(self.host)
            session_options.setServerPort(self.port)
            
            self.session = self.blpapi.Session(session_options)
            
            if not self.session.start():
                logger.error("Failed to start Bloomberg session")
                return False
                
            if not self.session.openService("//blp/refdata"):
                logger.error("Failed to open Bloomberg service")
                return False
                
            self.connected = True
            logger.info("Connected to Bloomberg Terminal")
            return True
            
        except Exception as e:
            logger.error(f"Bloomberg connection failed: {e}")
            return False
            
    async def get_reference_data(self, securities: List[BloombergSecurity], 
                                fields: List[str]) -> pd.DataFrame:
        """
        Get reference data from Bloomberg
        
        Args:
            securities: List of Bloomberg securities
            fields: Bloomberg fields (e.g., 'PX_LAST', 'VOLUME', 'MARKET_CAP')
        """
        if not self.connected:
            return self._mock_reference_data(securities, fields)
        try:
            
            service = self.session.getService("//blp/refdata")
            request = service.createRequest("ReferenceDataRequest")
            
            # Add securities
            for security in securities:
                request.append("securities", f"{security.ticker} {security.yellow_key}")
                
            # Add fields
            for field in fields:
                request.append("fields", field)
                
            # Send request
            self.session.sendRequest(request)
            
            # Process response
            data = []
            while True:
                event = self.session.nextEvent(500)
                
                if event.eventType() == self.blpapi.Event.RESPONSE or \
                   event.eventType() == self.blpapi.Event.PARTIAL_RESPONSE:
                    
                    for msg in event:
                        security_data = msg.getElement("securityData")
                        
                        for i in range(security_data.numValues()):
                            sec = security_data.getValueAsElement(i)
                            ticker = sec.getElementAsString("security")
                            
                            field_data = sec.getElement("fieldData")
                            row = {'security': ticker}
                            
                            for field in fields:
                                if field_data.hasElement(field):
                                    row[field] = field_data.getElementAsFloat(field)
                                else:
                                    row[field] = None
                                    
                            data.append(row)
                            
                if event.eventType() == self.blpapi.Event.RESPONSE:
                    break
                    
            return pd.DataFrame(data)
            
        except Exception as e:
            logger.error(f"Bloomberg reference data request failed: {e}")
            return self._mock_reference_data(securities, fields)
            
    async def get_historical_data(self, security: BloombergSecurity, 
                                 fields: List[str], start_date: str, 
                                 end_date: str) -> pd.DataFrame:
        """
        Get historical data from Bloomberg
        
        Args:
            security: Bloomberg security
            fields: Bloomberg fields
            start_date: Start date (YYYYMMDD)
            end_date: End date (YYYYMMDD)
        """
        if not self.connected:
            return self._mock_historical_data(security, fields, start_date, end_date)
        try:
            
            service = self.session.getService("//blp/refdata")
            request = service.createRequest("HistoricalDataRequest")
            
            request.append("securities", f"{security.ticker} {security.yellow_key}")
            
            for field in fields:
                request.append("fields", field)
                
            request.set("startDate", start_date)
            request.set("endDate", end_date)
            
            self.session.sendRequest(request)
            
            # Process response
            data = []
            while True:
                event = self.session.nextEvent(500)
                
                if event.eventType() == self.blpapi.Event.RESPONSE or \
                   event.eventType() == self.blpapi.Event.PARTIAL_RESPONSE:
                    
                    for msg in event:
                        security_data = msg.getElement("securityData")
                        field_data = security_data.getElement("fieldData")
                        
                        for i in range(field_data.numValues()):
                            point = field_data.getValueAsElement(i)
                            row = {'date': point.getElementAsDatetime("date")}
                            
                            for field in fields:
                                if point.hasElement(field):
                                    row[field] = point.getElementAsFloat(field)
                                else:
                                    row[field] = None
                                    
                            data.append(row)
                            
                if event.eventType() == self.blpapi.Event.RESPONSE:
                    break
                    
            df = pd.DataFrame(data)
            df['date'] = pd.to_datetime(df['date'])
            df.set_index('date', inplace=True)
            
            return df
            
        except Exception as e:
            logger.error(f"Bloomberg historical data request failed: {e}")
            return self._mock_historical_data(security, fields, start_date, end_date)
            
    async def subscribe_realtime(self, securities: List[BloombergSecurity], 
                                fields: List[str], callback: callable):
        """
        Subscribe to real-time data from Bloomberg
        """
        if not self.connected:
            logger.warning("Not connected to Bloomberg")
            return
        try:
            
            subscriptions = self.blpapi.SubscriptionList()
            
            for security in securities:
                security_str = f"{security.ticker} {security.yellow_key}"
                field_str = ",".join(fields)
                subscriptions.add(security_str, field_str, "", 
                                self.blpapi.CorrelationId(security.ticker))
                
            self.session.subscribe(subscriptions)
            
            # Process events
            while True:
                event = self.session.nextEvent()
                
                if event.eventType() == self.blpapi.Event.SUBSCRIPTION_DATA:
                    for msg in event:
                        ticker = msg.correlationIds()[0].value()
                        
                        data = {'ticker': ticker, 'timestamp': datetime.now()}
                        
                        for field in fields:
                            if msg.hasElement(field):
                                data[field] = msg.getElementAsFloat(field)
                                
                        await callback(data)
                        
        except Exception as e:
            logger.error(f"Bloomberg subscription failed: {e}")
            
    def _mock_reference_data(self, securities: List[BloombergSecurity], 
                            fields: List[str]) -> pd.DataFrame:
        """Mock reference data for testing"""
        
        data = []
        for security in securities:
            row = {'security': f"{security.ticker} {security.yellow_key}"}
            
            for field in fields:
                if field == 'PX_LAST':
                    row[field] = np.random.uniform(50, 200)
                elif field == 'VOLUME':
                    row[field] = np.random.uniform(1e6, 1e8)
                elif field == 'MARKET_CAP':
                    row[field] = np.random.uniform(1e9, 1e12)
                else:
                    row[field] = np.random.random()
                    
            data.append(row)
            
        return pd.DataFrame(data)
        
    def _mock_historical_data(self, security: BloombergSecurity, 
                             fields: List[str], start_date: str, 
                             end_date: str) -> pd.DataFrame:
        """Mock historical data for testing"""
        
        dates = pd.date_range(start=start_date, end=end_date, freq='D')
        data = {'date': dates}
        
        for field in fields:
            if field == 'PX_LAST':
                # Random walk
                returns = np.random.normal(0.0001, 0.02, len(dates))
                prices = 100 * np.exp(np.cumsum(returns))
                data[field] = prices
            elif field == 'VOLUME':
                data[field] = np.random.uniform(1e6, 1e8, len(dates))
            else:
                data[field] = np.random.random(len(dates))
                
        df = pd.DataFrame(data)
        df.set_index('date', inplace=True)
        
        return df
        
    async def disconnect(self):
        """Disconnect from Bloomberg"""
        if self.session is not None:
            self.session.stop()
            self.connected = False
            logger.info("Disconnected from Bloomberg")
