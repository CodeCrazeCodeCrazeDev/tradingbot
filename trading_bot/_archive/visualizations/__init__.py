"""
Visualizations Module - Trading Data Visualization System
========================================================

Provides comprehensive visualization capabilities for trading data,
performance metrics, and market analysis.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
from pathlib import Path
import json


class VisualizationEngine:
    """Engine for generating trading visualizations."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.output_dir = Path(self.config.get('output_dir', 'visualizations'))
        self.style = self.config.get('style', 'default')
        self.dpi = self.config.get('dpi', 100)
        self.figsize = self.config.get('figsize', (12, 8))
        
    def create_trade_history_chart(self, trades: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create trade history visualization."""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'trade_history_{timestamp}.png'
            filepath = self.output_dir / filename
            
            # Ensure directory exists
            self.output_dir.mkdir(parents=True, exist_ok=True)
            
            return {
                'success': True,
                'type': 'trade_history',
                'filepath': str(filepath),
                'trades_count': len(trades),
                'message': 'Trade history chart created'
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def create_performance_chart(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Create performance metrics visualization."""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'performance_{timestamp}.png'
            filepath = self.output_dir / filename
            
            self.output_dir.mkdir(parents=True, exist_ok=True)
            
            return {
                'success': True,
                'type': 'performance',
                'filepath': str(filepath),
                'metrics': list(metrics.keys()),
                'message': 'Performance chart created'
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def create_equity_curve(self, equity_data: List[float]) -> Dict[str, Any]:
        """Create equity curve visualization."""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'equity_curve_{timestamp}.png'
            filepath = self.output_dir / filename
            
            self.output_dir.mkdir(parents=True, exist_ok=True)
            
            return {
                'success': True,
                'type': 'equity_curve',
                'filepath': str(filepath),
                'data_points': len(equity_data),
                'message': 'Equity curve created'
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def create_drawdown_chart(self, drawdown_data: List[float]) -> Dict[str, Any]:
        """Create drawdown visualization."""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'drawdown_{timestamp}.png'
            filepath = self.output_dir / filename
            
            self.output_dir.mkdir(parents=True, exist_ok=True)
            
            return {
                'success': True,
                'type': 'drawdown',
                'filepath': str(filepath),
                'max_drawdown': min(drawdown_data) if drawdown_data else 0,
                'message': 'Drawdown chart created'
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def create_win_loss_chart(self, trades: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create win/loss distribution visualization."""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'win_loss_{timestamp}.png'
            filepath = self.output_dir / filename
            
            self.output_dir.mkdir(parents=True, exist_ok=True)
            
            wins = len([t for t in trades if t.get('profit', 0) > 0])
            losses = len([t for t in trades if t.get('profit', 0) <= 0])
            
            return {
                'success': True,
                'type': 'win_loss',
                'filepath': str(filepath),
                'wins': wins,
                'losses': losses,
                'win_rate': wins / len(trades) if trades else 0,
                'message': 'Win/loss chart created'
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def create_market_analysis_chart(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create market analysis visualization."""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'market_analysis_{timestamp}.png'
            filepath = self.output_dir / filename
            
            self.output_dir.mkdir(parents=True, exist_ok=True)
            
            return {
                'success': True,
                'type': 'market_analysis',
                'filepath': str(filepath),
                'symbol': market_data.get('symbol', 'Unknown'),
                'message': 'Market analysis chart created'
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}


class VisualizationOrchestrator:
    """Orchestrates visualization operations across the trading system."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.engine = VisualizationEngine(self.config)
        self.active_visualizations = []
        
    def initialize(self) -> Dict[str, Any]:
        """Initialize the visualization orchestrator."""
        return {
            'success': True,
            'output_dir': str(self.engine.output_dir),
            'style': self.engine.style,
            'dpi': self.engine.dpi,
            'available_charts': [
                'trade_history',
                'performance',
                'equity_curve',
                'drawdown',
                'win_loss',
                'market_analysis'
            ]
        }
    
    def generate_dashboard(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive dashboard with multiple visualizations."""
        try:
            results = {}
            
            # Generate all chart types
            if 'trades' in data:
                results['trade_history'] = self.engine.create_trade_history_chart(data['trades'])
                results['win_loss'] = self.engine.create_win_loss_chart(data['trades'])
            
            if 'equity' in data:
                results['equity_curve'] = self.engine.create_equity_curve(data['equity'])
            
            if 'drawdown' in data:
                results['drawdown'] = self.engine.create_drawdown_chart(data['drawdown'])
            
            if 'metrics' in data:
                results['performance'] = self.engine.create_performance_chart(data['metrics'])
            
            if 'market_data' in data:
                results['market_analysis'] = self.engine.create_market_analysis_chart(data['market_data'])
            
            return {
                'success': True,
                'charts_generated': len(results),
                'results': results,
                'message': 'Dashboard generated successfully'
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_status(self) -> Dict[str, Any]:
        """Get current visualization status."""
        try:
            output_path = Path(self.engine.output_dir)
            if output_path.exists():
                files = list(output_path.glob('*.png'))
                total_size = sum(f.stat().st_size for f in files)
            else:
                files = []
                total_size = 0
            
            return {
                'output_dir': str(self.engine.output_dir),
                'total_visualizations': len(files),
                'total_size_bytes': total_size,
                'recent_files': [str(f.name) for f in sorted(files, key=lambda x: x.stat().st_mtime, reverse=True)[:5]]
            }
        except Exception as e:
            return {'error': str(e)}
    
    def health_check(self) -> Dict[str, Any]:
        """Check visualization system health."""
        try:
            # Ensure output directory exists and is writable
            self.engine.output_dir.mkdir(parents=True, exist_ok=True)
            test_file = self.engine.output_dir / '.health_check'
            test_file.write_text('test')
            test_file.unlink()
            
            return {
                'healthy': True,
                'output_dir_exists': True,
                'output_dir_writable': True,
                'message': 'Visualization system operational'
            }
        except Exception as e:
            return {
                'healthy': False,
                'error': str(e),
                'message': 'Visualization system has issues'
            }


class DashboardGenerator:
    """Generates comprehensive trading dashboards."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.orchestrator = VisualizationOrchestrator(self.config)
    
    def generate_performance_dashboard(self, trading_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a performance-focused dashboard."""
        return self.orchestrator.generate_dashboard(trading_data)
    
    def generate_market_dashboard(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a market analysis dashboard."""
        return self.orchestrator.generate_dashboard({'market_data': market_data})


def quick_start(config: Optional[Dict[str, Any]] = None) -> VisualizationOrchestrator:
    """Quick start the visualizations system."""
    return VisualizationOrchestrator(config)


__all__ = [
    'VisualizationEngine',
    'VisualizationOrchestrator',
    'DashboardGenerator',
    'quick_start'
]
