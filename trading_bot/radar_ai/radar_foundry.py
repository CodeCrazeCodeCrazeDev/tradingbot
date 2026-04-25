"""
RadarFoundry - Data Operations Platform
========================================

Inspired by Palantir Foundry, this module handles:
- Data ingestion from multiple sources
- Data transformation and normalization
- Data pipeline orchestration
- Data quality monitoring
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum, auto
from typing import Any, Callable, Dict, List, Optional, Set
import uuid

logger = logging.getLogger(__name__)


class DataSourceType(Enum):
    """Types of data sources"""
    MARKET_DATA = "market_data"
    ALTERNATIVE_DATA = "alternative_data"
    NEWS = "news"
    SENTIMENT = "sentiment"
    ECONOMIC = "economic"
    FUNDAMENTAL = "fundamental"
    TECHNICAL = "technical"


class DataQuality(Enum):
    """Data quality levels"""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    UNKNOWN = "unknown"


@dataclass
class DataSource:
    """A data source configuration"""
    source_id: str
    name: str
    source_type: DataSourceType
    endpoint: str
    credentials: Optional[Dict[str, str]] = None
    refresh_interval_seconds: int = 60
    is_active: bool = True
    quality: DataQuality = DataQuality.UNKNOWN
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'source_id': self.source_id,
            'name': self.name,
            'source_type': self.source_type.value,
            'endpoint': self.endpoint,
            'refresh_interval_seconds': self.refresh_interval_seconds,
            'is_active': self.is_active,
            'quality': self.quality.value,
        }


@dataclass
class DataRecord:
    """A single data record"""
    record_id: str
    source_id: str
    timestamp: datetime
    data_type: str
    payload: Dict[str, Any]
    quality_score: float = 1.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'record_id': self.record_id,
            'source_id': self.source_id,
            'timestamp': self.timestamp.isoformat(),
            'data_type': self.data_type,
            'payload': self.payload,
            'quality_score': self.quality_score,
        }


class DataPipeline:
    """
    Data pipeline for processing and transforming data.
    """
    
    def __init__(self, name: str):
        self.pipeline_id = f"PIPE-{uuid.uuid4().hex[:8]}"
        self.name = name
        self.stages: List[Callable] = []
        self.is_running = False
        self.records_processed = 0
        
    def add_stage(self, stage: Callable):
        """Add a processing stage to the pipeline"""
        self.stages.append(stage)
        return self
    
    async def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process data through all stages"""
        result = data
        
        for stage in self.stages:
            try:
                if asyncio.iscoroutinefunction(stage):
                    result = await stage(result)
                else:
                    result = stage(result)
            except Exception as e:
                logger.error(f"Pipeline stage error: {e}")
                result['_pipeline_error'] = str(e)
                break
        
        self.records_processed += 1
        return result
    
    def get_status(self) -> Dict[str, Any]:
        """Get pipeline status"""
        return {
            'pipeline_id': self.pipeline_id,
            'name': self.name,
            'stages': len(self.stages),
            'is_running': self.is_running,
            'records_processed': self.records_processed,
        }


class RadarFoundry:
    """
    RadarFoundry - Central data operations platform.
    
    Manages:
    - Data sources
    - Data pipelines
    - Data quality
    - Data lineage
    """
    
    def __init__(self):
        self.foundry_id = f"FOUNDRY-{uuid.uuid4().hex[:8]}"
        self.sources: Dict[str, DataSource] = {}
        self.pipelines: Dict[str, DataPipeline] = {}
        self.data_store: Dict[str, List[DataRecord]] = {}
        self.quality_metrics: Dict[str, float] = {}
        
        logger.info(f"RadarFoundry initialized: {self.foundry_id}")
    
    def register_source(self, source: DataSource):
        """Register a data source"""
        self.sources[source.source_id] = source
        self.data_store[source.source_id] = []
        logger.info(f"Registered data source: {source.name}")
    
    def create_pipeline(self, name: str) -> DataPipeline:
        """Create a new data pipeline"""
        pipeline = DataPipeline(name)
        self.pipelines[pipeline.pipeline_id] = pipeline
        return pipeline
    
    async def ingest(self, source_id: str, data: Dict[str, Any]) -> DataRecord:
        """Ingest data from a source"""
        source = self.sources.get(source_id)
        if not source:
            raise ValueError(f"Unknown source: {source_id}")
        
        record = DataRecord(
            record_id=f"REC-{uuid.uuid4().hex[:8]}",
            source_id=source_id,
            timestamp=datetime.now(timezone.utc),
            data_type=source.source_type.value,
            payload=data,
            quality_score=self._assess_quality(data),
        )
        
        self.data_store[source_id].append(record)
        
        # Trim old records
        if len(self.data_store[source_id]) > 10000:
            self.data_store[source_id] = self.data_store[source_id][-5000:]
        
        return record
    
    def _assess_quality(self, data: Dict[str, Any]) -> float:
        """Assess data quality"""
        score = 1.0
        
        # Check for missing values
        if not data:
            return 0.0
        
        # Check for null values
        null_count = sum(1 for v in data.values() if v is None)
        score -= null_count * 0.1
        
        return max(0.0, min(1.0, score))
    
    async def query(
        self,
        source_id: Optional[str] = None,
        data_type: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100,
    ) -> List[DataRecord]:
        """Query data records"""
        results = []
        
        sources_to_query = [source_id] if source_id else list(self.data_store.keys())
        
        for sid in sources_to_query:
            records = self.data_store.get(sid, [])
            
            for record in records:
                if data_type and record.data_type != data_type:
                    continue
                if start_time and record.timestamp < start_time:
                    continue
                if end_time and record.timestamp > end_time:
                    continue
                
                results.append(record)
                
                if len(results) >= limit:
                    break
            
            if len(results) >= limit:
                break
        
        return results
    
    def get_status(self) -> Dict[str, Any]:
        """Get foundry status"""
        return {
            'foundry_id': self.foundry_id,
            'sources': len(self.sources),
            'pipelines': len(self.pipelines),
            'total_records': sum(len(r) for r in self.data_store.values()),
        }
