"""
Phase 4: Continuous Data Validation
Cross-checks all incoming internet data for integrity
"""

import logging
import json
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
import numpy as np
from dataclasses import field
import asyncio
import numpy

logger = logging.getLogger(__name__)


class DataIntegrity(Enum):
    """Data integrity status"""
    VALID = "valid"
    SUSPECT = "suspect"
    INVALID = "invalid"
    QUARANTINED = "quarantined"


@dataclass
class ValidationResult:
    """Result of data validation"""
    data_type: str
    source: str
    integrity: DataIntegrity
    timestamp: datetime
    issues: List[str]
    replacement_attempted: bool = False
    replacement_successful: bool = False


class DataValidator:
    """
    Validates all incoming internet data for integrity and consistency.
    """
    
    def __init__(self, config: Dict):
        self.config = config
        
        # Validation thresholds
        self.price_change_threshold = config.get('price_change_threshold', 0.10)  # 10%
        self.max_data_age_seconds = config.get('max_data_age', 300)  # 5 minutes
        
        # Quarantine storage
        self.quarantined_data: List[Dict] = []
        
        # Validation history
        self.validation_history: List[ValidationResult] = []
        
        # Data providers for replacement
        self.data_providers = config.get('data_providers', {})
        
        logger.info("Data Validator initialized")
    
    async def validate_market_data(self, data: Dict, source: str) -> ValidationResult:
        """
        Validate market data (OHLCV).
        """
        issues = []
        
        try:
            # Check 1: Missing timestamps
            if 'timestamp' not in data and 'time' not in data:
                issues.append("Missing timestamp")
            else:
                timestamp = data.get('timestamp') or data.get('time')
                
                # Check if timestamp is recent
                if isinstance(timestamp, str):
                    try:
                        dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                        age = (datetime.now() - dt).total_seconds()
                        
                        if age > self.max_data_age_seconds:
                            issues.append(f"Stale data (age: {age:.0f}s)")
                    except Exception:
                        issues.append("Invalid timestamp format")
            
            # Check 2: Invalid price values
            price_fields = ['open', 'high', 'low', 'close', 'price']
            for field in price_fields:
                if field in data:
                    price = data[field]
                    
                    if not isinstance(price, (int, float)):
                        issues.append(f"Invalid {field} type: {type(price)}")
                    elif price <= 0:
                        issues.append(f"Invalid {field} value: {price}")
                    elif np.isnan(price) or np.isinf(price):
                        issues.append(f"Invalid {field}: NaN or Inf")
            
            # Check 3: OHLC consistency
            if all(k in data for k in ['open', 'high', 'low', 'close']):
                o, h, l, c = data['open'], data['high'], data['low'], data['close']
                
                if h < max(o, c) or h < l:
                    issues.append("High price inconsistent")
                
                if l > min(o, c) or l > h:
                    issues.append("Low price inconsistent")
            
            # Check 4: Extreme price changes
            if 'close' in data and hasattr(self, 'last_close'):
                price_change = abs(data['close'] - self.last_close) / self.last_close
                
                if price_change > self.price_change_threshold:
                    issues.append(f"Extreme price change: {price_change:.2%}")
            
            # Check 5: Volume validation
            if 'volume' in data:
                volume = data['volume']
                
                if not isinstance(volume, (int, float)):
                    issues.append(f"Invalid volume type: {type(volume)}")
                elif volume < 0:
                    issues.append(f"Negative volume: {volume}")
            
            # Determine integrity
            if len(issues) == 0:
                integrity = DataIntegrity.VALID
            elif len(issues) <= 2:
                integrity = DataIntegrity.SUSPECT
            else:
                integrity = DataIntegrity.INVALID
            
            # Store last close for next validation
            if 'close' in data and integrity == DataIntegrity.VALID:
                self.last_close = data['close']
        
        except Exception as e:
            logger.error(f"Error validating market data: {e}")
            issues.append(f"Validation error: {str(e)}")
            integrity = DataIntegrity.INVALID
        
        result = ValidationResult(
            data_type='market_data',
            source=source,
            integrity=integrity,
            timestamp=datetime.now(),
            issues=issues
        )
        
        self.validation_history.append(result)
        
        if integrity != DataIntegrity.VALID:
            logger.warning(f"⚠️ Market data validation: {integrity.value}")
            for issue in issues:
                logger.warning(f"   - {issue}")
        
        return result
    
    async def validate_news_data(self, data: Dict, source: str) -> ValidationResult:
        """
        Validate news data.
        """
        issues = []
        
        try:
            # Check 1: Required fields
            required_fields = ['title', 'publishedAt']
            for field in required_fields:
                if field not in data:
                    issues.append(f"Missing required field: {field}")
            
            # Check 2: Timestamp validation
            if 'publishedAt' in data:
                try:
                    pub_time = datetime.fromisoformat(data['publishedAt'].replace('Z', '+00:00'))
                    age = (datetime.now() - pub_time).total_seconds()
                    
                    if age > 86400:  # 24 hours
                        issues.append(f"Old news (age: {age/3600:.1f}h)")
                except Exception:
                    issues.append("Invalid publishedAt format")
            
            # Check 3: Content validation
            if 'title' in data:
                title = data['title']
                
                if not isinstance(title, str):
                    issues.append("Invalid title type")
                elif len(title) < 10:
                    issues.append("Title too short")
            
            # Check 4: Source validation
            if 'source' in data:
                if not isinstance(data['source'], dict):
                    issues.append("Invalid source format")
            
            # Determine integrity
            if len(issues) == 0:
                integrity = DataIntegrity.VALID
            elif len(issues) <= 1:
                integrity = DataIntegrity.SUSPECT
            else:
                integrity = DataIntegrity.INVALID
        
        except Exception as e:
            logger.error(f"Error validating news data: {e}")
            issues.append(f"Validation error: {str(e)}")
            integrity = DataIntegrity.INVALID
        
        result = ValidationResult(
            data_type='news',
            source=source,
            integrity=integrity,
            timestamp=datetime.now(),
            issues=issues
        )
        
        self.validation_history.append(result)
        
        return result
    
    async def validate_sentiment_data(self, data: Dict, source: str) -> ValidationResult:
        """
        Validate sentiment data.
        """
        issues = []
        
        try:
            # Check 1: Sentiment score range
            if 'score' in data:
                score = data['score']
                
                if not isinstance(score, (int, float)):
                    issues.append(f"Invalid score type: {type(score)}")
                elif not (-1.0 <= score <= 1.0):
                    issues.append(f"Score out of range: {score}")
            else:
                issues.append("Missing sentiment score")
            
            # Check 2: Volume/count validation
            if 'volume' in data:
                volume = data['volume']
                
                if not isinstance(volume, (int, float)):
                    issues.append("Invalid volume type")
                elif volume < 0:
                    issues.append(f"Negative volume: {volume}")
            
            # Check 3: Symbol validation
            if 'symbol' in data:
                symbol = data['symbol']
                
                if not isinstance(symbol, str):
                    issues.append("Invalid symbol type")
                elif len(symbol) < 3:
                    issues.append("Invalid symbol format")
            
            # Determine integrity
            if len(issues) == 0:
                integrity = DataIntegrity.VALID
            elif len(issues) == 1:
                integrity = DataIntegrity.SUSPECT
            else:
                integrity = DataIntegrity.INVALID
        
        except Exception as e:
            logger.error(f"Error validating sentiment data: {e}")
            issues.append(f"Validation error: {str(e)}")
            integrity = DataIntegrity.INVALID
        
        result = ValidationResult(
            data_type='sentiment',
            source=source,
            integrity=integrity,
            timestamp=datetime.now(),
            issues=issues
        )
        
        self.validation_history.append(result)
        
        return result
    
    async def validate_json_structure(self, data: Any, source: str) -> ValidationResult:
        """
        Validate JSON structure and decoding.
        """
        issues = []
        
        try:
            # Check if data is valid JSON-serializable
            if data is None:
                issues.append("Data is None")
            
            # Try to serialize
            try:
                json.dumps(data)
            except (TypeError, ValueError) as e:
                issues.append(f"JSON serialization error: {str(e)}")
            
            # Check for common JSON issues
            if isinstance(data, dict):
                # Check for empty dict
                if len(data) == 0:
                    issues.append("Empty data dictionary")
                
                # Check for error fields
                if 'error' in data:
                    issues.append(f"Error in response: {data['error']}")
            
            # Determine integrity
            integrity = DataIntegrity.VALID if len(issues) == 0 else DataIntegrity.INVALID
        
        except Exception as e:
            logger.error(f"Error validating JSON: {e}")
            issues.append(f"Validation error: {str(e)}")
            integrity = DataIntegrity.INVALID
        
        result = ValidationResult(
            data_type='json',
            source=source,
            integrity=integrity,
            timestamp=datetime.now(),
            issues=issues
        )
        
        return result
    
    async def quarantine_data(self, data: Any, source: str, reason: str):
        """
        Quarantine suspect data.
        """
        logger.warning(f"🚨 Quarantining data from {source}: {reason}")
        
        quarantine_entry = {
            'timestamp': datetime.now().isoformat(),
            'source': source,
            'reason': reason,
            'data': data
        }
        
        self.quarantined_data.append(quarantine_entry)
        
        # Keep only last 1000 quarantined items
        if len(self.quarantined_data) > 1000:
            self.quarantined_data = self.quarantined_data[-1000:]
    
    async def get_replacement_data(self, data_type: str, source: str) -> Optional[Any]:
        """
        Get replacement data from another provider.
        """
        logger.info(f"🔄 Getting replacement data for {data_type} from alternate source")
        
        try:
            # Get list of providers for this data type
            providers = self.data_providers.get(data_type, [])
            
            # Remove the failed source
            alternate_providers = [p for p in providers if p != source]
            
            if not alternate_providers:
                logger.error(f"No alternate providers for {data_type}")
                return None
            
            # Try first alternate provider
            alternate_source = alternate_providers[0]
            logger.info(f"Trying alternate source: {alternate_source}")
            
            # Fetch from alternate source
            # (Implementation depends on data type and provider)
            # This is a placeholder
            
            return None  # Would return actual data
        
        except Exception as e:
            logger.error(f"Error getting replacement data: {e}")
            return None
    
    async def validate_and_replace(
        self,
        data: Any,
        data_type: str,
        source: str
    ) -> Tuple[ValidationResult, Optional[Any]]:
        """
        Validate data and replace if invalid.
        Returns (validation_result, replacement_data)
        """
        # Validate based on data type
        if data_type == 'market_data':
            result = await self.validate_market_data(data, source)
        elif data_type == 'news':
            result = await self.validate_news_data(data, source)
        elif data_type == 'sentiment':
            result = await self.validate_sentiment_data(data, source)
        else:
            result = await self.validate_json_structure(data, source)
        
        # If invalid, quarantine and get replacement
        if result.integrity == DataIntegrity.INVALID:
            await self.quarantine_data(data, source, ', '.join(result.issues))
            
            replacement = await self.get_replacement_data(data_type, source)
            result.replacement_attempted = True
            result.replacement_successful = replacement is not None
            
            return result, replacement
        
        return result, None
    
    def get_validation_stats(self) -> Dict:
        """Get validation statistics"""
        if not self.validation_history:
            return {'status': 'No validations performed'}
        
        recent = self.validation_history[-100:]
        
        valid_count = sum(1 for r in recent if r.integrity == DataIntegrity.VALID)
        suspect_count = sum(1 for r in recent if r.integrity == DataIntegrity.SUSPECT)
        invalid_count = sum(1 for r in recent if r.integrity == DataIntegrity.INVALID)
        
        return {
            'total_validations': len(recent),
            'valid': valid_count,
            'suspect': suspect_count,
            'invalid': invalid_count,
            'valid_pct': (valid_count / len(recent)) * 100,
            'quarantined_items': len(self.quarantined_data),
            'recent_issues': [
                {
                    'data_type': r.data_type,
                    'source': r.source,
                    'integrity': r.integrity.value,
                    'issues': r.issues
                }
                for r in recent[-10:] if r.integrity != DataIntegrity.VALID
            ]
        }
