"""
Phase 5: Auto-Update and Self-Learning System
Manages 24-hour update cycles, model retraining, and performance monitoring.
"""

import asyncio
import logging
import json
import shutil
from typing import Any, Dict, List, Optional
from pathlib import Path
from datetime import datetime, timedelta
from dataclasses import dataclass, field
import pickle
import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class ModelPerformance:
    """Track model performance metrics"""
    model_name: str
    timestamp: datetime
    accuracy: float
    precision: float
    recall: float
    f1_score: float
    profit_factor: float
    win_rate: float
    sharpe_ratio: float
    max_drawdown: float
    total_trades: int
    
    def to_dict(self) -> Dict:
        return {
            'model_name': self.model_name,
            'timestamp': self.timestamp.isoformat(),
            'accuracy': round(self.accuracy, 4),
            'precision': round(self.precision, 4),
            'recall': round(self.recall, 4),
            'f1_score': round(self.f1_score, 4),
            'profit_factor': round(self.profit_factor, 4),
            'win_rate': round(self.win_rate, 4),
            'sharpe_ratio': round(self.sharpe_ratio, 4),
            'max_drawdown': round(self.max_drawdown, 4),
            'total_trades': self.total_trades
        }
    
    def is_acceptable(self, min_performance: float = 0.70) -> bool:
        """Check if performance meets minimum threshold"""
        return self.accuracy >= min_performance and self.win_rate >= min_performance


@dataclass
class UpdateCycle:
    """Represents a single update cycle"""
    cycle_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    data_fetched: bool = False
    models_retrained: bool = False
    performance_evaluated: bool = False
    models_updated: bool = False
    success: bool = False
    errors: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        return {
            'cycle_id': self.cycle_id,
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'duration_minutes': (self.end_time - self.start_time).total_seconds() / 60 if self.end_time else None,
            'data_fetched': self.data_fetched,
            'models_retrained': self.models_retrained,
            'performance_evaluated': self.performance_evaluated,
            'models_updated': self.models_updated,
            'success': self.success,
            'errors': self.errors
        }


