"""
Decision Attribution Engine
============================
Every trading signal MUST output complete attribution.

REQUIRED FIELDS:
- feature_snapshot_hash: SHA256 of feature vector at decision time
- contributing_models: List of models with weights and confidence
- latent_regime_id: Current market regime classification
- historical_analogs: Similar past situations
- expected_outcome: Predicted direction and magnitude
- realized_outcome: Actual result (filled post-trade)
- confidence_score: Overall signal confidence
- reasoning_chain: Step-by-step logic trace

SCHEMA:
{
    "signal_id": "uuid",
    "timestamp": "ISO8601",
    "feature_snapshot_hash": "sha256:...",
    "contributing_models": [
        {"model_id": "...", "version": "...", "weight": 0.4, "confidence": 0.85}
    ],
    "latent_regime_id": "regime_cluster_7",
    "historical_analogs": [
        {"date": "2023-03-15", "similarity": 0.92, "outcome": 0.015}
    ],
    "expected_outcome": {"direction": "LONG", "magnitude": 0.02, "horizon": "1h"},
    "realized_outcome": null,  // Filled after trade completes
    "confidence_score": 0.78,
    "reasoning_chain": ["high_imbalance", "trend_confirmed", "vol_low"]
}

STORAGE:
- Hot storage: Last 7 days (fast query)
- Cold storage: Forever (compressed, indexed)

QUERY INTERFACE:
- By signal_id
- By time range
- By regime
- By model
- By outcome (win/loss)

DEBUG WORKFLOWS:
- "Why did signal X fail?"
- "What features drove signal Y?"
- "Compare attribution across regime Z"
"""

import hashlib
import json
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Tuple
from threading import RLock

logger = logging.getLogger(__name__)


class SignalDirection(Enum):
    """Signal direction."""
    LONG = "LONG"
    SHORT = "SHORT"
    FLAT = "FLAT"


class OutcomeStatus(Enum):
    """Outcome status."""
    PENDING = "pending"
    WIN = "win"
    LOSS = "loss"
    BREAKEVEN = "breakeven"
    CANCELLED = "cancelled"


@dataclass
class FeatureSnapshot:
    """Snapshot of features at decision time."""
    timestamp: datetime
    features: Dict[str, float]
    hash: str = ""
    
    def __post_init__(self):
        if not self.hash:
            self.hash = self._compute_hash()
    
    def _compute_hash(self) -> str:
        """Compute deterministic hash of features."""
        # Sort keys for determinism
        sorted_features = json.dumps(
            {k: round(v, 8) for k, v in sorted(self.features.items())},
            sort_keys=True
        )
        return f"sha256:{hashlib.sha256(sorted_features.encode()).hexdigest()}"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp.isoformat(),
            "features": self.features,
            "hash": self.hash,
        }


@dataclass
class ModelContribution:
    """Contribution from a single model."""
    model_id: str
    version: str
    weight: float
    confidence: float
    raw_output: Any
    features_used: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "model_id": self.model_id,
            "version": self.version,
            "weight": self.weight,
            "confidence": self.confidence,
            "raw_output": self.raw_output,
            "features_used": self.features_used,
        }


@dataclass
class HistoricalAnalog:
    """A similar historical situation."""
    date: datetime
    similarity: float
    outcome: float
    regime_id: str
    features_matched: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "date": self.date.isoformat(),
            "similarity": self.similarity,
            "outcome": self.outcome,
            "regime_id": self.regime_id,
            "features_matched": self.features_matched,
        }


@dataclass
class ExpectedOutcome:
    """Expected outcome prediction."""
    direction: SignalDirection
    magnitude: float
    horizon: str  # e.g., "1h", "4h", "1d"
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    probability: float = 0.5
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "direction": self.direction.value,
            "magnitude": self.magnitude,
            "horizon": self.horizon,
            "stop_loss": self.stop_loss,
            "take_profit": self.take_profit,
            "probability": self.probability,
        }


