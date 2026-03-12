# 🚀 DeepSeek-Coder-6.7B Quick Start Guide

**Get your autonomous AI engineer running in 5 minutes!**

---

## ⚡ Super Quick Start (3 Steps)

### Step 1: Install & Start DeepSeek Server

**Option A: Ollama (Easiest - Recommended)**
```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Pull DeepSeek model
ollama pull deepseek-coder:6.7b

# Start server (keep this terminal open)
ollama serve
```

**Option B: LM Studio (GUI)**
1. Download from https://lmstudio.ai/
2. Search "deepseek-coder-6.7b" and download
3. Load model and start local server

### Step 2: Export Windsurf Context (Optional but Recommended)

```bash
cd "c:\Users\peterson\trading bot"
python export_windsurf_context.py
```

This creates `alphaalgo_context/` with all your project history.

### Step 3: Activate DeepSeek Engineer

**Windows:**
```bash
START_DEEPSEEK_ENGINEER.bat
```

**Or manually:**
```bash
python ACTIVATE_DEEPSEEK_ENGINEER.py
```

**Select Mode:**
- Press `1` for single cycle (recommended first time)
- Press `2` for continuous 24-hour cycles
- Press `3` for custom interval
- Press `4` to view status only

---

## 📊 What Happens Next?

### First Run (Single Cycle)

1. **Initialization (30 seconds)**
   - Connects to DeepSeek server
   - Loads Windsurf context
   - Scans codebase

2. **Audit Phase (2-5 minutes)**
   - Scans all Python files
   - Finds TODO markers (currently 28)
   - Identifies missing tests
   - Detects circular imports
   - Checks for performance issues

3. **Task Generation (1 minute)**
   - Creates prioritized task list
   - Critical: Circular imports, security
   - High: TODOs, missing tests
   - Medium: Docstrings, optimizations

4. **Processing Phase (10-30 minutes)**
   - Processes up to 10 tasks
   - Generates code fixes
   - Calculates safety scores
   - Applies safe changes

5. **Testing Phase (5 minutes)**
   - Runs pytest on modified files
   - Verifies no regressions
   - Reports pass/fail

6. **Report Generation (1 minute)**
   - Creates comprehensive report
   - Saves to `logs/deepseek/cycle_1_TIMESTAMP.json`
   - Shows summary in terminal

**Total Time:** 20-45 minutes for first cycle

---

## 🎯 Expected First Cycle Results

### Tasks Completed (Typical)
- ✅ Fixed 2-3 circular imports
- ✅ Implemented 5-7 TODO markers
- ✅ Generated 3-5 missing test files
- ✅ Added docstrings to 5-8 files
- ✅ Optimized 2-3 performance bottlenecks

### Metrics Improvement
- **TODO Markers:** 28 → 21 (-25%)
- **Missing Tests:** 50+ → 45 (-10%)
- **Code Quality:** 95/100 → 96/100 (+1%)
- **Test Coverage:** 90% → 92% (+2%)

---

## 🔧 Configuration Options

### Basic Config (Default)

```python
# Automatically used by ACTIVATE_DEEPSEEK_ENGINEER.py
config = DeepSeekConfig(
    backend=InferenceBackend.OLLAMA,
    endpoint="http://localhost:11434/api/generate",
    model_name="deepseek-coder-6.7b",
    temperature=0.2,
    sandbox_mode=False,      # Apply changes
    require_approval=False,  # Fully autonomous
    auto_commit_safe_changes=True
)
```

### Safe Mode (For Testing)

```python
config = DeepSeekConfig(
    sandbox_mode=True,        # Don't apply changes
    require_approval=True     # Ask before each change
)
```

### Aggressive Mode (More Tasks)

```python
# In ACTIVATE_DEEPSEEK_ENGINEER.py, modify:
await orchestrator.run_autonomous_cycle(max_tasks_per_cycle=20)
```

---

## 📁 File Structure

### Created Files

