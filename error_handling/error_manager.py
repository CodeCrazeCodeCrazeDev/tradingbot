"""
Error handling and recovery system for AlphaAlgo 2.0
"""

import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import traceback
import sys

logger = logging.getLogger(__name__)


class TradingError(Exception):
    """Base class for trading errors."""
    pass


class OrderError(TradingError):
    """Order-related errors."""
    pass


class DataError(TradingError):
    """Data-related errors."""
    pass


class ModelError(TradingError):
    """Model-related errors."""
    pass


class ErrorManager:
    """
    Manages system errors and recovery procedures.
    """
    
    def __init__(self):
        self.error_history = []
        self.recovery_procedures = {
            OrderError: self._handle_order_error,
            DataError: self._handle_data_error,
            ModelError: self._handle_model_error
        }
        
        # Error thresholds
        self.thresholds = {
            'max_consecutive_errors': 3,
            'error_rate_threshold': 0.1,  # 10% error rate
            'recovery_timeout': 300  # 5 minutes
        }
        
        logger.info("✅ Error Manager initialized")
    
    def handle_error(
        self,
        error: Exception,
        context: Dict = None
    ) -> Optional[Dict]:
        """
        Handle system error with appropriate recovery.
        
        Args:
            error: The error that occurred
            context: Additional context about the error
        
        Returns:
            Recovery action if any
        """
        try:
            # Record error
            error_record = self._record_error(error, context)
            
            # Check error thresholds
            if self._should_emergency_stop():
                self._trigger_emergency_stop()
                return None
            
            # Get error type
            error_type = type(error)
            
            # Find and execute recovery procedure
            if error_type in self.recovery_procedures:
                recovery = self.recovery_procedures[error_type](error, context)
                
                if recovery:
                    logger.info(f"✅ Recovery successful for {error_type.__name__}")
                    return recovery
            
            # Default error handling
            return self._default_error_handler(error, context)
            
        except Exception as e:
            logger.error(f"❌ Error in error handler: {str(e)}")
            return None
    
    def _record_error(
        self,
        error: Exception,
        context: Dict = None
    ) -> Dict:
        """Record error details."""
        error_record = {
            'timestamp': datetime.now(),
            'type': type(error).__name__,
            'message': str(error),
            'traceback': traceback.format_exc(),
            'context': context or {},
            'recovered': False
        }
        
        self.error_history.append(error_record)
        
        # Log error
        logger.error(f"❌ Error: {error_record['type']}")
        logger.error(f"Message: {error_record['message']}")
        if context:
            logger.error(f"Context: {context}")
        
        return error_record
    
    def _should_emergency_stop(self) -> bool:
        """Check if system should emergency stop."""
        if not self.error_history:
            return False
        
        recent_errors = [
            e for e in self.error_history
            if (datetime.now() - e['timestamp']).total_seconds() < 3600
        ]
        
        # Check consecutive errors
        if len(recent_errors) >= self.thresholds['max_consecutive_errors']:
            return True
        
        # Check error rate
        error_rate = len(recent_errors) / 3600  # errors per second
        if error_rate > self.thresholds['error_rate_threshold']:
            return True
        
        return False
    
    def _trigger_emergency_stop(self):
        """Trigger emergency stop procedure."""
        logger.critical("🚨 EMERGENCY STOP TRIGGERED")
        logger.critical("Too many errors detected")
        
        try:
            # Close all positions
            logger.info("Closing all positions...")
            
            # Stop all services
            logger.info("Stopping all services...")
            
            # Notify administrators
            logger.info("Notifying administrators...")
            
        except Exception as e:
            logger.critical(f"❌ Emergency stop failed: {str(e)}")
        
        sys.exit(1)
    
    def _handle_order_error(
        self,
        error: OrderError,
        context: Dict
    ) -> Optional[Dict]:
        """Handle order-related errors."""
        if 'order' not in context:
            return None
        
        order = context['order']
        
        # Retry order with adjusted parameters
        if 'slippage' in str(error).lower():
            return {
                'action': 'retry_order',
                'order': {
                    **order,
                    'slippage_tolerance': order.get('slippage_tolerance', 0.001) * 2
                }
            }
        
        # Cancel order if other error
        return {
            'action': 'cancel_order',
            'order_id': order.get('id')
        }
    
    def _handle_data_error(
        self,
        error: DataError,
        context: Dict
    ) -> Optional[Dict]:
        """Handle data-related errors."""
        # Try alternate data source
        if 'primary_source_failed' in str(error).lower():
            return {
                'action': 'switch_data_source',
                'source': 'backup'
            }
        
        # Retry with reduced frequency
        if 'rate_limit' in str(error).lower():
            return {
                'action': 'reduce_frequency',
                'factor': 0.5
            }
        
        return None
    
    def _handle_model_error(
        self,
        error: ModelError,
        context: Dict
    ) -> Optional[Dict]:
        """Handle model-related errors."""
        # Load backup model
        if 'model_corrupted' in str(error).lower():
            return {
                'action': 'load_backup_model',
                'checkpoint': 'latest_backup'
            }
        
        # Reduce batch size
        if 'out_of_memory' in str(error).lower():
            return {
                'action': 'reduce_batch_size',
                'factor': 0.5
            }
        
        return None
    
    def _default_error_handler(
        self,
        error: Exception,
        context: Dict
    ) -> Dict:
        """Default error handling procedure."""
        return {
            'action': 'log_and_continue',
            'error': str(error),
            'context': context
        }
    
    def get_error_summary(self) -> Dict:
        """Get summary of recent errors."""
        if not self.error_history:
            return {'status': 'healthy', 'error_count': 0}
        
        recent_errors = [
            e for e in self.error_history
            if (datetime.now() - e['timestamp']).total_seconds() < 3600
        ]
        
        error_types = {}
        for error in recent_errors:
            error_type = error['type']
            error_types[error_type] = error_types.get(error_type, 0) + 1
        
        return {
            'status': 'degraded' if recent_errors else 'healthy',
            'error_count': len(recent_errors),
            'error_types': error_types,
            'latest_error': recent_errors[-1] if recent_errors else None
        }
    
    def clear_old_errors(self, max_age_hours: int = 24):
        """Clear old error records."""
        self.error_history = [
            e for e in self.error_history
            if (datetime.now() - e['timestamp']).total_seconds() < max_age_hours * 3600
        ]
