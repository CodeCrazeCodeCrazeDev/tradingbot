"""
Universal Model Connector
==========================

Generic interface for connecting to ANY frontier model provider.
Supports OpenAI, Anthropic, Google, Cohere, Mistral, local models, etc.
Model-agnostic abstraction with pluggable connectors.
"""

import asyncio
import json
import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Callable, AsyncIterator
from datetime import datetime
from enum import Enum
import hashlib

logger = logging.getLogger(__name__)


class ModelProvider(Enum):
    """Supported model providers"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    COHERE = "cohere"
    MISTRAL = "mistral"
    GROQ = "groq"
    TOGETHER = "together"
    LOCAL = "local"
    CUSTOM = "custom"


@dataclass
class ModelConfig:
    """Configuration for a model connection"""
    provider: ModelProvider
    model_id: str
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    timeout_seconds: float = 30.0
    max_retries: int = 3
    retry_delay: float = 1.0
    rate_limit_rpm: int = 60
    extra_headers: Dict[str, str] = field(default_factory=dict)
    custom_params: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ModelRequest:
    """Generic request to any model"""
    messages: List[Dict[str, str]]  # [{"role": "user", "content": "..."}]
    temperature: float = 0.7
    max_tokens: Optional[int] = None
    top_p: Optional[float] = None
    functions: Optional[List[Dict]] = None
    function_call: Optional[str] = None
    response_format: Optional[Dict[str, str]] = None
    extra_params: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ModelResponse:
    """Generic response from any model"""
    content: str
    role: str = "assistant"
    model_id: str = ""
    provider: str = ""
    usage: Dict[str, int] = field(default_factory=dict)
    latency_ms: float = 0.0
    finish_reason: str = ""
    function_call: Optional[Dict] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ModelCall:
    """Record of a model call"""
    call_id: str
    provider: str
    model_id: str
    request_hash: str
    latency_ms: float
    success: bool
    tokens_in: int = 0
    tokens_out: int = 0
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    error: Optional[str] = None


class BaseModelConnector(ABC):
    """Base class for all model connectors"""
    
    def __init__(self, config: ModelConfig):
        self.config = config
        self.call_history: List[ModelCall] = []
        self._rate_limit_lock = asyncio.Lock()
        self._last_call_time = 0.0
    
    @abstractmethod
    async def generate(self, request: ModelRequest) -> ModelResponse:
        """Generate response from model"""
        pass
    
    @abstractmethod
    async def stream(self, request: ModelRequest) -> AsyncIterator[str]:
        """Stream response from model"""
        pass
    
    async def _rate_limit(self):
        """Enforce rate limiting"""
        async with self._rate_limit_lock:
            min_interval = 60.0 / self.config.rate_limit_rpm
            elapsed = time.time() - self._last_call_time
            if elapsed < min_interval:
                await asyncio.sleep(min_interval - elapsed)
            self._last_call_time = time.time()
    
    def _record_call(self, call: ModelCall):
        """Record a model call"""
        self.call_history.append(call)
        # Keep only last 1000 calls
        if len(self.call_history) > 1000:
            self.call_history = self.call_history[-1000:]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get connector statistics"""
        if not self.call_history:
            return {'total_calls': 0}
        
        recent = [c for c in self.call_history[-100:]]
        successful = [c for c in recent if c.success]
        
        return {
            'total_calls': len(self.call_history),
            'recent_calls': len(recent),
            'success_rate': len(successful) / max(1, len(recent)),
            'avg_latency_ms': sum(c.latency_ms for c in recent) / max(1, len(recent)),
            'total_tokens_in': sum(c.tokens_in for c in self.call_history),
            'total_tokens_out': sum(c.tokens_out for c in self.call_history),
        }


