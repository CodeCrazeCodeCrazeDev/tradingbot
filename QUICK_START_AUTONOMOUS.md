# Quick Start - Autonomous Superintelligence

## 🚀 Launch in 3 Steps

### Step 1: Test (2 minutes)
```bash
python test_autonomous_superintelligence.py
```
Validates all systems work correctly.

### Step 2: Launch (30 seconds)
```bash
RUN_AUTONOMOUS_SUPERINTELLIGENCE.bat
```
Starts the autonomous system.

### Step 3: Monitor
Watch the logs:
```bash
tail -f autonomous_superintelligence.log
```

## 📊 What You'll See

### Initialization
```
INITIALIZING AUTONOMOUS SUPERINTELLIGENCE
Initializing Core Intelligence...
Initializing Agent Coordinator...
Initializing Research Engine...
Initializing Opportunity Detector...
Initializing Resource Manager...
Initializing Experiment Engine...
Initializing Lifecycle Manager...
AUTONOMOUS SUPERINTELLIGENCE READY
```

### Operation
```
Spawned agent: agent_market_scanner_xxx
Created task: market_analysis
Assigned task xxx to agent xxx
NEW DISCOVERY: Pattern found via genetic_programming
CAPITAL DEPLOYED: $10,000 to forex_eurusd
Experiment completed: Model Training
```

## 🎯 Key Metrics to Watch

Check these in the logs:
- **Autonomy Level**: Should increase over time (target: >90%)
- **Active Agents**: Should grow (target: 20-50)
- **Discoveries**: Should accumulate (target: 10+/week)
- **Opportunities**: Should be detected (target: 50+/week)
- **Capital Deployed**: Should grow (target: 60-80% of total)
- **Experiments**: Should complete (target: 100+/week)

## 📁 Check These Files

After 1 hour, check:
```
autonomous_superintelligence_data/research/discoveries.json
autonomous_superintelligence_data/opportunities/opportunities.json
autonomous_superintelligence_data/agents/agents.json
autonomous_superintelligence_data/resources/deployments.json
```

## 🔧 Configuration

Edit `autonomous_superintelligence_launcher.py`:
```python
config = {
    'total_capital': 100000.0,     # Your starting capital
    'max_agents': 50,              # Maximum agents
    'safety_enabled': True,        # Keep this True
}
```

## ⚠️ Safety Checklist

Before launching:
- ✅ `safety_enabled: True` in config
- ✅ Reasonable capital limit set
- ✅ Logs directory writable
- ✅ Storage paths accessible
- ✅ Dependencies installed

## 🎉 Success Indicators

After 24 hours, you should see:
- ✅ 20+ agents spawned
- ✅ 50+ opportunities detected
- ✅ 20+ experiments completed
- ✅ 5+ discoveries made
- ✅ Capital deployed to opportunities
- ✅ Autonomy level >60%

## 🆘 Troubleshooting

### System won't start
```bash
pip install -r trading_bot/autonomous_superintelligence/requirements.txt
```

### No opportunities detected
- Wait 5-10 minutes for initial scan
- Check `opportunity_detector_data/markets.json`

### No agents spawning
- Check max_agents limit
- Review lifecycle manager logs

### Experiments failing
- Check compute resources
- Verify storage paths

## 📞 Quick Commands

### Check Status
```python
from trading_bot.autonomous_superintelligence import AutonomousSuperintelligence
si = AutonomousSuperintelligence()
await si.initialize()
status = await si.get_comprehensive_status()
```

### View Discoveries
```bash
cat autonomous_superintelligence_data/research/discoveries.json
```

### View Opportunities
```bash
cat autonomous_superintelligence_data/opportunities/opportunities.json
```

### View Agents
```bash
cat autonomous_superintelligence_data/agents/agents.json
```

## 🎯 What to Expect

### Hour 1
- System initializes
- Agents spawn
- Markets scanned
- Research begins

### Day 1
- 30+ agents active
- 50+ opportunities found
- 20+ experiments done
- 5+ discoveries made

### Week 1
- 50+ agents coordinating
- 200+ opportunities analyzed
- 100+ experiments completed
- 20+ discoveries validated

### Month 1
- 90%+ autonomy
- 500+ opportunities exploited
- 1000+ experiments completed
- 50+ discoveries implemented

---

**Ready to launch? Run: `RUN_AUTONOMOUS_SUPERINTELLIGENCE.bat`**
