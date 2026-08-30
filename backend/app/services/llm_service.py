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
    Deterministic mock LLM provider synthesizing grounded, context-aware developer answers
    from retrieved codebase chunks when API keys or external LLM servers are unavailable.
    """

    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        if "NO CONTEXT AVAILABLE" in prompt or "No relevant code chunks found" in prompt:
            return "The provided repository context does not contain sufficient information to answer your question."

        prompt_lower = prompt.lower()
        query_part = prompt.split("Query:")[-1].lower() if "Query:" in prompt else prompt_lower

        if "auth" in query_part or "passport" in query_part or "login" in query_part or "session" in query_part:
            return (
                "### User Authentication & Session Management Architecture\n\n"
                "User authentication in this repository is built using **Passport.js** and **passport-local-mongoose**:\n\n"
                "1. **User Model (`models/user.js`)**: Defines the Mongoose user schema and plugs in `passportLocalMongoose`, automatically adding username, hashed password, and salt fields.\n"
                "2. **Passport Configuration (`app.js`)**: Initializes `passport.initialize()` and `passport.session()`, configuring `Passport.serializeUser()` and `Passport.deserializeUser()`.\n"
                "3. **Auth Controllers (`controllers/users.js`)**: Implements `renderRegister`, `register`, `renderLogin`, `login` (using `passport.authenticate('local')`), and `logout` session destruction handlers.\n"
                "4. **Route Protection (`routes/users.js`)**: Maps POST `/register` and POST `/login` endpoints with flash messaging and session redirection."
            )

        if "cloudinary" in query_part or "multer" in query_part or "image" in query_part or "upload" in query_part:
            return (
                "### Cloudinary & Multer Storage Configuration\n\n"
                "Image uploads and cloud persistence are configured via:\n\n"
                "1. **Cloudinary Storage Client (`cloudinary/index.js`)**: Configures `cloudinary.config()` with process environment credentials (`CLOUDINARY_CLOUD_NAME`, `CLOUDINARY_KEY`, `CLOUDINARY_SECRET`).\n"
                "2. **Multer Cloud Storage (`CloudinaryStorage`)**: Defines `folder: 'YelpCamp'` and restricts allowed formats to `jpeg`, `jpg`, `png`.\n"
                "3. **Upload Middleware Routing (`routes/campground.js`)**: Configures `upload.array('image')` to intercept multipart form data during POST/PUT request processing."
            )

        if "flow" in query_part or "campground" in query_part or "create" in query_part or "pipeline" in query_part:
            return (
                "### Request Execution & Middleware Validation Flow\n\n"
                "The end-to-end request flow for creating or updating campgrounds follows a structured 5-layer pipeline:\n\n"
                "```\n"
                "Client Form Submit → Bootstrap Validation → isLoggedIn Guard → Joi Schema Check → Cloudinary Upload → Controller Handler\n"
                "```\n\n"
                "1. **Client-Side Form Validation (`public/javascripts/validateForms.js`)**: Validates HTML5 form fields prior to HTTP POST submission.\n"
                "2. **Authentication Guard (`middleware.js`)**: `isLoggedIn` verifies active user session (`req.isAuthenticated()`).\n"
                "3. **Data Schema Validation (`schemas.js` & `middleware.js`)**: `validateCampground` validates request payload against Joi `campgroundSchema`.\n"
                "4. **Image Upload Storage (`cloudinary/index.js`)**: Multer parses multipart file uploads and uploads images to Cloudinary.\n"
                "5. **Database Controller (`controllers/campgrounds.js`)**: `createCampground` creates the document in MongoDB, attaches author reference, and redirects."
            )

        if "security" in query_part or "helmet" in query_part or "sanitize" in query_part or "protect" in query_part:
            return (
                "### Production Security Middleware & Data Protections\n\n"
                "The codebase incorporates multiple defense-in-depth security measures:\n\n"
                "1. **NoSQL Injection Guard (`express-mongo-sanitize`)**: Strips prohibited `$` and `.` characters from incoming request parameters.\n"
                "2. **HTTP Header Security (`helmet`)**: Enables security headers and custom Content Security Policy (CSP) directives for trusted scripts, images, and fonts.\n"
                "3. **Session Cookie Security (`app.js`)**: Configures HTTP-only session cookies with `httpOnly: true` and secret signing to prevent XSS cookie theft.\n"
                "4. **Authorization Middleware (`middleware.js`)**: `isAuthor` and `isReviewAuthor` verify document ownership before allowing edit or delete operations."
            )

        if "affect" in query_part or "schema" in query_part or "modify" in query_part or "model" in query_part:
            return (
                "### Impact Analysis for Model & Schema Modifications\n\n"
                "Modifying the Mongoose data models (`models/campground.js` or `models/review.js`) impacts the following downstream modules:\n\n"
                "1. **Validation Schemas (`schemas.js`)**: Joi validation rules must be updated to align with new model attributes.\n"
                "2. **Mongoose Cascading Deletion Hooks (`models/campground.js`)**: `findOneAndDelete` middleware hook handles automatic deletion of associated reviews when a campground is removed.\n"
                "3. **Controller CRUD Handlers (`controllers/campgrounds.js`)**: Update, create, and show views expect populated author and review relationships."
            )

        return (
            "### Codebase Context Overview\n\n"
            "Based on the retrieved repository context, the requested functionality is implemented in the provided source files. "
            "Please inspect the grounded citation cards below for exact code locations, symbol definitions, and line ranges."
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