```
trading_bot/
└── ai_engineer/
    ├── __init__.py                    # Module exports
    ├── deepseek_integration.py        # DeepSeek client (650 lines)
    └── autonomous_orchestrator.py     # Orchestrator (800 lines)

alphaalgo_context/                     # Windsurf context
├── reports.json                       # All reports
├── logs.txt                           # Log history
├── pending_tasks.json                 # Unfinished tasks
├── codebase_state.json               # Current state
└── checkpoint.json                    # Last checkpoint

logs/
└── deepseek/
    ├── activation_TIMESTAMP.log       # Activation logs
    └── cycle_N_TIMESTAMP.json         # Cycle reports

ACTIVATE_DEEPSEEK_ENGINEER.py         # Main activation script
START_DEEPSEEK_ENGINEER.bat           # Quick start batch file
export_windsurf_context.py            # Context exporter
DEEPSEEK_INTEGRATION_COMPLETE.md      # Full documentation
DEEPSEEK_QUICK_START.md               # This file
```

---

## 🎮 Interactive Commands

### During Execution

- **Ctrl+C** - Graceful shutdown (completes current task)
- **View logs** - Open `logs/deepseek/` in another terminal
- **Check status** - Run `python ACTIVATE_DEEPSEEK_ENGINEER.py` → Option 4

### After Execution

```bash
# View latest cycle report
cat logs/deepseek/cycle_1_*.json | python -m json.tool

# Check what was changed
git diff

# Review generated tests
ls tests/test_*.py

# See TODO progress
grep -r "TODO" trading_bot/ | wc -l
```

---

## 🔍 Monitoring Progress

### Real-Time Monitoring

```bash
# In another terminal, watch logs
tail -f logs/deepseek/activation_*.log

# Watch cycle reports
watch -n 5 'ls -lh logs/deepseek/cycle_*.json'
```

### Check Cycle Results

```python
import json
from pathlib import Path

# Load latest cycle
cycles = sorted(Path('logs/deepseek').glob('cycle_*.json'))
latest = json.load(open(cycles[-1]))

print(f"Cycle {latest['cycle_number']}")
print(f"Status: {latest['status']}")
print(f"Tasks Completed: {latest['phases']['processing']['completed']}")
print(f"Tests Passed: {latest['phases']['testing'].get('passed', 'N/A')}")
```

---

## 🐛 Troubleshooting

### Problem: "No DeepSeek server detected"

**Solution:**
```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# If not, start it
ollama serve

# Verify model is installed
ollama list | grep deepseek
```

### Problem: "Timeout errors"

**Solution:** Increase timeout in config
```python
config = DeepSeekConfig(timeout=600)  # 10 minutes
```

### Problem: "Too many changes"

**Solution:** Reduce tasks per cycle
```bash
# Edit ACTIVATE_DEEPSEEK_ENGINEER.py
# Change: max_tasks_per_cycle=10
# To: max_tasks_per_cycle=5
```

### Problem: "Low quality outputs"

**Solution:** Adjust temperature
```python
config = DeepSeekConfig(temperature=0.1)  # More deterministic
```

---

## 📊 Understanding Output

### Terminal Output Example

```
╔══════════════════════════════════════════════════════════════════════════════╗
║              🤖 DeepSeek-Coder-6.7B Autonomous Engineer 🤖                   ║
╚══════════════════════════════════════════════════════════════════════════════╝

🔍 Checking for DeepSeek inference servers...
  ✅ Ollama detected at http://localhost:11434/api/tags

⚙️  Configuration:
  • Project Root: c:\Users\peterson\trading bot
  • Inference Endpoint: http://localhost:11434/api/generate
  • Model: deepseek-coder-6.7b
  • Mode: Autonomous (no approval required)

🚀 Initializing Autonomous Orchestrator...

📊 Loading Windsurf context and performing initial audit...

📈 System Status:
  • Windsurf Reports Loaded: 15
  • Pending Tasks from Windsurf: 8
  • Tasks in Queue: 35

🔍 Initial Audit Results:
  • Total Files Scanned: 150
  • Files with Issues: 45
  • Critical Issues: 3
  • High Priority Issues: 12
  • TODO Markers: 28
  • Missing Tests: 52
  • Circular Imports: 5

🎯 Execution Mode:
  1. Single Cycle (run one audit/fix cycle)
  2. Continuous (run cycles every 24 hours)
  3. Custom Continuous (specify interval)
  4. Status Only (show status and exit)

Select mode (1-4): 1

▶️  Running single autonomous cycle...

[Processing tasks... this may take 20-45 minutes]

✅ Cycle Complete!
  • Status: completed
  • Duration: 1847.32s
  • Tasks Processed: 10
  • Tasks Completed: 8
  • Tasks Failed: 2
  • Tests Passed: True

================================================================================
FINAL STATUS
================================================================================
Total Cycles Run: 1
Tasks Completed: 8
Tasks Failed: 2
Tasks Remaining: 25
================================================================================

✨ DeepSeek Autonomous Engineer session complete!
📁 Logs saved to: c:\Users\peterson\trading bot\logs\deepseek
```

