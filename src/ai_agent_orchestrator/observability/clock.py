from __future__ import annotations

import time
from typing import Callable

Clock = Callable[[], int]


def system_clock_ms() -> int:
    return int(time.time() * 1000)
