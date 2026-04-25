"""Defense layer for AI-agent trap content.

The scanner is inspired by the Google DeepMind "AI Agent Traps" taxonomy:
content injection, semantic manipulation, cognitive-state poisoning,
behavioral-control attacks, systemic manipulation, and human-oversight traps.
It is deliberately conservative because trading actions are high impact.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence


class TrapCategory(str, Enum):
    CONTENT_INJECTION = "content_injection"
    SEMANTIC_MANIPULATION = "semantic_manipulation"
    COGNITIVE_STATE_POISONING = "cognitive_state_poisoning"
    BEHAVIORAL_CONTROL = "behavioral_control"
    SYSTEMIC_MANIPULATION = "systemic_manipulation"
    HUMAN_OVERSIGHT_MANIPULATION = "human_oversight_manipulation"


@dataclass(frozen=True)
class AgentTrapFinding:
    category: TrapCategory
    severity: str
    source: str
    reason: str
    evidence: str


@dataclass(frozen=True)
class AgentTrapReport:
    blocked: bool
    risk_score: int
    findings: List[AgentTrapFinding] = field(default_factory=list)

    @property
    def clean(self) -> bool:
        return not self.blocked and not self.findings


@dataclass(frozen=True)
class AgentTrapDefenseConfig:
    enabled: bool = True
    block_on_high: bool = True
    block_on_medium_count: int = 2
    max_text_chars: int = 20_000


class AgentTrapScanner:
    """Scan untrusted text/metadata before it can influence a trade."""

    _RULES: Sequence[tuple[TrapCategory, str, str, re.Pattern[str]]] = (
        (
            TrapCategory.CONTENT_INJECTION,
            "high",
            "hidden or machine-targeted instruction marker",
            re.compile(
                r"(?is)(<!--.*?(ignore|override|system prompt|developer message).*?-->|"
                r"display\s*:\s*none|visibility\s*:\s*hidden|aria-label\s*=\s*['\"][^'\"]*"
                r"(ignore|override|exfiltrate|secret)[^'\"]*['\"]|"
                r"data-(prompt|instruction)\s*=)"
            ),
        ),
        (
            TrapCategory.BEHAVIORAL_CONTROL,
            "high",
            "instruction attempts to override the agent or force an action",
            re.compile(
                r"(?is)\b(ignore|bypass|override|disable)\b.{0,80}"
                r"\b(previous|prior|safety|risk|guardrail|policy|instruction|validator|kill switch)\b|"
                r"\bexecute\s+(all|immediately|without approval)\b|"
                r"\bdo\s+not\s+(tell|log|record|ask|validate)\b"
            ),
        ),
        (
            TrapCategory.COGNITIVE_STATE_POISONING,
            "high",
            "content tries to write persistent memory or learned policy",
            re.compile(
                r"(?is)\b(store|remember|persist|save)\b.{0,80}"
                r"\b(this|instruction|rule|memory|policy|belief|system prompt)\b|"
                r"\bpoison(ed|ing)?\s+(memory|retrieval|knowledge|vector)\b"
            ),
        ),
        (
            TrapCategory.SEMANTIC_MANIPULATION,
            "medium",
            "authority or urgency framing tries to bias reasoning",
            re.compile(
                r"(?is)\b(certified|official|guaranteed|risk[- ]?free|100%\s+safe|cannot lose)\b|"
                r"\burgent\b.{0,80}\b(buy|sell|execute|approve)\b|"
                r"\btrusted source\b.{0,80}\b(no need|skip|ignore)\b"
            ),
        ),
        (
            TrapCategory.SYSTEMIC_MANIPULATION,
            "high",
            "content encourages coordinated market-impact behavior",
            re.compile(
                r"(?is)\b(all agents|every bot|coordinated|synchronized|mass)\b.{0,100}"
                r"\b(buy|sell|liquidate|short|pump|dump)\b|"
                r"\bflash crash\b|\bshort squeeze\b.{0,80}\btrigger\b"
            ),
        ),
        (
            TrapCategory.HUMAN_OVERSIGHT_MANIPULATION,
            "medium",
            "content pressures human approval or hides risk from review",
            re.compile(
                r"(?is)\b(approve|confirm)\b.{0,80}\b(without reading|quickly|no review|rubber stamp)\b|"
                r"\bhide\b.{0,80}\b(risk|loss|drawdown|audit|reason)\b"
            ),
        ),
    )

    def __init__(self, config: Optional[AgentTrapDefenseConfig] = None) -> None:
        self.config = config or AgentTrapDefenseConfig()

    def scan_mapping(self, values: Mapping[str, Any], *, source_prefix: str) -> AgentTrapReport:
        texts = self._flatten_mapping(values, source_prefix=source_prefix)
        return self.scan_texts(texts)

    def scan_texts(self, texts: Iterable[tuple[str, str]]) -> AgentTrapReport:
        if not self.config.enabled:
            return AgentTrapReport(blocked=False, risk_score=0)

        findings: List[AgentTrapFinding] = []
        for source, text in texts:
            clipped = str(text)[: self.config.max_text_chars]
            for category, severity, reason, pattern in self._RULES:
                match = pattern.search(clipped)
                if match:
                    findings.append(
                        AgentTrapFinding(
                            category=category,
                            severity=severity,
                            source=source,
                            reason=reason,
                            evidence=self._redact(match.group(0)),
                        )
                    )

        risk_score = self._score(findings)
        high_count = sum(1 for finding in findings if finding.severity == "high")
        medium_count = sum(1 for finding in findings if finding.severity == "medium")
        blocked = (
            (self.config.block_on_high and high_count > 0)
            or medium_count >= self.config.block_on_medium_count
        )
        return AgentTrapReport(blocked=blocked, risk_score=risk_score, findings=findings)

    def _flatten_mapping(self, values: Mapping[str, Any], *, source_prefix: str) -> List[tuple[str, str]]:
        flattened: List[tuple[str, str]] = []
        for key, value in values.items():
            source = f"{source_prefix}.{key}"
            if isinstance(value, str):
                flattened.append((source, value))
            elif isinstance(value, Mapping):
                flattened.extend(self._flatten_mapping(value, source_prefix=source))
            elif isinstance(value, (list, tuple, set)):
                for idx, item in enumerate(value):
                    if isinstance(item, str):
                        flattened.append((f"{source}[{idx}]", item))
                    elif isinstance(item, Mapping):
                        flattened.extend(self._flatten_mapping(item, source_prefix=f"{source}[{idx}]"))
        return flattened

    def _score(self, findings: Sequence[AgentTrapFinding]) -> int:
        score = 0
        for finding in findings:
            score += 50 if finding.severity == "high" else 25
        return min(score, 100)

    def _redact(self, text: str) -> str:
        compact = " ".join(text.split())
        compact = re.sub(r"(?i)(api[_-]?key|token|secret|password)\s*[:=]\s*\S+", r"\1=<redacted>", compact)
        return compact[:160]
