# 🚀 AlphaAlgo 2.0 Quick Start Guide

## 📋 Prerequisites

- Python 3.13+
- CUDA 12.0+ (for GPU support)
- PostgreSQL 15+
- Redis 7+
- Supervisor

## 🔧 Installation

1. **Clone the repository:**
```bash
git clone https://github.com/yourusername/alphaalgo-2.0.git
cd alphaalgo-2.0
```

2. **Create virtual environment:**
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

3. **Install dependencies:**
```bash
pip install -r requirements.txt
```

4. **Set up environment variables:**
```bash
cp .env.example .env
# Edit .env with your settings
```

5. **Initialize database:**
```bash
alembic upgrade head
```

## 🏃‍♂️ Running the System

### Development Mode
```bash
# Start the trading bot
python alphaalgo_2_0.py

# Start the API (separate terminal)
uvicorn api:app --reload
```

### Production Mode
```bash
# Deploy using supervisor
python scripts/deploy.py
```

## 🔍 Monitoring

1. **View logs:**
```bash
tail -f /var/log/trading_bot.log
```

2. **Check health status:**
```bash
curl http://localhost:8000/health
```

3. **Access monitoring dashboards:**
- Grafana: http://localhost:3000
- Prometheus: http://localhost:9090

## 🎛️ Configuration

Key configuration files:
- `config/deployment.yaml`: Deployment settings
- `config/trading.yaml`: Trading parameters
- `supervisord.conf`: Service management

## 🧪 Running Tests

```bash
# Run all tests
python tests/run_tests.py

# Run specific test suite
python -m unittest tests.test_advanced_rl
```

## 📊 Key Features

1. **Advanced RL & Forecasting**
   - Distributional RL (QR-DQN)
   - Multi-objective optimization
   - Risk-aware decisions

2. **Multi-Agent Architecture**
   - Specialized trading agents
   - Consensus-based decisions
   - Adaptive weighting

3. **Neuro-Symbolic Reasoning**
   - Knowledge graphs
   - Chain-of-thought reasoning
   - Neural + symbolic fusion

4. **World Models**
   - Market simulation
   - Imagination-based planning
   - Synthetic data generation

5. **Meta-Learning**
   - Quick adaptation
   - Evolutionary optimization
   - Self-rewriting code

6. **Multimodal Intelligence**
   - Text + price fusion
   - News/social sentiment
   - Alternative data

7. **Explainability**
   - Feature attribution
   - Natural language explanations
   - Confidence scoring

8. **Production Infrastructure**
   - Auto-scaling
   - Performance monitoring
   - Health checks

## 📈 Example Usage

```python
from alphaalgo_2_0 import AlphaAlgo2_0

# Initialize the system
bot = AlphaAlgo2_0()

# Start trading
bot.start()

# Monitor performance
bot.get_performance_metrics()

# View explanations
bot.explain_recent_decisions()
```

## 🔐 Security

- SSL enabled by default
- JWT authentication
- IP whitelisting
- Regular security audits

## 🆘 Troubleshooting

1. **System won't start:**
   - Check logs: `tail -f /var/log/trading_bot.log`
   - Verify database connection
   - Ensure all services are running

2. **High latency:**
   - Check system resources
   - Verify network connectivity
   - Review auto-scaling settings

3. **Deployment fails:**
   - Check deployment logs
   - Verify dependencies
   - Ensure backup is available

## 🤝 Support

- Documentation: `/docs`
- Issues: GitHub issue tracker
- Email: support@alphaalgo.com

## 🔄 Updates

```bash
# Update to latest version
git pull
pip install -r requirements.txt
alembic upgrade head
supervisorctl restart all
```

## 📝 License

MIT License - see LICENSE file for details
