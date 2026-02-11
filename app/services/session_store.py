"""In-memory session store for uploaded portfolio data."""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Optional

from app.models.portfolio import PortfolioData


@dataclass
class Session:
    session_id: str
    pdf_path: str
    raw_text: str = ""
    portfolio: Optional[PortfolioData] = None


class SessionStore:
    """Simple in-memory session store. Replace with Redis/DB for production."""

    def __init__(self):
        self._sessions: dict[str, Session] = {}

    def create(self, pdf_path: str, portfolio: PortfolioData, raw_text: str = "") -> str:
        session_id = uuid.uuid4().hex[:12]
        self._sessions[session_id] = Session(
            session_id=session_id,
            pdf_path=pdf_path,
            raw_text=raw_text,
            portfolio=portfolio,
        )
        return session_id

    def get(self, session_id: str) -> Optional[Session]:
        return self._sessions.get(session_id)

    def delete(self, session_id: str) -> bool:
        if session_id in self._sessions:
            del self._sessions[session_id]
            return True
        return False

    def list_sessions(self) -> list[str]:
        return list(self._sessions.keys())


# Singleton
store = SessionStore()
