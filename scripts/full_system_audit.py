#!/usr/bin/env python3
"""
Full System Audit Script for AlphaAlgo Trading Bot
Generates comprehensive health check report
"""

import sys
import os
import ast
import re
import json
import time
from pathlib import Path
from datetime import datetime
from collections import defaultdict

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
trading_bot_dir = PROJECT_ROOT / "trading_bot"

def count_todos():
    """Count TODO markers in codebase"""
    todos = []
    for py_file in trading_bot_dir.rglob("*.py"):
        if "__pycache__" in str(py_file) or "auto_fix_backups" in str(py_file):
            continue
        try:
            with open(py_file, "r", encoding="utf-8", errors="ignore") as f:
                for i, line in enumerate(f, 1):
                    if re.search(r"#\s*(TODO|FIXME|XXX|HACK)", line, re.I):
                        todos.append({
                            "file": str(py_file.relative_to(PROJECT_ROOT)),
                            "line": i,
                            "content": line.strip()[:100]
                        })
        except:
            pass
    return todos

def find_hardcoded_values():
    """Find hardcoded values that should be configurable"""
    hardcoded = []
    patterns = [
        (r"localhost:\d+", "Hardcoded localhost port"),
        (r"127\.0\.0\.1:\d+", "Hardcoded IP:port"),
        (r"max_position\s*=\s*\d+(?!\s*\*)", "Hardcoded max position"),
        (r"stop_loss\s*=\s*0\.\d+", "Hardcoded stop loss"),
        (r"take_profit\s*=\s*0\.\d+", "Hardcoded take profit"),
        (r"leverage\s*=\s*\d+", "Hardcoded leverage"),
        (r"timeout\s*=\s*\d+", "Hardcoded timeout"),
    ]
    
    for py_file in trading_bot_dir.rglob("*.py"):
        if "__pycache__" in str(py_file) or "auto_fix_backups" in str(py_file):
            continue
        try:
            with open(py_file, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
            for pattern, desc in patterns:
                matches = re.finditer(pattern, content, re.I)
                for match in matches:
                    hardcoded.append({
                        "file": str(py_file.relative_to(PROJECT_ROOT)),
                        "type": desc,
                        "match": match.group()[:50]
                    })
        except:
            pass
    return hardcoded

def check_unified_architecture():
    """Check unified architecture layers"""
    unified_dir = trading_bot_dir / "unified_architecture"
    layers = {}
    
    if unified_dir.exists():
        for i in range(1, 7):
            layer_files = list(unified_dir.glob(f"layer{i}_*.py"))
            if layer_files:
                layer_file = layer_files[0]
                with open(layer_file, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                # Check for key components
                has_class = "class " in content
                has_init = "def __init__" in content
                line_count = len(content.split("\n"))
                layers[f"layer_{i}"] = {
                    "file": layer_file.name,
                    "has_class": has_class,
                    "has_init": has_init,
                    "lines": line_count,
                    "status": "COMPLETE" if has_class and has_init else "INCOMPLETE"
                }
            else:
                layers[f"layer_{i}"] = {"status": "MISSING"}
    else:
        layers["unified_architecture"] = {"status": "NOT_FOUND"}
    
    return layers

def check_risk_management():
    """Audit risk management system"""
    risk_dir = trading_bot_dir / "risk"
    risk_status = {
        "max_risk_per_trade": False,
        "max_daily_loss": False,
        "max_drawdown": False,
        "position_sizing": False,
        "correlation_check": False,
        "portfolio_risk": False,
        "circuit_breaker": False,
        "kill_switch": False,
    }
    
    if risk_dir.exists():
        for py_file in risk_dir.rglob("*.py"):
            try:
                with open(py_file, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read().lower()
                
                if "max_risk" in content or "risk_per_trade" in content:
                    risk_status["max_risk_per_trade"] = True
                if "daily_loss" in content or "max_daily" in content:
                    risk_status["max_daily_loss"] = True
                if "drawdown" in content:
                    risk_status["max_drawdown"] = True
                if "position_size" in content or "position_sizing" in content:
                    risk_status["position_sizing"] = True
                if "correlation" in content:
                    risk_status["correlation_check"] = True
                if "portfolio" in content and "risk" in content:
                    risk_status["portfolio_risk"] = True
                if "circuit" in content and "breaker" in content:
                    risk_status["circuit_breaker"] = True
                if "kill" in content and "switch" in content:
                    risk_status["kill_switch"] = True
            except:
                pass
    
    return risk_status

def find_inactive_features():
    """Find implemented but inactive features"""
    inactive = []
    
    # Check config files
    config_dir = PROJECT_ROOT / "config"
    if config_dir.exists():
        for config_file in config_dir.glob("*.yaml"):
            try:
                with open(config_file, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                matches = re.finditer(r"(\w+):\s*\n\s*enabled:\s*false", content, re.I)
                for match in matches:
                    inactive.append({
                        "feature": match.group(1),
                        "config_file": config_file.name,
                        "how_to_enable": f"Set 'enabled: true' in config/{config_file.name}"
                    })
            except:
                pass
    
    return inactive

def check_broker_status():
    """Check broker adapter status"""
    brokers = {}
    broker_dir = trading_bot_dir / "brokers"
    
    if broker_dir.exists():
        for py_file in broker_dir.glob("*.py"):
            if py_file.name.startswith("__"):
                continue
            try:
                with open(py_file, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                
                is_mock = "Mock" in content or "Fake" in content or "Simulated" in content
                has_connect = "def connect" in content or "async def connect" in content
                has_execute = "def execute" in content or "def place_order" in content or "def submit_order" in content
                has_positions = "def get_positions" in content or "def positions" in content
                
                status = "MOCK" if is_mock else ("COMPLETE" if all([has_connect, has_execute, has_positions]) else "INCOMPLETE")
                brokers[py_file.stem] = {
                    "status": status,
                    "has_connect": has_connect,
                    "has_execute": has_execute,
                    "has_positions": has_positions,
                    "is_mock": is_mock
                }
            except:
                pass
    
    return brokers

def generate_report():
    """Generate comprehensive audit report"""
    print("=" * 80)
    print("COMPREHENSIVE SYSTEM AUDIT REPORT")
    print(f"Generated: {datetime.now().isoformat()}")
    print("=" * 80)
    
    report = {
        "timestamp": datetime.now().isoformat(),
        "sections": {}
    }
    
    # 1. TODO Markers
    print("\n[1] TODO MARKERS IN CODEBASE:")
    todos = count_todos()
    print(f"   Total TODO markers: {len(todos)}")
    report["sections"]["todos"] = {"count": len(todos), "items": todos[:20]}
    for t in todos[:10]:
        print(f"   - {t['file']}:{t['line']}")
    
    # 2. Hardcoded Values
    print("\n[2] HARDCODED VALUES:")
    hardcoded = find_hardcoded_values()
    print(f"   Total hardcoded values: {len(hardcoded)}")
    report["sections"]["hardcoded"] = {"count": len(hardcoded), "items": hardcoded[:20]}
    by_type = defaultdict(int)
    for h in hardcoded:
        by_type[h["type"]] += 1
    for t, c in by_type.items():
        print(f"   - {t}: {c}")
    
    # 3. Unified Architecture
    print("\n[3] UNIFIED ARCHITECTURE LAYERS:")
    layers = check_unified_architecture()
    report["sections"]["unified_architecture"] = layers
    for layer, status in layers.items():
        if isinstance(status, dict):
            s = status.get("status", "UNKNOWN")
            lines = status.get("lines", 0)
            print(f"   {layer}: {s} ({lines} lines)")
        else:
            print(f"   {layer}: {status}")
    
    # 4. Risk Management
    print("\n[4] RISK MANAGEMENT AUDIT:")
    risk_status = check_risk_management()
    report["sections"]["risk_management"] = risk_status
    for check, found in risk_status.items():
        status = "FOUND" if found else "MISSING"
        print(f"   {check}: {status}")
    
    # 5. Inactive Features
    print("\n[5] INACTIVE FEATURES:")
    inactive = find_inactive_features()
    report["sections"]["inactive_features"] = inactive
    print(f"   Total inactive features: {len(inactive)}")
    for feat in inactive[:10]:
        print(f"   - {feat['feature']} ({feat['config_file']})")
    
    # 6. Broker Status
    print("\n[6] BROKER ADAPTER STATUS:")
    brokers = check_broker_status()
    report["sections"]["brokers"] = brokers
    for broker, status in brokers.items():
        print(f"   {broker}: {status['status']}")
    
    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    
    issues = []
    if len(todos) > 20:
        issues.append(f"High TODO count: {len(todos)}")
    if len(hardcoded) > 50:
        issues.append(f"Many hardcoded values: {len(hardcoded)}")
    
    missing_risk = [k for k, v in risk_status.items() if not v]
    if missing_risk:
        issues.append(f"Missing risk checks: {missing_risk}")
    
    mock_brokers = [k for k, v in brokers.items() if v.get("is_mock")]
    if mock_brokers:
        issues.append(f"Mock brokers in use: {mock_brokers}")
    
    if issues:
        print("\nISSUES FOUND:")
        for issue in issues:
            print(f"   - {issue}")
    else:
        print("\nNo critical issues found!")
    
    # Save report
    report_path = PROJECT_ROOT / "diagnostics" / f"system_audit_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    report_path.parent.mkdir(exist_ok=True)
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2, default=str)
    print(f"\nFull report saved to: {report_path}")
    
    return report

if __name__ == "__main__":
    generate_report()
