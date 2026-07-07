from __future__ import annotations

from pathlib import Path


def expand_path(value: str | Path) -> Path:
    """Expand user markers and return an absolute path."""
    return Path(value).expanduser().resolve()