---

## 🎓 Next Steps After First Cycle

### 1. Review Changes

```bash
# See what was modified
git status
git diff

# Review specific files
git diff trading_bot/position_manager.py
```

### 2. Run Tests

```bash
# Run all tests
pytest tests/ -v

# Run specific test
pytest tests/test_position_manager.py -v
```

### 3. Check Logs

```bash
# View cycle report
cat logs/deepseek/cycle_1_*.json | python -m json.tool

# Check for errors
grep -i error logs/deepseek/activation_*.log
```

### 4. Plan Next Cycle

Based on results:
- If successful → Enable continuous mode
- If issues → Adjust config and retry
- If too aggressive → Reduce tasks per cycle

---

## 🔄 Enabling Continuous Operation

### For Development (12-hour cycles)

```bash
python ACTIVATE_DEEPSEEK_ENGINEER.py
# Select: 3
# Enter: 12 (hours)
# Enter: 10 (max cycles)
```

### For Production (Weekly cycles)

```bash
python ACTIVATE_DEEPSEEK_ENGINEER.py
# Select: 3
# Enter: 168 (hours = 1 week)
# Enter: (leave empty for unlimited)
```

### Running as Background Service

**Windows (Task Scheduler):**
1. Open Task Scheduler
2. Create Basic Task
3. Trigger: Daily at 2 AM
4. Action: Start Program
5. Program: `python`
6. Arguments: `ACTIVATE_DEEPSEEK_ENGINEER.py --mode continuous`
7. Start in: `c:\Users\peterson\trading bot`

**Linux (Cron):**
```bash
# Edit crontab
crontab -e

# Add line (runs daily at 2 AM)
0 2 * * * cd /path/to/trading-bot && python ACTIVATE_DEEPSEEK_ENGINEER.py --mode continuous
```

---

## 📞 Getting Help

### Check Documentation

- **Full Docs:** `DEEPSEEK_INTEGRATION_COMPLETE.md`
- **This Guide:** `DEEPSEEK_QUICK_START.md`
- **Code Docs:** See docstrings in `trading_bot/ai_engineer/`

### Debug Mode

```python
# Enable debug logging
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Common Issues

1. **Server not found** → Start Ollama/LM Studio
2. **Timeout** → Increase timeout in config
3. **Bad outputs** → Lower temperature
4. **Too many changes** → Reduce tasks per cycle
5. **Tests failing** → Review changes, may need manual fixes

---

## 🎉 Success Indicators

### After 1 Cycle
- ✅ 5-10 tasks completed
- ✅ No critical errors
- ✅ Tests still passing
- ✅ Code quality improved

### After 5 Cycles
- ✅ 30+ tasks completed
- ✅ TODO markers reduced by 50%
- ✅ Test coverage increased
- ✅ No circular imports

### After 10 Cycles
- ✅ 80+ tasks completed
- ✅ All critical issues resolved
- ✅ 95%+ test coverage
- ✅ Production ready

---

## 🚀 Ready to Start?

```bash
# 1. Start DeepSeek server
ollama serve

# 2. Export context (optional)
python export_windsurf_context.py

# 3. Activate engineer
START_DEEPSEEK_ENGINEER.bat

# 4. Select mode 1 for first run

# 5. Wait 20-45 minutes

# 6. Review results in logs/deepseek/
```

**That's it! Your autonomous AI engineer is now working on improving AlphaAlgo! 🎉**

---

**Last Updated:** 2025-10-26  
**Version:** 1.0.0  
**Status:** 🟢 OPERATIONAL
