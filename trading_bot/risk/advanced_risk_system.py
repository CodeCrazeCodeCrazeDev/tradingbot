"""
Advanced Risk Management System

Implements real-time portfolio stress testing, black swan detection,
and cross-asset correlation monitoring with extreme value theory.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
try:
    from scipy import stats
except ImportError:
    scipy = None
from scipy.optimize import minimize
import logging
from datetime import datetime, timedelta
import numpy
import pandas

logger = logging.getLogger(__name__)


@dataclass
class StressScenario:
    """Stress test scenario definition"""
    name: str
    market_shock: float  # % change
    volatility_multiplier: float
    correlation_shift: float
    probability: float
    description: str


@dataclass
class BlackSwanEvent:
    """Black swan event detection"""
    timestamp: datetime
    event_type: str
    severity: float  # 0-1
    affected_assets: List[str]
    probability: float
    description: str
    recommended_action: str


class ExtremeValueAnalyzer:
    """
    Extreme Value Theory (EVT) for tail risk analysis
    
    Uses Generalized Pareto Distribution (GPD) for modeling extreme losses.
    """
    
    def __init__(self, threshold_percentile: float = 0.95):
        self.threshold_percentile = threshold_percentile
        self.threshold = None
        self.gpd_params = {}
        
    def fit(self, returns: np.ndarray, asset_name: str):
        """
        Fit GPD to extreme losses
        
        Args:
            returns: Historical returns
            asset_name: Asset identifier
        """
        # Calculate threshold (negative returns beyond percentile)
        losses = -returns[returns < 0]
        if len(losses) == 0:
            logger.warning(f"No losses found for {asset_name}")
            return
        
        self.threshold = np.percentile(losses, self.threshold_percentile * 100)
        
        # Exceedances over threshold
        exceedances = losses[losses > self.threshold] - self.threshold
        
        if len(exceedances) < 10:
            logger.warning(f"Insufficient exceedances for {asset_name}")
            return
        try:
        
        # Fit GPD using maximum likelihood
            shape, loc, scale = stats.genpareto.fit(exceedances, floc=0)
            
            self.gpd_params[asset_name] = {
                'shape': shape,
                'scale': scale,
                'threshold': self.threshold,
                'n_exceedances': len(exceedances),
                'n_total': len(returns)
            }
            
            logger.info(f"Fitted GPD for {asset_name}: shape={shape:.4f}, scale={scale:.4f}")
            
        except Exception as e:
            logger.error(f"Error fitting GPD for {asset_name}: {e}")
    
    def estimate_var(self, asset_name: str, confidence: float = 0.99) -> float:
        """
        Estimate Value at Risk using EVT
        
        Args:
            asset_name: Asset identifier
            confidence: Confidence level
            
        Returns:
            VaR estimate
        """
        if asset_name not in self.gpd_params:
            return 0.0
        
        params = self.gpd_params[asset_name]
        shape = params['shape']
        scale = params['scale']
        threshold = params['threshold']
        n_exceedances = params['n_exceedances']
        n_total = params['n_total']
        
        # Probability of exceedance
        p_exceed = n_exceedances / n_total
        
        # VaR calculation
        if shape != 0:
            var = threshold + (scale / shape) * (
                ((1 - confidence) / p_exceed) ** (-shape) - 1
            )
        else:
            var = threshold - scale * np.log((1 - confidence) / p_exceed)
        
        return var
    
    def estimate_es(self, asset_name: str, confidence: float = 0.99) -> float:
        """
        Estimate Expected Shortfall (CVaR) using EVT
        
        Args:
            asset_name: Asset identifier
            confidence: Confidence level
            
        Returns:
            ES estimate
        """
        if asset_name not in self.gpd_params:
            return 0.0
        
        params = self.gpd_params[asset_name]
        shape = params['shape']
        scale = params['scale']
        
        var = self.estimate_var(asset_name, confidence)
        
        # ES calculation
        if shape < 1:
            es = var / (1 - shape) + (scale - shape * params['threshold']) / (1 - shape)
        else:
            es = var  # Undefined for shape >= 1, use VaR as approximation
        
        return es


class BlackSwanDetector:
    """
    Black Swan Event Detection System
    
    Monitors for extreme market events using statistical anomaly detection.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # Detection thresholds
        self.volatility_threshold = self.config.get('volatility_threshold', 3.0)  # std devs
        self.correlation_threshold = self.config.get('correlation_threshold', 0.5)
        self.volume_threshold = self.config.get('volume_threshold', 5.0)
        
        # Historical data
        self.price_history = {}
        self.volatility_history = {}
        self.correlation_history = []
        
        # Detected events
        self.detected_events = []
        
    def update_data(self, prices: Dict[str, float], volumes: Dict[str, float]):
        """Update historical data"""
        timestamp = datetime.now()
        
        for asset, price in prices.items():
            if asset not in self.price_history:
                self.price_history[asset] = []
            self.price_history[asset].append((timestamp, price))
            
            # Keep only recent history
            if len(self.price_history[asset]) > 1000:
                self.price_history[asset] = self.price_history[asset][-1000:]
    
    def detect_volatility_spike(self) -> Optional[BlackSwanEvent]:
        """Detect extreme volatility spikes"""
        for asset, history in self.price_history.items():
            if len(history) < 50:
                continue
            
            # Calculate returns
            prices = np.array([p for _, p in history])
            returns = np.diff(np.log(prices))
            
            # Rolling volatility
            window = 20
            if len(returns) < window * 2:
                continue
            
            recent_vol = np.std(returns[-window:])
            historical_vol = np.std(returns[:-window])
            
            # Check for spike
            if recent_vol > historical_vol * self.volatility_threshold:
                severity = min(1.0, recent_vol / (historical_vol * 5))
                
                event = BlackSwanEvent(
                    timestamp=datetime.now(),
                    event_type="VOLATILITY_SPIKE",
                    severity=severity,
                    affected_assets=[asset],
                    probability=1 - stats.norm.cdf(recent_vol / historical_vol),
                    description=f"Extreme volatility spike in {asset}: {recent_vol:.4f} vs {historical_vol:.4f}",
                    recommended_action="REDUCE_EXPOSURE"
                )
                
                self.detected_events.append(event)
                logger.warning(f"Black Swan detected: {event.description}")
                
                return event
        
        return None
    
    def detect_correlation_breakdown(self, correlation_matrix: np.ndarray, asset_names: List[str]) -> Optional[BlackSwanEvent]:
        """Detect correlation structure breakdown"""
        if len(self.correlation_history) < 10:
            self.correlation_history.append(correlation_matrix)
            return None
        
        # Compare with historical average
        historical_corr = np.mean(self.correlation_history[-10:], axis=0)
        corr_diff = np.abs(correlation_matrix - historical_corr)
        
        # Check for significant changes
        if np.max(corr_diff) > self.correlation_threshold:
            severity = min(1.0, np.max(corr_diff) / 0.8)
            
            # Find most affected assets
            max_idx = np.unravel_index(np.argmax(corr_diff), corr_diff.shape)
            affected = [asset_names[max_idx[0]], asset_names[max_idx[1]]]
            
            event = BlackSwanEvent(
                timestamp=datetime.now(),
                event_type="CORRELATION_BREAKDOWN",
                severity=severity,
                affected_assets=affected,
                probability=1 - stats.norm.cdf(np.max(corr_diff) / 0.2),
                description=f"Correlation breakdown detected between {affected[0]} and {affected[1]}",
                recommended_action="REBALANCE_PORTFOLIO"
            )
            
            self.detected_events.append(event)
            logger.warning(f"Black Swan detected: {event.description}")
            
            return event
        
        self.correlation_history.append(correlation_matrix)
        if len(self.correlation_history) > 100:
            self.correlation_history = self.correlation_history[-100:]
        
        return None


