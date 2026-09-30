"""Generate the complete AlphaAlgo wave/path inventory report."""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping

WAVE_MEANINGS = {
    0: "Canonical authorities",
    1: "Orchestrators, registries, lifecycle, and infrastructure fallback",
    2: "Risk, governance, approvals, safety, and compliance",
    3: "Broker, venue, exchange, execution, and market-data boundaries",
    4: "Strategy, signal, alpha, portfolio, and position intelligence",
    5: "AI, agents, models, cognition, memory, reasoning, and world models",
    6: "Research, backtesting, evaluation, experiment, and RSI evidence",
    7: "Standalone main/CLI facade surfaces",
}


def _directory(path: str) -> str:
    parts = path.split("/")
    if len(parts) <= 2:
        return "/".join(parts[:-1]) or path
    return "/".join(parts[:2])


def _flags(row: Mapping[str, Any]) -> str:
    flags = []
    if row.get("runtime_reachable"):
        flags.append("runtime_reachable")
    if row.get("cli_entrypoint"):
        flags.append("cli")
    if row.get("starts_loop"):
        flags.append("starts_loop")
    if row.get("direct_capital_path"):
        flags.append("direct_capital")
    if row.get("parse_status") != "pass":
        flags.append(f"parse_{row.get('parse_status')}")
    flags.extend(row.get("secondary_tags", []))
    return ", ".join(dict.fromkeys(flags)) or "none"


def _directory_rollups(rows: Iterable[Mapping[str, Any]]) -> str:
    counts = Counter(_directory(row["path"]) for row in rows)
    return "\n".join(f"- `{directory}`: {count} module(s)" for directory, count in sorted(counts.items()))


def _high_risk_rows(rows: Iterable[Mapping[str, Any]], flag: str) -> str:
    matched = [row for row in rows if row.get(flag)]
    if not matched:
        return "- none"
    return "\n".join(
        f"- Wave {row['migration_wave']}: `{row['path']}` — "
        f"{row['classification']} | owner={row['owner']} | port={row['canonical_port']}"
        for row in matched
    )


def render_inventory(manifest: Mapping[str, Any]) -> str:
    rows: List[Dict[str, Any]] = sorted(
        manifest.get("modules", []), key=lambda row: (row.get("migration_wave", 0), row.get("path", ""))
    )
    by_wave: Dict[int, List[Dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_wave[int(row.get("migration_wave", 0))].append(row)

    lines = [
        "# AlphaAlgo Wave Inventory",
        "",
        "Generated from `ARCHITECTURE_LEGACY_CLASSIFICATION.json` by "
        "`scripts/generate_wave_inventory.py`. This report lists every active "
        "scanned Python module and its assigned migration wave.",
        "",
        "## Summary",
        "",
        "| Wave | Modules | Boundary meaning | Runtime reachable | CLI | Loops | Direct capital |",
        "|---:|---:|---|---:|---:|---:|---:|",
    ]
    for wave in sorted(by_wave):
        wave_rows = by_wave[wave]
        lines.append(
            f"| {wave} | {len(wave_rows)} | {WAVE_MEANINGS.get(wave, 'Unclassified')} | "
            f"{sum(row['runtime_reachable'] for row in wave_rows)} | "
            f"{sum(row['cli_entrypoint'] for row in wave_rows)} | "
            f"{sum(row['starts_loop'] for row in wave_rows)} | "
            f"{sum(row['direct_capital_path'] for row in wave_rows)} |"
        )

    lines.extend([
        "",
        "## Important interpretation note",
        "",
        "The `migration_wave` field is assigned by path heuristics. Wave 1 is the broad "
        "orchestrator/lifecycle/infrastructure fallback, and Wave 7 currently detects only "
        "standalone main surfaces. Review `owner`, `canonical_port`, tags, and architectural "
        "targets together before migrating a module.",
        "",
        "## Directory rollups",
    ])
    for wave in sorted(by_wave):
        lines.extend([
            "",
            f"### Wave {wave}: {WAVE_MEANINGS.get(wave, 'Unclassified')}",
            _directory_rollups(by_wave[wave]),
        ])

    lines.extend([
        "",
        "## High-risk indexes",
        "",
        "### Runtime-reachable modules",
        _high_risk_rows(rows, "runtime_reachable"),
        "",
        "### CLI entry points",
        _high_risk_rows(rows, "cli_entrypoint"),
        "",
        "### Loop/worker starters",
        _high_risk_rows(rows, "starts_loop"),
        "",
        "### Direct capital-path findings",
        _high_risk_rows(rows, "direct_capital_path"),
        "",
        "## Adapter review queue",
        "",
        "Per-adapter `review_priority`: P0 = runtime-reachable (prove first), "
        "P1 = credential access, P2 = no test evidence, P3 = test-covered. "
        "P0/P1 paths are listed below; P2/P3 counts live in the manifest "
        "summary (`adapter_review_queue`).",
        "",
        "### P0 — reachable adapters",
        "\n".join(
            f"- `{row['path']}` — owner={row['owner']} | port={row['canonical_port']} | tests={len(row.get('tests', []))}"
            for row in rows if row.get("review_priority") == 0
        ) or "- none",
        "",
        "### P1 — credential-access adapters",
        "\n".join(
            f"- `{row['path']}` — owner={row['owner']} | tests={len(row.get('tests', []))}"
            for row in rows if row.get("review_priority") == 1
        ) or "- none",
    ])

    for wave in sorted(by_wave):
        lines.extend([
            "",
            f"## Wave {wave} file list — {WAVE_MEANINGS.get(wave, 'Unclassified')}",
            "",
        ])
        for row in by_wave[wave]:
            importers = row.get("importers", [])
            importer_text = ", ".join(f"`{item}`" for item in importers) if importers else "none"
            lines.append(
                f"- `{row['path']}` — class={row['classification']} | "
                f"owner={row['owner']} | port={row['canonical_port']} | "
                f"flags={_flags(row)} | importers={importer_text}"
            )

    lines.append("")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", default="ARCHITECTURE_LEGACY_CLASSIFICATION.json")
    parser.add_argument("--output", default="ARCHITECTURE_WAVE_INVENTORY.md")
    args = parser.parse_args()

    manifest_path = Path(args.manifest)
    output_path = Path(args.output)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    output_path.write_text(render_inventory(manifest), encoding="utf-8")
    print(f"wrote {output_path}")


if __name__ == "__main__":
    main()
