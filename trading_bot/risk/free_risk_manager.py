"""
Free Risk Management System ($0 Budget)
Uses only free libraries and mock implementations
"""

import numpy as np
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime
import hashlib
import json


import logging

logger = logging.getLogger(__name__)

@dataclass
class FreeCounterpartyRisk:
    """Free counterparty risk assessment using public data"""
    counterparty_id: str
    credit_score: float
    exposure: float
    risk_rating: str
    last_updated: datetime


class FreeEncryption:
    """Free encryption using standard Python hashlib"""
    
    def __init__(self):
        try:
            self.algorithm = "SHA256"  # Free, built-in
        except Exception as e:
            import logging as _log
            _log.getLogger(__name__).error(f"Error in __init__: {e}")
            raise
        
    def encrypt_trade_data(self, data: Dict) -> str:
        """Encrypt trade data using SHA256"""
        try:
            data_str = json.dumps(data, sort_keys=True)
            encrypted = hashlib.sha256(data_str.encode()).hexdigest()
            return encrypted
        except Exception as e:
            import logging as _log
            _log.getLogger(__name__).error(f"Error in encrypt_trade_data: {e}")
            raise
    
    def hash_api_key(self, api_key: str) -> str:
        """Hash API keys for secure storage"""
        return hashlib.sha256(api_key.encode()).hexdigest()


class FreeCounterpartyScorer:
    """Free counterparty risk scoring using public metrics"""
    
    def __init__(self):
        try:
            self.counterparties: Dict[str, FreeCounterpartyRisk] = {}
        except Exception as e:
            import logging as _log
            _log.getLogger(__name__).error(f"Error in __init__: {e}")
            raise
        
    def assess_counterparty(
        self,
        counterparty_id: str,
        public_data: Dict
    ) -> FreeCounterpartyRisk:
        """Assess counterparty using free public data"""
        
        # Use free public metrics
        try:
            market_cap = public_data.get('market_cap', 1e9)
            volume = public_data.get('daily_volume', 1e6)
            age_days = public_data.get('age_days', 365)
        
            # Simple scoring (0-1)
            cap_score = min(market_cap / 1e10, 1.0)  # Normalize to $10B
            volume_score = min(volume / 1e8, 1.0)  # Normalize to $100M
            age_score = min(age_days / 1825, 1.0)  # Normalize to 5 years
        
            credit_score = (cap_score + volume_score + age_score) / 3
        
            # Assign rating
            if credit_score >= 0.8:
                rating = 'A'
            elif credit_score >= 0.6:
                rating = 'B'
            elif credit_score >= 0.4:
                rating = 'C'
            else:
                rating = 'D'
        
            risk = FreeCounterpartyRisk(
                counterparty_id=counterparty_id,
                credit_score=credit_score,
                exposure=public_data.get('exposure', 0),
                risk_rating=rating,
                last_updated=datetime.now()
            )
        
            self.counterparties[counterparty_id] = risk
            return risk
        except Exception as e:
            import logging as _log
            _log.getLogger(__name__).error(f"Error in assess_counterparty: {e}")
            raise


