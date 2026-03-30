from __future__ import annotations

import re
from pathlib import Path
from typing import Iterable

_MIO_PATTERN = re.compile(r"^([+-]?\d+(?:[\.,]\d+)?)\s*(mio|m)$", re.IGNORECASE)
_K_PATTERN = re.compile(r"^([+-]?\d+(?:[\.,]\d+)?)\s*k$", re.IGNORECASE)
_COORD_PATTERN = re.compile(r"\[([^\]]+)\]\.\[([^\]]+)\]")
_DIGITS_ONLY_PATTERN = re.compile(r"^\d+$")


def decode_text_file(path: Path, encodings: Iterable[str] | None = None) -> str:
    """Decode potentially legacy Destatis text files with sensible fallbacks."""
    raw = path.read_bytes()
    for encoding in (encodings or ("utf-8-sig", "cp1252", "latin-1")):
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="replace")


def normalize_whitespace(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def normalize_ags(value: str | None) -> str | None:
    """Normalize AGS to district-level 5-digit code.

    Rules:
    - 5-digit AGS stays as-is.
    - 8-digit municipality AGS is rolled up to district AGS via first 5 digits.
    - Non-digit and other lengths become null.
    """
    if value is None:
        return None

    token = normalize_whitespace(str(value))
    if not token or not _DIGITS_ONLY_PATTERN.fullmatch(token):
        return None

    if len(token) == 5:
        return token
    if len(token) == 8:
        return token[:5]
    return None


def parse_german_number(value: str | None) -> float | None:
    """Parse values like '-', 'x', '1.234', '1,5K', '2,1 Mio'."""
    if value is None:
        return None

    token = normalize_whitespace(str(value)).replace("\u00a0", "")
    if token in {"", "-", "x", "X", ".", "..", "..."}:
        return None

    if token.endswith("%"):
        token = token[:-1]

    mio_match = _MIO_PATTERN.match(token)
    if mio_match:
        number = float(mio_match.group(1).replace(".", "").replace(",", "."))
        return number * 1_000_000

    k_match = _K_PATTERN.match(token)
    if k_match:
        number = float(k_match.group(1).replace(".", "").replace(",", "."))
        return number * 1_000

    normalized = token.replace(".", "").replace(",", ".")
    try:
        return float(normalized)
    except ValueError:
        return None


def parse_genesis_coordinate(coordinate: str) -> dict[str, str]:
    """Parse GENESIS coordinate tokens into {variable: code} pairs."""
    if not coordinate:
        return {}
    return {var: code for var, code in _COORD_PATTERN.findall(coordinate)}
