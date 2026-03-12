"""
Automatic Changelog Generator
Git-based changelog and release notes generation
"""

import asyncio
import logging
import subprocess
import re
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
import json

logger = logging.getLogger(__name__)


class ChangeType(Enum):
    """Types of changes"""
    FEATURE = "feature"
    FIX = "fix"
    IMPROVEMENT = "improvement"
    BREAKING = "breaking"
    SECURITY = "security"
    PERFORMANCE = "performance"
    DOCUMENTATION = "documentation"
    REFACTOR = "refactor"
    TEST = "test"
    CHORE = "chore"
    DEPENDENCY = "dependency"


@dataclass
class ChangeEntry:
    """Single changelog entry"""
    commit_hash: str
    short_hash: str
    change_type: ChangeType
    scope: Optional[str]
    description: str
    author: str
    author_email: str
    timestamp: datetime
    breaking: bool = False
    issues: List[str] = field(default_factory=list)
    pull_request: Optional[str] = None
    
    def to_markdown(self) -> str:
        """Convert to markdown format"""
        prefix = "⚠️ **BREAKING:** " if self.breaking else ""
        scope_str = f"**{self.scope}:** " if self.scope else ""
        issues_str = f" ({', '.join(self.issues)})" if self.issues else ""
        pr_str = f" (#{self.pull_request})" if self.pull_request else ""
        return f"- {prefix}{scope_str}{self.description}{issues_str}{pr_str}"


@dataclass
class ReleaseNotes:
    """Release notes for a version"""
    version: str
    date: datetime
    changes: Dict[ChangeType, List[ChangeEntry]]
    contributors: List[str]
    breaking_changes: List[ChangeEntry]
    highlights: List[str] = field(default_factory=list)
    
    def to_markdown(self) -> str:
        """Generate markdown release notes"""
        lines = [
            f"# Release {self.version}",
            f"",
            f"**Release Date:** {self.date.strftime('%Y-%m-%d')}",
            f"",
        ]
        
        # Highlights
        if self.highlights:
            lines.extend([
                "## 🌟 Highlights",
                "",
                *[f"- {h}" for h in self.highlights],
                ""
            ])
        
        # Breaking changes
        if self.breaking_changes:
            lines.extend([
                "## ⚠️ Breaking Changes",
                "",
                *[entry.to_markdown() for entry in self.breaking_changes],
                ""
            ])
        
        # Changes by type
        type_headers = {
            ChangeType.FEATURE: "## ✨ New Features",
            ChangeType.FIX: "## 🐛 Bug Fixes",
            ChangeType.IMPROVEMENT: "## 🚀 Improvements",
            ChangeType.SECURITY: "## 🔒 Security",
            ChangeType.PERFORMANCE: "## ⚡ Performance",
            ChangeType.DOCUMENTATION: "## 📚 Documentation",
            ChangeType.REFACTOR: "## ♻️ Refactoring",
            ChangeType.DEPENDENCY: "## 📦 Dependencies",
        }
        
        for change_type, header in type_headers.items():
            entries = self.changes.get(change_type, [])
            if entries:
                lines.extend([
                    header,
                    "",
                    *[entry.to_markdown() for entry in entries],
                    ""
                ])
        
        # Contributors
        if self.contributors:
            lines.extend([
                "## 👥 Contributors",
                "",
                f"Thanks to {', '.join(self.contributors)} for their contributions!",
                ""
            ])
        
        return "\n".join(lines)