class PortfolioStressTester:
    """
    Real-time Portfolio Stress Testing
    
    Simulates portfolio performance under extreme scenarios.
    """
    
    def __init__(self):
        # Define stress scenarios
        self.scenarios = [
            StressScenario(
                "2008_CRISIS",
                -0.40,
                3.0,
                0.8,
                0.01,
                "2008 Financial Crisis scenario"
            ),
            StressScenario(
                "COVID_CRASH",
                -0.35,
                5.0,
                0.9,
                0.02,
                "COVID-19 market crash scenario"
            ),
            StressScenario(
                "FLASH_CRASH",
                -0.10,
                10.0,
                0.5,
                0.05,
                "Flash crash scenario"
            ),
            StressScenario(
                "VOLATILITY_SPIKE",
                -0.05,
                4.0,
                0.3,
                0.10,
                "Extreme volatility spike"
            ),
            StressScenario(
                "CORRELATION_SHOCK",
                -0.15,
                2.0,
                1.0,
                0.05,
                "All assets move together"
            )
        ]
    
    def run_stress_test(
        self,
        portfolio: Dict[str, float],
        current_prices: Dict[str, float],
        returns_history: Dict[str, np.ndarray],
        correlation_matrix: np.ndarray
    ) -> Dict:
        """
        Run comprehensive stress test
        
        Args:
            portfolio: Asset positions {asset: quantity}
            current_prices: Current prices {asset: price}
            returns_history: Historical returns {asset: returns}
            correlation_matrix: Current correlation matrix
            
        Returns:
            Stress test results
        """
        results = {}
        
        # Calculate current portfolio value
        current_value = sum(
            qty * current_prices.get(asset, 0)
            for asset, qty in portfolio.items()
        )
        
        for scenario in self.scenarios:
            # Apply scenario shocks
            shocked_prices = {}
            for asset, price in current_prices.items():
                # Base shock
                shock = scenario.market_shock
                
                # Add asset-specific volatility
                if asset in returns_history:
                    vol = np.std(returns_history[asset])
                    shock += np.random.normal(0, vol * scenario.volatility_multiplier)
                
                shocked_prices[asset] = price * (1 + shock)
            
            # Calculate stressed portfolio value
            stressed_value = sum(
                qty * shocked_prices.get(asset, 0)
                for asset, qty in portfolio.items()
            )
            
            loss = current_value - stressed_value
            loss_pct = loss / current_value if current_value > 0 else 0
            
            results[scenario.name] = {
                'scenario': scenario.description,
                'current_value': current_value,
                'stressed_value': stressed_value,
                'loss': loss,
                'loss_pct': loss_pct,
                'probability': scenario.probability,
                'expected_loss': loss * scenario.probability
            }
            
            logger.info(f"Stress test {scenario.name}: Loss={loss_pct:.2%}, Prob={scenario.probability:.2%}")
        
        return results


