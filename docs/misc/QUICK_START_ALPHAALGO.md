# AlphaAlgo Quick Start Guide

**For Non-Coders** - Simple instructions to run your autonomous trading bot.

---

## ⚡ Quick Start (3 Steps)

### Step 1: Start the Bot
Double-click: **`START_ALPHAALGO.bat`**

### Step 2: Wait for Confirmation
You'll see:
```
AlphaAlgo started successfully
AlphaAlgo is now running autonomously
```

### Step 3: Let It Run
That's it! The bot is now trading automatically.

---

## 📊 Check Status

Run this anytime to see if it's working:
```
py check_alphaalgo_status.py
```

You should see:
- **Status: RUNNING** ✅
- System health metrics
- Recent activity

---

## 🛑 Stop the Bot

In the operator window, press: **`Ctrl+C`**

Wait for "AlphaAlgo shutdown complete"

---

## 📁 Important Files

- **START_ALPHAALGO.bat** - Starts the bot
- **check_alphaalgo_status.py** - Checks if it's running
- **.env** - Your settings (don't share this!)
- **logs/** - All activity logs

---

## ⚙️ Settings You Can Change

Edit the **`.env`** file to change:

```
MAX_DAILY_LOSS=100          # Stop trading after $100 loss
MAX_POSITION_SIZE=0.01      # Trade size (0.01 = micro lot)
MAX_POSITIONS=3             # Maximum trades at once
PAPER_TRADING=true          # false = real money!
```

**Important**: Keep `PAPER_TRADING=true` until you're confident!

---

## 🚨 What If Something Goes Wrong?

### Bot Stopped
1. Run: `py check_alphaalgo_status.py`
2. If "NOT RUNNING", restart with `START_ALPHAALGO.bat`

### High CPU/Memory
- Normal during active trading
- If computer is slow, restart the bot

### No Trades Happening
- Check if markets are open
- Review settings in `.env`
- Check logs for errors

---

## 📈 Understanding the Reports

Every hour, you'll see a report with:

- **System Health**: CPU, memory, disk usage
- **Bot Status**: Running or not
- **Errors/Warnings**: Any problems detected
- **Runtime**: How long it's been running

---

## 🎯 What the Bot Does Automatically

✅ Analyzes markets 24/7  
✅ Makes trading decisions  
✅ Executes trades safely  
✅ Monitors for problems  
✅ Fixes issues itself  
✅ Learns from mistakes  
✅ Reports status hourly  

---

## 💡 Tips for Success

1. **Start Small**: Use minimum position sizes
2. **Monitor Daily**: Check status once a day
3. **Read Reports**: Review hourly summaries
4. **Be Patient**: Let it learn for 1-2 weeks
5. **Stay in Demo**: Practice before going live

---

## 📞 Need Help?

Check these files:
- **MISSION_COMPLETE_ALPHAALGO.md** - Full documentation
- **ALPHAALGO_OPERATIONAL_STATUS.md** - System status
- **logs/alphaalgo_operator_*.log** - Detailed logs

---

## ✅ Daily Checklist

**Morning:**
- [ ] Run `py check_alphaalgo_status.py`
- [ ] Verify "Status: RUNNING"
- [ ] Check system health is OK

**Evening:**
- [ ] Review hourly reports
- [ ] Check for any errors
- [ ] Note any unusual activity

**Weekly:**
- [ ] Review overall performance
- [ ] Adjust settings if needed
- [ ] Check learning logs

---

## 🎓 Learning Curve

**Week 1**: Bot learns your market  
**Week 2**: Performance improves  
**Week 3**: More consistent results  
**Week 4+**: Stable, predictable trading  

---

## 🔒 Safety Features

The bot automatically:
- Stops at daily loss limit
- Limits position sizes
- Monitors for crashes
- Restarts if needed
- Pauses if internet fails

You're protected! 🛡️

---

## 🚀 When You're Ready for Live Trading

1. Test in demo for at least 2 weeks
2. Review all trades and results
3. Understand the strategy
4. Change `.env`: `PAPER_TRADING=false`
5. Start with VERY small sizes
6. Monitor closely for first week

---

**Remember**: The bot runs itself. Your job is just to monitor and learn!

Good luck! 🎉

---

*Last Updated: 2025-10-09*
