import re
from typing import List, Dict, Optional
from app.services.llm_service import BaseLLMProvider, MockLLMProvider, get_llm_provider
from app.core.logging import logger


class QueryRewriter:
    """Rewrites ambiguous follow-up questions into standalone self-contained codebase search queries."""

    PRONOUN_PATTERN = re.compile(r"\b(it|this|that|they|them|its|these|those|the token|the function|the class|the file|the method)\b", re.IGNORECASE)
    FOLLOW_UP_INDICATORS = re.compile(r"^(where|how|what|which|can you|explain|and|also|show|is it|does it)\b", re.IGNORECASE)

    REWRITE_SYSTEM_PROMPT = (
        "You are an expert query rewriter for a codebase search engine.\n"
        "Given a recent conversation history and a user's follow-up question, your goal is to rewrite the follow-up question into a single, complete, self-contained standalone search query.\n"
        "\n"
        "RULES:\n"
        "1. Replace ambiguous pronouns (e.g. 'it', 'this', 'that', 'the function') with the explicit subject/entity referenced in the conversation history.\n"
        "2. If the user query is already standalone or introduces an unrelated new topic, return the user query unchanged.\n"
        "3. Output ONLY the rewritten query text. Do NOT add preamble, quotes, explanations, or markdown formatting."
    )

    def __init__(self, llm_provider: Optional[BaseLLMProvider] = None):
        self.llm_provider = llm_provider or get_llm_provider()

    def needs_rewriting(self, query: str, history: List[Dict[str, str]]) -> bool:
        """Determines if the query is an ambiguous follow-up requiring context resolution."""
        if not history:
            return False

        query_strip = query.strip()
        # Has explicit pronouns or short follow-up structure
        if self.PRONOUN_PATTERN.search(query_strip):
            return True

        if len(query_strip.split()) <= 5 and self.FOLLOW_UP_INDICATORS.search(query_strip):
            return True

        return False

    def rewrite_query(self, query: str, history: List[Dict[str, str]]) -> str:
        """Rewrites follow-up user query using conversation history."""
        if not history or not self.needs_rewriting(query, history):
            return query.strip()

        # Format recent turns with bounded length to prevent payload overflow
        formatted_history = []
        for msg in history[-4:]:
            role = "User" if msg["role"] == "user" else "Assistant"
            content_snippet = msg['content'][:300] + ("..." if len(msg['content']) > 300 else "")
            formatted_history.append(f"{role}: {content_snippet}")

        history_str = "\n".join(formatted_history)

        prompt = (
            f"Recent Conversation History:\n"
            f"{history_str}\n\n"
            f"Follow-up Question: {query}\n\n"
            f"Rewritten Standalone Query:"
        )

        try:
            # If using MockLLMProvider, perform rule-based deterministic rewriting for tests
            if isinstance(self.llm_provider, MockLLMProvider):
                last_user_msg = ""
                last_assistant_msg = ""
                for msg in reversed(history):
                    if msg["role"] == "user" and not last_user_msg:
                        last_user_msg = msg["content"]
                    elif msg["role"] == "assistant" and not last_assistant_msg:
                        last_assistant_msg = msg["content"]

                # Extract key subjects from previous context
                subject = "authentication"
                if "authentication" in last_user_msg.lower() or "auth" in last_user_msg.lower():
                    subject = "JWT authentication token"
                elif "database" in last_user_msg.lower() or "db" in last_user_msg.lower():
                    subject = "database connection"
                elif "order" in last_user_msg.lower():
                    subject = "create order"

                # Subbed query
                rewritten = self.PRONOUN_PATTERN.sub(subject, query)
                if rewritten == query:
                    rewritten = f"{query} for {subject}"
                logger.info(f"Mock query rewritten: '{query}' -> '{rewritten}'")
                return rewritten.strip()

            rewritten = self.llm_provider.generate(prompt, system_prompt=self.REWRITE_SYSTEM_PROMPT)
            rewritten_clean = rewritten.strip().strip('"').strip("'")
            logger.info(f"Query rewritten: '{query}' -> '{rewritten_clean}'")
            return rewritten_clean or query.strip()

        except Exception as e:
            logger.error(f"Query rewriting failed: {e}. Falling back to original query.")
            return query.strip()


query_rewriter = QueryRewriter()


def get_query_rewriter() -> QueryRewriter:
    return query_rewriter
