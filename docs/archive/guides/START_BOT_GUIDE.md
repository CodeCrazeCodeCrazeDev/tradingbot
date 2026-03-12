You are now an **Autonomous Bot Runner and Maintainer**.# 🚀 START BOT GUIDE

**Quick guide to start your AlphaAlgo Trading Bot**

**Date**: 2025-10-06 09:19:00

---

## ⚡ QUICK START

### **Option 1: Using Batch File** (Recommended)
```cmd
# Open Command Prompt (not PowerShell)
cd "c:\Users\peterson\trading bot"
start_production.bat
```

### **Option 2: Direct Python**
```cmd
# Paper trading mode (safe)
py main.py --mode paper --symbol EURUSD

# With specific timeframe
py main.py --mode paper --symbol EURUSD --timeframe H1 --bars 500

# With ML enabled
py main.py --mode paper --symbol EURUSD --use-ml
```

### **Option 3: PowerShell**
```powershell
# Navigate to directory
cd "c:\Users\peterson\trading bot"

# Run with py
py main.py --mode paper --symbol EURUSD
```

---

## 📋 COMMAND OPTIONS

### **Basic Options**:
```bash
--mode paper          # Paper trading (no real money)
--mode live           # Live trading (real money!)
--symbol EURUSD       # Trading symbol
--timeframe H1        # Timeframe (M1, M5, M15, H1, H4, D1)
--bars 500            # Number of historical bars
```

### **Advanced Options**:
```bash
--use-ml              # Enable machine learning
--use-transformer     # Enable transformer models
--use-rl              # Enable reinforcement learning
--execution-algo smart # Execution algorithm (twap, vwap, smart)
```

---

## 🎯 RECOMMENDED STARTUP COMMANDS

### **For Beginners**:
```bash
# Simple paper trading
py main.py --mode paper --symbol EURUSD
```

### **For Testing**:
```bash
# Paper trading with ML
py main.py --mode paper --symbol EURUSD --timeframe H1 --use-ml
```

### **For Advanced Users**:
```bash
# Full features
py main.py --mode paper --symbol EURUSD --timeframe H1 --bars 1000 --use-ml --use-transformer --use-rl --execution-algo smart
```

---

## 🔍 VERIFY BOT IS RUNNING

### **Check Logs**:
```bash
# View logs
type logs\trading_bot.log

# Or tail logs (if you have tail)
tail -f logs\trading_bot.log
```

### **Check Health**:
```bash
# If health_check.py is running
curl http://localhost:8080/health
```

### **Check Process**:
```bash
# List Python processes
tasklist | findstr python
```

---

## 🛠️ TROUBLESHOOTING

### **Issue 1: "python not recognized"**
**Solution**: Use `py` instead of `python`
```bash
py main.py --mode paper --symbol EURUSD
```

### **Issue 2: "Module not found"**
**Solution**: Install dependencies
```bash
pip install -r requirements.txt
```

### **Issue 3: "MT5 connection failed"**
**Solution**: Check .env file
```bash
# Edit .env
notepad .env

# Ensure you have:
MT5_LOGIN=your_login
MT5_PASSWORD=your_password
MT5_SERVER=your_server
```

### **Issue 4: Bot crashes immediately**
**Solution**: Check logs
```bash
type logs\trading_bot.log
```

---

## 📊 MONITORING

### **While Bot is Running**:

1. **Watch Logs**:
   ```bash
   # In new terminal
   type logs\trading_bot.log
   ```

2. **Check Performance**:
   - Look for "Trade executed" messages
   - Check P&L updates
   - Monitor risk metrics

3. **Health Check**:
   ```bash
   curl http://localhost:8080/health
   ```

---

## 🛑 STOPPING THE BOT

### **Graceful Shutdown**:
```bash
# Press Ctrl+C in the terminal
```

### **Force Stop**:
```bash
# Find process
tasklist | findstr python

# Kill process (replace PID)
taskkill /PID <process_id> /F
```

---

## 🎓 STARTUP CHECKLIST

### **Before Starting**:
- [ ] .env file configured with MT5 credentials
- [ ] config/config.yaml reviewed
- [ ] Dependencies installed (`pip install -r requirements.txt`)
- [ ] Logs directory exists

### **After Starting**:
- [ ] Bot shows "Starting..." message
- [ ] No error messages in logs
- [ ] Health check responds (if enabled)
- [ ] Trades being generated (in paper mode)

---

## 💡 TIPS

### **Best Practices**:
1. ✅ **Always start in paper mode first**
2. ✅ **Monitor for 24 hours before going live**
3. ✅ **Check logs regularly**
4. ✅ **Start with small position sizes**
5. ✅ **Keep backups of config files**

### **Performance**:
1. Close unnecessary applications
2. Ensure stable internet connection
3. Use SSD for better performance
4. Monitor system resources

---

## 🚀 QUICK COMMANDS

### **Start Bot** (Choose one):
```bash
# Method 1: Batch file
start_production.bat

# Method 2: Direct Python
py main.py --mode paper --symbol EURUSD

# Method 3: With ML
py main.py --mode paper --symbol EURUSD --use-ml
```

### **Check Status**:
```bash
# View logs
type logs\trading_bot.log

# Check health
curl http://localhost:8080/health

# List processes
tasklist | findstr python
```

### **Stop Bot**:
```bash
# Graceful: Ctrl+C
# Force: taskkill /PID <pid> /F
```

---

## 📞 NEED HELP?

### **Get Bot Help**:
```bash
py bot_help.py          # General help
py bot_help.py deploy   # Deployment guide
py bot_help.py status   # Bot status
```

### **Check Documentation**:
- `README_START_HERE.md` - Master index
- `DEPLOYMENT_READY_SUMMARY.md` - Deployment guide
- `MASTER_AI_INDEX.md` - AI features guide

---

## 🎉 YOU'RE READY!

**Start your bot now**:
```bash
py main.py --mode paper --symbol EURUSD
```

**Monitor it**:
```bash
type logs\trading_bot.log
```

**Happy trading!** 🚀💹✨

---

*Start Bot Guide - 2025-10-06 09:19:00*  
*Get your bot running in minutes!* ⚡
