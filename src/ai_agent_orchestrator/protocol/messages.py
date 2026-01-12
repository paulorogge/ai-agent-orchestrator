from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel


class Message(BaseModel):
    role: Literal["user", "assistant", "tool", "system"]
    content: str
    name: Optional[str] = None
