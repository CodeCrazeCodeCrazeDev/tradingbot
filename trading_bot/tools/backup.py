#!/usr/bin/env python
"""
Backup Tool

This tool creates backups of critical configuration files and data
for the Elite Trading Bot.
"""

import os
import sys
import shutil
import datetime
import argparse
import zipfile
from pathlib import Path
from typing import Set
import json

import logging
logger = logging.getLogger(__name__)


# Add parent directory to path to allow importing from trading_bot
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))


# Critical files and directories to backup
BACKUP_ITEMS = [
    "config/survival_config.yaml",
    "config/api_keys.json",
    "config/encryption.key",
    "data/time_series",
    "logs"
]


def create_backup(backup_dir=None, include_data=True):
    """
    Create a backup of critical files and directories
    
    Args:
        backup_dir: Directory to store the backup
        include_data: Whether to include data files in the backup
    
    Returns:
        Path to the created backup file
    """
    # Create timestamp for backup filename
    try:
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    
        # Set backup directory
        if backup_dir is None:
            backup_dir = Path("backups")
        else:
            backup_dir = Path(backup_dir)
    
        # Create backup directory if it doesn't exist
        backup_dir.mkdir(parents=True, exist_ok=True)
    
        # Create backup filename
        backup_file = backup_dir / f"trading_bot_backup_{timestamp}.zip"
    
        # Items to backup
        items_to_backup = BACKUP_ITEMS.copy()
        if not include_data:
            items_to_backup = [item for item in items_to_backup if not item.startswith("data")]
    
        # Create zip file
        with zipfile.ZipFile(backup_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for item in items_to_backup:
                item_path = Path(item)
            
                if not item_path.exists():
                    logger.info(f"Warning: {item} does not exist, skipping")
                    continue
            
                logger.info(f"Backing up {item}")
            
                if item_path.is_file():
                    # Add file to zip
                    zipf.write(item_path, item_path)
                elif item_path.is_dir():
                    # Add directory contents to zip
                    for file_path in item_path.glob('**/*'):
                        if file_path.is_file():
                            zipf.write(file_path, file_path)
    
        logger.info(f"Backup created: {backup_file}")
        return backup_file
    except Exception as e:
        logger.error(f"Error in create_backup: {e}")
        raise


def restore_backup(backup_file, target_dir=None, overwrite=False):
    """
    Restore a backup
    
    Args:
        backup_file: Path to the backup file
        target_dir: Directory to restore to (default: current directory)
        overwrite: Whether to overwrite existing files
    """
    try:
        backup_path = Path(backup_file)
    
        if not backup_path.exists():
            logger.info(f"Error: Backup file {backup_file} does not exist")
            return False
    
        # Set target directory
        if target_dir is None:
            target_dir = Path(".")
        else:
            target_dir = Path(target_dir)
    
        # Create target directory if it doesn't exist
        target_dir.mkdir(parents=True, exist_ok=True)
    
        # Extract zip file
        with zipfile.ZipFile(backup_path, 'r') as zipf:
            for file_info in zipf.infolist():
                file_path = Path(file_info.filename)
                target_path = target_dir / file_path
            
                # Check if file exists
                if target_path.exists() and not overwrite:
                    logger.info(f"Skipping {file_path} (already exists)")
                    continue
            
                # Create parent directories if they don't exist
                target_path.parent.mkdir(parents=True, exist_ok=True)
            
                # Extract file
                logger.info(f"Restoring {file_path}")
                zipf.extract(file_info, target_dir)
    
        logger.info(f"Backup restored from {backup_file}")
        return True
    except Exception as e:
        logger.error(f"Error in restore_backup: {e}")
        raise


def main():
    """Main function"""
    try:
        parser = argparse.ArgumentParser(description="Elite Trading Bot - Backup Tool")
    
        # Create subparsers for backup and restore commands
        subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
        # Backup command
        backup_parser = subparsers.add_parser("backup", help="Create a backup")
        backup_parser.add_argument("--dir", help="Directory to store the backup")
        backup_parser.add_argument("--no-data", action="store_true", help="Exclude data files from backup")
    
        # Restore command
        restore_parser = subparsers.add_parser("restore", help="Restore a backup")
        restore_parser.add_argument("file", help="Backup file to restore")
        restore_parser.add_argument("--dir", help="Directory to restore to")
        restore_parser.add_argument("--overwrite", action="store_true", help="Overwrite existing files")
    
        # Parse arguments
        args = parser.parse_args()
    
        # Run command
        if args.command == "backup":
            create_backup(args.dir, not args.no_data)
        elif args.command == "restore":
            restore_backup(args.file, args.dir, args.overwrite)
        else:
            # Default to backup if no command specified
            logger.info("Elite Trading Bot - Backup Tool")
            logger.info("==============================")
            create_backup()
    except Exception as e:
        logger.error(f"Error in main: {e}")
        raise


if __name__ == "__main__":
    main()
