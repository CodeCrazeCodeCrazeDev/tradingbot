# AlphaAlgo Deployment Checklist

## Pre-Deployment

- [ ] All tests passing (`py -m pytest tests/`)
- [ ] No critical security issues
- [ ] `.env` file configured with production credentials
- [ ] Database connections tested
- [ ] API keys validated
- [ ] Backup strategy in place

## Configuration

- [ ] `PAPER_TRADING=false` for live trading (or `true` for paper trading)
- [ ] Risk limits configured (`MAX_DAILY_LOSS`, `MAX_POSITION_SIZE`)
- [ ] Email notifications configured
- [ ] Logging level set appropriately
- [ ] Health check port accessible

## Deployment

- [ ] Code deployed to production server
- [ ] Dependencies installed (`pip install -r requirements.txt`)
- [ ] Environment variables set
- [ ] Health check endpoint responding
- [ ] Auto-restart configured
- [ ] Monitoring enabled

## Post-Deployment

- [ ] Bot starts successfully
- [ ] Logs are being written
- [ ] Health check returns 200 OK
- [ ] No error messages in logs
- [ ] Performance metrics being tracked
- [ ] Alerts configured and working

## Monitoring

- [ ] Check logs regularly: `tail -f logs/trading_bot.log`
- [ ] Monitor health: `curl http://localhost:8080/health`
- [ ] Track performance metrics
- [ ] Set up alerts for errors
- [ ] Review trades daily

## Emergency Procedures

- [ ] Know how to stop the bot immediately
- [ ] Have rollback plan ready
- [ ] Emergency contacts configured
- [ ] Backup restoration tested

## Notes

- Start with paper trading mode first
- Monitor for 24-48 hours before going live
- Keep initial position sizes small
- Have stop-loss limits in place
