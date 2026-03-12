"""Code Repository for Self-Improving Trading Bot.

from pathlib import Path
This module implements a code repository that manages code versions and changes,
providing version control and rollback capabilities for self-modified code.
"""

import os
import shutil
import json
import logging
import hashlib
import difflib
import tempfile
import subprocess
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum

from .code_generator import GeneratedCode
import pathlib

logger = logging.getLogger(__name__)


@dataclass
class CodeVersion:
    """Version of a code file."""
    version_id: str
    file_path: str
    content: str
    timestamp: datetime
    description: str
    source_knowledge: List[str]  # Knowledge item IDs
    hash: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CodeChange:
    """Change between code versions."""
    change_id: str
    file_path: str
    from_version: str
    to_version: str
    timestamp: datetime
    diff: str
    description: str
    metadata: Dict[str, Any] = field(default_factory=dict)


class CodeRepository:
    """Repository for managing code versions and changes."""
    
    def __init__(self, repo_dir: Optional[str] = None):
        """Initialize the code repository.
        
        Args:
            repo_dir: Directory to store repository data
            use_git: Whether to use Git for version control
        """
        self.repo_dir = repo_dir or os.path.join(os.getcwd(), "code_repository")
        self.versions_dir = os.path.join(self.repo_dir, "versions")
        self.changes_dir = os.path.join(self.repo_dir, "changes")
        self.metadata_file = os.path.join(self.repo_dir, "metadata.json")
        
        # Create repository directories
        os.makedirs(self.versions_dir, exist_ok=True)
        os.makedirs(self.changes_dir, exist_ok=True)
        
        # Initialize metadata
        self.metadata = self._load_metadata()
        
        # Initialize backup system
        self._init_backup()
        
        logger.info(f"Code repository initialized at {self.repo_dir}")
    
    def _load_metadata(self) -> Dict[str, Any]:
        """Load repository metadata.
        
        Returns:
            Repository metadata
        """
        if os.path.exists(self.metadata_file):
            try:
                with open(self.metadata_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading metadata: {e}")
        
        # Initialize new metadata
        metadata = {
            "files": {},
            "latest_versions": {},
            "version_history": {},
            "changes": []
        }
        
        self._save_metadata(metadata)
        return metadata
    
    def _save_metadata(self, metadata: Optional[Dict[str, Any]] = None):
        """Save repository metadata.
        
        Args:
            metadata: Metadata to save (uses self.metadata if None)
        """
        try:
            with open(self.metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata or self.metadata, f, indent=2, default=self._json_serializer)
        except Exception as e:
            logger.error(f"Error saving metadata: {e}")
    
    def _json_serializer(self, obj):
        """Custom JSON serializer for datetime objects.
        
        Args:
            obj: Object to serialize
            
        Returns:
            Serialized object
        """
        if isinstance(obj, datetime):
            return obj.isoformat()
        raise TypeError(f"Type {type(obj)} not serializable")
    
    def _init_backup(self):
        """Initialize backup system."""
        # Create backup directory
        self.backup_dir = os.path.join(self.repo_dir, 'code_backups')
        os.makedirs(self.backup_dir, exist_ok=True)
        logger.info(f"Initialized backup system at {self.backup_dir}")
    
    def add_version(self, file_path: str, content: str, description: str,
                  source_knowledge: Optional[List[str]] = None,
                  metadata: Optional[Dict[str, Any]] = None) -> CodeVersion:
        """Add a new version of a code file.
        
        Args:
            file_path: Path to the code file
            content: Content of the code file
            description: Description of the version
            source_knowledge: IDs of knowledge items used for this version
            metadata: Additional metadata
            
        Returns:
            New code version
        """
        # Normalize file path
        file_path = os.path.normpath(file_path)
        
        # Generate version ID and hash
        timestamp = datetime.now()
        version_id = f"{os.path.basename(file_path)}_{timestamp.strftime('%Y%m%d_%H%M%S')}"
        content_hash = hashlib.sha256(content.encode('utf-8')).hexdigest()
        
        # Create version
        version = CodeVersion(
            version_id=version_id,
            file_path=file_path,
            content=content,
            timestamp=timestamp,
            description=description,
            source_knowledge=source_knowledge or [],
            hash=content_hash,
            metadata=metadata or {}
        )
        
        # Save version content
        version_file = os.path.join(self.versions_dir, f"{version_id}.py")
        with open(version_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        # Update metadata
        if file_path not in self.metadata["files"]:
            self.metadata["files"][file_path] = {
                "versions": [],
                "latest_version": version_id
            }
        
        self.metadata["files"][file_path]["versions"].append(version_id)
        self.metadata["files"][file_path]["latest_version"] = version_id
        self.metadata["latest_versions"][file_path] = version_id
        
        self.metadata["version_history"][version_id] = {
            "file_path": file_path,
            "timestamp": timestamp.isoformat(),
            "description": description,
            "source_knowledge": source_knowledge or [],
            "hash": content_hash,
            "metadata": metadata or {}
        }
        
        self._save_metadata()
        
        # Create change if not the first version
        if len(self.metadata["files"][file_path]["versions"]) > 1:
            prev_version_id = self.metadata["files"][file_path]["versions"][-2]
            self._create_change(file_path, prev_version_id, version_id, description)
        
        # Create backup of the file
        try:
            backup_file = os.path.join(self.backup_dir, f"{os.path.basename(file_path)}.{timestamp.strftime('%Y%m%d_%H%M%S')}.bak")
            shutil.copy2(version_file, backup_file)
            logger.info(f"Created backup at {backup_file}")
        except Exception as e:
            logger.warning(f"Backup creation failed: {e}")
        
        logger.info(f"Added version {version_id} for {file_path}")
        return version
    
    def _create_change(self, file_path: str, from_version: str, to_version: str, description: str):
        """Create a change record between versions.
        
        Args:
            file_path: Path to the code file
            from_version: ID of the source version
            to_version: ID of the target version
            description: Description of the change
        """
        # Generate change ID
        timestamp = datetime.now()
        change_id = f"change_{timestamp.strftime('%Y%m%d_%H%M%S')}"
        
        # Get version contents
        from_content = self.get_version_content(from_version)
        to_content = self.get_version_content(to_version)
        
        if from_content is None or to_content is None:
            logger.error(f"Cannot create change: version content not found")
            return
        
        # Generate diff
        diff = self._generate_diff(from_content, to_content, file_path)
        
        # Create change record
        change = CodeChange(
            change_id=change_id,
            file_path=file_path,
            from_version=from_version,
            to_version=to_version,
            timestamp=timestamp,
            diff=diff,
            description=description,
            metadata={}
        )
        
        # Save change
        change_file = os.path.join(self.changes_dir, f"{change_id}.diff")
        with open(change_file, 'w', encoding='utf-8') as f:
            f.write(diff)
        
        # Update metadata
        self.metadata["changes"].append({
            "change_id": change_id,
            "file_path": file_path,
            "from_version": from_version,
            "to_version": to_version,
            "timestamp": timestamp.isoformat(),
            "description": description
        })
        
        self._save_metadata()
        
        logger.info(f"Created change {change_id} for {file_path}")
    
    def _generate_diff(self, from_content: str, to_content: str, file_path: str) -> str:
        """Generate a diff between two versions.
        
        Args:
            from_content: Source content
            to_content: Target content
            file_path: Path to the file
            
        Returns:
            Diff string
        """
        from_lines = from_content.splitlines()
        to_lines = to_content.splitlines()
        
        diff = difflib.unified_diff(
            from_lines,
            to_lines,
            fromfile=f"a/{file_path}",
            tofile=f"b/{file_path}",
            lineterm=""
        )
        
        return "\n".join(diff)
    
    def get_version(self, version_id: str) -> Optional[CodeVersion]:
        """Get a specific code version.
        
        Args:
            version_id: ID of the version to get
            
        Returns:
            Code version if found, None otherwise
        """
        if version_id not in self.metadata["version_history"]:
            logger.warning(f"Version not found: {version_id}")
            return None
        
        version_info = self.metadata["version_history"][version_id]
        content = self.get_version_content(version_id)
        
        if content is None:
            logger.error(f"Version content not found: {version_id}")
            return None
        
        return CodeVersion(
            version_id=version_id,
            file_path=version_info["file_path"],
            content=content,
            timestamp=datetime.fromisoformat(version_info["timestamp"]),
            description=version_info["description"],
            source_knowledge=version_info["source_knowledge"],
            hash=version_info["hash"],
            metadata=version_info["metadata"]
        )
    
    def get_version_content(self, version_id: str) -> Optional[str]:
        """Get the content of a specific version.
        
        Args:
            version_id: ID of the version to get
            
        Returns:
            Version content if found, None otherwise
        """
        version_file = os.path.join(self.versions_dir, f"{version_id}.py")
        
        if not os.path.exists(version_file):
            logger.warning(f"Version file not found: {version_file}")
            return None
        try:
        
            with open(version_file, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            logger.error(f"Error reading version file: {e}")
            return None
    
    def get_latest_version(self, file_path: str) -> Optional[CodeVersion]:
        """Get the latest version of a file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Latest code version if found, None otherwise
        """
        # Normalize file path
        file_path = os.path.normpath(file_path)
        
        if file_path not in self.metadata["latest_versions"]:
            logger.warning(f"No versions found for file: {file_path}")
            return None
        
        version_id = self.metadata["latest_versions"][file_path]
        return self.get_version(version_id)
    
    def get_file_versions(self, file_path: str) -> List[CodeVersion]:
        """Get all versions of a file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            List of code versions
        """
        # Normalize file path
        file_path = os.path.normpath(file_path)
        
        if file_path not in self.metadata["files"]:
            logger.warning(f"No versions found for file: {file_path}")
            return []
        
        versions = []
        for version_id in self.metadata["files"][file_path]["versions"]:
            version = self.get_version(version_id)
            if version:
                versions.append(version)
        
        return versions
    
    def get_change(self, change_id: str) -> Optional[CodeChange]:
        """Get a specific change.
        
        Args:
            change_id: ID of the change to get
            
        Returns:
            Code change if found, None otherwise
        """
        change_info = None
        for change in self.metadata["changes"]:
            if change["change_id"] == change_id:
                change_info = change
                break
        
        if not change_info:
            logger.warning(f"Change not found: {change_id}")
            return None
        
        change_file = os.path.join(self.changes_dir, f"{change_id}.diff")
        
        if not os.path.exists(change_file):
            logger.warning(f"Change file not found: {change_file}")
            return None
        try:
        
            with open(change_file, 'r', encoding='utf-8') as f:
                diff = f.read()
        except Exception as e:
            logger.error(f"Error reading change file: {e}")
            return None
        
        return CodeChange(
            change_id=change_id,
            file_path=change_info["file_path"],
            from_version=change_info["from_version"],
            to_version=change_info["to_version"],
            timestamp=datetime.fromisoformat(change_info["timestamp"]),
            diff=diff,
            description=change_info["description"],
            metadata={}
        )
    
    def get_file_changes(self, file_path: str) -> List[CodeChange]:
        """Get all changes for a file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            List of code changes
        """
        # Normalize file path
        file_path = os.path.normpath(file_path)
        
        changes = []
        for change_info in self.metadata["changes"]:
            if change_info["file_path"] == file_path:
                change = self.get_change(change_info["change_id"])
                if change:
                    changes.append(change)
        
        return changes
    
    def rollback(self, file_path: str, version_id: str) -> bool:
        """Roll back a file to a specific version.
        
        Args:
            file_path: Path to the file
            version_id: ID of the version to roll back to
            
        Returns:
            True if successful, False otherwise
        """
        # Normalize file path
        file_path = os.path.normpath(file_path)
        
        # Check if version exists
        if version_id not in self.metadata["version_history"]:
            logger.warning(f"Version not found: {version_id}")
            return False
        
        # Check if version belongs to file
        version_info = self.metadata["version_history"][version_id]
        if version_info["file_path"] != file_path:
            logger.warning(f"Version {version_id} does not belong to file {file_path}")
            return False
        
        # Get version content
        content = self.get_version_content(version_id)
        if content is None:
            logger.error(f"Version content not found: {version_id}")
            return False
        
        # Add new version with rollback description
        self.add_version(
            file_path=file_path,
            content=content,
            description=f"Rollback to version {version_id}",
            source_knowledge=version_info["source_knowledge"],
            metadata={
                "rollback": True,
                "rollback_to": version_id,
                "original_timestamp": version_info["timestamp"]
            }
        )
        
        logger.info(f"Rolled back {file_path} to version {version_id}")
        return True
    
    def apply_generated_code(self, generated_code: GeneratedCode, description: str) -> Optional[CodeVersion]:
        """Apply generated code to a file.
        
        Args:
            generated_code: Generated code to apply
            description: Description of the change
            
        Returns:
            New code version if successful, None otherwise
        """
        file_path = generated_code.target_file
        
        # Add new version
        return self.add_version(
            file_path=file_path,
            content=generated_code.code,
            description=description,
            source_knowledge=generated_code.source_knowledge,
            metadata={
                "generated": True,
                "dependencies": generated_code.dependencies,
                "generated_at": generated_code.generated_at.isoformat(),
                "validated": generated_code.validated,
                "safety_checked": generated_code.safety_checked,
                **generated_code.metadata
            }
        )
    
    def get_stats(self) -> Dict[str, Any]:
        """Get repository statistics.
        
        Returns:
            Dictionary of statistics
        """
        stats = {
            "total_files": len(self.metadata["files"]),
            "total_versions": sum(len(file_info["versions"]) for file_info in self.metadata["files"].values()),
            "total_changes": len(self.metadata["changes"]),
            "files": {},
            "version_count_by_file": {},
            "change_count_by_file": {}
        }
        
        # Count versions and changes by file
        for file_path, file_info in self.metadata["files"].items():
            stats["version_count_by_file"][file_path] = len(file_info["versions"])
            
            change_count = 0
            for change_info in self.metadata["changes"]:
                if change_info["file_path"] == file_path:
                    change_count += 1
            
            stats["change_count_by_file"][file_path] = change_count
            
            stats["files"][file_path] = {
                "versions": len(file_info["versions"]),
                "changes": change_count,
                "latest_version": file_info["latest_version"]
            }
        
        return stats