class CrossAssetCorrelationMonitor:
    """
    Cross-Asset Correlation Monitoring
    
    Tracks correlations across multiple asset classes for global macro risk.
    """
    
    def __init__(self):
        self.correlation_history = []
        self.asset_classes = ['EQUITY', 'FIXED_INCOME', 'COMMODITY', 'FX', 'CRYPTO']
        
    def calculate_correlation_matrix(self, returns: Dict[str, np.ndarray]) -> np.ndarray:
        """Calculate correlation matrix from returns"""
        assets = list(returns.keys())
        n = len(assets)
        
        if n == 0:
            return np.array([])
        
        # Stack returns
        returns_matrix = np.column_stack([returns[asset] for asset in assets])
        
        # Calculate correlation
        corr_matrix = np.corrcoef(returns_matrix.T)
        
        return corr_matrix
    
    def detect_regime_change(self, current_corr: np.ndarray) -> bool:
        """Detect correlation regime change"""
        if len(self.correlation_history) < 20:
            self.correlation_history.append(current_corr)
            return False
        
        # Calculate average historical correlation
        historical_avg = np.mean(self.correlation_history[-20:], axis=0)
        
        # Calculate difference
        diff = np.abs(current_corr - historical_avg)
        
        # Check for significant change
        threshold = 0.3
        regime_change = np.max(diff) > threshold
        
        self.correlation_history.append(current_corr)
        if len(self.correlation_history) > 100:
            self.correlation_history = self.correlation_history[-100:]
        
        return regime_change


