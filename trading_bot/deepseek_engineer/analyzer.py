"""Minimal codebase analyzer — file statistics for the engineer surface."""

from dataclasses import dataclass
from pathlib import Path


@dataclass
class FileAnalysis:
    path: Path
    total_lines: int
    code_lines: int
    comment_lines: int
    blank_lines: int
    is_python: bool


class CodebaseAnalyzer:
    """Analyze a single source file under a repository root."""

    def __init__(self, root_path: str):
        self.root_path = Path(root_path)

    def analyze_file(self, file_path: str) -> FileAnalysis:
        path = Path(file_path)
        if not path.is_absolute():
            path = self.root_path / path
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        blank = sum(1 for l in lines if not l.strip())
        comments = sum(1 for l in lines if l.strip().startswith("#"))
        return FileAnalysis(
            path=path,
            total_lines=len(lines),
            code_lines=len(lines) - blank - comments,
            comment_lines=comments,
            blank_lines=blank,
            is_python=path.suffix == ".py",
        )
