from abc import ABC, abstractmethod
from typing import Optional
import httpx

from app.core.config import settings
from app.core.logging import logger


class BaseLLMProvider(ABC):
    """Abstract interface for LLM providers."""

    @abstractmethod
    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Generates a text completion for the given prompt and optional system instruction."""
        pass


class MockLLMProvider(BaseLLMProvider):
    """
    Deterministic mock LLM provider for fast offline testing and fallback operation
    when API keys or external LLM servers are unavailable.
    """

    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        if "NO CONTEXT AVAILABLE" in prompt or "No relevant code chunks found" in prompt:
            return "The provided repository context does not contain sufficient information to answer your question."

        return (
            "Based strictly on the retrieved repository context, the implementation is described in the provided source files. "
            "Refer to the source citations below for exact code locations and details."
        )


class OpenAILLMProvider(BaseLLMProvider):
    """OpenAI API Chat Completion provider."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ):
        self.api_key = api_key or settings.OPENAI_API_KEY
        self.model_name = model_name or settings.LLM_MODEL_NAME or "gpt-4o-mini"
        self.temperature = temperature if temperature is not None else settings.LLM_TEMPERATURE
        self.max_tokens = max_tokens if max_tokens is not None else settings.LLM_MAX_TOKENS

    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        if not self.api_key:
            logger.warning("OpenAI API key missing. Falling back to MockLLMProvider.")
            return MockLLMProvider().generate(prompt, system_prompt)

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.model_name,
            "messages": messages,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens
        }

        try:
            response = httpx.post(
                "https://api.openai.com/v1/chat/completions",
                json=payload,
                headers=headers,
                timeout=45.0
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"].strip()
        except Exception as e:
            logger.error(f"OpenAI API call failed: {e}. Falling back to Mock LLM answer.")
            return MockLLMProvider().generate(prompt, system_prompt)


class OllamaLLMProvider(BaseLLMProvider):
    """Local Ollama LLM provider."""

    def __init__(self, base_url: Optional[str] = None, model_name: Optional[str] = None):
        self.base_url = base_url or settings.OLLAMA_BASE_URL
        self.model_name = model_name or settings.LLM_MODEL_NAME or "llama3"

    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        url = f"{self.base_url.rstrip('/')}/api/generate"
        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "system": system_prompt or "",
            "stream": False,
            "options": {"temperature": settings.LLM_TEMPERATURE}
        }
        try:
            response = httpx.post(url, json=payload, timeout=60.0)
            response.raise_for_status()
            data = response.json()
            return data.get("response", "").strip()
        except Exception as e:
            logger.error(f"Ollama API call failed: {e}. Falling back to Mock LLM answer.")
            return MockLLMProvider().generate(prompt, system_prompt)


def get_llm_provider() -> BaseLLMProvider:
    """Factory creating the configured LLM provider."""
    provider_name = settings.LLM_PROVIDER.lower().strip()

    if provider_name == "openai" and settings.OPENAI_API_KEY:
        return OpenAILLMProvider()
    elif provider_name == "ollama":
        return OllamaLLMProvider()

    return MockLLMProvider()
