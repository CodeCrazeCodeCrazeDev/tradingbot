import logging
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional
from pythonjsonlogger import jsonlogger


class StructuredLogFormatter(jsonlogger.JsonFormatter):
    """Custom JSON formatter for structured logging."""
    
    def add_fields(self, log_record: Dict[str, Any], record: logging.LogRecord, message_dict: Dict[str, Any]) -> None:
        super().add_fields(log_record, record, message_dict)
        
        # Add timestamp
        log_record['timestamp'] = datetime.utcnow().isoformat()
        
        # Add log level
        log_record['level'] = record.levelname
        
        # Add source information
        log_record['logger'] = record.name
        log_record['source'] = {
            'file': record.pathname,
            'line': record.lineno,
            'function': record.funcName
        }
        
        # Add environment info
        log_record['environment'] = 'production'
        log_record['service'] = 'trading-bot'


class TradingBotLogger:
    """Centralized logging configuration for Trading Bot."""
    
    def __init__(self, log_dir: str = 'logs', log_level: str = 'INFO'):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        self.log_level = getattr(logging, log_level.upper())
        self.loggers = {}
    
    def get_logger(self, name: str) -> logging.Logger:
        """Get or create a logger with the specified name."""
        if name in self.loggers:
            return self.loggers[name]
        
        logger = logging.getLogger(name)
        logger.setLevel(self.log_level)
        
        # Clear existing handlers
        logger.handlers.clear()
        
        # Add handlers
        logger.addHandler(self._create_console_handler())
        logger.addHandler(self._create_file_handler(name))
        logger.addHandler(self._create_json_file_handler(name))
        
        self.loggers[name] = logger
        return logger
    
    def _create_console_handler(self) -> logging.Handler:
        """Create console handler with colored output."""
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(self.log_level)
        
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        handler.setFormatter(formatter)
        return handler
    
    def _create_file_handler(self, name: str) -> logging.Handler:
        """Create plain text file handler."""
        log_file = self.log_dir / f'{name}.log'
        handler = logging.FileHandler(log_file)
        handler.setLevel(self.log_level)
        
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        handler.setFormatter(formatter)
        return handler
    
    def _create_json_file_handler(self, name: str) -> logging.Handler:
        """Create JSON structured log handler."""
        log_file = self.log_dir / f'{name}.json'
        handler = logging.FileHandler(log_file)
        handler.setLevel(self.log_level)
        
        formatter = StructuredLogFormatter()
        handler.setFormatter(formatter)
        return handler
    
    def create_audit_logger(self) -> logging.Logger:
        """Create specialized audit logger for compliance."""
        logger = logging.getLogger('trading_bot.audit')
        logger.setLevel(logging.INFO)
        
        # Audit log file
        audit_file = self.log_dir / 'audit.log'
        handler = logging.FileHandler(audit_file)
        handler.setLevel(logging.INFO)
        
        formatter = StructuredLogFormatter()
        handler.setFormatter(formatter)
        
        logger.addHandler(handler)
        return logger
    
    def create_trade_logger(self) -> logging.Logger:
        """Create specialized trade execution logger."""
        logger = logging.getLogger('trading_bot.trades')
        logger.setLevel(logging.INFO)
        
        # Trade log file
        trade_file = self.log_dir / 'trades.json'
        handler = logging.FileHandler(trade_file)
        handler.setLevel(logging.INFO)
        
        formatter = StructuredLogFormatter()
        handler.setFormatter(formatter)
        
        logger.addHandler(handler)
        return logger
    
    def create_risk_logger(self) -> logging.Logger:
        """Create specialized risk management logger."""
        logger = logging.getLogger('trading_bot.risk')
        logger.setLevel(logging.DEBUG)
        
        # Risk log file
        risk_file = self.log_dir / 'risk.json'
        handler = logging.FileHandler(risk_file)
        handler.setLevel(logging.DEBUG)
        
        formatter = StructuredLogFormatter()
        handler.setFormatter(formatter)
        
        logger.addHandler(handler)
        return logger


# Global logger instance
_logger_factory: Optional[TradingBotLogger] = None


def setup_logging(log_dir: str = 'logs', log_level: str = 'INFO') -> TradingBotLogger:
    """Initialize global logging configuration."""
    global _logger_factory
    _logger_factory = TradingBotLogger(log_dir, log_level)
    return _logger_factory


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance."""
    if _logger_factory is None:
        setup_logging()
    return _logger_factory.get_logger(name)


def log_trade(
    trade_id: str,
    symbol: str,
    side: str,
    quantity: float,
    price: float,
    pnl: Optional[float] = None,
    metadata: Optional[Dict] = None
) -> None:
    """Log a trade execution."""
    logger = get_logger('trades')
    
    log_data = {
        'event_type': 'trade_executed',
        'trade_id': trade_id,
        'symbol': symbol,
        'side': side,
        'quantity': quantity,
        'price': price,
        'pnl': pnl,
        'metadata': metadata or {}
    }
    
    logger.info('Trade executed', extra=log_data)


def log_signal(
    signal_id: str,
    symbol: str,
    direction: str,
    confidence: float,
    strategy: str,
    metadata: Optional[Dict] = None
) -> None:
    """Log a signal generation."""
    logger = get_logger('signals')
    
    log_data = {
        'event_type': 'signal_generated',
        'signal_id': signal_id,
        'symbol': symbol,
        'direction': direction,
        'confidence': confidence,
        'strategy': strategy,
        'metadata': metadata or {}
    }
    
    logger.info('Signal generated', extra=log_data)


def log_risk_event(
    event_type: str,
    details: Dict[str, Any],
    severity: str = 'info'
) -> None:
    """Log a risk management event."""
    logger = get_logger('risk')
    
    log_data = {
        'event_type': f'risk_{event_type}',
        'severity': severity,
        'details': details
    }
    
    if severity == 'warning':
        logger.warning(f'Risk event: {event_type}', extra=log_data)
    elif severity == 'error':
        logger.error(f'Risk event: {event_type}', extra=log_data)
    else:
        logger.info(f'Risk event: {event_type}', extra=log_data)


def log_audit(
    action: str,
    user: Optional[str] = None,
    resource: Optional[str] = None,
    details: Optional[Dict] = None
) -> None:
    """Log an audit event for compliance."""
    logger = _logger_factory.create_audit_logger() if _logger_factory else logging.getLogger('audit')
    
    log_data = {
        'event_type': 'audit',
        'action': action,
        'user': user,
        'resource': resource,
        'details': details or {}
    }
    
    logger.info(f'Audit: {action}', extra=log_data)
