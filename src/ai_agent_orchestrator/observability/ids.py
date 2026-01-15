from __future__ import annotations

from typing import Callable
from uuid import uuid4

RunIdFactory = Callable[[], str]
SpanIdFactory = Callable[[], str]


def default_run_id() -> str:
    return f"run_{uuid4().hex}"


def default_span_id() -> str:
    return f"sp_{uuid4().hex}"
