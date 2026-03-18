"""
MindWall — Ollama LLM Client
Developed by Pradyumn Tandon (https://pradyumntandon.com) at VRIP7 (https://vrip7.com)

Async HTTP client for communicating with the Ollama LLM inference server.
"""

import asyncio
import httpx
import structlog

logger = structlog.get_logger(__name__)


class OllamaClientError(Exception):
    """Raised when the Ollama LLM client encounters an error."""
    pass


class OllamaClient:
    """
    Async HTTP client for Ollama API.
    Sends structured prompts and retrieves JSON analysis responses.
    """

    def __init__(self, base_url: str, model: str, timeout: int = 30):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=httpx.Timeout(timeout=float(timeout), connect=10.0),
        )

    async def generate(self, system_prompt: str, user_prompt: str) -> str:
        """
        Send a prompt to Ollama and return the raw response text.

        Args:
            system_prompt: System-level instruction prompt.
            user_prompt: User-level analysis prompt with email content.

        Returns:
            Raw JSON string from the LLM response.

        Raises:
            OllamaClientError: If the request fails or returns invalid response.
        """
        payload = {
            "model": self.model,
            "prompt": user_prompt,
            "system": system_prompt,
            "stream": False,
            "format": "json",
            "options": {
                "temperature": 0.1,
                "top_p": 0.9,
                "num_predict": 1024,
                "repeat_penalty": 1.1,
            },
        }

        logger.debug("ollama.request", model=self.model, prompt_length=len(user_prompt))

        try:
            response = await self._client.post("/api/generate", json=payload)
            response.raise_for_status()
        except httpx.TimeoutException:
            logger.error("ollama.timeout", model=self.model, timeout=self.timeout)
            raise OllamaClientError(f"Ollama request timed out after {self.timeout}s")
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                logger.error("ollama.model_not_found", model=self.model,
                             detail="Model not loaded in Ollama. Run 'ollama pull' first.")
            else:
                logger.error("ollama.http_error", status_code=e.response.status_code, detail=str(e))
            raise OllamaClientError(f"Ollama HTTP error: {e.response.status_code}")
        except httpx.RequestError as e:
            logger.error("ollama.connection_error", error=str(e))
            raise OllamaClientError(f"Ollama connection error: {e}")

        data = response.json()
        raw_response = data.get("response", "")

        if not raw_response:
            logger.error("ollama.empty_response", model=self.model)
            raise OllamaClientError("Ollama returned an empty response")

        logger.debug(
            "ollama.response",
            model=self.model,
            response_length=len(raw_response),
            eval_count=data.get("eval_count"),
            eval_duration_ns=data.get("eval_duration"),
        )

        return raw_response

    async def check_health(self) -> bool:
        """Check if Ollama server is reachable and model is loaded."""
        try:
            response = await self._client.get("/api/tags")
            response.raise_for_status()
            tags_data = response.json()
            models = [m.get("name", "") for m in tags_data.get("models", [])]
            model_available = any(self.model in m for m in models)
            logger.info("ollama.health", available=True, model_loaded=model_available, models=models)
            return True
        except Exception as e:
            logger.error("ollama.health_failed", error=str(e))
            return False

    async def ensure_model(self) -> None:
        """Pull the configured model if it is not already available. Retries with backoff."""
        max_retries = 3
        for attempt in range(1, max_retries + 1):
            try:
                response = await self._client.get("/api/tags")
                response.raise_for_status()
                tags_data = response.json()
                models = [m.get("name", "") for m in tags_data.get("models", [])]
                if any(self.model in m for m in models):
                    logger.info("ollama.model_ready", model=self.model)
                    return

                logger.info("ollama.model_pulling", model=self.model, attempt=attempt)
                pull_client = httpx.AsyncClient(
                    base_url=self.base_url,
                    timeout=httpx.Timeout(timeout=600.0, connect=30.0),
                )
                try:
                    pull_response = await pull_client.post(
                        "/api/pull",
                        json={"name": self.model, "stream": False},
                    )
                    pull_response.raise_for_status()
                    logger.info("ollama.model_pulled", model=self.model)
                    return
                finally:
                    await pull_client.aclose()
            except Exception as e:
                logger.error(
                    "ollama.model_pull_failed",
                    model=self.model,
                    attempt=attempt,
                    max_retries=max_retries,
                    error=str(e),
                )
                if attempt < max_retries:
                    wait = 5 * attempt
                    logger.info("ollama.model_pull_retry", wait_seconds=wait)
                    await asyncio.sleep(wait)

        logger.warning(
            "ollama.model_unavailable",
            model=self.model,
            message="Model could not be pulled. LLM analysis will fall back to rule-based pre-filter.",
        )

    async def warmup(self) -> None:
        """Send a minimal generate request to load the model into VRAM."""
        logger.info("ollama.warmup_start", model=self.model)
        warmup_client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=httpx.Timeout(timeout=300.0, connect=10.0),
        )
        try:
            response = await warmup_client.post(
                "/api/generate",
                json={
                    "model": self.model,
                    "prompt": "Hello",
                    "stream": False,
                    "options": {"num_predict": 1},
                },
            )
            response.raise_for_status()
            logger.info("ollama.warmup_complete", model=self.model)
        except Exception as e:
            logger.error("ollama.warmup_failed", model=self.model, error=str(e))
        finally:
            await warmup_client.aclose()

    async def close(self):
        """Close the HTTP client."""
        await self._client.aclose()
