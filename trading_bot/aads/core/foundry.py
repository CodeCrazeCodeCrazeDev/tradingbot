"""
AADS MODULE 1 — FOUNDRY: Data Sovereignty Layer

Absolute sovereignty over the data pipeline. All sources are:
- Version-controlled
- Schema-validated
- Lineage-tracked
- Timestamped with strict as_of enforcement to prevent lookahead contamination

Data Universe:
- Market microstructure (tick, OHLCV, L2, dark pool, options flow, futures)
- Macroeconomic signals (Fed, CPI, NFP, ISM, credit spreads, VIX)
- Alternative data (satellite, credit card, app rankings, shipping)
- On-chain and prediction markets (Polymarket, DeFi, whale wallets)
- Sentiment and NLP (SEC filings, earnings calls, news, social)
- Visual intelligence (earnings slides, satellite imagery, charts)

Nothing enters the system without a data contract.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Callable, Union, Type
from datetime import datetime, timedelta
from enum import Enum
import hashlib
import json
import logging
import uuid
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class DataCategory(Enum):
    """Categories of data sources in the AADS universe"""
    MARKET_MICROSTRUCTURE = "market_microstructure"
    MACROECONOMIC = "macroeconomic"
    ALTERNATIVE = "alternative"
    ONCHAIN = "onchain"
    PREDICTION_MARKET = "prediction_market"
    SENTIMENT = "sentiment"
    VISUAL = "visual"


class DataFrequency(Enum):
    """Data update frequencies"""
    TICK = "tick"
    SECOND = "second"
    MINUTE = "minute"
    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    EVENT_DRIVEN = "event_driven"


class DataQuality(Enum):
    """Data quality levels"""
    RAW = "raw"
    CLEANED = "cleaned"
    VALIDATED = "validated"
    PRODUCTION = "production"


@dataclass
class SchemaField:
    """Definition of a single field in a data schema"""
    name: str
    dtype: str  # "float", "int", "str", "datetime", "bool", "list", "dict"
    required: bool = True
    nullable: bool = False
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    allowed_values: Optional[List[Any]] = None
    description: str = ""


@dataclass
class DataSchema:
    """Schema definition for a data source"""
    schema_id: str
    name: str
    version: str
    fields: List[SchemaField]
    primary_key: List[str]
    timestamp_field: str
    created_at: datetime = field(default_factory=datetime.now)
    
    def validate(self, record: Dict[str, Any]) -> tuple[bool, List[str]]:
        """Validate a record against this schema"""
        errors = []
        
        for field_def in self.fields:
            value = record.get(field_def.name)
            
            # Check required
            if field_def.required and value is None:
                errors.append(f"Missing required field: {field_def.name}")
                continue
            
            if value is None and field_def.nullable:
                continue
            
            # Check type
            if not self._check_type(value, field_def.dtype):
                errors.append(f"Invalid type for {field_def.name}: expected {field_def.dtype}")
            
            # Check range
            if field_def.min_value is not None and isinstance(value, (int, float)):
                if value < field_def.min_value:
                    errors.append(f"{field_def.name} below min: {value} < {field_def.min_value}")
            
            if field_def.max_value is not None and isinstance(value, (int, float)):
                if value > field_def.max_value:
                    errors.append(f"{field_def.name} above max: {value} > {field_def.max_value}")
            
            # Check allowed values
            if field_def.allowed_values is not None and value not in field_def.allowed_values:
                errors.append(f"{field_def.name} not in allowed values: {value}")
        
        return len(errors) == 0, errors
    
    def _check_type(self, value: Any, dtype: str) -> bool:
        """Check if value matches expected type"""
        type_map = {
            "float": (int, float),
            "int": int,
            "str": str,
            "datetime": datetime,
            "bool": bool,
            "list": list,
            "dict": dict
        }
        expected = type_map.get(dtype)
        if expected is None:
            return True
        return isinstance(value, expected)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'schema_id': self.schema_id,
            'name': self.name,
            'version': self.version,
            'fields': [{'name': f.name, 'dtype': f.dtype, 'required': f.required} for f in self.fields],
            'primary_key': self.primary_key,
            'timestamp_field': self.timestamp_field
        }


@dataclass
class DataLineage:
    """Tracks the lineage of a data record"""
    lineage_id: str
    source_id: str
    source_name: str
    ingestion_time: datetime
    as_of_time: datetime  # Point-in-time timestamp
    transformation_chain: List[str] = field(default_factory=list)
    parent_lineage_ids: List[str] = field(default_factory=list)
    checksum: str = ""
    version: int = 1
    
    def add_transformation(self, transform_name: str) -> None:
        """Record a transformation applied to this data"""
        self.transformation_chain.append(f"{transform_name}@{datetime.now().isoformat()}")
        self.version += 1
    
    def compute_checksum(self, data: Any) -> str:
        """Compute checksum for data integrity"""
        data_str = json.dumps(data, sort_keys=True, default=str)
        self.checksum = hashlib.sha256(data_str.encode()).hexdigest()[:16]
        return self.checksum
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'lineage_id': self.lineage_id,
            'source_id': self.source_id,
            'source_name': self.source_name,
            'ingestion_time': self.ingestion_time.isoformat(),
            'as_of_time': self.as_of_time.isoformat(),
            'transformation_chain': self.transformation_chain,
            'parent_lineage_ids': self.parent_lineage_ids,
            'checksum': self.checksum,
            'version': self.version
        }


@dataclass
class DataContract:
    """
    Data contract defining expectations for a data source.
    Nothing enters the system without a data contract.
    """
    contract_id: str
    source_name: str
    category: DataCategory
    frequency: DataFrequency
    schema: DataSchema
    sla_latency_seconds: float  # Max acceptable latency
    sla_availability: float  # Required uptime (0-1)
    owner: str
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    is_active: bool = True
    
    # Quality expectations
    min_quality: DataQuality = DataQuality.VALIDATED
    max_null_pct: float = 0.05
    max_outlier_pct: float = 0.01
    
    # Lookahead prevention
    enforce_as_of: bool = True
    max_lookahead_seconds: float = 0.0
    
    def validate_record(self, record: Dict[str, Any], as_of: datetime) -> tuple[bool, List[str]]:
        """Validate a record against this contract"""
        errors = []
        
        # Schema validation
        schema_valid, schema_errors = self.schema.validate(record)
        errors.extend(schema_errors)
        
        # Lookahead check
        if self.enforce_as_of:
            record_time = record.get(self.schema.timestamp_field)
            if record_time and isinstance(record_time, datetime):
                if record_time > as_of + timedelta(seconds=self.max_lookahead_seconds):
                    errors.append(f"Lookahead violation: record time {record_time} > as_of {as_of}")
        
        return len(errors) == 0, errors
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'contract_id': self.contract_id,
            'source_name': self.source_name,
            'category': self.category.value,
            'frequency': self.frequency.value,
            'schema': self.schema.to_dict(),
            'sla_latency_seconds': self.sla_latency_seconds,
            'sla_availability': self.sla_availability,
            'owner': self.owner,
            'is_active': self.is_active
        }


@dataclass
class DataRecord:
    """A single data record with full lineage and validation"""
    record_id: str
    contract_id: str
    data: Dict[str, Any]
    lineage: DataLineage
    quality: DataQuality
    is_valid: bool = True
    validation_errors: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'record_id': self.record_id,
            'contract_id': self.contract_id,
            'data': self.data,
            'lineage': self.lineage.to_dict(),
            'quality': self.quality.value,
            'is_valid': self.is_valid,
            'validation_errors': self.validation_errors
        }


class DataSource(ABC):
    """Abstract base class for all data sources"""
    
    def __init__(self, contract: DataContract):
        self.contract = contract
        self.is_connected = False
        self.last_fetch_time: Optional[datetime] = None
        self.fetch_count = 0
        self.error_count = 0
    
    @abstractmethod
    async def connect(self) -> bool:
        """Connect to the data source"""
        pass
    
    @abstractmethod
    async def fetch(self, as_of: datetime) -> List[DataRecord]:
        """Fetch data with strict as_of enforcement"""
        pass
    
    @abstractmethod
    async def disconnect(self) -> None:
        """Disconnect from the data source"""
        pass
    
    def create_lineage(self, as_of: datetime) -> DataLineage:
        """Create lineage record for fetched data"""
        return DataLineage(
            lineage_id=str(uuid.uuid4()),
            source_id=self.contract.contract_id,
            source_name=self.contract.source_name,
            ingestion_time=datetime.now(),
            as_of_time=as_of
        )


class FoundryDataPipeline:
    """
    The Foundry Data Pipeline - Central data sovereignty layer.
    
    Manages all data sources, contracts, schemas, and lineage tracking.
    Enforces strict as_of semantics to prevent lookahead contamination.
    """
    
    def __init__(self):
        self.contracts: Dict[str, DataContract] = {}
        self.sources: Dict[str, DataSource] = {}
        self.schemas: Dict[str, DataSchema] = {}
        self.lineage_store: Dict[str, DataLineage] = {}
        self.data_store: Dict[str, List[DataRecord]] = {}
        
        # Initialize with core data contracts
        self._register_core_contracts()
        
        logger.info("FoundryDataPipeline initialized")
    
    def _register_core_contracts(self) -> None:
        """Register core data contracts for AADS"""
        
        # Market Microstructure - OHLCV
        ohlcv_schema = DataSchema(
            schema_id="ohlcv_v1",
            name="OHLCV Price Data",
            version="1.0",
            fields=[
                SchemaField("symbol", "str", required=True),
                SchemaField("timestamp", "datetime", required=True),
                SchemaField("open", "float", required=True, min_value=0),
                SchemaField("high", "float", required=True, min_value=0),
                SchemaField("low", "float", required=True, min_value=0),
                SchemaField("close", "float", required=True, min_value=0),
                SchemaField("volume", "float", required=True, min_value=0),
                SchemaField("vwap", "float", required=False, min_value=0),
            ],
            primary_key=["symbol", "timestamp"],
            timestamp_field="timestamp"
        )
        
        self.register_contract(DataContract(
            contract_id="ohlcv_equity",
            source_name="Polygon.io OHLCV",
            category=DataCategory.MARKET_MICROSTRUCTURE,
            frequency=DataFrequency.MINUTE,
            schema=ohlcv_schema,
            sla_latency_seconds=5.0,
            sla_availability=0.999,
            owner="market_data_team"
        ))
        
        # Level 2 Order Book
        l2_schema = DataSchema(
            schema_id="l2_orderbook_v1",
            name="Level 2 Order Book",
            version="1.0",
            fields=[
                SchemaField("symbol", "str", required=True),
                SchemaField("timestamp", "datetime", required=True),
                SchemaField("bids", "list", required=True),
                SchemaField("asks", "list", required=True),
                SchemaField("bid_depth", "float", required=True),
                SchemaField("ask_depth", "float", required=True),
                SchemaField("spread_bps", "float", required=True),
            ],
            primary_key=["symbol", "timestamp"],
            timestamp_field="timestamp"
        )
        
        self.register_contract(DataContract(
            contract_id="l2_orderbook",
            source_name="Alpaca L2 WebSocket",
            category=DataCategory.MARKET_MICROSTRUCTURE,
            frequency=DataFrequency.TICK,
            schema=l2_schema,
            sla_latency_seconds=0.1,
            sla_availability=0.999,
            owner="market_data_team"
        ))
        
        # Options Flow
        options_schema = DataSchema(
            schema_id="options_flow_v1",
            name="Options Flow Data",
            version="1.0",
            fields=[
                SchemaField("symbol", "str", required=True),
                SchemaField("timestamp", "datetime", required=True),
                SchemaField("call_volume", "int", required=True),
                SchemaField("put_volume", "int", required=True),
                SchemaField("put_call_ratio", "float", required=True),
                SchemaField("unusual_activity", "bool", required=True),
                SchemaField("gex", "float", required=False),
                SchemaField("dex", "float", required=False),
                SchemaField("iv_skew", "float", required=False),
            ],
            primary_key=["symbol", "timestamp"],
            timestamp_field="timestamp"
        )
        
        self.register_contract(DataContract(
            contract_id="options_flow",
            source_name="Options Flow Analytics",
            category=DataCategory.MARKET_MICROSTRUCTURE,
            frequency=DataFrequency.MINUTE,
            schema=options_schema,
            sla_latency_seconds=60.0,
            sla_availability=0.99,
            owner="derivatives_team"
        ))
        
        # Macroeconomic Data
        macro_schema = DataSchema(
            schema_id="macro_indicator_v1",
            name="Macroeconomic Indicator",
            version="1.0",
            fields=[
                SchemaField("indicator", "str", required=True),
                SchemaField("timestamp", "datetime", required=True),
                SchemaField("value", "float", required=True),
                SchemaField("prior", "float", required=False),
                SchemaField("forecast", "float", required=False),
                SchemaField("surprise", "float", required=False),
                SchemaField("revision", "float", required=False),
            ],
            primary_key=["indicator", "timestamp"],
            timestamp_field="timestamp"
        )
        
        self.register_contract(DataContract(
            contract_id="macro_indicators",
            source_name="Economic Calendar",
            category=DataCategory.MACROECONOMIC,
            frequency=DataFrequency.EVENT_DRIVEN,
            schema=macro_schema,
            sla_latency_seconds=1.0,
            sla_availability=0.999,
            owner="macro_team"
        ))
        
        # Sentiment Data
        sentiment_schema = DataSchema(
            schema_id="sentiment_v1",
            name="Sentiment Score",
            version="1.0",
            fields=[
                SchemaField("entity", "str", required=True),
                SchemaField("entity_type", "str", required=True, allowed_values=["asset", "sector", "macro"]),
                SchemaField("timestamp", "datetime", required=True),
                SchemaField("sentiment_score", "float", required=True, min_value=-1, max_value=1),
                SchemaField("confidence", "float", required=True, min_value=0, max_value=1),
                SchemaField("source", "str", required=True),
                SchemaField("article_count", "int", required=False),
            ],
            primary_key=["entity", "source", "timestamp"],
            timestamp_field="timestamp"
        )
        
        self.register_contract(DataContract(
            contract_id="sentiment_news",
            source_name="FinBERT News Sentiment",
            category=DataCategory.SENTIMENT,
            frequency=DataFrequency.HOURLY,
            schema=sentiment_schema,
            sla_latency_seconds=300.0,
            sla_availability=0.99,
            owner="nlp_team"
        ))
        
        # Polymarket Data
        polymarket_schema = DataSchema(
            schema_id="polymarket_v1",
            name="Polymarket Contract",
            version="1.0",
            fields=[
                SchemaField("contract_id", "str", required=True),
                SchemaField("question", "str", required=True),
                SchemaField("timestamp", "datetime", required=True),
                SchemaField("yes_price", "float", required=True, min_value=0, max_value=1),
                SchemaField("no_price", "float", required=True, min_value=0, max_value=1),
                SchemaField("volume_24h", "float", required=True),
                SchemaField("liquidity", "float", required=True),
                SchemaField("closes_at", "datetime", required=True),
            ],
            primary_key=["contract_id", "timestamp"],
            timestamp_field="timestamp"
        )
        
        self.register_contract(DataContract(
            contract_id="polymarket",
            source_name="Polymarket CLOB",
            category=DataCategory.PREDICTION_MARKET,
            frequency=DataFrequency.MINUTE,
            schema=polymarket_schema,
            sla_latency_seconds=5.0,
            sla_availability=0.99,
            owner="prediction_markets_team"
        ))
        
        # Visual Signal Data
        visual_schema = DataSchema(
            schema_id="visual_signal_v1",
            name="Visual Signal",
            version="1.0",
            fields=[
                SchemaField("signal_id", "str", required=True),
                SchemaField("timestamp", "datetime", required=True),
                SchemaField("image_hash", "str", required=True),
                SchemaField("category", "str", required=True),
                SchemaField("sentiment", "str", required=True, allowed_values=["bullish", "bearish", "neutral"]),
                SchemaField("confidence", "float", required=True, min_value=0, max_value=1),
                SchemaField("affected_assets", "list", required=False),
            ],
            primary_key=["signal_id"],
            timestamp_field="timestamp"
        )
        
        self.register_contract(DataContract(
            contract_id="visual_signals",
            source_name="OpenCLIP Visual Pipeline",
            category=DataCategory.VISUAL,
            frequency=DataFrequency.EVENT_DRIVEN,
            schema=visual_schema,
            sla_latency_seconds=60.0,
            sla_availability=0.95,
            owner="vision_team"
        ))
        
        logger.info(f"Registered {len(self.contracts)} core data contracts")
    
    def register_contract(self, contract: DataContract) -> None:
        """Register a new data contract"""
        self.contracts[contract.contract_id] = contract
        self.schemas[contract.schema.schema_id] = contract.schema
        self.data_store[contract.contract_id] = []
        logger.info(f"Registered contract: {contract.source_name}")
    
    def register_source(self, source: DataSource) -> None:
        """Register a data source"""
        self.sources[source.contract.contract_id] = source
        logger.info(f"Registered source: {source.contract.source_name}")
    
    def ingest(
        self,
        contract_id: str,
        data: Dict[str, Any],
        as_of: datetime,
        parent_lineage_ids: Optional[List[str]] = None
    ) -> Optional[DataRecord]:
        """
        Ingest a data record with full validation and lineage tracking.
        Enforces strict as_of semantics to prevent lookahead.
        """
        contract = self.contracts.get(contract_id)
        if not contract:
            logger.error(f"Unknown contract: {contract_id}")
            return None
        
        # Validate against contract
        is_valid, errors = contract.validate_record(data, as_of)
        
        # Create lineage
        lineage = DataLineage(
            lineage_id=str(uuid.uuid4()),
            source_id=contract_id,
            source_name=contract.source_name,
            ingestion_time=datetime.now(),
            as_of_time=as_of,
            parent_lineage_ids=parent_lineage_ids or []
        )
        lineage.compute_checksum(data)
        
        # Create record
        record = DataRecord(
            record_id=str(uuid.uuid4()),
            contract_id=contract_id,
            data=data,
            lineage=lineage,
            quality=DataQuality.VALIDATED if is_valid else DataQuality.RAW,
            is_valid=is_valid,
            validation_errors=errors
        )
        
        # Store
        self.data_store[contract_id].append(record)
        self.lineage_store[lineage.lineage_id] = lineage
        
        if not is_valid:
            logger.warning(f"Invalid record ingested: {errors}")
        
        return record
    
    def query(
        self,
        contract_id: str,
        as_of: datetime,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 1000
    ) -> List[DataRecord]:
        """
        Query data with strict as_of enforcement.
        Only returns data that was available at the as_of timestamp.
        """
        records = self.data_store.get(contract_id, [])
        
        # Filter by as_of (no lookahead)
        valid_records = [
            r for r in records
            if r.lineage.as_of_time <= as_of and r.is_valid
        ]
        
        # Apply additional filters
        if filters:
            for key, value in filters.items():
                valid_records = [
                    r for r in valid_records
                    if r.data.get(key) == value
                ]
        
        # Sort by timestamp descending, limit
        valid_records.sort(
            key=lambda r: r.lineage.as_of_time,
            reverse=True
        )
        
        return valid_records[:limit]
    
    def get_lineage(self, lineage_id: str) -> Optional[DataLineage]:
        """Get lineage record by ID"""
        return self.lineage_store.get(lineage_id)
    
    def trace_lineage(self, lineage_id: str) -> List[DataLineage]:
        """Trace full lineage chain back to source"""
        chain = []
        current = self.get_lineage(lineage_id)
        
        while current:
            chain.append(current)
            if current.parent_lineage_ids:
                current = self.get_lineage(current.parent_lineage_ids[0])
            else:
                break
        
        return chain
    
    def get_contract_stats(self, contract_id: str) -> Dict[str, Any]:
        """Get statistics for a data contract"""
        records = self.data_store.get(contract_id, [])
        valid_records = [r for r in records if r.is_valid]
        
        return {
            'contract_id': contract_id,
            'total_records': len(records),
            'valid_records': len(valid_records),
            'invalid_records': len(records) - len(valid_records),
            'validity_rate': len(valid_records) / max(len(records), 1),
            'latest_ingestion': max(
                (r.lineage.ingestion_time for r in records),
                default=None
            )
        }
    
    def get_pipeline_health(self) -> Dict[str, Any]:
        """Get overall pipeline health status"""
        stats = {
            'total_contracts': len(self.contracts),
            'active_contracts': sum(1 for c in self.contracts.values() if c.is_active),
            'total_sources': len(self.sources),
            'connected_sources': sum(1 for s in self.sources.values() if s.is_connected),
            'total_records': sum(len(r) for r in self.data_store.values()),
            'total_lineage_entries': len(self.lineage_store),
            'contracts': {
                cid: self.get_contract_stats(cid)
                for cid in self.contracts
            }
        }
        return stats


# Singleton instance
_foundry_instance: Optional[FoundryDataPipeline] = None


def get_foundry() -> FoundryDataPipeline:
    """Get the global Foundry instance"""
    global _foundry_instance
    if _foundry_instance is None:
        _foundry_instance = FoundryDataPipeline()
    return _foundry_instance