class ChangelogGenerator:
    """
    Automatic changelog generator from Git history
    """
    
    # Conventional commit patterns
    COMMIT_PATTERNS = {
        r'^feat(\(.+\))?!?:': ChangeType.FEATURE,
        r'^fix(\(.+\))?!?:': ChangeType.FIX,
        r'^perf(\(.+\))?!?:': ChangeType.PERFORMANCE,
        r'^docs(\(.+\))?!?:': ChangeType.DOCUMENTATION,
        r'^refactor(\(.+\))?!?:': ChangeType.REFACTOR,
        r'^test(\(.+\))?!?:': ChangeType.TEST,
        r'^chore(\(.+\))?!?:': ChangeType.CHORE,
        r'^style(\(.+\))?!?:': ChangeType.CHORE,
        r'^ci(\(.+\))?!?:': ChangeType.CHORE,
        r'^build(\(.+\))?!?:': ChangeType.CHORE,
        r'^security(\(.+\))?!?:': ChangeType.SECURITY,
        r'^deps?(\(.+\))?!?:': ChangeType.DEPENDENCY,
        r'^improve(\(.+\))?!?:': ChangeType.IMPROVEMENT,
    }
    
    def __init__(self, repo_path: Optional[str] = None, config: Optional[Dict] = None):
        self.repo_path = Path(repo_path) if repo_path else Path.cwd()
        self.config = config or {}
        
        # Configuration
        self.include_merge_commits = self.config.get('include_merge_commits', False)
        self.group_by_scope = self.config.get('group_by_scope', False)
        self.max_commits = self.config.get('max_commits', 500)
        
        logger.info(f"Changelog generator initialized for {self.repo_path}")
        
    def _run_git(self, *args) -> str:
        """Run git command and return output"""
        try:
            result = subprocess.run(
                ['git', *args],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            logger.error(f"Git command failed: {e.stderr}")
            raise
            
    def get_tags(self) -> List[Tuple[str, datetime]]:
        """Get all version tags sorted by date"""
        try:
            output = self._run_git(
                'tag', '-l', '--sort=-version:refname',
                '--format=%(refname:short)|%(creatordate:iso)'
            )
            tags = []
            for line in output.split('\n'):
                if '|' in line:
                    tag, date_str = line.split('|', 1)
                    if re.match(r'^v?\d+\.\d+', tag):
                        try:
                            date = datetime.fromisoformat(date_str.strip().replace(' ', 'T').split('+')[0])
                            tags.append((tag, date))
                        except ValueError:
                            pass
            return tags
        except Exception as e:
            logger.warning(f"Failed to get tags: {e}")
            return []
            
    def get_commits(
        self,
        since: Optional[str] = None,
        until: Optional[str] = None,
        since_date: Optional[datetime] = None
    ) -> List[ChangeEntry]:
        """
        Get commits in range
        
        Args:
            since: Starting commit/tag (exclusive)
            until: Ending commit/tag (inclusive)
            since_date: Get commits since date
        """
        args = [
            'log',
            f'--max-count={self.max_commits}',
            '--format=%H|%h|%s|%an|%ae|%aI',
        ]
        
        if not self.include_merge_commits:
            args.append('--no-merges')
            
        if since and until:
            args.append(f'{since}..{until}')
        elif since:
            args.append(f'{since}..HEAD')
        elif until:
            args.append(until)
        elif since_date:
            pass
        try:
            args.append(f'--since={since_date.isoformat()}')
            
            output = self._run_git(*args)
        except Exception as e:
            logger.error(f"Failed to get commits: {e}")
            return []
            
        entries = []
        for line in output.split('\n'):
            if not line.strip():
                continue
                
            parts = line.split('|', 5)
            if len(parts) < 6:
                continue
                
            commit_hash, short_hash, message, author, email, timestamp = parts
            
            # Parse commit message
            entry = self._parse_commit(
                commit_hash, short_hash, message, author, email, timestamp
            )
            if entry:
                entries.append(entry)
                
        return entries
    
    def _parse_commit(
        self,
        commit_hash: str,
        short_hash: str,
        message: str,
        author: str,
        email: str,
        timestamp: str
    ) -> Optional[ChangeEntry]:
        """Parse a commit message into a ChangeEntry"""
        
        # Determine change type
        change_type = ChangeType.CHORE
        scope = None
        breaking = '!' in message.split(':')[0] if ':' in message else False
        
        for pattern, ctype in self.COMMIT_PATTERNS.items():
            match = re.match(pattern, message, re.IGNORECASE)
            if match:
                change_type = ctype
                # Extract scope
                scope_match = re.search(r'\(([^)]+)\)', message.split(':')[0])
                if scope_match:
                    scope = scope_match.group(1)
                break
        
        # Clean description
        description = message
        if ':' in message:
            description = message.split(':', 1)[1].strip()
            
        # Extract issue references
        issues = re.findall(r'#(\d+)', message)
        
        # Extract PR reference
        pr_match = re.search(r'\(#(\d+)\)$', message)
        pull_request = pr_match.group(1) if pr_match else None
        
        try:
            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        except ValueError:
            dt = datetime.now()
            
        return ChangeEntry(
            commit_hash=commit_hash,
            short_hash=short_hash,
            change_type=change_type,
            scope=scope,
            description=description,
            author=author,
            author_email=email,
            timestamp=dt,
            breaking=breaking,
            issues=issues,
            pull_request=pull_request
        )
    
    def generate_changelog(
        self,
        since: Optional[str] = None,
        until: Optional[str] = None,
        version: Optional[str] = None
    ) -> ReleaseNotes:
        """
        Generate changelog for a version range
        
        Args:
            since: Starting tag/commit
            until: Ending tag/commit
            version: Version string for release notes
        """
        commits = self.get_commits(since=since, until=until)
        
        # Group by type
        changes: Dict[ChangeType, List[ChangeEntry]] = {}
        breaking_changes: List[ChangeEntry] = []
        contributors: set = set()
        
        for entry in commits:
            if entry.change_type not in changes:
                changes[entry.change_type] = []
            changes[entry.change_type].append(entry)
            
            if entry.breaking:
                breaking_changes.append(entry)
                
            contributors.add(entry.author)
            
        return ReleaseNotes(
            version=version or until or "Unreleased",
            date=datetime.now(),
            changes=changes,
            contributors=sorted(contributors),
            breaking_changes=breaking_changes
        )
    
    def generate_full_changelog(self) -> str:
        """Generate full changelog from all tags"""
        tags = self.get_tags()
        
        if not tags:
            # No tags, generate from all commits
            notes = self.generate_changelog(version="Unreleased")
            return notes.to_markdown()
            
        sections = []
        
        # Unreleased changes
        if tags:
            latest_tag = tags[0][0]
            unreleased = self.get_commits(since=latest_tag)
            if unreleased:
                notes = self.generate_changelog(since=latest_tag, version="Unreleased")
                sections.append(notes.to_markdown())
        
        # Each version
        for i, (tag, date) in enumerate(tags):
            since = tags[i + 1][0] if i + 1 < len(tags) else None
            notes = self.generate_changelog(since=since, until=tag, version=tag)
            notes.date = date
            sections.append(notes.to_markdown())
            
        return "\n---\n\n".join(sections)
    
    def generate_deployment_diff(
        self,
        from_ref: str,
        to_ref: str = "HEAD"
    ) -> Dict[str, Any]:
        """
        Generate deployment diff between two refs
        
        Returns:
            Dict with changes, files modified, and risk assessment
        """
        # Get commits
        commits = self.get_commits(since=from_ref, until=to_ref)
        
        # Get changed files
        try:
            files_output = self._run_git('diff', '--name-status', f'{from_ref}..{to_ref}')
            files_changed = []
            for line in files_output.split('\n'):
                if line.strip():
                    parts = line.split('\t')
                    if len(parts) >= 2:
                        files_changed.append({
                            'status': parts[0],
                            'file': parts[1]
                        })
        except Exception:
            files_changed = []
        # Get stats
            stats = self._run_git('diff', '--stat', f'{from_ref}..{to_ref}')
        except Exception:
            stats = ""
            
        # Risk assessment
        risk_level = "low"
        risk_factors = []
        
        breaking_count = sum(1 for c in commits if c.breaking)
        if breaking_count > 0:
            risk_level = "high"
            risk_factors.append(f"{breaking_count} breaking changes")
            
        security_count = sum(1 for c in commits if c.change_type == ChangeType.SECURITY)
        if security_count > 0:
            risk_factors.append(f"{security_count} security changes")
            
        # Check for risky file changes
        risky_patterns = ['config', 'database', 'migration', 'secret', 'key', 'password']
        risky_files = [f for f in files_changed if any(p in f['file'].lower() for p in risky_patterns)]
        if risky_files:
            risk_level = "medium" if risk_level == "low" else risk_level
            risk_factors.append(f"{len(risky_files)} sensitive files changed")
            
        return {
            'from_ref': from_ref,
            'to_ref': to_ref,
            'commit_count': len(commits),
            'commits': [c.to_markdown() for c in commits[:20]],  # Limit for readability
            'files_changed': files_changed,
            'stats': stats,
            'risk_level': risk_level,
            'risk_factors': risk_factors,
            'breaking_changes': [c.description for c in commits if c.breaking],
            'generated_at': datetime.now().isoformat()
        }
    
    def save_changelog(self, filepath: str = "CHANGELOG.md"):
        """Generate and save changelog to file"""
        changelog = self.generate_full_changelog()
        
        header = """# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

"""
        
        full_content = header + changelog
        
        output_path = self.repo_path / filepath
        with open(output_path, 'w') as f:
            f.write(full_content)
            
        logger.info(f"Changelog saved to {output_path}")
        return str(output_path)
    
    def save_deployment_report(
        self,
        from_ref: str,
        to_ref: str = "HEAD",
        filepath: str = "DEPLOYMENT_REPORT.md"
    ) -> str:
        """Generate and save deployment report"""
        diff = self.generate_deployment_diff(from_ref, to_ref)
        
        content = f"""# Deployment Report

**From:** {diff['from_ref']}  
**To:** {diff['to_ref']}  
**Generated:** {diff['generated_at']}

## Risk Assessment

**Risk Level:** {diff['risk_level'].upper()}

### Risk Factors
{chr(10).join(f'- {f}' for f in diff['risk_factors']) if diff['risk_factors'] else '- None identified'}

## Summary

- **Commits:** {diff['commit_count']}
- **Files Changed:** {len(diff['files_changed'])}

## Breaking Changes

{chr(10).join(f'- {c}' for c in diff['breaking_changes']) if diff['breaking_changes'] else 'None'}

## Recent Commits

{chr(10).join(diff['commits'])}

## Files Changed

| Status | File |
|--------|------|
{chr(10).join(f"| {f['status']} | {f['file']} |" for f in diff['files_changed'][:50])}

## Statistics

```
{diff['stats']}
```
"""
        
        output_path = self.repo_path / filepath
        with open(output_path, 'w') as f:
            f.write(content)
            
        logger.info(f"Deployment report saved to {output_path}")
        return str(output_path)


# CLI interface
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate changelog from Git history")
    parser.add_argument('--repo', default='.', help='Repository path')
    parser.add_argument('--output', default='CHANGELOG.md', help='Output file')
    parser.add_argument('--since', help='Starting tag/commit')
    parser.add_argument('--until', help='Ending tag/commit')
    parser.add_argument('--deployment', action='store_true', help='Generate deployment report')
    
    args = parser.parse_args()
    
    generator = ChangelogGenerator(args.repo)
    
    if args.deployment and args.since:
        generator.save_deployment_report(args.since, args.until or 'HEAD')
    else:
        generator.save_changelog(args.output)