class OpenAIConnector(BaseModelConnector):
    """Connector for OpenAI and OpenAI-compatible APIs"""
    
    async def generate(self, request: ModelRequest) -> ModelResponse:
        try:
            import openai
            
            client = openai.AsyncOpenAI(
                api_key=self.config.api_key,
                base_url=self.config.base_url,
                timeout=self.config.timeout_seconds,
                max_retries=self.config.max_retries
            )
            
            await self._rate_limit()
            start_time = time.time()
            
            params = {
                "model": self.config.model_id,
                "messages": request.messages,
                "temperature": request.temperature,
            }
            
            if request.max_tokens:
                params["max_tokens"] = request.max_tokens
            if request.top_p is not None:
                params["top_p"] = request.top_p
            if request.functions:
                params["tools"] = [{"type": "function", "function": f} for f in request.functions]
            if request.response_format:
                params["response_format"] = request.response_format
            
            params.update(request.extra_params)
            
            response = await client.chat.completions.create(**params)
            
            latency_ms = (time.time() - start_time) * 1000
            
            choice = response.choices[0]
            
            model_response = ModelResponse(
                content=choice.message.content or "",
                role=choice.message.role,
                model_id=self.config.model_id,
                provider=self.config.provider.value,
                usage={
                    "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                    "completion_tokens": response.usage.completion_tokens if response.usage else 0,
                    "total_tokens": response.usage.total_tokens if response.usage else 0
                },
                latency_ms=latency_ms,
                finish_reason=choice.finish_reason or "",
                function_call=choice.message.tool_calls[0].function if choice.message.tool_calls else None
            )
            
            self._record_call(ModelCall(
                call_id=f"call_{time.time()}",
                provider=self.config.provider.value,
                model_id=self.config.model_id,
                request_hash=hashlib.md5(json.dumps(request.messages).encode()).hexdigest()[:16],
                latency_ms=latency_ms,
                success=True,
                tokens_in=model_response.usage.get("prompt_tokens", 0),
                tokens_out=model_response.usage.get("completion_tokens", 0)
            ))
            
            return model_response
            
        except Exception as e:
            self._record_call(ModelCall(
                call_id=f"call_{time.time()}",
                provider=self.config.provider.value,
                model_id=self.config.model_id,
                request_hash="",
                latency_ms=0,
                success=False,
                error=str(e)
            ))
            raise
    
    async def stream(self, request: ModelRequest) -> AsyncIterator[str]:
        try:
            import openai
            
            client = openai.AsyncOpenAI(
                api_key=self.config.api_key,
                base_url=self.config.base_url
            )
            
            await self._rate_limit()
            
            stream = await client.chat.completions.create(
                model=self.config.model_id,
                messages=request.messages,
                temperature=request.temperature,
                stream=True,
                **request.extra_params
            )
            
            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
                    
        except Exception as e:
            logger.error(f"OpenAI streaming error: {e}")
            raise


class AnthropicConnector(BaseModelConnector):
    """Connector for Anthropic Claude"""
    
    async def generate(self, request: ModelRequest) -> ModelResponse:
        try:
            import anthropic
            
            client = anthropic.AsyncAnthropic(api_key=self.config.api_key)
            
            await self._rate_limit()
            start_time = time.time()
            
            # Convert messages to Anthropic format
            system_msg = None
            messages = []
            
            for msg in request.messages:
                if msg["role"] == "system":
                    system_msg = msg["content"]
                else:
                    messages.append({"role": msg["role"], "content": msg["content"]})
            
            params = {
                "model": self.config.model_id,
                "messages": messages,
                "max_tokens": request.max_tokens or 1024,
                "temperature": request.temperature,
            }
            
            if system_msg:
                params["system"] = system_msg
            if request.top_p is not None:
                params["top_p"] = request.top_p
            
            params.update(request.extra_params)
            
            response = await client.messages.create(**params)
            
            latency_ms = (time.time() - start_time) * 1000
            
            content = "".join(block.text for block in response.content if hasattr(block, 'text'))
            
            model_response = ModelResponse(
                content=content,
                role="assistant",
                model_id=self.config.model_id,
                provider=self.config.provider.value,
                usage={
                    "input_tokens": response.usage.input_tokens,
                    "output_tokens": response.usage.output_tokens
                },
                latency_ms=latency_ms,
                finish_reason=response.stop_reason or ""
            )
            
            self._record_call(ModelCall(
                call_id=f"call_{time.time()}",
                provider=self.config.provider.value,
                model_id=self.config.model_id,
                request_hash=hashlib.md5(json.dumps(request.messages).encode()).hexdigest()[:16],
                latency_ms=latency_ms,
                success=True,
                tokens_in=response.usage.input_tokens,
                tokens_out=response.usage.output_tokens
            ))
            
            return model_response
            
        except Exception as e:
            self._record_call(ModelCall(
                call_id=f"call_{time.time()}",
                provider=self.config.provider.value,
                model_id=self.config.model_id,
                request_hash="",
                latency_ms=0,
                success=False,
                error=str(e)
            ))
            raise
    
    async def stream(self, request: ModelRequest) -> AsyncIterator[str]:
        try:
            import anthropic
            
            client = anthropic.AsyncAnthropic(api_key=self.config.api_key)
            
            await self._rate_limit()
            
            messages = [{"role": m["role"], "content": m["content"]} 
                       for m in request.messages if m["role"] != "system"]
            
            async with client.messages.stream(
                model=self.config.model_id,
                messages=messages,
                max_tokens=request.max_tokens or 1024,
                temperature=request.temperature
            ) as stream:
                async for text in stream.text_stream:
                    yield text
                    
        except Exception as e:
            logger.error(f"Anthropic streaming error: {e}")
            raise


