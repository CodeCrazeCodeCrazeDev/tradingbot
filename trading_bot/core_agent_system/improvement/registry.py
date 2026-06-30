"""
Unified Improvement Registry (UIR)
Central source of truth for all proposed system enhancements.
"""

import json
import logging
import uuid
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field, asdict

logger = logging.getLogger(__name__)

class ImprovementType(Enum):
    META = "meta"           # Reasoning, workflow, agent collaboration
    TRADING = "trading"     # Alpha, models, risk, execution
    CODE = "code"           # Source code modifications, performance, infra

class ImprovementStatus(Enum):
    CANDIDATE = "candidate" # Proposed, waiting for evaluation
    EVALUATING = "evaluating" # Currently being tested
    SHADOW = "shadow"       # Passed initial tests, running in parallel
    PRODUCTION = "production" # Fully promoted
    REJECTED = "rejected"   # Failed validation
    ARCHIVED = "archived"   # Superseded

@dataclass
class ImprovementRecord:
    improvement_id: str
    type: ImprovementType
    domain: str
    source: str
    proposal: Dict[str, Any]
    status: ImprovementStatus = ImprovementStatus.CANDIDATE
    evidence: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    version_link: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data['type'] = self.type.value
        data['status'] = self.status.value
        data['created_at'] = self.created_at.isoformat()
        data['updated_at'] = self.updated_at.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ImprovementRecord':
        data['type'] = ImprovementType(data['type'])
        data['status'] = ImprovementStatus(data['status'])
        data['created_at'] = datetime.fromisoformat(data['created_at'])
        data['updated_at'] = datetime.fromisoformat(data['updated_at'])
        return cls(**data)

class ImprovementRegistry:
    """
    Manages the lifecycle of system improvements.
    """
    def __init__(self, storage_path: Optional[Path] = None):
        self.storage_path = storage_path or Path("core_agent_data/improvements")
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.db_file = self.storage_path / "registry.json"
        self.improvements: Dict[str, ImprovementRecord] = {}
        self._load()

    def _load(self):
        if self.db_file.exists():
            try:
                with open(self.db_file, 'r') as f:
                    data = json.load(f)
                    for imp_id, imp_data in data.items():
                        self.improvements[imp_id] = ImprovementRecord.from_dict(imp_data)
                logger.info(f"Loaded {len(self.improvements)} improvement records")
            except Exception as e:
                logger.error(f"Failed to load registry: {e}")

    def _save(self):
        try:
            with open(self.db_file, 'w') as f:
                json.dump({k: v.to_dict() for k, v in self.improvements.items()}, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save registry: {e}")

    def register_proposal(self, type: ImprovementType, domain: str, source: str, proposal: Dict[str, Any]) -> str:
        imp_id = f"IMP-{uuid.uuid4().hex[:8].upper()}"
        record = ImprovementRecord(
            improvement_id=imp_id,
            type=type,
            domain=domain,
            source=source,
            proposal=proposal
        )
        self.improvements[imp_id] = record
        self._save()
        logger.info(f"Registered new improvement proposal: {imp_id} ({type.value})")
        return imp_id

    def update_status(self, improvement_id: str, status: ImprovementStatus, evidence: Optional[Dict] = None):
        if improvement_id in self.improvements:
            record = self.improvements[improvement_id]
            record.status = status
            record.updated_at = datetime.now()
            if evidence:
                record.evidence.update(evidence)
            self._save()
            logger.info(f"Updated improvement {improvement_id} status to {status.value}")

    def get_by_status(self, status: ImprovementStatus) -> List[ImprovementRecord]:
        return [imp for imp in self.improvements.values() if imp.status == status]

    def get_record(self, improvement_id: str) -> Optional[ImprovementRecord]:
        return self.improvements.get(improvement_id)
