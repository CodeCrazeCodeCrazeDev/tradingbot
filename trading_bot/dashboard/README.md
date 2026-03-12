# Elite Trading Bot Dashboard

A modern, real-time web interface for monitoring and controlling the Elite Trading Bot.

## Features

### Real-Time Monitoring
- System health and component status
- Active trading positions
- Market data streams
- Performance metrics
- Alerts and notifications

### Trading Controls
- Pause/Resume trading
- Change trading modes (Aggressive/Balanced/Conservative)
- Close positions
- Emergency shutdown

### Advanced Analytics
- Multi-timeframe performance charts
- Position correlation analysis
- Risk metrics visualization
- Market intelligence insights
- Order flow analysis

### System Management
- Component health monitoring
- Resource usage tracking
- Error detection and recovery
- Configuration management

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Configure Redis:
Make sure Redis is installed and running on your system. Update the Redis configuration in `config.yaml` if needed.

3. Configure the dashboard:
Review and adjust settings in `config.yaml` according to your needs.

## Usage

1. Start the dashboard:
```bash
python run_dashboard.py
```

Optional arguments:
- `--host`: Bind to specific host (default: from config)
- `--port`: Use specific port (default: from config)
- `--debug`: Enable debug mode

2. Access the dashboard:
Open your web browser and navigate to `http://localhost:8000` (or your configured host/port)

## Architecture

### Components
- FastAPI backend for API endpoints
- WebSocket for real-time data streaming
- Redis for state management and caching
- Chart.js for performance visualization
- GridJS for dynamic data tables

### Integration Points
- Market Data Stream
- Trading Engine
- Risk Management System
- Analytics Engine
- Alert System

## Security Features

- Redis connection security
- WebSocket authentication
- API endpoint protection
- Session management
- Audit logging

## Advanced Features

### Quantum Integration
- Quantum portfolio optimization visualization
- Quantum risk parity metrics
- Nash equilibrium analysis

### Blockchain Features
- Trading prediction validation
- Performance verification
- Cryptographic proof visualization

### AI/ML Features
- Market regime visualization
- Sentiment analysis dashboard
- Pattern recognition insights
- Multi-agent consensus display

## Performance Optimization

- WebSocket connection pooling
- Redis caching
- Efficient data serialization
- Lazy loading of components
- Request batching

## Troubleshooting

### Common Issues
1. Redis Connection:
```bash
# Test Redis connection
redis-cli ping
```

2. Port Conflicts:
```bash
# Check if port is in use
netstat -an | grep 8000
```

3. Performance Issues:
- Check system resources
- Monitor Redis memory usage
- Review WebSocket connections

### Logging
Logs are stored in the `logs` directory with daily rotation.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

Copyright (c) 2025 Elite Trading Bot Team. All rights reserved.
