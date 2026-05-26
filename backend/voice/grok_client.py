"""
GrokDent FL — Grok Voice Client
Async client for the xAI Grok API used for the AI receptionist's
natural-language understanding and response generation.
"""

import asyncio
import logging
import time
from typing import AsyncGenerator, Dict, List, Optional

import httpx

from backend.config import settings

logger = logging.getLogger(__name__)

# Retry configuration
MAX_RETRIES = 3
RETRY_BACKOFF_BASE = 1.0  # seconds


class GrokVoiceClient:
    """
    Async wrapper around the xAI / Grok chat-completions API.

    Features:
    - Streaming and non-streaming modes
    - Automatic retry with exponential backoff
    - Request/response logging for audit
    - Convenience ``dental_response`` method for the receptionist flow
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
    ) -> None:
        self.api_key = api_key or settings.XAI_API_KEY
        self.base_url = (base_url or settings.XAI_BASE_URL).rstrip("/")
        self._client: Optional[httpx.AsyncClient] = None

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------
    async def _get_client(self) -> httpx.AsyncClient:
        """Lazily create (and reuse) an ``httpx.AsyncClient``."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                timeout=httpx.Timeout(60.0, connect=10.0),
            )
        return self._client

    async def close(self) -> None:
        """Close the underlying HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    # ------------------------------------------------------------------
    # Chat completion (non-streaming)
    # ------------------------------------------------------------------
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: str = "grok-4.20-reasoning",
        temperature: float = 0.7,
        max_tokens: int = 500,
    ) -> str:
        """
        Send a chat completion request and return the assistant's text.

        Retries up to ``MAX_RETRIES`` times with exponential backoff on
        transient failures (HTTP 429, 500, 502, 503).
        """
        if not self.api_key:
            logger.warning("XAI_API_KEY not set — returning fallback response.")
            return self._fallback_response()

        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        last_exc: Optional[Exception] = None
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                client = await self._get_client()
                start = time.perf_counter()
                response = await client.post("/chat/completions", json=payload)
                elapsed = round(time.perf_counter() - start, 3)

                if response.status_code == 200:
                    data = response.json()
                    content = data["choices"][0]["message"]["content"]
                    logger.info(
                        "Grok API — model=%s tokens=%s elapsed=%ss",
                        model,
                        data.get("usage", {}).get("total_tokens", "?"),
                        elapsed,
                    )
                    return content.strip()

                # Retryable status codes
                if response.status_code in (429, 500, 502, 503):
                    logger.warning(
                        "Grok API transient error %s (attempt %d/%d)",
                        response.status_code, attempt, MAX_RETRIES,
                    )
                    await asyncio.sleep(RETRY_BACKOFF_BASE * (2 ** (attempt - 1)))
                    continue

                # Non-retryable error
                logger.error(
                    "Grok API error %s: %s", response.status_code, response.text[:300]
                )
                return self._fallback_response()

            except httpx.TimeoutException as exc:
                logger.warning("Grok API timeout (attempt %d/%d): %s", attempt, MAX_RETRIES, exc)
                last_exc = exc
                await asyncio.sleep(RETRY_BACKOFF_BASE * (2 ** (attempt - 1)))
            except Exception as exc:
                logger.error("Grok API unexpected error: %s", exc)
                last_exc = exc
                break

        logger.error("Grok API failed after %d retries: %s", MAX_RETRIES, last_exc)
        return self._fallback_response()

    # ------------------------------------------------------------------
    # Chat completion (streaming)
    # ------------------------------------------------------------------
    async def stream_chat(
        self,
        messages: List[Dict[str, str]],
        model: str = "grok-4.20-reasoning",
        temperature: float = 0.7,
    ) -> AsyncGenerator[str, None]:
        """
        Stream a chat completion and yield text chunks as they arrive.
        Falls back to a single non-streaming call if streaming fails.
        """
        if not self.api_key:
            yield self._fallback_response()
            return

        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "stream": True,
        }

        try:
            client = await self._get_client()
            async with client.stream("POST", "/chat/completions", json=payload) as resp:
                if resp.status_code != 200:
                    logger.error("Grok stream error %s", resp.status_code)
                    yield self._fallback_response()
                    return

                async for line in resp.aiter_lines():
                    if not line or not line.startswith("data: "):
                        continue
                    data_str = line[6:]
                    if data_str.strip() == "[DONE]":
                        break
                    try:
                        import json
                        chunk = json.loads(data_str)
                        delta = chunk["choices"][0].get("delta", {})
                        content = delta.get("content", "")
                        if content:
                            yield content
                    except (KeyError, IndexError, ValueError):
                        continue

        except Exception as exc:
            logger.error("Grok stream failed: %s — falling back", exc)
            yield self._fallback_response()

    # ------------------------------------------------------------------
    # Convenience: dental receptionist response
    # ------------------------------------------------------------------
    async def dental_response(
        self,
        system_prompt: str,
        conversation_history: List[Dict[str, str]],
        patient_input: str,
    ) -> str:
        """
        Generate a response for the dental receptionist flow.

        Assembles the message list from the system prompt, conversation
        history, and latest patient input, then calls ``chat_completion``.
        """
        messages: List[Dict[str, str]] = [
            {"role": "system", "content": system_prompt},
        ]
        messages.extend(conversation_history)
        messages.append({"role": "user", "content": patient_input})

        return await self.chat_completion(
            messages=messages,
            model="grok-4.20-reasoning",
            temperature=0.7,
            max_tokens=500,
        )

    # ------------------------------------------------------------------
    # Fallback
    # ------------------------------------------------------------------
    @staticmethod
    def _fallback_response() -> str:
        """Return a safe fallback when the Grok API is unavailable."""
        return (
            "I apologize, but I'm having a temporary technical difficulty. "
            "Please hold for a moment while I connect you to our staff, "
            "or you can call back shortly. Thank you for your patience!"
        )
