"""
DGS API Documentation and REST Interface

Comprehensive API documentation and REST interface for DGS.
Provides HTTP endpoints for all DGS functionality.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import asdict
import json
import logging

logger = logging.getLogger(__name__)


class DGSAPIDocumentation:
    """
    Auto-generated API documentation for DGS.
    """
    
    @staticmethod
    def get_openapi_spec() -> Dict[str, Any]:
        """Generate OpenAPI specification for DGS"""
        
        return {
            "openapi": "3.0.0",
            "info": {
                "title": "Decision Governance System API",
                "version": "2.0.0",
                "description": "REST API for the Decision Governance System - AI-powered trading decision validation"
            },
            "servers": [
                {
                    "url": "/api/v1",
                    "description": "DGS API v1"
                }
            ],
            "paths": {
                "/health": {
                    "get": {
                        "summary": "Health check",
                        "responses": {
                            "200": {
                                "description": "System health status",
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "$ref": "#/components/schemas/HealthResponse"
                                        }
                                    }
                                }
                            }
                        }
                    }
                },
                
                "/decisions/evaluate": {
                    "post": {
                        "summary": "Evaluate a trading signal",
                        "requestBody": {
                            "required": True,
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "$ref": "#/components/schemas/SignalRequest"
                                    }
                                }
                            }
                        },
                        "responses": {
                            "200": {
                                "description": "Decision evaluation result",
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "$ref": "#/components/schemas/DecisionResponse"
                                        }
                                    }
                                }
                            },
                            "400": {
                                "description": "Invalid signal"
                            }
                        }
                    }
                },
                
                "/decisions/{decision_id}": {
                    "get": {
                        "summary": "Get decision details",
                        "parameters": [
                            {
                                "name": "decision_id",
                                "in": "path",
                                "required": True,
                                "schema": {"type": "string"}
                            }
                        ],
                        "responses": {
                            "200": {
                                "description": "Decision details",
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "$ref": "#/components/schemas/DecisionRecord"
                                        }
                                    }
                                }
                            }
                        }
                    }
                },
                
                "/decisions/{decision_id}/outcome": {
                    "post": {
                        "summary": "Record outcome for a decision",
                        "parameters": [
                            {
                                "name": "decision_id",
                                "in": "path",
                                "required": True,
                                "schema": {"type": "string"}
                            }
                        ],
                        "requestBody": {
                            "required": True,
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "$ref": "#/components/schemas/OutcomeRequest"
                                    }
                                }
                            }
                        },
                        "responses": {
                            "200": {
                                "description": "Outcome recorded"
                            }
                        }
                    }
                },
                
                "/dashboard": {
                    "get": {
                        "summary": "Get dashboard overview",
                        "responses": {
                            "200": {
                                "description": "Dashboard data",
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "$ref": "#/components/schemas/DashboardData"
                                        }
                                    }
                                }
                            }
                        }
                    }
                },
                
                "/metrics": {
                    "get": {
                        "summary": "Get system metrics",
                        "parameters": [
                            {
                                "name": "metric_name",
                                "in": "query",
                                "schema": {"type": "string"}
                            }
                        ],
                        "responses": {
                            "200": {
                                "description": "System metrics",
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "$ref": "#/components/schemas/MetricsResponse"
                                        }
                                    }
                                }
                            }
                        }
                    }
                },
                
                "/risk/portfolio": {
                    "get": {
                        "summary": "Get portfolio risk metrics",
                        "responses": {
                            "200": {
                                "description": "Portfolio risk report",
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "$ref": "#/components/schemas/RiskReport"
                                        }
                                    }
                                }
                            }
                        }
                    }
                },
                
                "/config": {
                    "get": {
                        "summary": "Get current configuration",
                        "responses": {
                            "200": {
                                "description": "DGS configuration",
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "$ref": "#/components/schemas/DGSConfig"
                                        }
                                    }
                                }
                            }
                        }
                    },
                    "put": {
                        "summary": "Update configuration",
                        "requestBody": {
                            "required": True,
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "$ref": "#/components/schemas/DGSConfig"
                                    }
                                }
                            }
                        },
                        "responses": {
                            "200": {
                                "description": "Configuration updated"
                            }
                        }
                    }
                },
                
                "/audit/export": {
                    "post": {
                        "summary": "Export audit log",
                        "requestBody": {
                            "required": True,
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "$ref": "#/components/schemas/AuditExportRequest"
                                    }
                                }
                            }
                        },
                        "responses": {
                            "200": {
                                "description": "Audit export initiated"
                            }
                        }
                    }
                }
            },
            
            "components": {
                "schemas": {
                    "HealthResponse": {
                        "type": "object",
                        "properties": {
                            "status": {"type": "string"},
                            "timestamp": {"type": "string"},
                            "components": {
                                "type": "array",
                                "items": {"$ref": "#/components/schemas/ComponentHealth"}
                            }
                        }
                    },
                    
                    "ComponentHealth": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "status": {"type": "string"},
                            "response_time_ms": {"type": "number"}
                        }
                    },
                    
                    "SignalRequest": {
                        "type": "object",
                        "required": ["symbol", "direction", "confidence"],
                        "properties": {
                            "symbol": {"type": "string"},
                            "direction": {"type": "string", "enum": ["buy", "sell", "hold"]},
                            "confidence": {"type": "number", "minimum": 0, "maximum": 1},
                            "size": {"type": "number"},
                            "rationale": {"type": "string"},
                            "evidence": {"type": "array", "items": {"type": "string"}},
                            "market_data": {"type": "object"}
                        }
                    },
                    
                    "DecisionResponse": {
                        "type": "object",
                        "properties": {
                            "decision_id": {"type": "string"},
                            "decision": {"type": "string", "enum": ["approve", "reject", "resize", "defer", "abstain"]},
                            "confidence": {"type": "number"},
                            "reasoning": {"type": "string"},
                            "approved_size": {"type": "number"},
                            "risk_adjusted_size": {"type": "number"},
                            "quality_metrics": {"type": "object"},
                            "validation_results": {"type": "object"}
                        }
                    },
                    
                    "DecisionRecord": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "string"},
                            "timestamp": {"type": "string"},
                            "symbol": {"type": "string"},
                            "final_decision": {"type": "string"},
                            "confidence": {"type": "number"},
                            "robustness_score": {"type": "number"},
                            "regime_applicability_score": {"type": "number"}
                        }
                    },
                    
                    "OutcomeRequest": {
                        "type": "object",
                        "required": ["pnl"],
                        "properties": {
                            "pnl": {"type": "number"},
                            "slippage": {"type": "number"},
                            "fill_behavior": {"type": "string"},
                            "invalidation_hit": {"type": "boolean"},
                            "market_context": {"type": "object"}
                        }
                    },
                    
                    "DashboardData": {
                        "type": "object",
                        "properties": {
                            "overview": {"type": "object"},
                            "decisions": {"type": "object"},
                            "risk": {"type": "object"},
                            "alerts": {"type": "array"}
                        }
                    },
                    
                    "MetricsResponse": {
                        "type": "object",
                        "properties": {
                            "timestamp": {"type": "string"},
                            "metrics": {"type": "object"}
                        }
                    },
                    
                    "RiskReport": {
                        "type": "object",
                        "properties": {
                            "timestamp": {"type": "string"},
                            "portfolio_value": {"type": "number"},
                            "var_1d": {"type": "number"},
                            "portfolio_beta": {"type": "number"},
                            "concentration_risk": {"type": "number"},
                            "stress_test_results": {"type": "array"}
                        }
                    },
                    
                    "DGSConfig": {
                        "type": "object",
                        "properties": {
                            "environment": {"type": "string"},
                            "risk_limits": {"type": "object"},
                            "execution_settings": {"type": "object"},
                            "feature_flags": {"type": "object"}
                        }
                    },
                    
                    "AuditExportRequest": {
                        "type": "object",
                        "required": ["start_date", "end_date"],
                        "properties": {
                            "start_date": {"type": "string"},
                            "end_date": {"type": "string"},
                            "format": {"type": "string", "enum": ["json", "csv"]}
                        }
                    }
                }
            }
        }
    
    @staticmethod
    def get_postman_collection() -> Dict[str, Any]:
        """Generate Postman collection for DGS"""
        
        return {
            "info": {
                "name": "DGS API",
                "description": "Decision Governance System API Collection",
                "schema": "https://schema.getpostman.com/json/collection/v2.1.0/"
            },
            "item": [
                {
                    "name": "Health Check",
                    "request": {
                        "method": "GET",
                        "url": "{{base_url}}/api/v1/health"
                    }
                },
                {
                    "name": "Evaluate Signal",
                    "request": {
                        "method": "POST",
                        "url": "{{base_url}}/api/v1/decisions/evaluate",
                        "body": {
                            "mode": "raw",
                            "raw": json.dumps({
                                "symbol": "AAPL",
                                "direction": "buy",
                                "confidence": 0.75,
                                "size": 1.0,
                                "rationale": "Strong technical setup",
                                "evidence": ["Price above MA50", "RSI bullish"]
                            }, indent=2)
                        }
                    }
                },
                {
                    "name": "Get Decision",
                    "request": {
                        "method": "GET",
                        "url": "{{base_url}}/api/v1/decisions/{{decision_id}}"
                    }
                },
                {
                    "name": "Record Outcome",
                    "request": {
                        "method": "POST",
                        "url": "{{base_url}}/api/v1/decisions/{{decision_id}}/outcome",
                        "body": {
                            "mode": "raw",
                            "raw": json.dumps({
                                "pnl": 0.05,
                                "slippage": 0.001,
                                "fill_behavior": "full"
                            }, indent=2)
                        }
                    }
                },
                {
                    "name": "Dashboard",
                    "request": {
                        "method": "GET",
                        "url": "{{base_url}}/api/v1/dashboard"
                    }
                },
                {
                    "name": "Metrics",
                    "request": {
                        "method": "GET",
                        "url": "{{base_url}}/api/v1/metrics"
                    }
                },
                {
                    "name": "Risk Report",
                    "request": {
                        "method": "GET",
                        "url": "{{base_url}}/api/v1/risk/portfolio"
                    }
                }
            ],
            "variable": [
                {
                    "key": "base_url",
                    "value": "http://localhost:8000"
                },
                {
                    "key": "decision_id",
                    "value": ""
                }
            ]
        }


class DGSAPIHandler:
    """
    API request handler for DGS.
    Can be integrated with FastAPI, Flask, or other frameworks.
    """
    
    def __init__(self, dgs_instance):
        self.dgs = dgs_instance
        self.docs = DGSAPIDocumentation()
    
    async def handle_health_check(self) -> Dict[str, Any]:
        """Handle health check request"""
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "version": "2.0.0"
        }
    
    async def handle_evaluate_signal(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle signal evaluation request"""
        try:
            signal = request.get('signal', {})
            symbol = request.get('symbol', '')
            market_data = request.get('market_data', {})
            
            # Call DGS evaluation
            decision, record, metadata = await self.dgs.evaluate_trade_signal(
                signal=signal,
                symbol=symbol,
                market_data=market_data
            )
            
            return {
                "decision_id": record.id,
                "decision": decision.value,
                "confidence": record.uncertainty_profile.overall_confidence if record.uncertainty_profile else 0,
                "reasoning": record.decision_reasoning,
                "approved_size": record.approved_size,
                "risk_adjusted_size": record.risk_adjusted_size,
                "quality_metrics": metadata.get('signal_validation', {}),
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error evaluating signal: {e}")
            return {
                "error": str(e),
                "decision": "abstain",
                "reasoning": "Error during evaluation"
            }
    
    async def handle_get_decision(self, decision_id: str) -> Dict[str, Any]:
        """Handle get decision request"""
        record = self.dgs.decision_memory.get_decision(decision_id)
        
        if not record:
            return {"error": "Decision not found"}
        
        return asdict(record)
    
    async def handle_record_outcome(
        self,
        decision_id: str,
        request: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle outcome recording request"""
        try:
            result = await self.dgs.record_trade_outcome(
                decision_id=decision_id,
                pnl=request.get('pnl', 0),
                slippage=request.get('slippage', 0),
                fill_behavior=request.get('fill_behavior', 'full'),
                invalidation_hit=request.get('invalidation_hit', False),
                market_context=request.get('market_context')
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error recording outcome: {e}")
            return {"error": str(e)}
    
    async def handle_dashboard(self) -> Dict[str, Any]:
        """Handle dashboard request"""
        return self.dgs.get_system_status()
    
    async def handle_get_metrics(self, metric_name: Optional[str] = None) -> Dict[str, Any]:
        """Handle metrics request"""
        # Would integrate with monitoring system
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "metrics": {}
        }
    
    async def handle_risk_report(self) -> Dict[str, Any]:
        """Handle risk report request"""
        # Would integrate with portfolio risk manager
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "portfolio_value": 0,
            "var_1d": 0,
            "risk_metrics": {}
        }
    
    def get_api_spec(self) -> Dict[str, Any]:
        """Get API specification"""
        return self.docs.get_openapi_spec()
