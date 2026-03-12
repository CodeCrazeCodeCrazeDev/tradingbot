"""
Comprehensive Documentation vs Implementation Gap Scanner
Scans all documentation files and checks if documented features exist in code
"""

import os
import re
from pathlib import Path
from typing import Dict, List, Set, Tuple
import json

class DocumentationGapScanner:
    def __init__(self, root_dir: str):
        self.root_dir = Path(root_dir)
        self.trading_bot_dir = self.root_dir / "trading_bot"
        self.gaps = []
        self.implemented = []
        
    def scan_all_docs(self) -> Dict:
        """Scan all markdown documentation files"""
        print("Scanning documentation files...")
        
        doc_files = list(self.root_dir.glob("*.md"))
        doc_files.extend(list((self.root_dir / "docs").glob("*.md")) if (self.root_dir / "docs").exists() else [])
        
        print(f"Found {len(doc_files)} documentation files")
        
        features = {
            'files': [],
            'classes': [],
            'modules': [],
            'systems': [],
            'features': []
        }
        
        for doc_file in doc_files:
            try:
                content = doc_file.read_text(encoding='utf-8', errors='ignore')
                features['files'].extend(self.extract_file_references(content))
                features['classes'].extend(self.extract_class_references(content))
                features['modules'].extend(self.extract_module_references(content))
                features['systems'].extend(self.extract_system_references(content))
                features['features'].extend(self.extract_feature_descriptions(content, doc_file.name))
            except Exception as e:
                print(f"Warning: Error reading {doc_file.name}: {e}")
        
        # Remove duplicates (except for features which contains dicts)
        for key in features:
            if key != 'features':
                features[key] = list(set(features[key]))
        
        return features
    
    def extract_file_references(self, content: str) -> List[str]:
        """Extract file path references from documentation"""
        patterns = [
            r'`trading_bot/[\w/]+\.py`',
            r'trading_bot/[\w/]+\.py',
            r'File.*?:.*?`([\w/]+\.py)`',
            r'\*\*File\*\*:.*?`([\w/]+\.py)`',
        ]
        
        files = []
        for pattern in patterns:
            matches = re.findall(pattern, content)
            files.extend([m.strip('`') for m in matches])
        
        return files
    
    def extract_class_references(self, content: str) -> List[str]:
        """Extract class name references"""
        patterns = [
            r'class\s+(\w+)',
            r'`(\w+System)`',
            r'`(\w+Engine)`',
            r'`(\w+Manager)`',
            r'`(\w+Optimizer)`',
            r'`(\w+Detector)`',
            r'`(\w+Analyzer)`',
            r'`(\w+Strategy)`',
        ]
        
        classes = []
        for pattern in patterns:
            matches = re.findall(pattern, content)
            classes.extend(matches)
        
        return classes
    
    def extract_module_references(self, content: str) -> List[str]:
        """Extract module references"""
        patterns = [
            r'from trading_bot\.([\w.]+) import',
            r'import trading_bot\.([\w.]+)',
            r'trading_bot\.([\w.]+)',
        ]
        
        modules = []
        for pattern in patterns:
            matches = re.findall(pattern, content)
            modules.extend(matches)
        
        return modules
    
    def extract_system_references(self, content: str) -> List[str]:
        """Extract system/feature names"""
        patterns = [
            r'✅\s+\*\*([^*]+)\*\*',
            r'##\s+(.+System)',
            r'##\s+(.+Engine)',
            r'##\s+(.+Manager)',
            r'###\s+(.+System)',
            r'###\s+(.+Engine)',
        ]
        
        systems = []
        for pattern in patterns:
            matches = re.findall(pattern, content)
            systems.extend([m.strip() for m in matches])
        
        return systems
    
    def extract_feature_descriptions(self, content: str, filename: str) -> List[Dict]:
        """Extract feature descriptions with context"""
        features = []
        
        # Look for numbered features
        feature_pattern = r'(\d+)\.\s+✅\s+\*\*([^*]+)\*\*\s*-\s*`?([^`\n]+)`?'
        matches = re.findall(feature_pattern, content)
        
        for num, name, path in matches:
            features.append({
                'number': num,
                'name': name.strip(),
                'path': path.strip(),
                'source_doc': filename
            })
        
        return features
    
    def check_file_exists(self, file_path: str) -> bool:
        """Check if a file exists in the codebase"""
        # Clean up the path
        file_path = file_path.strip('`').strip()
        
        # Try different variations
        variations = [
            self.root_dir / file_path,
            self.trading_bot_dir / file_path.replace('trading_bot/', ''),
            self.root_dir / file_path.replace('trading_bot/', 'trading_bot/'),
        ]
        
        for path in variations:
            if path.exists():
                return True
        
        return False
    
    def check_class_exists(self, class_name: str) -> Tuple[bool, List[str]]:
        """Check if a class exists in the codebase"""
        found_in = []
        
        # Search for class definition
        for py_file in self.trading_bot_dir.rglob("*.py"):
            try:
                content = py_file.read_text(encoding='utf-8', errors='ignore')
                if re.search(rf'class\s+{class_name}\b', content):
                    found_in.append(str(py_file.relative_to(self.root_dir)))
            except:
                pass
        
        return len(found_in) > 0, found_in
    
    def check_module_exists(self, module_path: str) -> bool:
        """Check if a module exists"""
        module_path = module_path.replace('.', '/')
        variations = [
            self.trading_bot_dir / f"{module_path}.py",
            self.trading_bot_dir / module_path / "__init__.py",
        ]
        
        for path in variations:
            if path.exists():
                return True
        
        return False
    
    def generate_report(self) -> Dict:
        """Generate comprehensive gap analysis report"""
        print("\n" + "="*80)
        print("DOCUMENTATION vs IMPLEMENTATION GAP ANALYSIS")
        print("="*80 + "\n")
        
        features = self.scan_all_docs()
        
        report = {
            'files': {'documented': 0, 'implemented': 0, 'missing': []},
            'classes': {'documented': 0, 'implemented': 0, 'missing': []},
            'modules': {'documented': 0, 'implemented': 0, 'missing': []},
            'features': {'documented': 0, 'implemented': 0, 'missing': []},
        }
        
        # Check files
        print("Checking documented files...")
        for file_path in features['files']:
            report['files']['documented'] += 1
            if self.check_file_exists(file_path):
                report['files']['implemented'] += 1
            else:
                report['files']['missing'].append(file_path)
        
        # Check classes
        print("Checking documented classes...")
        for class_name in features['classes']:
            report['classes']['documented'] += 1
            exists, locations = self.check_class_exists(class_name)
            if exists:
                report['classes']['implemented'] += 1
            else:
                report['classes']['missing'].append(class_name)
        
        # Check modules
        print("Checking documented modules...")
        for module_path in features['modules']:
            report['modules']['documented'] += 1
            if self.check_module_exists(module_path):
                report['modules']['implemented'] += 1
            else:
                report['modules']['missing'].append(module_path)
        
        # Check features
        print("Checking documented features...")
        for feature in features['features']:
            report['features']['documented'] += 1
            if self.check_file_exists(feature['path']):
                report['features']['implemented'] += 1
            else:
                report['features']['missing'].append(feature)
        
        return report
    
    def print_report(self, report: Dict):
        """Print formatted report"""
        print("\n" + "="*80)
        print("FINAL REPORT")
        print("="*80 + "\n")
        
        for category, data in report.items():
            documented = data['documented']
            implemented = data['implemented']
            missing_count = len(data['missing'])
            
            if documented > 0:
                percentage = (implemented / documented) * 100
                print(f"\n{category.upper()}:")
                print(f"  Documented: {documented}")
                print(f"  Implemented: {implemented} ({percentage:.1f}%)")
                print(f"  Missing: {missing_count}")
                
                if missing_count > 0 and missing_count <= 20:
                    print(f"\n  Missing {category}:")
                    for item in data['missing'][:20]:
                        if isinstance(item, dict):
                            print(f"    - {item['name']} ({item['path']})")
                        else:
                            print(f"    - {item}")
        
        # Calculate overall score
        total_documented = sum(d['documented'] for d in report.values())
        total_implemented = sum(d['implemented'] for d in report.values())
        
        if total_documented > 0:
            overall_percentage = (total_implemented / total_documented) * 100
            print(f"\n{'='*80}")
            print(f"OVERALL IMPLEMENTATION: {overall_percentage:.1f}%")
            print(f"Total Documented: {total_documented}")
            print(f"Total Implemented: {total_implemented}")
            print(f"Total Missing: {total_documented - total_implemented}")
            print(f"{'='*80}\n")
        
        # Save detailed report
        output_file = self.root_dir / "DOCUMENTATION_GAP_ANALYSIS.json"
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2)
        print(f"Detailed report saved to: {output_file}")

def main():
    root_dir = Path(__file__).parent
    scanner = DocumentationGapScanner(str(root_dir))
    
    report = scanner.generate_report()
    scanner.print_report(report)
    
    print("\nScan complete!")

if __name__ == "__main__":
    main()
