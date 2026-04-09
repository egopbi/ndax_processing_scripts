from __future__ import annotations

from pathlib import Path
import re
from urllib.parse import unquote, urlparse

_TOKEN_PATTERN = re.compile(r'"([^"]+)"|([^\s]+)')


def _normalize_token(token: str) -> str:
    normalized = token.strip().strip('"').strip("'")
    if normalized.startswith("file://"):
        parsed = urlparse(normalized)
        normalized = unquote(parsed.path)
        if re.match(r"^/[A-Za-z]:", normalized):
            normalized = normalized[1:]
    return normalized


def parse_dropped_paths(payload: str) -> tuple[Path, ...]:
    stripped = payload.strip()
    if not stripped:
        return ()

    raw_tokens: list[str] = []
    if "\n" in stripped or "\r" in stripped:
        raw_tokens.extend(
            line for line in stripped.splitlines() if line.strip()
        )
    else:
        for match in _TOKEN_PATTERN.finditer(stripped):
            raw_tokens.append(match.group(1) or match.group(2) or "")

    paths: list[Path] = []
    seen: set[str] = set()
    for token in raw_tokens:
        normalized = _normalize_token(token)
        if not normalized:
            continue

        path = Path(normalized)
        if path.suffix.casefold() != ".ndax":
            continue

        key = str(path)
        if key in seen:
            continue
        seen.add(key)
        paths.append(path)

    return tuple(paths)
