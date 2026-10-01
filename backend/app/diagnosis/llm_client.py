"""
P_311 Local LLM Client (Ollama Integration)
Communicates with locally running Ollama instance via HTTP with timeout and graceful degradation.
"""
import json
import logging
from typing import Any, Dict, Optional
import httpx

from backend.app.core.config import settings

logger = logging.getLogger("llm")


class LocalLLMClient:
    def __init__(
        self,
        base_url: str = settings.LLM_BASE_URL,
        model: str = settings.LLM_MODEL,
        timeout_seconds: float = settings.LLM_TIMEOUT_SECONDS,
        num_ctx: int = settings.LLM_NUM_CTX,
        temperature: float = settings.LLM_TEMPERATURE,
    ):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout_seconds
        self.num_ctx = num_ctx
        self.temperature = temperature

    async def is_available(self) -> bool:
        """Checks if local Ollama daemon is reachable."""
        try:
            async with httpx.AsyncClient(timeout=2.0) as client:
                res = await client.get(f"{self.base_url}/api/version")
                return res.status_code == 200
        except Exception:
            return False

    async def generate_json(self, prompt: str, system: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Sends structured prompt to Ollama requesting strict JSON output.
        Returns parsed dict or None if unavailable / error.
        """
        payload: Dict[str, Any] = {
            "model": self.model,
            "prompt": prompt,
            "format": "json",
            "stream": False,
            "options": {
                "temperature": self.temperature,
                "num_ctx": self.num_ctx,
            }
        }
        if system:
            payload["system"] = system

        try:
            logger.info("Invoking Local LLM (%s) at %s...", self.model, self.base_url)
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(f"{self.base_url}/api/generate", json=payload)
                if response.status_code != 200:
                    logger.warning("Ollama returned status %d: %s", response.status_code, response.text)
                    return None

                data = response.json()
                raw_response = data.get("response", "").strip()
                if not raw_response:
                    return None

                # Parse JSON output from LLM
                parsed = json.loads(raw_response)
                return parsed

        except httpx.ConnectError:
            logger.warning("Local Ollama daemon is not running or unreachable at %s.", self.base_url)
            return None
        except httpx.TimeoutException:
            logger.warning("Ollama LLM inference timed out (> %.1f seconds).", self.timeout)
            return None
        except json.JSONDecodeError as jde:
            logger.warning("Failed to decode JSON from LLM response: %s", jde)
            return None
        except Exception as e:
            logger.error("Unexpected error during LLM inference: %s", e)
            return None


llm_client = LocalLLMClient()
