"""
Export Windsurf Context for DeepSeek Handoff
Creates a comprehensive context export from current project state
"""

import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Any, Dict, List
import re

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class WindsurfContextExporter:
    """Export Windsurf context for DeepSeek continuation"""
    
    def __init__(self, project_root: Path):
        self.project_root = Path(project_root)
        self.context_dir = self.project_root / "alphaalgo_context"
        self.context_dir.mkdir(exist_ok=True)
        
    def export_all(self):
        """Export complete Windsurf context"""
        logger.info("Starting Windsurf context export...")
        
        # Export reports
        reports = self.collect_reports()
        self.save_json(reports, "reports.json")
        logger.info(f"Exported {len(reports)} reports")
        
        # Export logs
        logs = self.collect_logs()
        self.save_text(logs, "logs.txt")
        logger.info(f"Exported {len(logs)} log entries")
        
        # Export pending tasks
        tasks = self.collect_pending_tasks()
        self.save_json(tasks, "pending_tasks.json")
        logger.info(f"Exported {len(tasks)} pending tasks")
        
        # Export codebase state
        state = self.collect_codebase_state()
        self.save_json(state, "codebase_state.json")
        logger.info("Exported codebase state")
        
        # Create checkpoint
        checkpoint = {
            "timestamp": datetime.now().isoformat(),
            "reports_count": len(reports),
            "tasks_count": len(tasks),
            "status": "ready_for_deepseek"
        }
        self.save_json(checkpoint, "checkpoint.json")
        
        logger.info(f"✅ Context export complete: {self.context_dir}")
        
    def collect_reports(self) -> List[Dict[str, Any]]:
        """Collect all markdown reports"""
        reports = []
        
        # Find all markdown files with reports
        report_patterns = [
            "*_REPORT.md",
            "*_SUMMARY.md",
            "*_STATUS.md",
            "*_COMPLETE.md",
            "*_RESULTS.md"
        ]
        
        for pattern in report_patterns:
            for file_path in self.project_root.glob(pattern):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    reports.append({
                        "file": file_path.name,
                        "type": self._classify_report(file_path.name),
                        "content": content[:5000],  # First 5000 chars
                        "size": len(content),
                        "modified": datetime.fromtimestamp(
                            file_path.stat().st_mtime
                        ).isoformat()
                    })
                except Exception as e:
                    logger.warning(f"Failed to read {file_path}: {e}")
        
        return sorted(reports, key=lambda x: x['modified'], reverse=True)
    
    def _classify_report(self, filename: str) -> str:
        """Classify report type"""
        filename_lower = filename.lower()
        if 'fix' in filename_lower or 'bug' in filename_lower:
            return 'bug_fix'
        elif 'test' in filename_lower:
            return 'testing'
        elif 'deploy' in filename_lower:
            return 'deployment'
        elif 'audit' in filename_lower:
            return 'audit'
        elif 'complete' in filename_lower:
            return 'completion'
        elif 'status' in filename_lower:
            return 'status'
        else:
            return 'general'
    
    def collect_logs(self) -> List[str]:
        """Collect recent log entries"""
        logs = []
        
        # Check for log files
        log_files = [
            self.project_root / "logs" / "trading_bot.log",
            self.project_root / "bot_crash_log.txt",
            self.project_root / "supervisor_log.txt"
        ]
        
        for log_file in log_files:
            if log_file.exists():
                try:
                    with open(log_file, 'r', encoding='utf-8') as f:
                        # Get last 1000 lines
                        lines = f.readlines()
                        logs.extend(lines[-1000:])
                except Exception as e:
                    logger.warning(f"Failed to read {log_file}: {e}")
        
        return logs
    
    def collect_pending_tasks(self) -> List[Dict[str, Any]]:
        """Collect pending tasks from various sources"""
        tasks = []
        task_id = 0
        
        # 1. Scan for TODO/FIXME markers
        for py_file in self.project_root.glob("trading_bot/**/*.py"):
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    for line_num, line in enumerate(f, 1):
                        if 'TODO' in line or 'FIXME' in line:
                            tasks.append({
                                "id": f"todo_{task_id}",
                                "type": "refactor",
                                "description": line.strip(),
                                "file": str(py_file.relative_to(self.project_root)),
                                "line": line_num,
                                "priority": 7,
                                "context": {
                                    "marker_type": "TODO" if "TODO" in line else "FIXME"
                                }
                            })
                            task_id += 1
            except Exception as e:
                logger.warning(f"Failed to scan {py_file}: {e}")
        
        # 2. Parse MISSING_FEATURES_REPORT.md
        missing_features_file = self.project_root / "MISSING_FEATURES_REPORT.md"
        if missing_features_file.exists():
            try:
                with open(missing_features_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Extract features marked as NOT IMPLEMENTED
                pattern = r'### \d+\. ❌ (.+?)\n.*?Status.*?NOT IMPLEMENTED'
                matches = re.findall(pattern, content, re.DOTALL)
                
                for feature in matches:
                    tasks.append({
                        "id": f"feature_{task_id}",
                        "type": "integrate",
                        "description": f"Implement missing feature: {feature}",
                        "priority": 9,
                        "context": {
                            "feature_name": feature,
                            "source": "MISSING_FEATURES_REPORT.md"
                        }
                    })
                    task_id += 1
            except Exception as e:
                logger.warning(f"Failed to parse missing features: {e}")
        
        # 3. Parse BOT_IMPROVEMENT_ROADMAP.md
        roadmap_file = self.project_root / "BOT_IMPROVEMENT_ROADMAP.md"
        if roadmap_file.exists():
            try:
                with open(roadmap_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Extract items marked as 🔄 Next
                pattern = r'- 🔄 \*\*Next:\*\* (.+?)(?:\n|$)'
                matches = re.findall(pattern, content)
                
                for item in matches:
                    tasks.append({
                        "id": f"roadmap_{task_id}",
                        "type": "optimize",
                        "description": item,
                        "priority": 6,
                        "context": {
                            "source": "BOT_IMPROVEMENT_ROADMAP.md"
                        }
                    })
                    task_id += 1
            except Exception as e:
                logger.warning(f"Failed to parse roadmap: {e}")
        
        return tasks
    
    def collect_codebase_state(self) -> Dict[str, Any]:
        """Collect current codebase state metrics"""
        state = {
            "timestamp": datetime.now().isoformat(),
            "project_root": str(self.project_root),
            "metrics": {}
        }
        
        # Count Python files
        py_files = list(self.project_root.glob("trading_bot/**/*.py"))
        state["metrics"]["python_files"] = len(py_files)
        
        # Count test files
        test_files = list(self.project_root.glob("tests/**/*.py"))
        state["metrics"]["test_files"] = len(test_files)
        
        # Count total lines of code
        total_lines = 0
        for py_file in py_files:
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    total_lines += len(f.readlines())
            except:
                pass
        state["metrics"]["total_lines"] = total_lines
        
        # Count TODO markers
        todo_count = 0
        for py_file in py_files:
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    todo_count += content.count('TODO')
                    todo_count += content.count('FIXME')
            except:
                pass
        state["metrics"]["todo_markers"] = todo_count
        
        # List main modules
        modules = []
        trading_bot_dir = self.project_root / "trading_bot"
        if trading_bot_dir.exists():
            for item in trading_bot_dir.iterdir():
                if item.is_dir() and not item.name.startswith('_'):
                    modules.append(item.name)
        state["modules"] = sorted(modules)
        
        # Recent activity
        recent_files = []
        for py_file in sorted(py_files, key=lambda p: p.stat().st_mtime, reverse=True)[:10]:
            recent_files.append({
                "file": str(py_file.relative_to(self.project_root)),
                "modified": datetime.fromtimestamp(py_file.stat().st_mtime).isoformat()
            })
        state["recent_activity"] = recent_files
        
        return state
    
    def save_json(self, data: Any, filename: str):
        """Save data as JSON"""
        file_path = self.context_dir / filename
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def save_text(self, lines: List[str], filename: str):
        """Save lines as text file"""
        file_path = self.context_dir / filename
        with open(file_path, 'w', encoding='utf-8') as f:
            f.writelines(lines)


def main():
    """Main export function"""
    print("=" * 80)
    print("Windsurf Context Exporter for DeepSeek Handoff")
    print("=" * 80)
    print()
    
    project_root = Path(__file__).parent
    exporter = WindsurfContextExporter(project_root)
    
    print(f"Project Root: {project_root}")
    print(f"Export Directory: {exporter.context_dir}")
    print()
    
    exporter.export_all()
    
    print()
    print("=" * 80)
    print("Export Complete!")
    print("=" * 80)
    print()
    print("Next Steps:")
    print("1. Review exported context in: alphaalgo_context/")
    print("2. Start DeepSeek inference server (Ollama, LM Studio, etc.)")
    print("3. Run: python ACTIVATE_DEEPSEEK_ENGINEER.py")
    print()


if __name__ == "__main__":
    main()
