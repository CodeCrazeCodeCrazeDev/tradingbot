"""
Data Leakage Prevention System
Implements HI-ANA-004: Data Leakage Guards in Feature Computation

Prevents look-ahead bias and data leakage in ML pipelines.
Critical for ensuring models don't have access to future information.
"""

import numpy as np
import pandas as pd
from typing import Any, Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import logging
import warnings
import numpy
import pandas

logger = logging.getLogger(__name__)


class LeakageType(Enum):
    """Types of data leakage"""
    LOOK_AHEAD = "look_ahead"  # Using future data
    TARGET_LEAKAGE = "target_leakage"  # Target in features
    TRAIN_TEST_CONTAMINATION = "train_test_contamination"  # Test data in training
    TEMPORAL_LEAKAGE = "temporal_leakage"  # Wrong time ordering
    GROUP_LEAKAGE = "group_leakage"  # Data from same group in train/test


@dataclass
class LeakageViolation:
    """Detected data leakage violation"""
    leakage_type: LeakageType
    severity: str  # CRITICAL/HIGH/MEDIUM/LOW
    description: str
    affected_features: List[str]
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'leakage_type': self.leakage_type.value,
            'severity': self.severity,
            'description': self.description,
            'affected_features': self.affected_features,
            'timestamp': self.timestamp.isoformat(),
            'metadata': self.metadata
        }


