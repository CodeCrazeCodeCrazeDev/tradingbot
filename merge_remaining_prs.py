"""Merge remaining open PRs via refs/pull/N/head (no GitHub API needed).

Resumable: skips PRs already in merge_progress.txt; resolves conflicts
favoring the PR side; stops cleanly on low disk or persistent failure.
"""

import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent
PROGRESS = REPO / "merge_progress.txt"
MIN_FREE_GB = 1.5

TARGETS = [395, 426] + list(range(433, 447))


def git(*args, check=True):
    r = subprocess.run(["git", "-C", str(REPO)] + list(args),
                       capture_output=True, text=True)
    if check and r.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed: {r.stderr[:400]}")
    return r


def free_gb() -> float:
    import shutil
    return shutil.disk_usage(REPO).free / 1e9


def done_prs() -> set:
    if not PROGRESS.exists():
        return set()
    return {int(l.split("|")[0]) for l in PROGRESS.read_text().splitlines()
            if l.split("|")[0].isdigit() and "|" in l}


def log(num, status, extra=""):
    with PROGRESS.open("a") as f:
        f.write(f"{num}|{status}|{extra}\n")


def resolve_unmerged():
    """Resolve every remaining conflict in favor of 'theirs' (the PR)."""
    out = git("diff", "--name-only", "--diff-filter=U", check=False).stdout
    for path in [p for p in out.splitlines() if p.strip()]:
        r = git("checkout", "--theirs", "--", path, check=False)
        if r.returncode != 0:
            git("rm", "-f", "--", path, check=False)
        else:
            git("add", "--", path, check=False)
    left = git("ls-files", "-u", check=False).stdout
    return not left.strip()


def merge_one(num: int) -> str:
    ref = f"refs/pull/{num}/head"
    git("fetch", "origin", f"{ref}:refs/remotes/pr/{num}")
    target = f"refs/remotes/pr/{num}"
    # already merged?
    if git("merge-base", "--is-ancestor", target, "HEAD",
           check=False).returncode == 0:
        return "ALREADY-MERGED"
    r = git("merge", "--no-ff", "-X", "theirs", "-m",
            f"Merge PR #{num} ({ref})", target, check=False)
    if r.returncode != 0:
        if resolve_unmerged():
            c = git("commit", "--no-edit", check=False)
            return "RESOLVED" if c.returncode == 0 else "FAILED|commit-failed"
        git("merge", "--abort", check=False)
        return "FAILED|unresolved"
    return "CLEAN"


def main():
    done = done_prs()
    for num in TARGETS:
        if num in done:
            continue
        if free_gb() < MIN_FREE_GB:
            print(f"disk low ({free_gb():.2f} GB) — stopping")
            break
        try:
            status = merge_one(num)
        except Exception as e:
            status = f"FAILED|{type(e).__name__}"
        status = status.replace("\n", " ")
        log(num, status)
        print(f"PR #{num}: {status}", flush=True)


if __name__ == "__main__":
    main()
