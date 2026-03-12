"""
Upgrade Gym to Gymnasium
Automatically replaces gym imports with gymnasium
"""

import os
import sys
import io
from pathlib import Path
import re

# Set UTF-8 encoding for Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')


class GymUpgrader:
    """Upgrade Gym to Gymnasium"""
    
    def __init__(self, root_dir: str):
        self.root_dir = Path(root_dir)
        self.files_updated = []
    
    def print_header(self, text: str):
        """Print formatted header"""
        print(f"\n{'='*80}")
        print(f"{text.center(80)}")
        print(f"{'='*80}\n")
    
    def find_gym_imports(self):
        """Find all files with gym imports"""
        py_files = list(self.root_dir.glob('**/*.py'))
        py_files = [f for f in py_files if '.venv' not in str(f) and 'backups' not in str(f)]
        
        gym_files = []
        for file in py_files:
            try:
                with open(file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                if 'import gym' in content and 'gymnasium' not in content:
                    gym_files.append(file)
            except Exception as e:
                pass
        
        return gym_files
    
    def upgrade_file(self, file_path: Path) -> bool:
        """Upgrade a single file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Replace imports
            original_content = content
            
            # Replace: import gym
            content = re.sub(
                r'^import gym$',
                'import gymnasium as gym',
                content,
                flags=re.MULTILINE
            )
            
            # Replace: from gym import ...
            content = re.sub(
                r'^from gym import',
                'from gymnasium import',
                content,
                flags=re.MULTILINE
            )
            
            # Only write if changed
            if content != original_content:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                self.files_updated.append(file_path)
                return True
            
            return False
            
        except Exception as e:
            print(f"    ❌ Error updating {file_path}: {e}")
            return False
    
    def run_upgrade(self):
        """Run the upgrade"""
        self.print_header("GYM TO GYMNASIUM UPGRADE")
        
        print("  Finding files with gym imports...")
        gym_files = self.find_gym_imports()
        
        if not gym_files:
            print("  ✅ No files found with gym imports")
            print("  Either already upgraded or gym not used")
            return
        
        print(f"  Found {len(gym_files)} files with gym imports\n")
        
        print("  Upgrading files...")
        for file in gym_files:
            if self.upgrade_file(file):
                print(f"    ✅ {file.relative_to(self.root_dir)}")
            else:
                print(f"    ⚠️ {file.relative_to(self.root_dir)} - No changes needed")
        
        self.print_header("UPGRADE COMPLETE")
        
        print(f"  Files Updated: {len(self.files_updated)}")
        
        if self.files_updated:
            print(f"\n  Updated files:")
            for file in self.files_updated:
                print(f"    - {file.relative_to(self.root_dir)}")
        
        print(f"\n  Next steps:")
        print(f"    1. Uninstall gym: pip uninstall gym")
        print(f"    2. Install gymnasium: pip install gymnasium")
        print(f"    3. Test the bot: py main.py --mode paper")
        
        print(f"\n  ✅ Upgrade complete!")


def main():
    """Main entry point"""
    root_dir = Path(__file__).parent
    
    upgrader = GymUpgrader(root_dir)
    upgrader.run_upgrade()


if __name__ == '__main__':
    main()
