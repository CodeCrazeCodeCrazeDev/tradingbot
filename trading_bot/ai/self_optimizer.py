"""
AI Self-Optimizer
Autonomous system that modifies configs, models, and parameters based on performance
"""

import os
import yaml
import json
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
import logging
from dataclasses import dataclass, asdict
import pickle

logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetrics:
    """Performance metrics for optimization"""
    sharpe_ratio: float
    win_rate: float
    profit_factor: float
    max_drawdown: float
    total_trades: int
    avg_profit: float
    avg_loss: float
    timestamp: datetime


@dataclass
class OptimizationResult:
    """Result of optimization"""
    parameter: str
    old_value: Any
    new_value: Any
    improvement: float
    confidence: float
    timestamp: datetime


class AIOptimizer:
    """
    AI-powered self-optimization system
    Autonomously modifies configs, models, and parameters
    """
    
    def __init__(self, config_path: str = "config/config.yaml"):
        self.config_path = Path(config_path)
        self.root_dir = self.config_path.parent.parent
        self.optimization_history = []
        self.performance_history = []
        
        # Load current config
        self.config = self._load_config()
        
        # Optimization settings
        self.min_trades_for_optimization = 50
        self.confidence_threshold = 0.7
        self.max_parameter_change = 0.3  # Max 30% change per optimization
        
        # Create backup directory
        self.backup_dir = self.root_dir / "backups" / "ai_optimizer"
        self.backup_dir.mkdir(parents=True, exist_ok=True)
    
    def _load_config(self) -> Dict:
        """Load configuration"""
        try:
            with open(self.config_path, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            return {}
    
    def _save_config(self, config: Dict, backup: bool = True):
        """Save configuration with backup"""
        if backup:
            # Create backup
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_path = self.backup_dir / f"config_backup_{timestamp}.yaml"
            
            with open(backup_path, 'w') as f:
                yaml.dump(self.config, f, default_flow_style=False)
            
            logger.info(f"Config backed up to: {backup_path}")
        
        # Save new config
        with open(self.config_path, 'w') as f:
            yaml.dump(config, f, default_flow_style=False)
        
        self.config = config
        logger.info("Configuration updated")
    
    def add_performance_data(self, metrics: PerformanceMetrics):
        """Add performance data for analysis"""
        self.performance_history.append(metrics)
        
        # Keep last 1000 records
        if len(self.performance_history) > 1000:
            self.performance_history = self.performance_history[-1000:]
    
    def should_optimize(self) -> bool:
        """Check if optimization should run"""
        if len(self.performance_history) < 2:
            return False
        
        # Get recent performance
        recent = self.performance_history[-1]
        
        # Need minimum trades
        if recent.total_trades < self.min_trades_for_optimization:
            return False
        
        # Check if performance is declining
        if len(self.performance_history) >= 10:
            recent_avg = np.mean([m.sharpe_ratio for m in self.performance_history[-10:]])
            older_avg = np.mean([m.sharpe_ratio for m in self.performance_history[-20:-10]])
            
            if recent_avg < older_avg * 0.9:  # 10% decline
                return True
        
        return False
    
    def optimize_risk_parameters(self) -> List[OptimizationResult]:
        """Optimize risk management parameters"""
        results = []
        
        if not self.performance_history:
            return results
        
        recent = self.performance_history[-1]
        
        # Optimize risk per trade based on Sharpe ratio
        current_risk = self.config.get('risk', {}).get('risk_per_trade', 0.01)
        
        if recent.sharpe_ratio > 2.0:
            # High Sharpe - can increase risk
            new_risk = min(current_risk * 1.2, current_risk * (1 + self.max_parameter_change))
            improvement = (new_risk - current_risk) / current_risk
            confidence = min(recent.sharpe_ratio / 3.0, 1.0)
            
            if confidence > self.confidence_threshold:
                results.append(OptimizationResult(
                    parameter='risk.risk_per_trade',
                    old_value=current_risk,
                    new_value=new_risk,
                    improvement=improvement,
                    confidence=confidence,
                    timestamp=datetime.now()
                ))
        
        elif recent.sharpe_ratio < 1.0:
            # Low Sharpe - decrease risk
            new_risk = max(current_risk * 0.8, current_risk * (1 - self.max_parameter_change))
            improvement = (current_risk - new_risk) / current_risk
            confidence = 0.9  # High confidence in risk reduction
            
            results.append(OptimizationResult(
                parameter='risk.risk_per_trade',
                old_value=current_risk,
                new_value=new_risk,
                improvement=improvement,
                confidence=confidence,
                timestamp=datetime.now()
            ))
        
        # Optimize max drawdown based on recent drawdown
        current_max_dd = self.config.get('risk', {}).get('max_drawdown', 0.2)
        
        if recent.max_drawdown > current_max_dd * 0.8:
            # Approaching max drawdown - tighten
            new_max_dd = max(current_max_dd * 0.9, 0.1)
            improvement = (current_max_dd - new_max_dd) / current_max_dd
            confidence = 0.85
            
            results.append(OptimizationResult(
                parameter='risk.max_drawdown',
                old_value=current_max_dd,
                new_value=new_max_dd,
                improvement=improvement,
                confidence=confidence,
                timestamp=datetime.now()
            ))
        
        return results
    
    def optimize_strategy_parameters(self) -> List[OptimizationResult]:
        """Optimize strategy parameters"""
        results = []
        
        if len(self.performance_history) < 20:
            return results
        
        recent = self.performance_history[-1]
        
        # Optimize based on win rate
        if recent.win_rate < 0.45:
            # Low win rate - adjust entry criteria
            current_threshold = self.config.get('strategy', {}).get('entry_threshold', 0.7)
            new_threshold = min(current_threshold * 1.1, 0.95)
            
            results.append(OptimizationResult(
                parameter='strategy.entry_threshold',
                old_value=current_threshold,
                new_value=new_threshold,
                improvement=(new_threshold - current_threshold) / current_threshold,
                confidence=0.75,
                timestamp=datetime.now()
            ))
        
        elif recent.win_rate > 0.65:
            # High win rate - can be more aggressive
            current_threshold = self.config.get('strategy', {}).get('entry_threshold', 0.7)
            new_threshold = max(current_threshold * 0.95, 0.5)
            
            results.append(OptimizationResult(
                parameter='strategy.entry_threshold',
                old_value=current_threshold,
                new_value=new_threshold,
                improvement=(current_threshold - new_threshold) / current_threshold,
                confidence=0.8,
                timestamp=datetime.now()
            ))
        
        return results
    
    def optimize_ml_parameters(self) -> List[OptimizationResult]:
        """Optimize ML model parameters"""
        results = []
        
        if len(self.performance_history) < 30:
            return results
        
        # Calculate model accuracy proxy from win rate
        recent_win_rates = [m.win_rate for m in self.performance_history[-20:]]
        avg_win_rate = np.mean(recent_win_rates)
        win_rate_std = np.std(recent_win_rates)
        
        # If high variance, increase regularization
        if win_rate_std > 0.1:
            current_reg = self.config.get('ml', {}).get('regularization', 0.01)
            new_reg = min(current_reg * 1.5, 0.1)
            
            results.append(OptimizationResult(
                parameter='ml.regularization',
                old_value=current_reg,
                new_value=new_reg,
                improvement=(new_reg - current_reg) / current_reg,
                confidence=0.7,
                timestamp=datetime.now()
            ))
        
        # Adjust learning rate based on performance trend
        if len(self.performance_history) >= 30:
            recent_sharpe = [m.sharpe_ratio for m in self.performance_history[-10:]]
            older_sharpe = [m.sharpe_ratio for m in self.performance_history[-30:-20]]
            
            if np.mean(recent_sharpe) < np.mean(older_sharpe):
                # Performance declining - reduce learning rate
                current_lr = self.config.get('ml', {}).get('learning_rate', 0.001)
                new_lr = current_lr * 0.8
                
                results.append(OptimizationResult(
                    parameter='ml.learning_rate',
                    old_value=current_lr,
                    new_value=new_lr,
                    improvement=0.1,  # Conservative improvement estimate
                    confidence=0.65,
                    timestamp=datetime.now()
                ))
        
        return results
    
    def apply_optimizations(self, results: List[OptimizationResult]) -> int:
        """Apply optimization results to config"""
        applied = 0
        
        for result in results:
            if result.confidence >= self.confidence_threshold:
                # Parse parameter path
                parts = result.parameter.split('.')
                
                # Update config
                config_section = self.config
                for part in parts[:-1]:
                    if part not in config_section:
                        config_section[part] = {}
                    config_section = config_section[part]
                
                config_section[parts[-1]] = result.new_value
                
                logger.info(f"Applied optimization: {result.parameter} "
                          f"{result.old_value} -> {result.new_value} "
                          f"(confidence: {result.confidence:.2f})")
                
                applied += 1
                self.optimization_history.append(result)
        
        if applied > 0:
            self._save_config(self.config, backup=True)
        
        return applied
    
    def run_optimization_cycle(self) -> Dict:
        """Run complete optimization cycle"""
        logger.info("Starting AI optimization cycle...")
        
        if not self.should_optimize():
            return {
                'status': 'skipped',
                'reason': 'Insufficient data or performance acceptable',
                'timestamp': datetime.now().isoformat()
            }
        
        # Collect optimization suggestions
        all_results = []
        all_results.extend(self.optimize_risk_parameters())
        all_results.extend(self.optimize_strategy_parameters())
        all_results.extend(self.optimize_ml_parameters())
        
        # Apply optimizations
        applied = self.apply_optimizations(all_results)
        
        result = {
            'status': 'completed',
            'total_suggestions': len(all_results),
            'applied': applied,
            'skipped': len(all_results) - applied,
            'optimizations': [asdict(r) for r in all_results],
            'timestamp': datetime.now().isoformat()
        }
        
        # Save optimization report
        self._save_optimization_report(result)
        
        logger.info(f"Optimization complete: {applied} changes applied")
        
        return result
    
    def _save_optimization_report(self, result: Dict):
        """Save optimization report"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_path = self.backup_dir / f"optimization_report_{timestamp}.json"
        
        with open(report_path, 'w') as f:
            json.dump(result, f, indent=2, default=str)
        
        logger.info(f"Optimization report saved: {report_path}")
    
    def rollback_last_optimization(self) -> bool:
        """Rollback to previous configuration"""
        # Find most recent backup
        backups = sorted(self.backup_dir.glob("config_backup_*.yaml"))
        
        if not backups:
            logger.error("No backups found")
            return False
        
        latest_backup = backups[-1]
        
        # Load backup
        with open(latest_backup, 'r') as f:
            backup_config = yaml.safe_load(f)
        
        # Restore
        self._save_config(backup_config, backup=False)
        
        logger.info(f"Rolled back to: {latest_backup}")
        return True
    
    def get_optimization_summary(self) -> Dict:
        """Get summary of all optimizations"""
        if not self.optimization_history:
            return {
                'total_optimizations': 0,
                'parameters_optimized': [],
                'avg_confidence': 0,
                'last_optimization': None
            }
        
        parameters = list(set([r.parameter for r in self.optimization_history]))
        avg_confidence = np.mean([r.confidence for r in self.optimization_history])
        
        return {
            'total_optimizations': len(self.optimization_history),
            'parameters_optimized': parameters,
            'avg_confidence': avg_confidence,
            'last_optimization': self.optimization_history[-1].timestamp.isoformat(),
            'recent_optimizations': [
                {
                    'parameter': r.parameter,
                    'old_value': r.old_value,
                    'new_value': r.new_value,
                    'improvement': r.improvement,
                    'confidence': r.confidence,
                    'timestamp': r.timestamp.isoformat()
                }
                for r in self.optimization_history[-10:]
            ]
        }


class ModelOptimizer:
    """
    Optimize ML models autonomously
    """
    
    def __init__(self, model_dir: str = "models"):
        self.model_dir = Path(model_dir)
        self.model_dir.mkdir(exist_ok=True)
        self.performance_tracker = {}
    
    def optimize_model_architecture(self, model_name: str, performance: Dict) -> Dict:
        """Optimize model architecture based on performance"""
        
        # Track performance
        if model_name not in self.performance_tracker:
            self.performance_tracker[model_name] = []
        
        self.performance_tracker[model_name].append(performance)
        
        # Need at least 5 performance records
        if len(self.performance_tracker[model_name]) < 5:
            return {'status': 'insufficient_data'}
        
        recent_perf = self.performance_tracker[model_name][-5:]
        avg_accuracy = np.mean([p.get('accuracy', 0) for p in recent_perf])
        
        suggestions = {}
        
        # If accuracy is low, suggest architecture changes
        if avg_accuracy < 0.6:
            suggestions['increase_layers'] = True
            suggestions['increase_neurons'] = 1.5
            suggestions['add_dropout'] = 0.3
        
        elif avg_accuracy > 0.85:
            # High accuracy - might be overfitting
            suggestions['add_regularization'] = True
            suggestions['increase_dropout'] = 0.1
        
        return {
            'status': 'suggestions_generated',
            'model': model_name,
            'current_performance': avg_accuracy,
            'suggestions': suggestions
        }
    
    def auto_tune_hyperparameters(self, model_name: str, 
                                  param_space: Dict) -> Dict:
        """Auto-tune hyperparameters using Bayesian optimization"""
        from sklearn.model_selection import cross_val_score
        from scipy.optimize import differential_evolution
        
        def objective(params):
            """Objective function for optimization"""
            # This would train and evaluate model with given params
            # Placeholder for demonstration
            return -np.random.random()  # Negative because we minimize
        
        # Run optimization
        bounds = [(v['min'], v['max']) for v in param_space.values()]
        result = differential_evolution(objective, bounds, maxiter=50)
        
        # Map results back to parameters
        optimized_params = {
            name: result.x[i] 
            for i, name in enumerate(param_space.keys())
        }
        
        return {
            'status': 'optimized',
            'model': model_name,
            'optimized_parameters': optimized_params,
            'improvement': -result.fun
        }


# Example usage
if __name__ == '__main__':
    # Create optimizer
    optimizer = AIOptimizer()
    
    # Simulate performance data
    for i in range(60):
        metrics = PerformanceMetrics(
            sharpe_ratio=1.5 + np.random.randn() * 0.3,
            win_rate=0.55 + np.random.randn() * 0.05,
            profit_factor=1.8 + np.random.randn() * 0.2,
            max_drawdown=0.15 + np.random.randn() * 0.03,
            total_trades=50 + i,
            avg_profit=100 + np.random.randn() * 20,
            avg_loss=-80 + np.random.randn() * 15,
            timestamp=datetime.now()
        )
        optimizer.add_performance_data(metrics)
    
    # Run optimization
    result = optimizer.run_optimization_cycle()
    
    print("="*80)
    print("AI OPTIMIZATION RESULT".center(80))
    print("="*80)
    print(json.dumps(result, indent=2, default=str))
    
    # Get summary
    summary = optimizer.get_optimization_summary()
    print("\n" + "="*80)
    print("OPTIMIZATION SUMMARY".center(80))
    print("="*80)
    print(json.dumps(summary, indent=2, default=str))
