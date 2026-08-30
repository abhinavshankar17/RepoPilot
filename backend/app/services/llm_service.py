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


import re

class MockLLMProvider(BaseLLMProvider):
    """
    Dynamic mock LLM provider synthesizing grounded, context-aware developer answers
    directly from retrieved codebase chunks for ANY ingested GitHub repository.
    """

    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        if "NO CONTEXT AVAILABLE" in prompt or "No relevant code chunks found" in prompt:
            return "The provided repository context does not contain sufficient information to answer your question."

        # Extract user query
        query_match = re.search(r"User Question:\s*(.*?)(?=\n\n|\nRetrieved|\Z)", prompt, re.DOTALL)
        user_query = query_match.group(1).strip() if query_match else "Codebase Query"

        # Parse all retrieved chunks dynamically from prompt
        chunk_blocks = re.findall(
            r"\[Chunk (\d+):\s*(.*?) L(\d+)-L(\d+)\]\s*\nLanguage:\s*(.*?)\s*\|\s*Symbol:\s*(.*?)\s*\|.*?\nCode Content:\n(.*?)(?=\n\n\[Chunk|\Z)",
            prompt,
            re.DOTALL
        )

        if not chunk_blocks:
            return (
                f"**Analysis for: {user_query}**\n\n"
                "Based strictly on the retrieved repository context, refer to the source citations below for exact code locations and details."
            )

        # Build dynamic response using retrieved chunks metadata & code content
        files_mentioned = list(dict.fromkeys([c[1].strip() for c in chunk_blocks]))
        symbols_mentioned = list(dict.fromkeys([c[5].strip() for c in chunk_blocks if c[5].strip() and c[5].strip() != "None"]))

        response_lines = [
            f"Here is what I found in the codebase regarding **{user_query}**:\n",
            f"Based strictly on the retrieved codebase chunks across **{len(files_mentioned)} file(s)**:\n"
        ]

        # Summarize each retrieved chunk dynamically
        for idx, (c_num, file_path, s_line, e_line, lang, symbol, code) in enumerate(chunk_blocks, start=1):
            lines = [l.strip() for l in code.strip().split("\n") if l.strip()]
            snippet_summary = lines[0] if lines else "Source implementation"
            if len(snippet_summary) > 90:
                snippet_summary = snippet_summary[:87] + "..."

            symbol_desc = f" (Symbol: `{symbol}`)" if symbol and symbol != "None" else ""
            lang_label = lang.capitalize() if lang and lang != "None" else "Code"

            response_lines.append(
                f"{idx}. **`{file_path}` (Lines {s_line}–{e_line})**{symbol_desc}:\n"
                f"   - **Module Type**: Written in `{lang_label}`.\n"
                f"   - **Implementation**: `{snippet_summary}`"
            )

        # Synthesize structural flow
        if len(files_mentioned) > 1:
            response_lines.append("\n**Execution Flow**:")
            flow_chain = " -> ".join([f"`{f}`" for f in files_mentioned[:5]])
            response_lines.append(f"{flow_chain}")

        if symbols_mentioned:
            response_lines.append("\n**Key Symbols Referenced**:")
            symbol_list = ", ".join([f"`{s}`" for s in symbols_mentioned[:8]])
            response_lines.append(f"{symbol_list}")

        return "\n".join(response_lines)


class GroqLLMProvider(BaseLLMProvider):
    """Groq API Provider (100% Free ultra-fast Groq Compound & Qwen models)."""

    def __init__(self, api_key: Optional[str] = None, model_name: Optional[str] = None):
        self.api_key = api_key or settings.GROQ_API_KEY
        self.model_name = model_name or settings.LLM_MODEL_NAME or "groq/compound"

    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        if not self.api_key:
            logger.warning("Groq API key missing. Falling back to MockLLMProvider.")
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
            "temperature": settings.LLM_TEMPERATURE,
            "max_tokens": settings.LLM_MAX_TOKENS
        }
        try:
            response = httpx.post("https://api.groq.com/openai/v1/chat/completions", json=payload, headers=headers, timeout=45.0)
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"].strip()
        except Exception as e:
            logger.error(f"Groq API call failed: {e}. Falling back to Mock LLM answer.")
            return MockLLMProvider().generate(prompt, system_prompt)


class GeminiLLMProvider(BaseLLMProvider):
    """Google Gemini API Provider (100% Free Tier via Google AI Studio)."""

    def __init__(self, api_key: Optional[str] = None, model_name: Optional[str] = None):
        self.api_key = api_key or settings.GEMINI_API_KEY
        self.model_name = model_name or (settings.LLM_MODEL_NAME if "gemini" in settings.LLM_MODEL_NAME else "gemini-1.5-flash")

    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        if not self.api_key:
            logger.warning("Gemini API key missing. Falling back to MockLLMProvider.")
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
            "temperature": settings.LLM_TEMPERATURE,
            "max_tokens": settings.LLM_MAX_TOKENS
        }
        try:
            response = httpx.post("https://generativelanguage.googleapis.com/v1beta/openai/chat/completions", json=payload, headers=headers, timeout=45.0)
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"].strip()
        except Exception as e:
            logger.error(f"Gemini API call failed: {e}. Falling back to Mock LLM answer.")
            return MockLLMProvider().generate(prompt, system_prompt)


class OpenRouterLLMProvider(BaseLLMProvider):
    """OpenRouter API Provider (Free models available like DeepSeek R1 & Llama 3.3)."""

    def __init__(self, api_key: Optional[str] = None, model_name: Optional[str] = None):
        self.api_key = api_key or settings.OPENROUTER_API_KEY
        self.model_name = model_name or (settings.LLM_MODEL_NAME if "/" in settings.LLM_MODEL_NAME else "deepseek/deepseek-r1:free")

    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        if not self.api_key:
            logger.warning("OpenRouter API key missing. Falling back to MockLLMProvider.")
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
            "temperature": settings.LLM_TEMPERATURE,
            "max_tokens": settings.LLM_MAX_TOKENS
        }
        try:
            response = httpx.post("https://openrouter.ai/api/v1/chat/completions", json=payload, headers=headers, timeout=45.0)
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"].strip()
        except Exception as e:
            logger.error(f"OpenRouter API call failed: {e}. Falling back to Mock LLM answer.")
            return MockLLMProvider().generate(prompt, system_prompt)


def get_llm_provider() -> BaseLLMProvider:
    """Factory creating the configured or auto-detected LLM provider."""
    provider_name = settings.LLM_PROVIDER.lower().strip()

    if provider_name == "groq" or settings.GROQ_API_KEY:
        return GroqLLMProvider()
    elif provider_name == "gemini" or settings.GEMINI_API_KEY:
        return GeminiLLMProvider()
    elif provider_name == "openrouter" or settings.OPENROUTER_API_KEY:
        return OpenRouterLLMProvider()
    elif provider_name == "openai" and settings.OPENAI_API_KEY:
        return OpenAILLMProvider()
    elif provider_name == "ollama":
        return OllamaLLMProvider()

    return MockLLMProvider()