class FreeBlackSwanDetector:
    """Free black swan detection using public market data"""
    
    def __init__(self):
        try:
            self.alerts: List[Dict] = []
        except Exception as e:
            import logging as _log
            _log.getLogger(__name__).error(f"Error in __init__: {e}")
            raise
        
    def detect_market_stress(self, market_data: Dict) -> List[Dict]:
        """Detect market stress using free indicators"""
        
        try:
            alerts = []
        
            # VIX proxy (use price volatility)
            if 'prices' in market_data:
                prices = np.array(market_data['prices'])
                returns = np.diff(prices) / prices[:-1]
                volatility = np.std(returns) * np.sqrt(252)
            
                if volatility > 0.30:  # 30% annualized
                    alerts.append({
                        'type': 'high_volatility',
                        'severity': 'high',
                        'value': volatility,
                        'threshold': 0.30
                    })
        
            # Volume spike detection
            if 'volumes' in market_data:
                volumes = np.array(market_data['volumes'])
                avg_volume = np.mean(volumes[-20:])  # 20-period average
                current_volume = volumes[-1]
            
                if current_volume > avg_volume * 3:  # 3x average
                    alerts.append({
                        'type': 'volume_spike',
                        'severity': 'medium',
                        'value': current_volume / avg_volume,
                        'threshold': 3.0
                    })
        
            # Price gap detection
            if 'prices' in market_data and len(market_data['prices']) > 1:
                prices = market_data['prices']
                gap = abs(prices[-1] - prices[-2]) / prices[-2]
            
                if gap > 0.05:  # 5% gap
                    alerts.append({
                        'type': 'price_gap',
                        'severity': 'high',
                        'value': gap,
                        'threshold': 0.05
                    })
        
            self.alerts.extend(alerts)
            return alerts
        except Exception as e:
            import logging as _log
            _log.getLogger(__name__).error(f"Error in detect_market_stress: {e}")
            raise
    
    def get_hedge_recommendation(self, alerts: List[Dict]) -> Dict:
        """Get free hedging recommendations"""
        
        try:
            if not alerts:
                return {'action': 'none', 'reason': 'no_alerts'}
        
            high_severity = [a for a in alerts if a['severity'] == 'high']
        
            if high_severity:
                return {
                    'action': 'reduce_exposure',
                    'percentage': 0.5,  # Reduce by 50%
                    'reason': f"{len(high_severity)} high severity alerts",
                    'cost': 0  # Free action
                }
        
            return {
                'action': 'monitor',
                'reason': 'medium severity alerts',
                'cost': 0
            }
        except Exception as e:
            import logging as _log
            _log.getLogger(__name__).error(f"Error in get_hedge_recommendation: {e}")
            raise


class FreeComplianceChecker:
    """Free compliance checking using public rules"""
    
    def __init__(self):
        try:
            self.rules = {
                'max_position_size': 0.10,  # 10% of portfolio
                'max_leverage': 3.0,
                'max_daily_trades': 10,
                'min_account_balance': 1000
            }
            self.violations: List[Dict] = []
        except Exception as e:
            import logging as _log
            _log.getLogger(__name__).error(f"Error in __init__: {e}")
            raise
        
    def check_trade_compliance(
        self,
        trade: Dict,
        account: Dict
    ) -> Dict:
        """Check trade compliance with free rules"""
        
        try:
            violations = []
        
            # Position size check
            position_size = trade.get('size', 0)
            account_value = account.get('balance', 1)
            position_pct = position_size / account_value
        
            if position_pct > self.rules['max_position_size']:
                violations.append({
                    'rule': 'max_position_size',
                    'limit': self.rules['max_position_size'],
                    'actual': position_pct
                })
        
            # Leverage check
            leverage = trade.get('leverage', 1.0)
            if leverage > self.rules['max_leverage']:
                violations.append({
                    'rule': 'max_leverage',
                    'limit': self.rules['max_leverage'],
                    'actual': leverage
                })
        
            # Daily trades check
            daily_trades = account.get('daily_trades', 0)
            if daily_trades >= self.rules['max_daily_trades']:
                violations.append({
                    'rule': 'max_daily_trades',
                    'limit': self.rules['max_daily_trades'],
                    'actual': daily_trades
                })
        
            # Account balance check
            if account_value < self.rules['min_account_balance']:
                violations.append({
                    'rule': 'min_account_balance',
                    'limit': self.rules['min_account_balance'],
                    'actual': account_value
                })
        
            self.violations.extend(violations)
        
            return {
                'compliant': len(violations) == 0,
                'violations': violations,
                'timestamp': datetime.now()
            }
        except Exception as e:
            import logging as _log
            _log.getLogger(__name__).error(f"Error in check_trade_compliance: {e}")
            raise


