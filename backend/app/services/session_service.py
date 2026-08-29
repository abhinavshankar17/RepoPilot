import uuid
from typing import List, Dict, Optional
from collections import defaultdict
from app.core.logging import logger


class SessionService:
    """Manages conversation sessions and bounded message history windows."""

    def __init__(self, max_turns_per_session: int = 6):
        self.max_turns = max_turns_per_session
        self._sessions: Dict[str, List[Dict[str, str]]] = defaultdict(list)

    def get_or_create_session_id(self, session_id: Optional[str] = None) -> str:
        """Returns provided session_id or generates a new UUID session_id."""
        if session_id and session_id.strip():
            return session_id.strip()
        return str(uuid.uuid4())[:8]

    def add_turn(self, session_id: str, user_query: str, assistant_answer: str) -> None:
        """Appends user query and assistant response to session history."""
        history = self._sessions[session_id]
        history.append({"role": "user", "content": user_query})
        history.append({"role": "assistant", "content": assistant_answer})

        # Trim to recent message window
        if len(history) > self.max_turns * 2:
            self._sessions[session_id] = history[-(self.max_turns * 2):]
            logger.debug(f"Trimmed session history for '{session_id}' to last {self.max_turns} turns.")

    def get_recent_history(self, session_id: str, max_turns: int = 3) -> List[Dict[str, str]]:
        """Retrieves bounded recent conversation history for query rewriting."""
        history = self._sessions.get(session_id, [])
        return history[-(max_turns * 2):]

    def clear_session(self, session_id: str) -> None:
        """Clears session history."""
        if session_id in self._sessions:
            del self._sessions[session_id]


session_service = SessionService()


def get_session_service() -> SessionService:
    return session_service
