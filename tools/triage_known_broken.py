"""Triage tests/known_broken_merge.txt entries.

For each manifest entry, loads tests.conftest (identical builtins/meta-path
shims to real collection) then attempts to execute the module exactly as
pytest collection would. Records the failure class:

  missing      - file no longer exists (stale entry)
  syntax       - SyntaxError at parse time
  import-dead  - ModuleNotFoundError / ImportError on a deleted subsystem
  api-drift    - AttributeError / NameError against moved or renamed APIs
  error        - any other exception during import
  collects     - module executes clean; entry can be removed from manifest

Writes tools/known_broken_triage.json and prints a summary.
Usage: python tools/triage_known_broken.py
"""
import importlib.util
import json
import sys
import traceback
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
MANIFEST = REPO / "tests" / "known_broken_merge.txt"


def classify(exc: BaseException) -> str:
    if isinstance(exc, SyntaxError):
        return "syntax"
    if isinstance(exc, (ModuleNotFoundError, ImportError)):
        return "import-dead"
    if isinstance(exc, (AttributeError, NameError)):
        return "api-drift"
    return "error"


def main():
    sys.path.insert(0, str(REPO))
    sys.path.insert(0, str(REPO / "tests"))
    import tests.conftest  # noqa: F401 — installs the compat shims

    entries = [
        line.strip() for line in MANIFEST.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.startswith("#")
    ]
    results = {}
    for i, rel in enumerate(entries):
        path = REPO / "tests" / rel
        if not path.exists():
            results[rel] = {"status": "missing"}
            continue
        try:
            spec = importlib.util.spec_from_file_location(f"_triage_{i}", path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            results[rel] = {"status": "collects"}
        except Exception as exc:
            results[rel] = {
                "status": classify(exc),
                "error": f"{type(exc).__name__}: {exc}",
                "trace": traceback.format_exc(limit=3),
            }

    summary = {}
    for r in results.values():
        summary[r["status"]] = summary.get(r["status"], 0) + 1
    out = REPO / "tools" / "known_broken_triage.json"
    out.write_text(json.dumps({"summary": summary, "results": results}, indent=2))
    print(json.dumps(summary, indent=2))
    print(f"wrote {out} ({len(results)} entries)")


if __name__ == "__main__":
    main()