class AutoUpdater:
    """
    Manages automatic updates and self-learning for AlphaAlgo.
    Runs 24-hour update cycles to fetch data, retrain models, and optimize performance.
    """
    
    def __init__(self, config: Dict):
        self.config = config
        
        # Paths
        self.models_dir = Path(config.get('models_dir', 'models'))
        self.models_dir.mkdir(exist_ok=True)
        
        self.archive_dir = Path(config.get('archive_dir', 'models/archive'))
        self.archive_dir.mkdir(exist_ok=True)
        
        self.update_log_path = Path(config.get('update_log', 'update_report.log'))
        
        # Update schedule
        self.update_interval_hours = config.get('update_interval_hours', 24)
        self.min_performance_threshold = config.get('min_performance', 0.70)
        
        # State
        self.last_update: Optional[datetime] = None
        self.update_history: List[UpdateCycle] = []
        self.current_performance: Dict[str, ModelPerformance] = {}
        self.update_task: Optional[asyncio.Task] = None
        self.is_running = False
        
        # Performance dashboard
        self.dashboard_data: Dict[str, Any] = {
            'total_updates': 0,
            'successful_updates': 0,
            'failed_updates': 0,
            'models_retrained': 0,
            'avg_performance': 0.0,
            'last_update': None
        }
        
        logger.info(f"Auto-Updater initialized (interval: {self.update_interval_hours}h)")
    
    async def run_update_cycle(self) -> UpdateCycle:
        """
        Execute a complete 24-hour update cycle.
        Steps:
        1. Fetch new data
        2. Evaluate current model performance
        3. Retrain models if performance < threshold
        4. Archive old models
        5. Update dashboard
        """
        cycle_id = datetime.now().strftime('%Y%m%d_%H%M%S')
        cycle = UpdateCycle(
            cycle_id=cycle_id,
            start_time=datetime.now()
        )
        
        logger.info(f"🔄 Starting update cycle: {cycle_id}")
        
        try:
            # Step 1: Fetch new data
            logger.info("📊 Step 1/5: Fetching new data...")
            await self._fetch_new_data()
            cycle.data_fetched = True
            logger.info("✓ Data fetch complete")
            
            # Step 2: Evaluate current performance
            logger.info("📈 Step 2/5: Evaluating model performance...")
            performance = await self._evaluate_performance()
            cycle.performance_evaluated = True
            logger.info(f"✓ Performance evaluation complete (avg: {performance:.2%})")
            
            # Step 3: Retrain models if needed
            if performance < self.min_performance_threshold:
                logger.warning(f"⚠️ Performance below threshold ({performance:.2%} < {self.min_performance_threshold:.2%})")
                logger.info("🧠 Step 3/5: Retraining models...")
                await self._retrain_models()
                cycle.models_retrained = True
                logger.info("✓ Model retraining complete")
            else:
                logger.info(f"✓ Step 3/5: Performance acceptable ({performance:.2%}), skipping retraining")
            
            # Step 4: Archive old models
            logger.info("📦 Step 4/5: Archiving previous models...")
            await self._archive_old_models()
            logger.info("✓ Archiving complete")
            
            # Step 5: Update dashboard
            logger.info("📊 Step 5/5: Updating performance dashboard...")
            await self._update_dashboard()
            cycle.models_updated = True
            logger.info("✓ Dashboard updated")
            
            cycle.success = True
            logger.info(f"✅ Update cycle {cycle_id} completed successfully")
        
        except Exception as e:
            error_msg = f"Error in update cycle: {e}"
            logger.error(error_msg)
            cycle.errors.append(error_msg)
            cycle.success = False
        
        finally:
            cycle.end_time = datetime.now()
            self.update_history.append(cycle)
            self._log_update_cycle(cycle)
            self._update_dashboard_stats(cycle)
        
        return cycle
    
    async def _fetch_new_data(self):
        """Fetch new market data, news, sentiment, etc."""
        # This would integrate with DataAcquisitionEngine
        # For now, simulate data fetch
        await asyncio.sleep(2)
        logger.debug("Simulated data fetch")
    
    async def _evaluate_performance(self) -> float:
        """
        Evaluate current model performance.
        Returns average performance score (0.0 to 1.0)
        """
        # In production, this would:
        # 1. Load recent trading results
        # 2. Calculate metrics (accuracy, profit factor, Sharpe ratio, etc.)
        # 3. Compare against benchmarks
        
        # Simulate performance evaluation
        await asyncio.sleep(1)
        
        # Mock performance data
        models = ['technical_model', 'sentiment_model', 'fusion_model']
        performances = []
        
        for model_name in models:
            # Simulate varying performance
            import random
            accuracy = random.uniform(0.60, 0.85)
            win_rate = random.uniform(0.55, 0.80)
            sharpe = random.uniform(0.5, 2.5)
            
            perf = ModelPerformance(
                model_name=model_name,
                timestamp=datetime.now(),
                accuracy=accuracy,
                precision=accuracy * 0.95,
                recall=accuracy * 0.90,
                f1_score=accuracy * 0.92,
                profit_factor=1.5 + (accuracy - 0.5),
                win_rate=win_rate,
                sharpe_ratio=sharpe,
                max_drawdown=0.15,
                total_trades=100
            )
            
            self.current_performance[model_name] = perf
            performances.append(accuracy)
            
            logger.debug(f"  {model_name}: accuracy={accuracy:.2%}, win_rate={win_rate:.2%}")
        
        avg_performance = np.mean(performances)
        return avg_performance
    
    async def _retrain_models(self):
        """
        Retrain models with new data.
        """
        logger.info("Starting model retraining...")
        
        # In production, this would:
        # 1. Load training data
        # 2. Preprocess and feature engineering
        # 3. Train models (could take hours)
        # 4. Validate on holdout set
        # 5. Save new models
        
        # Simulate retraining
        models_to_retrain = list(self.current_performance.keys())
        
        for model_name in models_to_retrain:
            logger.info(f"  Retraining {model_name}...")
            await asyncio.sleep(2)  # Simulate training time
            
            # Simulate improved performance
            old_perf = self.current_performance[model_name]
            new_accuracy = min(old_perf.accuracy * 1.1, 0.95)  # 10% improvement
            
            logger.info(f"  ✓ {model_name} retrained (accuracy: {old_perf.accuracy:.2%} → {new_accuracy:.2%})")
            
            # Update performance
            self.current_performance[model_name].accuracy = new_accuracy
            self.current_performance[model_name].timestamp = datetime.now()
        
        self.dashboard_data['models_retrained'] += len(models_to_retrain)
    
    async def _archive_old_models(self):
        """
        Archive previous model versions before replacing.
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Find all model files
        model_files = list(self.models_dir.glob('*.pkl')) + list(self.models_dir.glob('*.h5'))
        
        if not model_files:
            logger.debug("No models to archive")
            return
        
        # Create archive subdirectory
        archive_subdir = self.archive_dir / f"archive_{timestamp}"
        archive_subdir.mkdir(exist_ok=True)
        
        # Copy models to archive
        for model_file in model_files:
            try:
                dest = archive_subdir / model_file.name
                shutil.copy2(model_file, dest)
                logger.debug(f"  Archived: {model_file.name}")
            except Exception as e:
                logger.error(f"  Failed to archive {model_file.name}: {e}")
        
        logger.info(f"Archived {len(model_files)} models to {archive_subdir}")
        
        # Clean up old archives (keep last 10)
        archives = sorted(self.archive_dir.glob('archive_*'))
        if len(archives) > 10:
            for old_archive in archives[:-10]:
                try:
                    shutil.rmtree(old_archive)
                    logger.debug(f"  Removed old archive: {old_archive.name}")
                except Exception as e:
                    logger.error(f"  Failed to remove {old_archive.name}: {e}")
    
    async def _update_dashboard(self):
        """
        Update live performance dashboard.
        """
        dashboard_file = Path('dashboard_data.json')
        
        dashboard_data = {
            'timestamp': datetime.now().isoformat(),
            'models': {
                name: perf.to_dict()
                for name, perf in self.current_performance.items()
            },
            'summary': {
                'avg_accuracy': np.mean([p.accuracy for p in self.current_performance.values()]),
                'avg_win_rate': np.mean([p.win_rate for p in self.current_performance.values()]),
                'avg_sharpe': np.mean([p.sharpe_ratio for p in self.current_performance.values()]),
                'total_trades': sum([p.total_trades for p in self.current_performance.values()])
            },
            'update_stats': self.dashboard_data
        }
        
        try:
            with open(dashboard_file, 'w') as f:
                json.dump(dashboard_data, f, indent=2)
            
            logger.debug(f"Dashboard updated: {dashboard_file}")
        except Exception as e:
            logger.error(f"Failed to update dashboard: {e}")
    
    def _log_update_cycle(self, cycle: UpdateCycle):
        """Log update cycle to file"""
        try:
            with open(self.update_log_path, 'a') as f:
                f.write(json.dumps(cycle.to_dict()) + '\n')
        except Exception as e:
            logger.error(f"Failed to log update cycle: {e}")
    
    def _update_dashboard_stats(self, cycle: UpdateCycle):
        """Update dashboard statistics"""
        self.dashboard_data['total_updates'] += 1
        
        if cycle.success:
            self.dashboard_data['successful_updates'] += 1
        else:
            self.dashboard_data['failed_updates'] += 1
        
        self.dashboard_data['last_update'] = cycle.end_time.isoformat() if cycle.end_time else None
        
        if self.current_performance:
            self.dashboard_data['avg_performance'] = np.mean([
                p.accuracy for p in self.current_performance.values()
            ])
    
    async def continuous_update_loop(self):
        """
        Continuously run update cycles at specified intervals.
        """
        logger.info(f"🔄 Starting continuous update loop (every {self.update_interval_hours}h)")
        self.is_running = True
        
        while self.is_running:
            try:
                # Run update cycle
                cycle = await self.run_update_cycle()
                
                # Update last update time
                self.last_update = datetime.now()
                
                # Calculate next update time
                next_update = self.last_update + timedelta(hours=self.update_interval_hours)
                wait_seconds = (next_update - datetime.now()).total_seconds()
                
                if wait_seconds > 0:
                    logger.info(f"⏰ Next update scheduled for: {next_update.strftime('%Y-%m-%d %H:%M:%S')}")
                    logger.info(f"   Waiting {wait_seconds/3600:.1f} hours...")
                    
                    # Sleep until next update
                    await asyncio.sleep(wait_seconds)
                else:
                    # If we're behind schedule, run immediately
                    logger.warning("Update cycle took longer than interval, running next cycle immediately")
            
            except asyncio.CancelledError:
                logger.info("Update loop cancelled")
                break
            
            except Exception as e:
                logger.error(f"Error in update loop: {e}")
                # Wait 1 hour before retrying on error
                await asyncio.sleep(3600)
        
        self.is_running = False
        logger.info("Continuous update loop stopped")
    
    async def start(self):
        """Start the auto-updater"""
        if self.update_task and not self.update_task.done():
            logger.warning("Auto-updater already running")
            return
        
        self.update_task = asyncio.create_task(self.continuous_update_loop())
        logger.info("✅ Auto-updater started")
    
    async def stop(self):
        """Stop the auto-updater"""
        if self.update_task:
            self.is_running = False
            self.update_task.cancel()
            try:
                await self.update_task
            except asyncio.CancelledError:
                pass
            logger.info("Auto-updater stopped")
    
    def get_status_report(self) -> Dict:
        """Generate status report"""
        return {
            'is_running': self.is_running,
            'last_update': self.last_update.isoformat() if self.last_update else None,
            'update_interval_hours': self.update_interval_hours,
            'total_cycles': len(self.update_history),
            'successful_cycles': sum(1 for c in self.update_history if c.success),
            'failed_cycles': sum(1 for c in self.update_history if not c.success),
            'current_performance': {
                name: perf.to_dict()
                for name, perf in self.current_performance.items()
            },
            'dashboard_stats': self.dashboard_data,
            'recent_cycles': [
                c.to_dict() for c in self.update_history[-5:]
            ]
        }
    
    async def force_update(self) -> UpdateCycle:
        """Force an immediate update cycle"""
        logger.info("🔄 Forcing immediate update cycle...")
        return await self.run_update_cycle()