class DataLeakageGuard:
    """
    Comprehensive data leakage prevention system
    
    Features:
    - Look-ahead bias detection
    - Target leakage detection
    - Temporal ordering validation
    - Feature computation validation
    - Train/test contamination checks
    """
    
    def __init__(self,
                 strict_mode: bool = True,
                 raise_on_violation: bool = True,
                 log_violations: bool = True):
        """
        Initialize data leakage guard
        
        Args:
            strict_mode: Enable strict validation
            raise_on_violation: Raise exception on violation
            log_violations: Log all violations
        """
        self.strict_mode = strict_mode
        self.raise_on_violation = raise_on_violation
        self.log_violations = log_violations
        
        # Tracking
        self.violations: List[LeakageViolation] = []
        self.validated_features: Set[str] = set()
        self.feature_computation_times: Dict[str, datetime] = {}
        
        # Statistics
        self.stats = {
            'total_validations': 0,
            'violations_detected': 0,
            'features_validated': 0
        }
        
        logger.info(f"Data Leakage Guard initialized (strict_mode: {strict_mode})")
    
    def validate_feature_computation(self,
                                    feature_name: str,
                                    data: pd.DataFrame,
                                    computation_time: datetime,
                                    lookback_window: int,
                                    target_column: Optional[str] = None) -> bool:
        """
        Validate that feature computation doesn't use future data
        
        Args:
            feature_name: Name of feature being computed
            data: DataFrame with timestamp index
            computation_time: Time at which feature is computed
            lookback_window: Number of periods to look back
            target_column: Target variable column name
        
        Returns:
            True if validation passes
        
        Raises:
            ValueError: If leakage detected and raise_on_violation=True
        """
        self.stats['total_validations'] += 1
        
        violations = []
        
        # Check 1: Temporal ordering
        if not isinstance(data.index, pd.DatetimeIndex):
            violation = LeakageViolation(
                leakage_type=LeakageType.TEMPORAL_LEAKAGE,
                severity="HIGH",
                description=f"Feature {feature_name}: Data must have DatetimeIndex for temporal validation",
                affected_features=[feature_name]
            )
            violations.append(violation)
        else:
            # Check if any data is from the future
            future_data = data[data.index > computation_time]
            if len(future_data) > 0:
                violation = LeakageViolation(
                    leakage_type=LeakageType.LOOK_AHEAD,
                    severity="CRITICAL",
                    description=f"Feature {feature_name}: Uses {len(future_data)} future data points",
                    affected_features=[feature_name],
                    metadata={'future_points': len(future_data)}
                )
                violations.append(violation)
        
        # Check 2: Target leakage
        if target_column and target_column in data.columns:
            # Check if feature is highly correlated with target (potential leakage)
            if feature_name in data.columns:
                correlation = abs(data[feature_name].corr(data[target_column]))
                if correlation > 0.99:
                    violation = LeakageViolation(
                        leakage_type=LeakageType.TARGET_LEAKAGE,
                        severity="CRITICAL",
                        description=f"Feature {feature_name}: Suspiciously high correlation with target ({correlation:.4f})",
                        affected_features=[feature_name],
                        metadata={'correlation': correlation}
                    )
                    violations.append(violation)
        
        # Check 3: Lookback window validation
        if lookback_window > 0:
            required_data_points = lookback_window
            available_data_points = len(data[data.index <= computation_time])
            
            if available_data_points < required_data_points:
                violation = LeakageViolation(
                    leakage_type=LeakageType.TEMPORAL_LEAKAGE,
                    severity="HIGH",
                    description=f"Feature {feature_name}: Insufficient historical data "
                               f"(need {required_data_points}, have {available_data_points})",
                    affected_features=[feature_name],
                    metadata={
                        'required': required_data_points,
                        'available': available_data_points
                    }
                )
                violations.append(violation)
        
        # Handle violations
        if violations:
            self.stats['violations_detected'] += len(violations)
            self.violations.extend(violations)
            
            if self.log_violations:
                for v in violations:
                    logger.error(f"Data leakage detected: {v.description}")
            
            if self.raise_on_violation:
                raise ValueError(f"Data leakage detected in {feature_name}: {violations[0].description}")
            
            return False
        
        # Mark as validated
        self.validated_features.add(feature_name)
        self.feature_computation_times[feature_name] = computation_time
        self.stats['features_validated'] += 1
        
        return True
    
    def validate_train_test_split(self,
                                  train_data: pd.DataFrame,
                                  test_data: pd.DataFrame,
                                  time_column: Optional[str] = None) -> bool:
        """
        Validate train/test split for temporal leakage
        
        Args:
            train_data: Training dataset
            test_data: Test dataset
            time_column: Column name for timestamps
        
        Returns:
            True if validation passes
        """
        violations = []
        
        # Check 1: No overlap in indices
        train_indices = set(train_data.index)
        test_indices = set(test_data.index)
        overlap = train_indices.intersection(test_indices)
        
        if overlap:
            violation = LeakageViolation(
                leakage_type=LeakageType.TRAIN_TEST_CONTAMINATION,
                severity="CRITICAL",
                description=f"Train/test split: {len(overlap)} overlapping indices",
                affected_features=["train_test_split"],
                metadata={'overlap_count': len(overlap)}
            )
            violations.append(violation)
        
        # Check 2: Temporal ordering (if time column provided)
        if time_column:
            if time_column in train_data.columns and time_column in test_data.columns:
                max_train_time = train_data[time_column].max()
                min_test_time = test_data[time_column].min()
                
                if max_train_time >= min_test_time:
                    violation = LeakageViolation(
                        leakage_type=LeakageType.TEMPORAL_LEAKAGE,
                        severity="CRITICAL",
                        description=f"Train/test split: Training data extends into test period",
                        affected_features=["train_test_split"],
                        metadata={
                            'max_train_time': str(max_train_time),
                            'min_test_time': str(min_test_time)
                        }
                    )
                    violations.append(violation)
        
        # Handle violations
        if violations:
            self.violations.extend(violations)
            
            if self.log_violations:
                for v in violations:
                    logger.error(f"Train/test leakage: {v.description}")
            
            if self.raise_on_violation:
                raise ValueError(f"Train/test contamination detected")
            
            return False
        
        return True
    
    def validate_rolling_window(self,
                               data: pd.DataFrame,
                               window_size: int,
                               feature_columns: List[str],
                               current_time: datetime) -> bool:
        """
        Validate rolling window feature computation
        
        Args:
            data: DataFrame with features
            window_size: Size of rolling window
            feature_columns: Columns to validate
            current_time: Current timestamp
        
        Returns:
            True if validation passes
        """
        violations = []
        
        # Ensure data is sorted by time
        if isinstance(data.index, pd.DatetimeIndex):
            if not data.index.is_monotonic_increasing:
                violation = LeakageViolation(
                    leakage_type=LeakageType.TEMPORAL_LEAKAGE,
                    severity="HIGH",
                    description="Rolling window: Data not sorted by time",
                    affected_features=feature_columns
                )
                violations.append(violation)
            
            # Check for future data
            future_mask = data.index > current_time
            if future_mask.any():
                violation = LeakageViolation(
                    leakage_type=LeakageType.LOOK_AHEAD,
                    severity="CRITICAL",
                    description=f"Rolling window: Contains {future_mask.sum()} future data points",
                    affected_features=feature_columns,
                    metadata={'future_count': int(future_mask.sum())}
                )
                violations.append(violation)
        
        # Check window size
        valid_data = data[data.index <= current_time]
        if len(valid_data) < window_size:
            violation = LeakageViolation(
                leakage_type=LeakageType.TEMPORAL_LEAKAGE,
                severity="MEDIUM",
                description=f"Rolling window: Insufficient data (need {window_size}, have {len(valid_data)})",
                affected_features=feature_columns,
                metadata={'required': window_size, 'available': len(valid_data)}
            )
            violations.append(violation)
        
        if violations:
            self.violations.extend(violations)
            
            if self.log_violations:
                for v in violations:
                    logger.warning(f"Rolling window issue: {v.description}")
            
            if self.raise_on_violation and any(v.severity == "CRITICAL" for v in violations):
                raise ValueError("Critical rolling window violation detected")
            
            return False
        
        return True
    
    def create_safe_feature(self,
                           data: pd.DataFrame,
                           feature_name: str,
                           computation_func: callable,
                           lookback_window: int,
                           current_time: Optional[datetime] = None) -> pd.Series:
        """
        Create feature with automatic leakage prevention
        
        Args:
            data: Input data
            feature_name: Name of feature to create
            computation_func: Function to compute feature
            lookback_window: Lookback window size
            current_time: Current time (uses latest data time if None)
        
        Returns:
            Computed feature series
        """
        if current_time is None:
            if isinstance(data.index, pd.DatetimeIndex):
                current_time = data.index.max()
            else:
                current_time = datetime.now()
        
        # Filter to only past data
        if isinstance(data.index, pd.DatetimeIndex):
            past_data = data[data.index <= current_time]
        else:
            past_data = data
        
        # Ensure sufficient data
        if len(past_data) < lookback_window:
            logger.warning(f"Insufficient data for {feature_name}: need {lookback_window}, have {len(past_data)}")
            return pd.Series(index=data.index, dtype=float)
        try:
        
        # Compute feature
            feature = computation_func(past_data)
            
            # Validate
            self.validate_feature_computation(
                feature_name=feature_name,
                data=past_data,
                computation_time=current_time,
                lookback_window=lookback_window
            )
            
            return feature
            
        except Exception as e:
            logger.error(f"Error computing safe feature {feature_name}: {e}")
            raise
    
    def get_violations(self,
                      severity: Optional[str] = None,
                      leakage_type: Optional[LeakageType] = None) -> List[LeakageViolation]:
        """Get violations, optionally filtered"""
        violations = self.violations
        
        if severity:
            violations = [v for v in violations if v.severity == severity]
        
        if leakage_type:
            violations = [v for v in violations if v.leakage_type == leakage_type]
        
        return violations
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get guard statistics"""
        return {
            **self.stats,
            'total_violations': len(self.violations),
            'critical_violations': len([v for v in self.violations if v.severity == "CRITICAL"]),
            'validated_features': len(self.validated_features)
        }
    
    def generate_report(self) -> str:
        """Generate leakage detection report"""
        report = ["=" * 60]
        report.append("DATA LEAKAGE GUARD REPORT")
        report.append("=" * 60)
        
        stats = self.get_statistics()
        report.append(f"\nStatistics:")
        report.append(f"  Total validations: {stats['total_validations']}")
        report.append(f"  Features validated: {stats['features_validated']}")
        report.append(f"  Violations detected: {stats['violations_detected']}")
        report.append(f"  Critical violations: {stats['critical_violations']}")
        
        if self.violations:
            report.append(f"\nViolations by Type:")
            by_type = {}
            for v in self.violations:
                by_type[v.leakage_type.value] = by_type.get(v.leakage_type.value, 0) + 1
            
            for leak_type, count in by_type.items():
                report.append(f"  {leak_type}: {count}")
            
            report.append(f"\nCritical Violations:")
            critical = [v for v in self.violations if v.severity == "CRITICAL"]
            for v in critical[:10]:  # Show first 10
                report.append(f"  - {v.description}")
        
        report.append("=" * 60)
        return "\n".join(report)


# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Create guard
    guard = DataLeakageGuard(strict_mode=True, raise_on_violation=False)
    
    # Create test data
    dates = pd.date_range('2024-01-01', periods=100, freq='H')
    data = pd.DataFrame({
        'price': np.random.randn(100).cumsum() + 100,
        'volume': np.random.randint(1000, 10000, 100)
    }, index=dates)
    
    # Test 1: Valid feature computation
    current_time = dates[50]
    result = guard.validate_feature_computation(
        feature_name='sma_20',
        data=data[:51],  # Only past data
        computation_time=current_time,
        lookback_window=20
    )
    logger.info(f"Valid feature: {result}")
    
    # Test 2: Look-ahead bias (using future data)
    try:
        result = guard.validate_feature_computation(
            feature_name='future_sma',
            data=data,  # Includes future data!
            computation_time=current_time,
            lookback_window=20
        )
    except ValueError as e:
        logger.info(f"Caught leakage: {e}")
    
    # Test 3: Train/test split validation
    train = data[:70]
    test = data[70:]
    result = guard.validate_train_test_split(train, test, time_column=None)
    logger.info(f"Train/test valid: {result}")
    
    # Generate report
    print("\n" + guard.generate_report())
