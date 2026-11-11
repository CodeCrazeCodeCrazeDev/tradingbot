"""
Legal Compliance and Data Entitlement Gate for London Strategic Edge (LSE) Datasets.
Enforces strict license verification as detailed in LSE_DATASET_INTEGRATION_LEGAL_REPORT.md:
- Blocks automated scraping or API ingestion without explicit written authorization.
- Blocks machine learning model training and derivative work generation under standard ToS.
- Enforces data entitlement boundaries across Ingestion, Training, Model Export, and Live Trading.
- Permits compliant execution with authorized internal synthetic fixtures or independently licensed data.
"""

import os
import logging
from enum import Enum
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime

logger = logging.getLogger("AlphaAlgo.LondonSessionEntitlementGate")


class DataLicenseType(str, Enum):
    SYNTHETIC_RESEARCH = "SYNTHETIC_RESEARCH"
    INDEPENDENT_LICENSED = "INDEPENDENT_LICENSED"
    LSE_STANDARD_FREE = "LSE_STANDARD_FREE"
    LSE_EXPLICIT_ENTERPRISE_WAIVER = "LSE_EXPLICIT_ENTERPRISE_WAIVER"
    UNKNOWN = "UNKNOWN"


class EntitlementAction(str, Enum):
    INGESTION = "INGESTION"
    FEATURE_ENGINEERING = "FEATURE_ENGINEERING"
    MODEL_TRAINING = "MODEL_TRAINING"
    MODEL_EXPORT = "MODEL_EXPORT"
    COMMERCIAL_TRADING = "COMMERCIAL_TRADING"


@dataclass
class EntitlementVerificationResult:
    is_permitted: bool
    license_type: DataLicenseType
    action: EntitlementAction
    reason: str
    provenance_tag: str
    timestamp: datetime = field(default_factory=datetime.utcnow)


class DataEntitlementException(PermissionError):
    """Raised when an operation violates dataset legal licensing constraints."""
    pass


class DataEntitlementGate:
    """
    Guards all pipelines interacting with London Strategic Edge data.
    Ensures zero violations of Section 6 (Acceptable Use) and Section 7 (Intellectual Property).
    """

    def __init__(self, override_env_lookup: bool = False) -> None:
        self.override_env_lookup = override_env_lookup

    def _get_env_flag(self, key: str, default: str = "") -> str:
        if self.override_env_lookup:
            return default
        return os.getenv(key, default).strip()

    def determine_license_type(self, source_type: str, has_explicit_waiver: bool = False) -> DataLicenseType:
        """Determines the appropriate license type based on origin and explicit agreements."""
        source_upper = source_type.upper()
        if "SYNTHETIC" in source_upper or "FIXTURE" in source_upper or "SIMULATED" in source_upper:
            return DataLicenseType.SYNTHETIC_RESEARCH
        if "INDEPENDENT" in source_upper or "MT5" in source_upper or "PROPRIETARY" in source_upper:
            return DataLicenseType.INDEPENDENT_LICENSED

        # Check environment for explicit enterprise waiver / written consent
        waiver_env = self._get_env_flag("LSE_EXPLICIT_TRAINING_CONSENT", "false").lower() in ("true", "1", "yes")
        if has_explicit_waiver or waiver_env:
            return DataLicenseType.LSE_EXPLICIT_ENTERPRISE_WAIVER

        if "LSE" in source_upper or "LONDON_STRATEGIC_EDGE" in source_upper:
            return DataLicenseType.LSE_STANDARD_FREE

        return DataLicenseType.UNKNOWN

    def verify_action(
        self,
        action: EntitlementAction,
        license_type: DataLicenseType,
        raise_on_prohibited: bool = True
    ) -> EntitlementVerificationResult:
        """
        Validates whether a specific action is legally entitled under the detected license.
        """
        is_permitted = False
        reason = ""

        if license_type == DataLicenseType.SYNTHETIC_RESEARCH:
            is_permitted = True
            reason = "Synthetic fixture: fully unencumbered for all research and model training."

        elif license_type == DataLicenseType.INDEPENDENT_LICENSED:
            if action == EntitlementAction.COMMERCIAL_TRADING:
                is_permitted = False
                reason = "Commercial live trading requires production risk committee sign-off."
            else:
                is_permitted = True
                reason = "Independently licensed data: permitted for institutional research and training."

        elif license_type == DataLicenseType.LSE_EXPLICIT_ENTERPRISE_WAIVER:
            if action == EntitlementAction.COMMERCIAL_TRADING:
                is_permitted = False
                reason = "LSE Enterprise Waiver permits internal research/training; commercial live execution restricted."
            else:
                is_permitted = True
                reason = "Explicit LSE Enterprise Written Consent active (LSE_EXPLICIT_TRAINING_CONSENT)."

        elif license_type == DataLicenseType.LSE_STANDARD_FREE:
            # Under standard LSE terms (as audited in LSE_DATASET_INTEGRATION_LEGAL_REPORT.md):
            # Section 7 prohibits creating derivative works (ML model weights / aggregate representations).
            # Section 6 prohibits automated extraction and commercial exploitation.
            if action == EntitlementAction.INGESTION:
                is_permitted = False
                reason = (
                    "PROHIBITED: LSE Standard Terms Section 6 prohibits automated systems from accessing "
                    "or scraping data without express written permission. Obtain an enterprise waiver or API agreement."
                )
            elif action in (EntitlementAction.FEATURE_ENGINEERING, EntitlementAction.MODEL_TRAINING):
                is_permitted = False
                reason = (
                    "PROHIBITED: LSE Standard Terms Section 7 prohibits creating derivative works. "
                    "Training ML models on raw/derived LSE compilations requires express written consent."
                )
            elif action in (EntitlementAction.MODEL_EXPORT, EntitlementAction.COMMERCIAL_TRADING):
                is_permitted = False
                reason = (
                    "PROHIBITED: Commercial exploitation or redistribution of models derived from LSE data "
                    "is strictly prohibited by Section 6 and Section 7."
                )
            else:
                is_permitted = False
                reason = "Action prohibited under standard LSE Terms of Service."

        else: # UNKNOWN
            is_permitted = False
            reason = f"Unknown or untracked license type '{license_type}'. Access blocked by default."

        provenance_tag = f"LIC:{license_type.value}:ACT:{action.value}:PERM:{is_permitted}"

        result = EntitlementVerificationResult(
            is_permitted=is_permitted,
            license_type=license_type,
            action=action,
            reason=reason,
            provenance_tag=provenance_tag
        )

        if not is_permitted:
            logger.warning(f"DataEntitlementGate BLOCKED {action.value}: {reason}")
            if raise_on_prohibited:
                raise DataEntitlementException(
                    f"Legal Entitlement Gate Violation [{license_type.value} -> {action.value}]: {reason}"
                )
        else:
            logger.info(f"DataEntitlementGate APPROVED {action.value} under {license_type.value}")

        return result
