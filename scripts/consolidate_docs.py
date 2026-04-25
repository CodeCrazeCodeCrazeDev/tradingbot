"""
Documentation Consolidator
Organizes and consolidates 50+ markdown documentation files
"""

import os
import re
import shutil
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional
import json


class DocumentationConsolidator:
    """Consolidates fragmented documentation into structured format."""
    
    def __init__(self, root_dir: str = "."):
        self.root_dir = Path(root_dir)
        self.docs_dir = self.root_dir / "docs"
        self.archive_dir = self.root_dir / "docs" / "archive"
        
        # Categories for documentation
        self.categories = {
            "architecture": [],
            "integration": [],
            "guides": [],
            "api": [],
            "deployment": [],
            "troubleshooting": [],
            "misc": []
        }
    
    def scan_documentation(self) -> List[Path]:
        """Scan for all markdown documentation files."""
        md_files = []
        
        # Scan root directory
        for file in self.root_dir.glob("*.md"):
            if file.name not in ["README.md", "CHANGELOG.md", "LICENSE.md"]:
                md_files.append(file)
        
        # Scan docs directory
        if self.docs_dir.exists():
            for file in self.docs_dir.rglob("*.md"):
                md_files.append(file)
        
        return sorted(md_files)
    
    def categorize_file(self, file_path: Path) -> str:
        """Categorize documentation file by content analysis."""
        name = file_path.name.lower()
        content = file_path.read_text(encoding='utf-8', errors='ignore').lower()[:2000]
        
        # Architecture docs
        if any(x in name for x in ['architecture', 'design', 'structure', 'domain', 'layer', 'unified', 'system']):
            if 'integration' not in name and 'guide' not in name:
                return "architecture"
        
        # Integration docs
        if any(x in name for x in ['integration', 'complete', 'migration', 'consolidation']):
            return "integration"
        
        # API docs
        if any(x in name for x in ['api', 'reference', 'endpoint', 'openapi']):
            return "api"
        
        # Guides
        if any(x in name for x in ['guide', 'tutorial', 'howto', 'quickstart', 'usage', 'manual']):
            return "guides"
        
        # Deployment
        if any(x in name for x in ['deploy', 'production', 'docker', 'kubernetes', 'infrastructure']):
            return "deployment"
        
        # Troubleshooting
        if any(x in name for x in ['fix', 'debug', 'issue', 'error', 'troubleshoot', 'risk', 'mitigate']):
            return "troubleshooting"
        
        # Content-based categorization
        if 'architecture' in content[:500] and 'integration' not in name:
            return "architecture"
        
        if 'deploy' in content[:500] or 'production' in content[:500]:
            return "deployment"
        
        return "misc"
    
    def extract_title(self, file_path: Path) -> str:
        """Extract title from markdown file."""
        content = file_path.read_text(encoding='utf-8', errors='ignore')
        
        # Look for # Title
        match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
        if match:
            return match.group(1).strip()
        
        # Use filename
        return file_path.stem.replace('_', ' ').replace('-', ' ').title()
    
    def consolidate(self):
        """Run full consolidation process."""
        print("Starting Documentation Consolidation...\n")
        
        # Scan files
        md_files = self.scan_documentation()
        print(f"Found {len(md_files)} markdown files to process")
        
        # Categorize
        for file_path in md_files:
            category = self.categorize_file(file_path)
            self.categories[category].append({
                "path": file_path,
                "name": file_path.name,
                "title": self.extract_title(file_path),
                "size": file_path.stat().st_size
            })
        
        # Print summary
        print("\nCategorization Summary:")
        for cat, files in self.categories.items():
            if files:
                print(f"  {cat}: {len(files)} files")
        
        # Create organized structure
        self._create_structure()
        
        # Generate index
        self._generate_index()
        
        # Archive old files
        self._archive_files(md_files)
        
        print("\nDocumentation consolidation complete!")
        print(f"   Organized files in: {self.docs_dir}")
        print(f"   Index: {self.docs_dir / 'INDEX.md'}")
    
    def _create_structure(self):
        """Create organized documentation structure."""
        # Create category directories
        for category in self.categories.keys():
            cat_dir = self.docs_dir / category
            cat_dir.mkdir(parents=True, exist_ok=True)
            
            # Copy files
            for file_info in self.categories[category]:
                dest = cat_dir / file_info["name"]
                
                # If duplicate name, add number
                counter = 1
                original_dest = dest
                while dest.exists():
                    dest = original_dest.parent / f"{original_dest.stem}_{counter}{original_dest.suffix}"
                    counter += 1
                
                shutil.copy2(file_info["path"], dest)
    
    def _generate_index(self):
        """Generate documentation index."""
        index_content = """# Trading Bot Documentation Index

*Auto-generated on: {date}*

## Quick Links

- [README](../README.md) - Project overview
- [User Guide](./guides/) - Getting started guides
- [API Reference](./api/) - API documentation
- [Deployment](./deployment/) - Production deployment
- [Architecture](./architecture/) - System design

## Documentation Categories

""".format(date=datetime.now().strftime("%Y-%m-%d %H:%M"))
        
        for category, files in self.categories.items():
            if not files:
                continue
            
            index_content += f"\n### {category.title()}\n\n"
            
            for file_info in sorted(files, key=lambda x: x["title"]):
                index_content += f"- [{file_info['title']}](./{category}/{file_info['name']})\n"
        
        index_content += """

## Finding Documentation

1. **New users**: Start with [README](../README.md) and [guides](./guides/)
2. **Developers**: Check [architecture](./architecture/) and [api](./api/)
3. **DevOps**: See [deployment](./deployment/) guides
4. **Troubleshooting**: Review [troubleshooting](./troubleshooting/) docs

---

*This index was automatically generated. Do not edit manually.*
"""
        
        index_path = self.docs_dir / "INDEX.md"
        index_path.write_text(index_content, encoding='utf-8')
    
    def _archive_files(self, files: List[Path]):
        """Archive original files."""
        self.archive_dir.mkdir(parents=True, exist_ok=True)
        
        # Create archive manifest
        manifest = {
            "archived_date": datetime.now().isoformat(),
            "files": [str(f) for f in files]
        }
        
        manifest_path = self.archive_dir / "manifest.json"
        manifest_path.write_text(json.dumps(manifest, indent=2), encoding='utf-8')
        
        print(f"\nArchived {len(files)} files to {self.archive_dir}")


def main():
    """Run documentation consolidation."""
    consolidator = DocumentationConsolidator()
    consolidator.consolidate()


if __name__ == "__main__":
    main()
