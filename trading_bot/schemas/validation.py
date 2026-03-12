"""
Validation Schema Definitions
Defines Pydantic models for validation, testing, and performance monitoring
"""

from pydantic import BaseModel, Field, validator
from typing import Any, Callable, Dict, List, Optional, Union
from datetime import datetime
from enum import Enum
from uuid import uuid4
import numpy as np
import numpy

import logging
logger = logging.getLogger(__name__)



class ValidationLevel(str, Enum):
    """Validation levels for different contexts"""
    STRICT = "strict"  # Fail on any validation error
    STANDARD = "standard"  # Fail on critical errors, warn on others
    PERMISSIVE = "permissive"  # Only warn, never fail
    SILENT = "silent"  # No validation


class ValidationResult(BaseModel):
    """Result of a validation check"""
    valid: bool
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class SchemaValidationConfig(BaseModel):
    """Configuration for schema validation"""
    level: ValidationLevel = ValidationLevel.STANDARD
    strict_fields: List[str] = Field(default_factory=list)
    optional_fields: List[str] = Field(default_factory=list)
    custom_validators: Dict[str, Callable] = Field(default=None)
    
    class Config:
        arbitrary_types_allowed = True


class TestCase(BaseModel):
    """Test case definition for trading system components"""
    test_id: str = Field(default_factory=lambda: f"TEST_{uuid4().hex[:8]}")
    name: str
    description: str
    component: str
    inputs: Dict[str, Any]
    expected_outputs: Dict[str, Any]
    timeout_seconds: float = 10.0
    tags: List[str] = Field(default_factory=list)
    enabled: bool = True


class TestResult(BaseModel):
    """Result of a test execution"""
    test_id: str
    success: bool
    execution_time: float  # seconds
    actual_outputs: Dict[str, Any]
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=datetime.now)


class TestSuite(BaseModel):
    """Collection of test cases"""
    suite_id: str = Field(default_factory=lambda: f"SUITE_{uuid4().hex[:8]}")
    name: str
    description: str
    test_cases: List[TestCase]
    setup: Optional[Dict[str, Any]] = None
    teardown: Optional[Dict[str, Any]] = None


class TestReport(BaseModel):
    """Test execution report"""
    suite_id: str
    timestamp: datetime = Field(default_factory=datetime.now)
    total_tests: int
    passed_tests: int
    failed_tests: int
    skipped_tests: int
    total_execution_time: float  # seconds
    results: List[TestResult]
    summary: str
    
    @validator('passed_tests', 'failed_tests', 'skipped_tests')
    def validate_counts(cls, v, values):
        try:
            if 'total_tests' in values and v > values['total_tests']:
                raise ValueError(f"Count ({v}) cannot exceed total tests ({values['total_tests']})")
            return v
        except Exception as e:
            logger.error(f"Error in validate_counts: {e}")
            raise


class LatencyMeasurement(BaseModel):
    """Latency measurement for performance monitoring"""
    component: str
    operation: str
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_ms: Optional[float] = None
    success: bool = True
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    def complete(self) -> 'LatencyMeasurement':
        """Complete the latency measurement"""
        try:
            self.end_time = datetime.now()
            self.duration_ms = (self.end_time - self.start_time).total_seconds() * 1000
            return self
        except Exception as e:
            logger.error(f"Error in complete: {e}")
            raise


class PerformanceThresholds(BaseModel):
    """Performance thresholds for monitoring"""
    max_latency_ms: Dict[str, float]  # component -> max latency
    max_error_rate: float = 0.01  # 1%
    max_memory_usage_mb: float = 1000  # 1GB
    max_cpu_usage_percent: float = 80
    min_throughput: Dict[str, float]  # component -> min throughput


class PerformanceReport(BaseModel):
    """Performance monitoring report"""
    timestamp: datetime = Field(default_factory=datetime.now)
    latency_metrics: Dict[str, Dict[str, float]]  # component -> metric -> value
    throughput_metrics: Dict[str, float]  # component -> throughput
    error_rates: Dict[str, float]  # component -> error rate
    resource_usage: Dict[str, float]  # resource -> usage
    bottlenecks: List[Dict[str, Any]] = Field(default_factory=list)
    alerts: List[Dict[str, Any]] = Field(default_factory=list)
    
    def get_p95_latency(self, component: str) -> Optional[float]:
        """Get P95 latency for a component"""
        try:
            if component in self.latency_metrics and 'p95' in self.latency_metrics[component]:
                return self.latency_metrics[component]['p95']
            return None
        except Exception as e:
            logger.error(f"Error in get_p95_latency: {e}")
            raise
    
    def get_average_latency(self, component: str) -> Optional[float]:
        """Get average latency for a component"""
        try:
            if component in self.latency_metrics and 'avg' in self.latency_metrics[component]:
                return self.latency_metrics[component]['avg']
            return None
        except Exception as e:
            logger.error(f"Error in get_average_latency: {e}")
            raise


class SyntheticDataConfig(BaseModel):
    """Configuration for synthetic data generation"""
    symbols: List[str]
    start_time: datetime
    end_time: datetime
    timeframes: List[str]
    tick_frequency_ms: int = 100  # milliseconds between ticks
    volatility: float = 0.01
    trend: float = 0.0
    random_seed: Optional[int] = None
    include_gaps: bool = True
    include_anomalies: bool = True
    anomaly_frequency: float = 0.01  # 1% of data points are anomalies


class BacktestConfig(BaseModel):
    """Configuration for backtesting"""
    start_date: datetime
    end_date: datetime
    symbols: List[str]
    initial_capital: float
    timeframes: List[str]
    commission_rate: float = 0.001  # 0.1%
    slippage_model: str = "fixed"  # "fixed", "percentage", "market_impact"
    slippage_value: float = 0.0001  # 1 pip for fixed, 0.01% for percentage
    data_source: str = "sqlite"  # "sqlite", "csv", "parquet"
    data_path: str
    
    @validator('end_date')
    def validate_dates(cls, v, values):
        try:
            if 'start_date' in values and v <= values['start_date']:
                raise ValueError("End date must be after start date")
            return v
        except Exception as e:
            logger.error(f"Error in validate_dates: {e}")
            raise
    
    @validator('initial_capital', 'commission_rate', 'slippage_value')
    def validate_positive(cls, v):
        try:
            if v < 0:
                raise ValueError("Value must be non-negative")
            return v
        except Exception as e:
            logger.error(f"Error in validate_positive: {e}")
            raise


class LiveParityTestConfig(BaseModel):
    """Configuration for live-parity testing"""
    symbols: List[str]
    duration_minutes: int
    max_trades: int
    max_capital_usage_percent: float = 10.0  # Use at most 10% of capital
    compare_with_backtest: bool = True
    backtest_id: Optional[str] = None
    enable_execution: bool = False  # If True, actually execute trades
    
    @validator('max_capital_usage_percent')
    def validate_capital_usage(cls, v):
        try:
            if not 0 < v <= 100:
                raise ValueError("Capital usage percent must be between 0 and 100")
            return v
        except Exception as e:
            logger.error(f"Error in validate_capital_usage: {e}")
            raise
