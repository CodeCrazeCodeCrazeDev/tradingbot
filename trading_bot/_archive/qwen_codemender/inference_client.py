"""
Qwen 3 8B Inference Client

Handles communication with Qwen 3 8B running locally via Ollama, vLLM, or LM Studio.
Supports streaming, retry logic, and context management.
"""

import json
import logging
import asyncio
import time
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

try:
    import aiohttp
except ImportError:
    aiohttp = None

logger = logging.getLogger(__name__)


class InferenceBackend(Enum):
    """Supported local inference backends"""
    OLLAMA = "ollama"
    LM_STUDIO = "lm_studio"
    VLLM = "vllm"


@dataclass
class InferenceResponse:
    """Response from the Qwen inference server"""
    text: str
    tokens_used: int = 0
    latency_ms: float = 0.0
    model: str = ""
    finish_reason: str = ""
    raw_response: Optional[Dict[str, Any]] = None


class QwenInferenceClient:
    """Client for communicating with Qwen 3 8B local inference server"""

    def __init__(
        self,
        endpoint: str = "http://localhost:11434/api/generate",
        model_name: str = "qwen3:8b",
        backend: InferenceBackend = InferenceBackend.OLLAMA,
        temperature: float = 0.2,
        max_tokens: int = 8192,
        timeout: int = 300,
        retry_attempts: int = 3,
        retry_delay: int = 5,
        max_context_length: int = 32768,
    ):
        self.endpoint = endpoint
        self.model_name = model_name
        self.backend = backend
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.timeout = timeout
        self.retry_attempts = retry_attempts
        self.retry_delay = retry_delay
        self.max_context_length = max_context_length

        self._session: Optional[aiohttp.ClientSession] = None
        self._request_count = 0
        self._total_tokens = 0
        self._total_latency = 0.0

    async def _get_session(self) -> 'aiohttp.ClientSession':
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            self._session = aiohttp.ClientSession(timeout=timeout)
        return self._session

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        stop_sequences: Optional[List[str]] = None,
    ) -> InferenceResponse:
        """Generate a response from Qwen 3 8B"""
        temp = temperature if temperature is not None else self.temperature
        tokens = max_tokens if max_tokens is not None else self.max_tokens

        if self.backend == InferenceBackend.OLLAMA:
            return await self._generate_ollama(prompt, system_prompt, temp, tokens, stop_sequences)
        elif self.backend == InferenceBackend.VLLM:
            return await self._generate_vllm(prompt, system_prompt, temp, tokens, stop_sequences)
        elif self.backend == InferenceBackend.LM_STUDIO:
            return await self._generate_openai_compat(prompt, system_prompt, temp, tokens, stop_sequences)
        else:
            raise ValueError(f"Unsupported backend: {self.backend}")

    async def _generate_ollama(
        self, prompt: str, system_prompt: Optional[str],
        temperature: float, max_tokens: int, stop_sequences: Optional[List[str]]
    ) -> InferenceResponse:
        """Generate via Ollama API"""
        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
                "num_ctx": min(self.max_context_length, 4096),
            }
        }
        if system_prompt:
            payload["system"] = system_prompt
        if stop_sequences:
            payload["options"]["stop"] = stop_sequences

        return await self._send_request(payload)

    async def _generate_vllm(
        self, prompt: str, system_prompt: Optional[str],
        temperature: float, max_tokens: int, stop_sequences: Optional[List[str]]
    ) -> InferenceResponse:
        """Generate via vLLM OpenAI-compatible API"""
        return await self._generate_openai_compat(
            prompt, system_prompt, temperature, max_tokens, stop_sequences
        )

    async def _generate_openai_compat(
        self, prompt: str, system_prompt: Optional[str],
        temperature: float, max_tokens: int, stop_sequences: Optional[List[str]]
    ) -> InferenceResponse:
        """Generate via OpenAI-compatible API (vLLM, LM Studio)"""
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.model_name,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if stop_sequences:
            payload["stop"] = stop_sequences

        endpoint = self.endpoint.replace("/api/generate", "/v1/chat/completions")
        return await self._send_request(payload, endpoint=endpoint, openai_format=True)

    async def _send_request(
        self, payload: Dict[str, Any],
        endpoint: Optional[str] = None,
        openai_format: bool = False,
    ) -> InferenceResponse:
        """Send request with retry logic"""
        if aiohttp is None:
            raise ImportError("aiohttp is required for inference client. Install with: pip install aiohttp")

        url = endpoint or self.endpoint
        last_error = None

        for attempt in range(self.retry_attempts):
            try:
                start_time = time.monotonic()
                session = await self._get_session()

                async with session.post(url, json=payload) as resp:
                    if resp.status != 200:
                        error_text = await resp.text()
                        raise ConnectionError(f"Inference server returned {resp.status}: {error_text}")

                    data = await resp.json()
                    latency = (time.monotonic() - start_time) * 1000

                    if openai_format:
                        text = data["choices"][0]["message"]["content"]
                        tokens = data.get("usage", {}).get("total_tokens", 0)
                        finish = data["choices"][0].get("finish_reason", "")
                    else:
                        text = data.get("response", "")
                        tokens = data.get("eval_count", 0) + data.get("prompt_eval_count", 0)
                        finish = "stop" if data.get("done", False) else "length"

                    self._request_count += 1
                    self._total_tokens += tokens
                    self._total_latency += latency

                    return InferenceResponse(
                        text=text,
                        tokens_used=tokens,
                        latency_ms=latency,
                        model=self.model_name,
                        finish_reason=finish,
                        raw_response=data,
                    )

            except Exception as e:
                last_error = e
                logger.warning(f"Inference attempt {attempt + 1}/{self.retry_attempts} failed: {e}")
                if attempt < self.retry_attempts - 1:
                    await asyncio.sleep(self.retry_delay * (attempt + 1))

        raise ConnectionError(f"All {self.retry_attempts} inference attempts failed. Last error: {last_error}")

    async def health_check(self) -> bool:
        """Check if the inference server is reachable"""
        try:
            if self.backend == InferenceBackend.OLLAMA:
                url = self.endpoint.replace("/api/generate", "/api/tags")
            else:
                url = self.endpoint.replace("/v1/chat/completions", "/v1/models")

            session = await self._get_session()
            async with session.get(url) as resp:
                return resp.status == 200
        except Exception as e:
            logger.debug(f"Health check failed: {e}")
            return False

    def get_stats(self) -> Dict[str, Any]:
        """Get inference statistics"""
        avg_latency = self._total_latency / max(self._request_count, 1)
        return {
            "total_requests": self._request_count,
            "total_tokens": self._total_tokens,
            "avg_latency_ms": round(avg_latency, 2),
            "model": self.model_name,
            "backend": self.backend.value,
        }

    async def close(self):
        """Close the HTTP session"""
        if self._session and not self._session.closed:
            await self._session.close()
            self._session = None

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        await self.close()
