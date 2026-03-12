"""
UNIFIED SYSTEM INTEGRATION & ORPHANED CODE LINKER
============================================================

Scans, identifies, and integrates all trading bot components.

Features:
- Scan all modules
- Identify orphaned code
- Link components
- Create unified interfaces
- Generate integration report

Author: AI Assistant
Date: October 24, 2025
Version: 1.0.0
"""

import logging
import os
import sys
from pathlib import Path
from typing import Dict, List, Set, Tuple
from dataclasses import dataclass

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class ModuleInfo:
    """Information about a module."""
    name: str
    path: str
    imports: List[str]
    exports: List[str]
    is_orphaned: bool = False
    dependencies: List[str] = None
    
    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []


class UnifiedSystemIntegrator:
    """Integrates all trading bot components."""
    
    def __init__(self, base_path: str = "c:/Users/peterson/trading bot/trading_bot"):
        """Initialize integrator."""
        self.base_path = Path(base_path)
        self.modules: Dict[str, ModuleInfo] = {}
        self.orphaned_modules: List[str] = []
        self.integration_map: Dict[str, List[str]] = {}
        
        logger.info(f"Unified System Integrator initialized: {base_path}")
    
    def scan_modules(self) -> Dict[str, ModuleInfo]:
        """Scan all Python modules in the project."""
        logger.info("Scanning modules...")
        
        py_files = list(self.base_path.rglob("*.py"))
        logger.info(f"Found {len(py_files)} Python files")
        
        for py_file in py_files:
            try:
                relative_path = py_file.relative_to(self.base_path)
                module_name = str(relative_path).replace("\\", "/").replace(".py", "")
                
                # Skip __pycache__ and test files
                if "__pycache__" in str(py_file) or "test_" in py_file.name:
                    continue
                
                # Read file
                with open(py_file, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                # Extract imports and exports
                imports = self._extract_imports(content)
                exports = self._extract_exports(content)
                
                module_info = ModuleInfo(
                    name=module_name,
                    path=str(py_file),
                    imports=imports,
                    exports=exports
                )
                
                self.modules[module_name] = module_info
                
            except Exception as e:
                logger.warning(f"Error scanning {py_file}: {e}")
        
        logger.info(f"✓ Scanned {len(self.modules)} modules")
        return self.modules
    
    def _extract_imports(self, content: str) -> List[str]:
        """Extract imports from Python code."""
        imports = []
        
        for line in content.split('\n'):
            line = line.strip()
            if line.startswith('from ') or line.startswith('import '):
                imports.append(line)
        
        return imports
    
    def _extract_exports(self, content: str) -> List[str]:
        """Extract exports from Python code."""
        exports = []
        
        # Look for __all__
        for line in content.split('\n'):
            if '__all__' in line:
                # Extract list items
                start = line.find('[')
                end = line.find(']')
                if start != -1 and end != -1:
                    items = line[start+1:end].split(',')
                    exports.extend([item.strip().strip("'\"") for item in items])
        
        # Look for class and function definitions
        for line in content.split('\n'):
            line = line.strip()
            if line.startswith('class ') or line.startswith('def '):
                name = line.split('(')[0].replace('class ', '').replace('def ', '')
                if not name.startswith('_'):
                    exports.append(name)
        
        return exports
    
    def identify_orphaned_modules(self) -> List[str]:
        """Identify orphaned modules (not imported by others)."""
        logger.info("Identifying orphaned modules...")
        
        # Collect all imports
        all_imports = set()
        for module in self.modules.values():
            for imp in module.imports:
                # Extract module name from import
                if 'from ' in imp:
                    parts = imp.split('from ')[1].split(' import')[0].strip()
                    all_imports.add(parts)
                elif 'import ' in imp:
                    parts = imp.split('import ')[1].split(' as')[0].strip()
                    all_imports.add(parts)
        
        # Find modules not imported
        orphaned = []
        for module_name in self.modules.keys():
            if module_name not in all_imports:
                # Check if it's a main entry point
                if not any(x in module_name for x in ['main', '__init__', 'test']):
                    orphaned.append(module_name)
                    self.modules[module_name].is_orphaned = True
        
        self.orphaned_modules = orphaned
        logger.info(f"✓ Found {len(orphaned)} orphaned modules")
        
        return orphaned
    
    def create_integration_map(self) -> Dict[str, List[str]]:
        """Create integration map showing module dependencies."""
        logger.info("Creating integration map...")
        
        categories = {
            'core': [],
            'analysis': [],
            'execution': [],
            'risk': [],
            'ml': [],
            'infrastructure': [],
            'monitoring': [],
            'other': []
        }
        
        for module_name in self.modules.keys():
            if 'core' in module_name:
                categories['core'].append(module_name)
            elif 'analysis' in module_name:
                categories['analysis'].append(module_name)
            elif 'execution' in module_name:
                categories['execution'].append(module_name)
            elif 'risk' in module_name:
                categories['risk'].append(module_name)
            elif 'ml' in module_name:
                categories['ml'].append(module_name)
            elif 'infrastructure' in module_name or 'monitoring' in module_name:
                categories['infrastructure'].append(module_name)
            elif 'monitoring' in module_name:
                categories['monitoring'].append(module_name)
            else:
                categories['other'].append(module_name)
        
        self.integration_map = categories
        logger.info(f"✓ Created integration map with {len(categories)} categories")
        
        return categories
    
    def generate_integration_report(self) -> str:
        """Generate comprehensive integration report."""
        report = "\n" + "="*80 + "\n"
        report += "UNIFIED SYSTEM INTEGRATION REPORT\n"
        report += "="*80 + "\n\n"
        
        report += f"Total Modules: {len(self.modules)}\n"
        report += f"Orphaned Modules: {len(self.orphaned_modules)}\n"
        report += f"Categories: {len(self.integration_map)}\n\n"
        
        # Module breakdown by category
        report += "MODULE BREAKDOWN BY CATEGORY:\n"
        report += "-"*80 + "\n"
        
        for category, modules in self.integration_map.items():
            report += f"\n{category.upper()} ({len(modules)} modules):\n"
            for module in sorted(modules)[:10]:  # Show first 10
                status = "ORPHANED" if self.modules[module].is_orphaned else "LINKED"
                report += f"  ├─ {module} [{status}]\n"
            
            if len(modules) > 10:
                report += f"  └─ ... and {len(modules) - 10} more\n"
        
        # Orphaned modules
        report += "\n" + "-"*80 + "\n"
        report += "ORPHANED MODULES (Not imported by others):\n"
        
        if self.orphaned_modules:
            for module in sorted(self.orphaned_modules)[:20]:
                report += f"  ├─ {module}\n"
            
            if len(self.orphaned_modules) > 20:
                report += f"  └─ ... and {len(self.orphaned_modules) - 20} more\n"
        else:
            report += "  No orphaned modules found\n"
        
        # Integration recommendations
        report += "\n" + "-"*80 + "\n"
        report += "INTEGRATION RECOMMENDATIONS:\n"
        report += "  1. Link orphaned modules to core system\n"
        report += "  2. Create unified __init__.py files\n"
        report += "  3. Establish clear module dependencies\n"
        report += "  4. Create integration layer\n"
        report += "  5. Document module interfaces\n"
        
        report += "\n" + "="*80 + "\n"
        
        return report
    
    def create_unified_init_files(self) -> int:
        """Create unified __init__.py files for all packages."""
        logger.info("Creating unified __init__.py files...")
        
        created = 0
        
        # Get all directories
        directories = set()
        for module_path in self.modules.keys():
            parts = module_path.split('/')
            for i in range(1, len(parts)):
                dir_path = '/'.join(parts[:i])
                directories.add(dir_path)
        
        for dir_name in directories:
            dir_path = self.base_path / dir_name
            init_file = dir_path / "__init__.py"
            
            if not init_file.exists():
                try:
                    init_file.parent.mkdir(parents=True, exist_ok=True)
                    
                    # Create __init__.py content
                    content = f'"""\n{dir_name.replace("/", ".")} package\n"""\n\n'
                    
                    with open(init_file, 'w') as f:
                        f.write(content)
                    
                    created += 1
                    logger.debug(f"Created {init_file}")
                
                except Exception as e:
                    logger.warning(f"Failed to create {init_file}: {e}")
        
        logger.info(f"✓ Created {created} __init__.py files")
        return created
    
    def link_orphaned_modules(self) -> Dict[str, str]:
        """Create links for orphaned modules to core system."""
        logger.info("Linking orphaned modules...")
        
        links = {}
        
        # Create a linking module
        linking_content = '"""\nOrphaned Module Linker\nAutomatically links orphaned modules to core system\n"""\n\n'
        
        for orphaned in self.orphaned_modules[:10]:  # Link first 10
            try:
                linking_content += f"from trading_bot.{orphaned} import *\n"
                links[orphaned] = "linked"
            except Exception as e:
                logger.warning(f"Failed to link {orphaned}: {e}")
                links[orphaned] = "failed"
        
        # Save linking module
        linking_file = self.base_path / "orphaned_linker.py"
        try:
            with open(linking_file, 'w') as f:
                f.write(linking_content)
            logger.info(f"✓ Created orphaned linker: {linking_file}")
        except Exception as e:
            logger.error(f"Failed to create linker: {e}")
        
        return links
    
    def run_full_integration(self) -> Dict:
        """Run full integration process."""
        logger.info("\n" + "="*80)
        logger.info("STARTING FULL SYSTEM INTEGRATION")
        logger.info("="*80 + "\n")
        
        # Scan modules
        self.scan_modules()
        
        # Identify orphaned
        self.identify_orphaned_modules()
        
        # Create integration map
        self.create_integration_map()
        
        # Create __init__ files
        init_created = self.create_unified_init_files()
        
        # Link orphaned modules
        links = self.link_orphaned_modules()
        
        # Generate report
        report = self.generate_integration_report()
        logger.info(report)
        
        # Save report
        report_file = "c:/Users/peterson/trading bot/SYSTEM_INTEGRATION_REPORT.txt"
        try:
            with open(report_file, 'w') as f:
                f.write(report)
            logger.info(f"✓ Report saved to {report_file}")
        except Exception as e:
            logger.error(f"Failed to save report: {e}")
        
        return {
            'modules_scanned': len(self.modules),
            'orphaned_found': len(self.orphaned_modules),
            'init_files_created': init_created,
            'modules_linked': len([v for v in links.values() if v == 'linked']),
            'report': report
        }


def main():
    """Main execution."""
    logger.info("Starting Unified System Integration")
    
    try:
        integrator = UnifiedSystemIntegrator()
        results = integrator.run_full_integration()
        
        logger.info("\n" + "="*80)
        logger.info("INTEGRATION COMPLETE")
        logger.info("="*80)
        logger.info(f"Modules Scanned: {results['modules_scanned']}")
        logger.info(f"Orphaned Found: {results['orphaned_found']}")
        logger.info(f"Init Files Created: {results['init_files_created']}")
        logger.info(f"Modules Linked: {results['modules_linked']}")
        
    except Exception as e:
        logger.error(f"Integration failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