@dataclass
class RealizedOutcome:
    """Actual outcome after trade completion."""
    status: OutcomeStatus
    pnl: float
    pnl_percent: float
    entry_price: float
    exit_price: float
    entry_time: datetime
    exit_time: datetime
    slippage: float
    fees: float
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status.value,
            "pnl": self.pnl,
            "pnl_percent": self.pnl_percent,
            "entry_price": self.entry_price,
            "exit_price": self.exit_price,
            "entry_time": self.entry_time.isoformat(),
            "exit_time": self.exit_time.isoformat(),
            "slippage": self.slippage,
            "fees": self.fees,
        }


@dataclass
class AttributionRecord:
    """Complete attribution record for a trading signal."""
    signal_id: str
    symbol: str
    timestamp: datetime
    feature_snapshot: FeatureSnapshot
    contributing_models: List[ModelContribution]
    latent_regime_id: str
    historical_analogs: List[HistoricalAnalog]
    expected_outcome: ExpectedOutcome
    realized_outcome: Optional[RealizedOutcome]
    confidence_score: float
    reasoning_chain: List[str]
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "signal_id": self.signal_id,
            "symbol": self.symbol,
            "timestamp": self.timestamp.isoformat(),
            "feature_snapshot": self.feature_snapshot.to_dict(),
            "feature_snapshot_hash": self.feature_snapshot.hash,
            "contributing_models": [m.to_dict() for m in self.contributing_models],
            "latent_regime_id": self.latent_regime_id,
            "historical_analogs": [a.to_dict() for a in self.historical_analogs],
            "expected_outcome": self.expected_outcome.to_dict(),
            "realized_outcome": self.realized_outcome.to_dict() if self.realized_outcome else None,
            "confidence_score": self.confidence_score,
            "reasoning_chain": self.reasoning_chain,
            "metadata": self.metadata,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AttributionRecord":
        """Create from dictionary."""
        return cls(
            signal_id=data["signal_id"],
            symbol=data["symbol"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            feature_snapshot=FeatureSnapshot(
                timestamp=datetime.fromisoformat(data["feature_snapshot"]["timestamp"]),
                features=data["feature_snapshot"]["features"],
                hash=data["feature_snapshot"]["hash"],
            ),
            contributing_models=[
                ModelContribution(**m) for m in data["contributing_models"]
            ],
            latent_regime_id=data["latent_regime_id"],
            historical_analogs=[
                HistoricalAnalog(
                    date=datetime.fromisoformat(a["date"]),
                    similarity=a["similarity"],
                    outcome=a["outcome"],
                    regime_id=a["regime_id"],
                    features_matched=a.get("features_matched", []),
                )
                for a in data["historical_analogs"]
            ],
            expected_outcome=ExpectedOutcome(
                direction=SignalDirection(data["expected_outcome"]["direction"]),
                magnitude=data["expected_outcome"]["magnitude"],
                horizon=data["expected_outcome"]["horizon"],
                stop_loss=data["expected_outcome"].get("stop_loss"),
                take_profit=data["expected_outcome"].get("take_profit"),
                probability=data["expected_outcome"].get("probability", 0.5),
            ),
            realized_outcome=RealizedOutcome(
                status=OutcomeStatus(data["realized_outcome"]["status"]),
                pnl=data["realized_outcome"]["pnl"],
                pnl_percent=data["realized_outcome"]["pnl_percent"],
                entry_price=data["realized_outcome"]["entry_price"],
                exit_price=data["realized_outcome"]["exit_price"],
                entry_time=datetime.fromisoformat(data["realized_outcome"]["entry_time"]),
                exit_time=datetime.fromisoformat(data["realized_outcome"]["exit_time"]),
                slippage=data["realized_outcome"]["slippage"],
                fees=data["realized_outcome"]["fees"],
            ) if data.get("realized_outcome") else None,
            confidence_score=data["confidence_score"],
            reasoning_chain=data["reasoning_chain"],
            metadata=data.get("metadata", {}),
        )


@dataclass
class AttributionQuery:
    """Query for attribution records."""
    signal_ids: Optional[List[str]] = None
    symbols: Optional[List[str]] = None
    time_range: Optional[Tuple[datetime, datetime]] = None
    regime_ids: Optional[List[str]] = None
    model_ids: Optional[List[str]] = None
    outcome_status: Optional[List[OutcomeStatus]] = None
    min_confidence: Optional[float] = None
    max_confidence: Optional[float] = None
    limit: int = 100
    offset: int = 0


class AttributionStore:
    """Storage for attribution records."""
    
    HOT_RETENTION_DAYS = 7
    
    def __init__(self, storage_path: Optional[str] = None):
        self.storage_path = storage_path
        self._hot_store: Dict[str, AttributionRecord] = {}
        self._cold_store: Dict[str, AttributionRecord] = {}
        self._lock = RLock()
        
        # Indexes for fast queries
        self._by_symbol: Dict[str, List[str]] = {}
        self._by_regime: Dict[str, List[str]] = {}
        self._by_model: Dict[str, List[str]] = {}
        self._by_date: Dict[str, List[str]] = {}
    
    def store(self, record: AttributionRecord) -> bool:
        """Store an attribution record."""
        with self._lock:
            self._hot_store[record.signal_id] = record
            
            # Update indexes
            if record.symbol not in self._by_symbol:
                self._by_symbol[record.symbol] = []
            self._by_symbol[record.symbol].append(record.signal_id)
            
            if record.latent_regime_id not in self._by_regime:
                self._by_regime[record.latent_regime_id] = []
            self._by_regime[record.latent_regime_id].append(record.signal_id)
            
            for model in record.contributing_models:
                if model.model_id not in self._by_model:
                    self._by_model[model.model_id] = []
                self._by_model[model.model_id].append(record.signal_id)
            
            date_key = record.timestamp.date().isoformat()
            if date_key not in self._by_date:
                self._by_date[date_key] = []
            self._by_date[date_key].append(record.signal_id)
            
            return True
    
    def get(self, signal_id: str) -> Optional[AttributionRecord]:
        """Get a single attribution record."""
        with self._lock:
            record = self._hot_store.get(signal_id)
            if record is None:
                record = self._cold_store.get(signal_id)
            return record
    
    def update_outcome(
        self,
        signal_id: str,
        outcome: RealizedOutcome,
    ) -> bool:
        """Update the realized outcome for a signal."""
        with self._lock:
            record = self._hot_store.get(signal_id) or self._cold_store.get(signal_id)
            if record is None:
                return False
            
            record.realized_outcome = outcome
            return True
    
    def query(self, query: AttributionQuery) -> List[AttributionRecord]:
        """Query attribution records."""
        with self._lock:
            # Start with all signal IDs
            candidate_ids = set(self._hot_store.keys()) | set(self._cold_store.keys())
            
            # Filter by signal_ids
            if query.signal_ids:
                candidate_ids &= set(query.signal_ids)
            
            # Filter by symbols
            if query.symbols:
                symbol_ids = set()
                for symbol in query.symbols:
                    symbol_ids.update(self._by_symbol.get(symbol, []))
                candidate_ids &= symbol_ids
            
            # Filter by regime
            if query.regime_ids:
                regime_ids = set()
                for regime in query.regime_ids:
                    regime_ids.update(self._by_regime.get(regime, []))
                candidate_ids &= regime_ids
            
            # Filter by model
            if query.model_ids:
                model_ids = set()
                for model in query.model_ids:
                    model_ids.update(self._by_model.get(model, []))
                candidate_ids &= model_ids
            
            # Get records and apply remaining filters
            results = []
            for signal_id in candidate_ids:
                record = self._hot_store.get(signal_id) or self._cold_store.get(signal_id)
                if record is None:
                    continue
                
                # Time range filter
                if query.time_range:
                    start, end = query.time_range
                    if not (start <= record.timestamp <= end):
                        continue
                
                # Outcome status filter
                if query.outcome_status:
                    if record.realized_outcome is None:
                        if OutcomeStatus.PENDING not in query.outcome_status:
                            continue
                    elif record.realized_outcome.status not in query.outcome_status:
                        continue
                
                # Confidence filter
                if query.min_confidence and record.confidence_score < query.min_confidence:
                    continue
                if query.max_confidence and record.confidence_score > query.max_confidence:
                    continue
                
                results.append(record)
            
            # Sort by timestamp descending
            results.sort(key=lambda r: r.timestamp, reverse=True)
            
            # Apply offset and limit
            return results[query.offset:query.offset + query.limit]
    
    def archive_old_records(self) -> int:
        """Move old records from hot to cold storage."""
        with self._lock:
            cutoff = datetime.utcnow() - timedelta(days=self.HOT_RETENTION_DAYS)
            archived = 0
            
            for signal_id, record in list(self._hot_store.items()):
                if record.timestamp < cutoff:
                    self._cold_store[signal_id] = record
                    del self._hot_store[signal_id]
                    archived += 1
            
            return archived


class DecisionAttributionEngine:
    """
    Decision Attribution Engine.
    
    Ensures every trading signal has complete attribution including:
    - Feature snapshot with hash
    - Model contributions with weights
    - Regime classification
    - Historical analogs
    - Expected vs realized outcomes
    - Reasoning chain
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.store = AttributionStore(
            storage_path=self.config.get("storage_path")
        )
        self._analog_finder = None  # Injected dependency
    
    def create_attribution(
        self,
        symbol: str,
        features: Dict[str, float],
        model_outputs: List[Dict[str, Any]],
        regime_id: str,
        expected_direction: SignalDirection,
        expected_magnitude: float,
        horizon: str,
        reasoning: List[str],
        confidence: float,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> AttributionRecord:
        """Create a new attribution record."""
        timestamp = datetime.utcnow()
        
        # Create feature snapshot
        feature_snapshot = FeatureSnapshot(
            timestamp=timestamp,
            features=features,
        )
        
        # Create model contributions
        contributing_models = [
            ModelContribution(
                model_id=m["model_id"],
                version=m.get("version", "unknown"),
                weight=m["weight"],
                confidence=m["confidence"],
                raw_output=m.get("raw_output"),
                features_used=m.get("features_used", []),
            )
            for m in model_outputs
        ]
        
        # Find historical analogs
        historical_analogs = self._find_analogs(
            features=features,
            regime_id=regime_id,
        )
        
        # Create expected outcome
        expected_outcome = ExpectedOutcome(
            direction=expected_direction,
            magnitude=expected_magnitude,
            horizon=horizon,
            probability=confidence,
        )
        
        # Create attribution record
        record = AttributionRecord(
            signal_id=str(uuid.uuid4()),
            symbol=symbol,
            timestamp=timestamp,
            feature_snapshot=feature_snapshot,
            contributing_models=contributing_models,
            latent_regime_id=regime_id,
            historical_analogs=historical_analogs,
            expected_outcome=expected_outcome,
            realized_outcome=None,
            confidence_score=confidence,
            reasoning_chain=reasoning,
            metadata=metadata or {},
        )
        
        # Store the record
        self.store.store(record)
        
        logger.info(f"Created attribution record: {record.signal_id}")
        return record
    
    def record_outcome(
        self,
        signal_id: str,
        status: OutcomeStatus,
        pnl: float,
        pnl_percent: float,
        entry_price: float,
        exit_price: float,
        entry_time: datetime,
        exit_time: datetime,
        slippage: float,
        fees: float,
    ) -> bool:
        """Record the realized outcome for a signal."""
        outcome = RealizedOutcome(
            status=status,
            pnl=pnl,
            pnl_percent=pnl_percent,
            entry_price=entry_price,
            exit_price=exit_price,
            entry_time=entry_time,
            exit_time=exit_time,
            slippage=slippage,
            fees=fees,
        )
        
        success = self.store.update_outcome(signal_id, outcome)
        if success:
            logger.info(f"Recorded outcome for signal {signal_id}: {status.value}")
        else:
            logger.warning(f"Failed to record outcome for signal {signal_id}")
        
        return success
    
    def _find_analogs(
        self,
        features: Dict[str, float],
        regime_id: str,
        max_analogs: int = 5,
    ) -> List[HistoricalAnalog]:
        """Find historical situations similar to current."""
        # Query past records with same regime
        query = AttributionQuery(
            regime_ids=[regime_id],
            outcome_status=[OutcomeStatus.WIN, OutcomeStatus.LOSS],
            limit=1000,
        )
        past_records = self.store.query(query)
        
        if not past_records:
            return []
        
        # Compute similarity scores
        analogs = []
        for record in past_records:
            similarity = self._compute_feature_similarity(
                features,
                record.feature_snapshot.features,
            )
            
            if similarity > 0.7:  # Threshold
                outcome = 0.0
                if record.realized_outcome:
                    outcome = record.realized_outcome.pnl_percent
                
                analogs.append(HistoricalAnalog(
                    date=record.timestamp,
                    similarity=similarity,
                    outcome=outcome,
                    regime_id=record.latent_regime_id,
                    features_matched=self._get_matched_features(
                        features,
                        record.feature_snapshot.features,
                    ),
                ))
        
        # Sort by similarity and return top N
        analogs.sort(key=lambda a: a.similarity, reverse=True)
        return analogs[:max_analogs]
    
    def _compute_feature_similarity(
        self,
        features1: Dict[str, float],
        features2: Dict[str, float],
    ) -> float:
        """Compute cosine similarity between feature vectors."""
        common_keys = set(features1.keys()) & set(features2.keys())
        if not common_keys:
            return 0.0
        
        # Compute cosine similarity
        dot_product = sum(features1[k] * features2[k] for k in common_keys)
        norm1 = sum(features1[k] ** 2 for k in common_keys) ** 0.5
        norm2 = sum(features2[k] ** 2 for k in common_keys) ** 0.5
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return dot_product / (norm1 * norm2)
    
    def _get_matched_features(
        self,
        features1: Dict[str, float],
        features2: Dict[str, float],
        threshold: float = 0.1,
    ) -> List[str]:
        """Get list of features that closely match."""
        matched = []
        common_keys = set(features1.keys()) & set(features2.keys())
        
        for key in common_keys:
            v1, v2 = features1[key], features2[key]
            max_val = max(abs(v1), abs(v2), 1e-10)
            if abs(v1 - v2) / max_val < threshold:
                matched.append(key)
        
        return matched
    
    # Debug Workflows
    
    def debug_signal_failure(self, signal_id: str) -> Dict[str, Any]:
        """
        Debug workflow: "Why did signal X fail?"
        
        Returns analysis of what went wrong.
        """
        record = self.store.get(signal_id)
        if record is None:
            return {"error": f"Signal {signal_id} not found"}
        
        if record.realized_outcome is None:
            return {"error": "Signal has no realized outcome yet"}
        
        analysis = {
            "signal_id": signal_id,
            "expected": record.expected_outcome.to_dict(),
            "realized": record.realized_outcome.to_dict(),
            "regime_at_signal": record.latent_regime_id,
            "confidence_at_signal": record.confidence_score,
            "model_contributions": [m.to_dict() for m in record.contributing_models],
            "reasoning_chain": record.reasoning_chain,
            "potential_issues": [],
        }
        
        # Analyze potential issues
        if record.realized_outcome.slippage > 0.001:  # > 10 bps
            analysis["potential_issues"].append({
                "type": "HIGH_SLIPPAGE",
                "detail": f"Slippage was {record.realized_outcome.slippage:.4f}",
            })
        
        # Check if any model had low confidence
        low_conf_models = [
            m for m in record.contributing_models
            if m.confidence < 0.6
        ]
        if low_conf_models:
            analysis["potential_issues"].append({
                "type": "LOW_MODEL_CONFIDENCE",
                "detail": f"Models with low confidence: {[m.model_id for m in low_conf_models]}",
            })
        
        # Check historical analog performance
        if record.historical_analogs:
            analog_outcomes = [a.outcome for a in record.historical_analogs]
            avg_analog_outcome = sum(analog_outcomes) / len(analog_outcomes)
            if avg_analog_outcome < 0:
                analysis["potential_issues"].append({
                    "type": "NEGATIVE_ANALOG_HISTORY",
                    "detail": f"Historical analogs had avg outcome: {avg_analog_outcome:.4f}",
                })
        
        return analysis
    
    def debug_feature_drivers(self, signal_id: str) -> Dict[str, Any]:
        """
        Debug workflow: "What features drove signal Y?"
        
        Returns feature importance analysis.
        """
        record = self.store.get(signal_id)
        if record is None:
            return {"error": f"Signal {signal_id} not found"}
        
        # Aggregate features used by models
        feature_usage = {}
        for model in record.contributing_models:
            for feature in model.features_used:
                if feature not in feature_usage:
                    feature_usage[feature] = {
                        "models": [],
                        "total_weight": 0.0,
                    }
                feature_usage[feature]["models"].append(model.model_id)
                feature_usage[feature]["total_weight"] += model.weight
        
        # Get feature values
        feature_analysis = []
        for feature, usage in feature_usage.items():
            value = record.feature_snapshot.features.get(feature)
            feature_analysis.append({
                "feature": feature,
                "value": value,
                "models_using": usage["models"],
                "total_weight": usage["total_weight"],
            })
        
        # Sort by total weight
        feature_analysis.sort(key=lambda x: x["total_weight"], reverse=True)
        
        return {
            "signal_id": signal_id,
            "feature_snapshot_hash": record.feature_snapshot.hash,
            "top_features": feature_analysis[:10],
            "all_features": record.feature_snapshot.features,
            "reasoning_chain": record.reasoning_chain,
        }
    
    def compare_regime_attribution(
        self,
        regime_id: str,
        time_range: Optional[Tuple[datetime, datetime]] = None,
    ) -> Dict[str, Any]:
        """
        Debug workflow: "Compare attribution across regime Z"
        
        Returns aggregated analysis for a regime.
        """
        query = AttributionQuery(
            regime_ids=[regime_id],
            time_range=time_range,
            limit=1000,
        )
        records = self.store.query(query)
        
        if not records:
            return {"error": f"No records found for regime {regime_id}"}
        
        # Aggregate statistics
        total_signals = len(records)
        completed = [r for r in records if r.realized_outcome]
        wins = [r for r in completed if r.realized_outcome.status == OutcomeStatus.WIN]
        losses = [r for r in completed if r.realized_outcome.status == OutcomeStatus.LOSS]
        
        # Model performance in this regime
        model_performance = {}
        for record in completed:
            for model in record.contributing_models:
                if model.model_id not in model_performance:
                    model_performance[model.model_id] = {
                        "signals": 0,
                        "wins": 0,
                        "total_pnl": 0.0,
                        "avg_confidence": 0.0,
                    }
                
                model_performance[model.model_id]["signals"] += 1
                model_performance[model.model_id]["avg_confidence"] += model.confidence
                
                if record.realized_outcome.status == OutcomeStatus.WIN:
                    model_performance[model.model_id]["wins"] += 1
                
                model_performance[model.model_id]["total_pnl"] += (
                    record.realized_outcome.pnl_percent * model.weight
                )
        
        # Compute averages
        for model_id, perf in model_performance.items():
            if perf["signals"] > 0:
                perf["win_rate"] = perf["wins"] / perf["signals"]
                perf["avg_confidence"] /= perf["signals"]
        
        return {
            "regime_id": regime_id,
            "total_signals": total_signals,
            "completed_signals": len(completed),
            "win_rate": len(wins) / len(completed) if completed else 0,
            "avg_confidence": sum(r.confidence_score for r in records) / total_signals,
            "model_performance": model_performance,
            "avg_pnl": sum(r.realized_outcome.pnl_percent for r in completed) / len(completed) if completed else 0,
        }
    
    def get_attribution_summary(
        self,
        time_range: Optional[Tuple[datetime, datetime]] = None,
    ) -> Dict[str, Any]:
        """Get summary statistics for attribution records."""
        query = AttributionQuery(
            time_range=time_range,
            limit=10000,
        )
        records = self.store.query(query)
        
        if not records:
            return {"total_signals": 0}
        
        completed = [r for r in records if r.realized_outcome]
        
        return {
            "total_signals": len(records),
            "completed_signals": len(completed),
            "pending_signals": len(records) - len(completed),
            "unique_regimes": len(set(r.latent_regime_id for r in records)),
            "unique_models": len(set(
                m.model_id
                for r in records
                for m in r.contributing_models
            )),
            "avg_confidence": sum(r.confidence_score for r in records) / len(records),
            "win_rate": (
                len([r for r in completed if r.realized_outcome.status == OutcomeStatus.WIN])
                / len(completed)
            ) if completed else 0,
        }