class GoogleConnector(BaseModelConnector):
    """Connector for Google Gemini"""
    
    async def generate(self, request: ModelRequest) -> ModelResponse:
        try:
            import google.generativeai as genai
            
            genai.configure(api_key=self.config.api_key)
            
            model = genai.GenerativeModel(self.config.model_id)
            
            await self._rate_limit()
            start_time = time.time()
            
            # Convert messages to Gemini format
            contents = []
            for msg in request.messages:
                if msg["role"] == "user":
                    contents.append(msg["content"])
                elif msg["role"] == "assistant":
                    contents.append(f"Assistant: {msg['content']}")
            
            prompt = "\n".join(contents)
            
            response = await model.generate_content_async(prompt)
            
            latency_ms = (time.time() - start_time) * 1000
            
            model_response = ModelResponse(
                content=response.text if hasattr(response, 'text') else str(response),
                role="assistant",
                model_id=self.config.model_id,
                provider=self.config.provider.value,
                usage={},
                latency_ms=latency_ms,
                finish_reason="stop"
            )
            
            self._record_call(ModelCall(
                call_id=f"call_{time.time()}",
                provider=self.config.provider.value,
                model_id=self.config.model_id,
                request_hash=hashlib.md5(prompt.encode()).hexdigest()[:16],
                latency_ms=latency_ms,
                success=True
            ))
            
            return model_response
            
        except Exception as e:
            self._record_call(ModelCall(
                call_id=f"call_{time.time()}",
                provider=self.config.provider.value,
                model_id=self.config.model_id,
                request_hash="",
                latency_ms=0,
                success=False,
                error=str(e)
            ))
            raise
    
    async def stream(self, request: ModelRequest) -> AsyncIterator[str]:
        # Implement streaming for Gemini
        raise NotImplementedError("Gemini streaming not yet implemented")


class CustomConnector(BaseModelConnector):
    """Connector for custom/local models via HTTP"""
    
    async def generate(self, request: ModelRequest) -> ModelResponse:
        import aiohttp
        
        await self._rate_limit()
        start_time = time.time()
        
        headers = {
            "Content-Type": "application/json",
            **self.config.extra_headers
        }
        
        if self.config.api_key:
            headers["Authorization"] = f"Bearer {self.config.api_key}"
        
        payload = {
            "model": self.config.model_id,
            "messages": request.messages,
            "temperature": request.temperature,
            **request.extra_params
        }
        
        if request.max_tokens:
            payload["max_tokens"] = request.max_tokens
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                self.config.base_url or "http://localhost:8000/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=self.config.timeout_seconds)
            ) as response:
                result = await response.json()
                
                latency_ms = (time.time() - start_time) * 1000
                
                model_response = ModelResponse(
                    content=result["choices"][0]["message"]["content"],
                    role=result["choices"][0]["message"].get("role", "assistant"),
                    model_id=self.config.model_id,
                    provider=self.config.provider.value,
                    usage=result.get("usage", {}),
                    latency_ms=latency_ms,
                    finish_reason=result["choices"][0].get("finish_reason", "")
                )
                
                self._record_call(ModelCall(
                    call_id=f"call_{time.time()}",
                    provider=self.config.provider.value,
                    model_id=self.config.model_id,
                    request_hash=hashlib.md5(json.dumps(request.messages).encode()).hexdigest()[:16],
                    latency_ms=latency_ms,
                    success=True,
                    tokens_in=result.get("usage", {}).get("prompt_tokens", 0),
                    tokens_out=result.get("usage", {}).get("completion_tokens", 0)
                ))
                
                return model_response
    
    async def stream(self, request: ModelRequest) -> AsyncIterator[str]:
        # Implement streaming for custom models
        raise NotImplementedError("Custom streaming not yet implemented")


