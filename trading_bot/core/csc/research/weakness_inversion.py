"""Weakness Inversion Engine (ECIE service #12).

Audits weaknesses found in untrusted external sources and emits the
DEFENSIVE RULE that inverts them — a repo missing OOS validation
generates an internal gate; code with eval() generates an AST ban;
a strategy with look-ahead leakage patterns generates a leakage
check. Rules are advisory evidence — never auto-enforced; they feed
the electorate and the governance ledger like every other claim.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List

# weakness signature -> the inverted control it should generate
_SIGNATURES = [
    (re.compile(r"\beval\s*\(|\bexec\s*\(", re.I),
     "code_eval_exec",
     "AST-gate: reject any candidate containing eval/exec"),
    (re.compile(r"\bos\.system|subprocess\.(?:call|run|Popen)", re.I),
     "code_shell_spawn",
     "AST-gate: reject candidates spawning shell/subprocess"),
    (re.compile(r"shift\(\s*-\s*\d|\.iloc\s*\[\s*-|lookahead|"
                r"future[_\s]?(?:return|price|data)", re.I),
     "lookahead_leakage",
     "Eval-gate: require walk-forward + embargo; audit for "
     "future-indexed features"),
    (re.compile(r"in[-_ ]?sample only|no oos|without out[-_ ]?of[-_ ]"
                r"?sample|train\s*=\s*test|fitted on all data", re.I),
     "no_oos_validation",
     "Eval-gate: OOS must exceed IS baseline before promotion"),
    (re.compile(r"except\s*:\s*pass|except Exception\s*:\s*pass", re.I),
     "swallowed_errors",
     "Lint-gate: bare except:pass rejected; failures must surface"),
    (re.compile(r"no (?:unit )?tests?|tests?\s*:\s*none|"
                r"0%\s*(?:coverage|test)", re.I),
     "missing_tests",
     "Quality-gate: candidate must ship tests that fail pre-fix"),
    (re.compile(r"(?:api[_-]?key|secret|password|token)\s*="
                r"\s*[\"'][^\"']+[\"']", re.I),
     "hardcoded_secret",
     "Security-gate: reject literals matching credential patterns"),
    (re.compile(r"random\.(?!seed)|np\.random\.(?!default_rng|seed)",
                re.I),
     "unseeded_randomness",
     "Repro-gate: all stochastic paths must take explicit seeds"),
    (re.compile(r"no (?:drawdown|risk) (?:limit|cap|check)|"
                r"unlimited (?:leverage|position)", re.I),
     "ungoverned_risk",
     "Risk-gate: canonical risk sizing is non-negotiable"),
]


def invert_weaknesses(text: str) -> List[Dict[str, Any]]:
    """Scan one source's text/code for weakness signatures; return the
    inverted governance rules each weakness implies."""
    # Weakness signatures live in CODE — pull fenced blocks first so
    # marketing prose can't hide or fake a finding.
    blocks = re.findall("```(?:\\w*)?\\n?(.*?)```", text or "", re.S)
    scan_target = chr(10).join(blocks) if blocks else (text or "")
    findings = []
    for rx, wid, rule in _SIGNATURES:
        m = rx.search(scan_target)
        if m:
            findings.append({
                "weakness_id": wid,
                "matched": m.group(0)[:80],
                "inverted_rule": rule,
                "severity": "high" if wid in (
                    "code_eval_exec", "code_shell_spawn",
                    "hardcoded_secret", "lookahead_leakage") else "med",
            })
    return findings


def invert_documents(docs) -> Dict[str, Any]:
    """Batch inversion over fetched SourceDocuments. Returns the rule
    ledger — deduped by weakness_id — plus per-doc findings."""
    ledger: Dict[str, Dict[str, Any]] = {}
    per_doc = []
    for d in docs:
        found = invert_weaknesses(getattr(d, "text", "") or "")
        per_doc.append({"source_id": getattr(d, "source_id", "?"),
                        "weaknesses": len(found)})
        for f in found:
            rec = ledger.setdefault(
                f["weakness_id"],
                {"weakness_id": f["weakness_id"],
                 "inverted_rule": f["inverted_rule"],
                 "severity": f["severity"], "seen_in": []})
            rec["seen_in"].append(getattr(d, "source_id", "?"))
    return {"rules": list(ledger.values()),
            "per_doc": per_doc,
            "rules_total": len(ledger),
            "note": ("advisory rules — enforcement requires the "
                     "canonical governance path, not auto-apply")}
