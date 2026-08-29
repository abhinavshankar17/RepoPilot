import re
from typing import List


class CodeTokenizer:
    """Code-aware tokenizer handling camelCase, snake_case, symbols, and punctuation."""

    IDENTIFIER_REGEX = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")

    @classmethod
    def split_identifier(cls, token: str) -> List[str]:
        """Splits camelCase and snake_case identifiers into individual terms."""
        terms = [token.lower()]
        # Split camelCase
        camel_sub = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", token)
        # Split snake_case
        snake_sub = camel_sub.replace("_", " ")
        parts = [p.lower() for p in snake_sub.split() if len(p) > 1]
        terms.extend(parts)
        return list(set(terms))

    @classmethod
    def tokenize(cls, text: str) -> List[str]:
        """Tokenizes text or code into a normalized list of search terms."""
        if not text:
            return []

        raw_tokens = cls.IDENTIFIER_REGEX.findall(text)
        all_terms = []
        for tok in raw_tokens:
            all_terms.extend(cls.split_identifier(tok))
        return all_terms