class UniversalModelConnector:
    """
    Universal connector manager for ANY frontier model.
    
    Provides unified interface to:
    - OpenAI (GPT-4, GPT-3.5, etc.)
    - Anthropic (Claude 3, etc.)
    - Google (Gemini, etc.)
    - Cohere
    - Mistral
    - Groq
    - Together AI
    - Local models (via HTTP)
    - Custom API endpoints
    """
    
    def __init__(self):
        self.connectors: Dict[str, BaseModelConnector] = {}
        self.provider_registry: Dict[ModelProvider, type] = {
            ModelProvider.OPENAI: OpenAIConnector,
            ModelProvider.ANTHROPIC: AnthropicConnector,
            ModelProvider.GOOGLE: GoogleConnector,
            ModelProvider.CUSTOM: CustomConnector,
            ModelProvider.LOCAL: CustomConnector,
        }
        logger.info("UniversalModelConnector initialized")
    
    def register_model(self, config: ModelConfig) -> str:
        """
        Register a model connection.
        
        Returns connector_id for referencing this connection.
        """
        connector_id = f"{config.provider.value}/{config.model_id}"
        
        connector_class = self.provider_registry.get(config.provider, CustomConnector)
        self.connectors[connector_id] = connector_class(config)
        
        logger.info(f"Registered model: {connector_id}")
        return connector_id
    
    async def generate(self, 
                      connector_id: str, 
                      messages: List[Dict[str, str]],
                      temperature: float = 0.7,
                      **kwargs) -> ModelResponse:
        """
        Generate response from any registered model.
        
        Universal interface regardless of provider.
        """
        connector = self.connectors.get(connector_id)
        if not connector:
            raise ValueError(f"Unknown connector: {connector_id}")
        
        request = ModelRequest(
            messages=messages,
            temperature=temperature,
            extra_params=kwargs
        )
        
        return await connector.generate(request)
    
    async def call_any(self,
                      provider: str,
                      model_id: str,
                      messages: List[Dict[str, str]],
                      api_key: Optional[str] = None,
                      temperature: float = 0.7,
                      **kwargs) -> ModelResponse:
        """
        One-shot call to any model without pre-registration.
        
        Automatically creates and uses temporary connector.
        """
        try:
            provider_enum = ModelProvider(provider.lower())
        except ValueError:
            provider_enum = ModelProvider.CUSTOM
        
        config = ModelConfig(
            provider=provider_enum,
            model_id=model_id,
            api_key=api_key,
            **kwargs
        )
        
        temp_id = f"temp_{provider}_{model_id}_{time.time()}"
        self.register_model(config)
        
        try:
            return await self.generate(temp_id, messages, temperature)
        finally:
            # Cleanup temp connector
            del self.connectors[temp_id]
    
    def get_connector_stats(self, connector_id: Optional[str] = None) -> Dict[str, Any]:
        """Get statistics for all or specific connector"""
        if connector_id:
            connector = self.connectors.get(connector_id)
            return {connector_id: connector.get_stats()} if connector else {}
        
        return {cid: conn.get_stats() for cid, conn in self.connectors.items()}
    
    def list_registered_models(self) -> List[str]:
        """List all registered model connector IDs"""
        return list(self.connectors.keys())


def create_universal_connector() -> UniversalModelConnector:
    """Factory function to create universal model connector"""
    return UniversalModelConnector()
