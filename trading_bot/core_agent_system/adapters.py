"""
Reasoning and Tool Call Adapters - Research Grade

Standardizes reasoning traces and tool calls to be compatible with:
- OpenAI
- Anthropic
- Gemini
- xAI
"""

import json
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field, asdict

@dataclass
class ReasoningTrace:
    """Standardized reasoning trace format"""
    goal: str
    analysis_summary: str
    plan: List[str]
    reflection: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

class ToolCallAdapter:
    """Adapts tool calls to various provider formats"""

    @staticmethod
    def to_openai(tool_name: str, parameters: Dict[str, Any], call_id: Optional[str] = None) -> Dict[str, Any]:
        return {
            "id": call_id or f"call_{tool_name}",
            "type": "function",
            "function": {
                "name": tool_name,
                "arguments": json.dumps(parameters)
            }
        }

    @staticmethod
    def to_anthropic(tool_name: str, parameters: Dict[str, Any], call_id: Optional[str] = None) -> Dict[str, Any]:
        return {
            "type": "tool_use",
            "id": call_id or f"tool_{tool_name}",
            "name": tool_name,
            "input": parameters
        }

    @staticmethod
    def to_gemini(tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "function_call": {
                "name": tool_name,
                "args": parameters
            }
        }

    @staticmethod
    def to_xai(tool_name: str, parameters: Dict[str, Any], call_id: Optional[str] = None) -> Dict[str, Any]:
        # xAI often follows OpenAI format
        return ToolCallAdapter.to_openai(tool_name, parameters, call_id)

class ResponseFormatter:
    """Formats final response with thinking block and standardized tool calls"""

    @staticmethod
    def format_response(
        trace: ReasoningTrace,
        tool_calls: List[Dict[str, Any]],
        format_type: str = "openai"
    ) -> Dict[str, Any]:
        """Combine reasoning and tool calls into a provider-specific response"""

        response = {
            "reasoning": trace.to_dict(),
            "tool_calls": []
        }

        adapter_map = {
            "openai": ToolCallAdapter.to_openai,
            "anthropic": ToolCallAdapter.to_anthropic,
            "gemini": ToolCallAdapter.to_gemini,
            "xai": ToolCallAdapter.to_xai
        }

        adapter = adapter_map.get(format_type.lower(), ToolCallAdapter.to_openai)

        for tc in tool_calls:
            name = tc.get("name") or tc.get("tool_name")
            params = tc.get("parameters") or tc.get("params") or {}
            response["tool_calls"].append(adapter(name, params))

        return response
