# AlphaAlgo 2.0 API Reference

## Authentication

AlphaAlgo 2.0 API uses OAuth 2.0 with JWT tokens for authentication.

### Get Access Token

```
POST /token
```

**Parameters:**
- `username`: User's username
- `password`: User's password

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**Usage:**
Include the token in the Authorization header for all API requests:
```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

## Market Data

### Get Market Data

```
GET /market/data
```

**Parameters:**
- `symbol`: Trading symbol (e.g., "EURUSD")
- `timeframe`: Timeframe (e.g., "1h", "4h", "1d")
- `limit`: Number of candles to return (default: 100)

**Response:**
```json
{
  "symbol": "EURUSD",
  "timeframe": "1h",
  "data": [
    {
      "timestamp": "2023-10-13T12:00:00Z",
      "open": 1.0876,
      "high": 1.0889,
      "low": 1.0872,
      "close": 1.0885,
      "volume": 1250
    },
    ...
  ]
}
```

## Trading

### Place Trade

```
POST /trade
```

**Parameters:**
```json
{
  "symbol": "EURUSD",
  "side": "BUY",
  "quantity": 1.0,
  "price": 1.0885  // Optional for market orders
}
```

**Response:**
```json
{
  "trade_id": "trade_1697183245",
  "symbol": "EURUSD",
  "side": "BUY",
  "quantity": 1.0,
  "price": 1.0885,
  "status": "PENDING",
  "timestamp": "2023-10-13T12:00:45Z"
}
```

### Get Trade

```
GET /trade/{trade_id}
```

**Parameters:**
- `trade_id`: Trade ID

**Response:**
```json
{
  "trade_id": "trade_1697183245",
  "symbol": "EURUSD",
  "side": "BUY",
  "quantity": 1.0,
  "price": 1.0885,
  "status": "FILLED",
  "timestamp": "2023-10-13T12:00:45Z"
}
```

### Get Trades

```
GET /trades
```

**Parameters:**
- `symbol`: Filter by symbol (optional)
- `status`: Filter by status (optional)
- `limit`: Number of trades to return (default: 100)

**Response:**
```json
[
  {
    "trade_id": "trade_1697183245",
    "symbol": "EURUSD",
    "side": "BUY",
    "quantity": 1.0,
    "price": 1.0885,
    "status": "FILLED",
    "timestamp": "2023-10-13T12:00:45Z"
  },
  ...
]
```

## Analysis

### Get Symbol Analysis

```
GET /analysis/{symbol}
```

**Parameters:**
- `symbol`: Trading symbol (e.g., "EURUSD")

**Response:**
```json
{
  "symbol": "EURUSD",
  "timestamp": "2023-10-13T12:05:00Z",
  "signal": "BUY",
  "confidence": 0.85,
  "risk_metrics": {
    "expected_return": 0.02,
    "cvar_5%": -0.01,
    "var_5%": -0.005,
    "std": 0.01,
    "downside_risk": 0.015
  },
  "technical_indicators": {
    "rsi": 35,
    "macd": 0.001,
    "sma_20": 1.0850,
    "sma_50": 1.0800
  }
}
```

## Performance

### Get Performance Metrics

```
GET /performance
```

**Response:**
```json
{
  "timestamp": "2023-10-13T12:10:00Z",
  "total_trades": 100,
  "winning_trades": 65,
  "losing_trades": 35,
  "win_rate": 0.65,
  "total_pnl": 5000.0,
  "sharpe_ratio": 1.8,
  "max_drawdown": 0.15,
  "cvar_5%": -0.02,
  "daily_returns": [
    {
      "date": "2023-10-13",
      "return": 0.01
    },
    ...
  ]
}
```

## System

### Get System Status

```
GET /system/status
```

**Response:**
```json
{
  "timestamp": "2023-10-13T12:15:00Z",
  "status": "running",
  "uptime": "3d 12h 45m",
  "cpu_usage": 25.5,
  "memory_usage": 512.0,
  "active_connections": 5,
  "error_rate": 0.01,
  "components": {
    "data_feed": "healthy",
    "model": "healthy",
    "database": "healthy",
    "api": "healthy",
    "trading": "healthy"
  }
}
```

### Health Check

```
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2023-10-13T12:20:00Z",
  "version": "2.0.0"
}
```

## Error Handling

All API endpoints return standard HTTP status codes:

- `200 OK`: Request successful
- `400 Bad Request`: Invalid parameters
- `401 Unauthorized`: Authentication required
- `403 Forbidden`: Insufficient permissions
- `404 Not Found`: Resource not found
- `500 Internal Server Error`: Server error

Error responses include a JSON body with details:

```json
{
  "detail": "Error message"
}
```

## Rate Limiting

API requests are limited to 100 requests per minute per user. Rate limit headers are included in all responses:

```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1697183500
```

## Websocket API

Real-time updates are available via WebSocket:

```
ws://api.alphaalgo.com/ws
```

**Authentication:**
Send authentication message after connecting:

```json
{
  "type": "auth",
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Subscribe to channels:**

```json
{
  "type": "subscribe",
  "channels": ["trades", "market:EURUSD"]
}
```

**Message types:**

- `trade`: Trade updates
- `market`: Market data updates
- `status`: System status updates