class FreeRiskManager:
    """Free unified risk management system"""
    
    def __init__(self):
        try:
            self.encryption = FreeEncryption()
            self.counterparty_scorer = FreeCounterpartyScorer()
            self.black_swan_detector = FreeBlackSwanDetector()
            self.compliance_checker = FreeComplianceChecker()
        except Exception as e:
            import logging as _log
            _log.getLogger(__name__).error(f"Error in __init__: {e}")
            raise
        
    def assess_trade_risk(
        self,
        trade: Dict,
        account: Dict,
        market_data: Dict
    ) -> Dict:
        """Comprehensive free risk assessment"""
        
        # 1. Encrypt sensitive data
        try:
            trade_hash = self.encryption.encrypt_trade_data(trade)
        
            # 2. Check counterparty (if applicable)
            counterparty_risk = None
            if 'counterparty' in trade:
                counterparty_risk = self.counterparty_scorer.assess_counterparty(
                    trade['counterparty'],
                    trade.get('counterparty_data', {})
                )
        
            # 3. Detect black swan risks
            black_swan_alerts = self.black_swan_detector.detect_market_stress(market_data)
            hedge_recommendation = self.black_swan_detector.get_hedge_recommendation(black_swan_alerts)
        
            # 4. Check compliance
            compliance = self.compliance_checker.check_trade_compliance(trade, account)
        
            # 5. Calculate overall risk score
            risk_factors = []
        
            if counterparty_risk:
                risk_factors.append(1 - counterparty_risk.credit_score)
        
            if black_swan_alerts:
                risk_factors.append(len(black_swan_alerts) / 10)
        
            if not compliance['compliant']:
                risk_factors.append(len(compliance['violations']) / 5)
        
            overall_risk = np.mean(risk_factors) if risk_factors else 0
        
            # 6. Recommendation
            if overall_risk > 0.7:
                recommendation = 'REJECT'
            elif overall_risk > 0.5:
                recommendation = 'REDUCE_SIZE'
            elif overall_risk > 0.3:
                recommendation = 'PROCEED_WITH_CAUTION'
            else:
                recommendation = 'PROCEED'
        
            return {
                'risk_score': overall_risk,
                'trade_hash': trade_hash,
                'counterparty_risk': counterparty_risk,
                'black_swan_alerts': black_swan_alerts,
                'hedge_recommendation': hedge_recommendation,
                'compliance': compliance,
                'recommendation': recommendation,
                'cost': 0,  # $0 budget
                'timestamp': datetime.now()
            }
        except Exception as e:
            import logging as _log
            _log.getLogger(__name__).error(f"Error in assess_trade_risk: {e}")
            raise
    
    def get_risk_report(self) -> Dict:
        """Generate free risk report"""
        
        return {
            'total_counterparties': len(self.counterparty_scorer.counterparties),
            'total_alerts': len(self.black_swan_detector.alerts),
            'total_violations': len(self.compliance_checker.violations),
            'avg_credit_score': np.mean([
                cp.credit_score 
                for cp in self.counterparty_scorer.counterparties.values()
            ]) if self.counterparty_scorer.counterparties else 0,
            'timestamp': datetime.now()
        }


# Example usage
if __name__ == '__main__':
    # Initialize free risk manager
    risk_manager = FreeRiskManager()
    
    # Test trade
    trade = {
        'symbol': 'BTCUSD',
        'size': 1000,
        'leverage': 2.0,
        'counterparty': 'exchange_a',
        'counterparty_data': {
            'market_cap': 5e9,
            'daily_volume': 1e8,
            'age_days': 1000
        }
    }
    
    account = {
        'balance': 10000,
        'daily_trades': 3
    }
    
    market_data = {
        'prices': [50000, 49000, 48000, 47000, 46000],
        'volumes': [1e6, 1.2e6, 1.5e6, 5e6, 1.1e6]  # Volume spike
    }
    
    # Assess risk
    result = risk_manager.assess_trade_risk(trade, account, market_data)
    
    print("Free Risk Assessment:")
    print(f"Risk Score: {result['risk_score']:.2%}")
    print(f"Recommendation: {result['recommendation']}")
    print(f"Black Swan Alerts: {len(result['black_swan_alerts'])}")
    print(f"Compliant: {result['compliance']['compliant']}")
    print(f"Cost: ${result['cost']}")
