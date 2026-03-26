# Configuration Layout

The runtime configuration now uses a layered model:

1. `config/base.yaml` - shared defaults for every environment.
2. `config/environments/<env>.yaml` - environment-specific overrides (`development`, `production`).
3. Environment variables - final overrides for secrets and operational tuning.

## Environment Variables

- `BOT_ENV` (default: `development`)
- `TRADING_MODE`
- `TRADING_SYMBOLS` (comma-separated)
- `LOG_LEVEL`
- `HEALTH_PORT`
- `STATUS_INTERVAL`
- `MT5_LOGIN`
- `MT5_PASSWORD`
- `MT5_SERVER`

Use `.env.template` as the template for deployment.
