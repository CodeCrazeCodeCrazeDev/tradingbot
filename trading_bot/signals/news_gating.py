"""News Gating - Embargo Periods [HI-ANA-013]"""
import logging
from datetime import datetime, timedelta
from typing import List, Tuple

logger = logging.getLogger(__name__)

class NewsGating:
    def __init__(self, pre_minutes: int = 5, post_minutes: int = 15):
        try:
            self.pre_minutes = pre_minutes
            self.post_minutes = post_minutes
            self.embargo_periods: List[Tuple[datetime, datetime]] = []
            self.high_impact_events = {}
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
        
    def add_embargo(self, event_time: datetime, event_name: str = "", 
                   pre_min: int = None, post_min: int = None):
        """Add embargo around news event"""
        try:
            pre = pre_min or self.pre_minutes
            post = post_min or self.post_minutes
            start = event_time - timedelta(minutes=pre)
            end = event_time + timedelta(minutes=post)
            self.embargo_periods.append((start, end))
            logger.info(f"Added embargo for {event_name}: {start} to {end}")
        except Exception as e:
            logger.error(f"Error in add_embargo: {e}")
            raise
    
    def is_trading_allowed(self, check_time: datetime = None) -> bool:
        """Check if trading allowed at time"""
        try:
            check_time = check_time or datetime.now()
            for start, end in self.embargo_periods:
                if start <= check_time <= end:
                    logger.warning(f"Trading blocked: news embargo active")
                    return False
            return True
        except Exception as e:
            logger.error(f"Error in is_trading_allowed: {e}")
            raise
    
    def get_next_embargo(self) -> Tuple[datetime, datetime]:
        """Get next upcoming embargo period"""
        try:
            now = datetime.now()
            future_embargos = [(s, e) for s, e in self.embargo_periods if s > now]
            return min(future_embargos) if future_embargos else (None, None)
        except Exception as e:
            logger.error(f"Error in get_next_embargo: {e}")
            raise
    
    def clear_old_embargos(self):
        """Remove past embargo periods"""
        try:
            now = datetime.now()
            self.embargo_periods = [(s, e) for s, e in self.embargo_periods if e > now]
        except Exception as e:
            logger.error(f"Error in clear_old_embargos: {e}")
            raise
    
    def should_gate_trading(self, news_event: dict) -> tuple:
        """
        Determine if trading should be gated based on news event
        
        Args:
            news_event: Dictionary with news event details (impact, event, timestamp, etc.)
            
        Returns:
            tuple: (should_gate, reason)
        """
        try:
            impact = news_event.get('impact', 'LOW')
            event_name = news_event.get('event', 'Unknown')
        
            if impact == 'HIGH':
                return True, f"High-impact news: {event_name}"
            elif impact == 'MEDIUM':
                return False, "Medium-impact news - proceed with caution"
            else:
                return False, "Low-impact news"
        except Exception as e:
            logger.error(f"Error in should_gate_trading: {e}")
            raise