class AdvancedRiskSystem:
    """
    Integrated Advanced Risk Management System
    
    Combines EVT, black swan detection, stress testing, and correlation monitoring.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # Initialize components
        self.evt_analyzer = ExtremeValueAnalyzer()
        self.black_swan_detector = BlackSwanDetector(config)
        self.stress_tester = PortfolioStressTester()
        self.correlation_monitor = CrossAssetCorrelationMonitor()
        
        # Risk limits
        self.max_var = self.config.get('max_var', 0.05)
        self.max_es = self.config.get('max_es', 0.08)
        self.max_stress_loss = self.config.get('max_stress_loss', 0.20)
        
        logger.info("Advanced Risk System initialized")
    
    def assess_portfolio_risk(
        self,
        portfolio: Dict[str, float],
        prices: Dict[str, float],
        returns_history: Dict[str, np.ndarray],
        volumes: Dict[str, float]
    ) -> Dict:
        """
        Comprehensive portfolio risk assessment
        
        Returns:
            Risk assessment report
        """
        # Calculate correlation matrix
        corr_matrix = self.correlation_monitor.calculate_correlation_matrix(returns_history)
        
        # EVT analysis
        evt_results = {}
        for asset, returns in returns_history.items():
            self.evt_analyzer.fit(returns, asset)
            var_99 = self.evt_analyzer.estimate_var(asset, 0.99)
            es_99 = self.evt_analyzer.estimate_es(asset, 0.99)
            evt_results[asset] = {'VaR_99': var_99, 'ES_99': es_99}
        
        # Black swan detection
        self.black_swan_detector.update_data(prices, volumes)
        vol_event = self.black_swan_detector.detect_volatility_spike()
        corr_event = self.black_swan_detector.detect_correlation_breakdown(
            corr_matrix, list(returns_history.keys())
        )
        
        # Stress testing
        stress_results = self.stress_tester.run_stress_test(
            portfolio, prices, returns_history, corr_matrix
        )
        
        # Correlation regime detection
        regime_change = self.correlation_monitor.detect_regime_change(corr_matrix)
        
        # Aggregate risk assessment
        risk_score = self._calculate_risk_score(evt_results, stress_results, vol_event, corr_event)
        
        return {
            'timestamp': datetime.now(),
            'risk_score': risk_score,
            'evt_analysis': evt_results,
            'black_swan_events': [vol_event, corr_event],
            'stress_test_results': stress_results,
            'correlation_regime_change': regime_change,
            'recommended_actions': self._generate_recommendations(risk_score, stress_results)
        }
    
    def _calculate_risk_score(self, evt_results, stress_results, vol_event, corr_event) -> float:
        """Calculate aggregate risk score (0-1)"""
        score = 0.0
        
        # EVT contribution
        max_var = max([r['VaR_99'] for r in evt_results.values()]) if evt_results else 0
        score += min(1.0, max_var / self.max_var) * 0.3
        
        # Stress test contribution
        max_stress_loss = max([r['loss_pct'] for r in stress_results.values()]) if stress_results else 0
        score += min(1.0, abs(max_stress_loss) / self.max_stress_loss) * 0.4
        
        # Black swan contribution
        if vol_event:
            score += vol_event.severity * 0.15
        if corr_event:
            score += corr_event.severity * 0.15
        
        return min(1.0, score)
    
    def _generate_recommendations(self, risk_score: float, stress_results: Dict) -> List[str]:
        """Generate risk management recommendations"""
        recommendations = []
        
        if risk_score > 0.8:
            recommendations.append("CRITICAL: Reduce portfolio exposure immediately")
            recommendations.append("Consider hedging with options or inverse positions")
        elif risk_score > 0.6:
            recommendations.append("HIGH RISK: Reduce position sizes by 30-50%")
            recommendations.append("Increase cash allocation")
        elif risk_score > 0.4:
            recommendations.append("MODERATE RISK: Monitor closely")
            recommendations.append("Consider tightening stop losses")
        
        # Scenario-specific recommendations
        for scenario, result in stress_results.items():
            if abs(result['loss_pct']) > 0.15:
                recommendations.append(f"High exposure to {scenario} scenario: {result['loss_pct']:.1%} loss")
        
        return recommendations


if __name__ == "__main__":
    # Example usage
    logging.basicConfig(level=logging.INFO)
    
    # Sample data
    portfolio = {'AAPL': 100, 'GOOGL': 50, 'MSFT': 75}
    prices = {'AAPL': 150.0, 'GOOGL': 2800.0, 'MSFT': 300.0}
    returns_history = {
        'AAPL': np.random.randn(252) * 0.02,
        'GOOGL': np.random.randn(252) * 0.025,
        'MSFT': np.random.randn(252) * 0.018
    }
    volumes = {'AAPL': 1000000, 'GOOGL': 500000, 'MSFT': 800000}
    
    # Run risk assessment
    risk_system = AdvancedRiskSystem()
    assessment = risk_system.assess_portfolio_risk(portfolio, prices, returns_history, volumes)
    
    logger.info(f"\nRisk Score: {assessment['risk_score']:.2f}")
    logger.info(f"\nRecommendations:")
    for rec in assessment['recommended_actions']:
        logger.info(f"  - {rec}")
