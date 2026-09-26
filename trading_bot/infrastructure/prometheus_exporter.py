"""Compat shim: prometheus_exporter lives in monitoring/ — re-export for the
legacy ``trading_bot.infrastructure.prometheus_exporter`` import path."""

from trading_bot.monitoring.prometheus_exporter import *  # noqa: F401,F403
from trading_bot.monitoring.prometheus_exporter import (
    TradingMetricsExporter,
    TradingMetricsExporter as PrometheusExporter,
)
