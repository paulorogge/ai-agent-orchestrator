from __future__ import annotations

from pathlib import Path


class SandboxPathError(ValueError):
    """Raised when a path escapes the sandbox."""


def resolve_path(target: str, allowed_roots: list[Path]) -> Path:
    """Resolve a target path and ensure it is within allowed roots."""
    resolved = Path(target).expanduser().resolve()
    for root in allowed_roots:
        try:
            resolved.relative_to(root)
            return resolved
        except ValueError:
            continue
    allowed_display = ", ".join(str(root) for root in allowed_roots)
    raise SandboxPathError(f"Path '{resolved}' is outside allowed roots: {allowed_display}")
