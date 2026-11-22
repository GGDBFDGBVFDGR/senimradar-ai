"""Passive URL checks. The address is never resolved or opened."""

from __future__ import annotations

import ipaddress
import re
from urllib.parse import urlsplit

_CYRILLIC_RE = re.compile(r"[А-Яа-яЁёӘәҒғҚқҢңӨөҰұҮүҺһІі]")
_HOST_SAFE_RE = re.compile(r"^[a-z0-9.\-:\[\]]+$", re.IGNORECASE)
_LOCAL_SUFFIXES = (".localhost", ".local", ".internal", ".intranet", ".home", ".lan")


def admission(value: str) -> str | None:
    """Return a limitation code, or None when the string may be scored. Never fetches."""
    text = value.strip()
    if not text or _CYRILLIC_RE.search(text) or any(char.isspace() for char in text):
        return "ocr_damaged"
    if "://" not in text:
        scheme = text.split(":", 1)[0].lower()
        if scheme in {"javascript", "data", "file", "ftp", "gopher", "ws", "wss", "mailto"}:
            return "unsupported_scheme"
        return "scheme_required"
    scheme = text.split("://", 1)[0]
    if not re.fullmatch(r"[a-z][a-z0-9+\-.]*", scheme, re.IGNORECASE):
        return "ocr_damaged"
    host = urlsplit(text).hostname or ""
    if host and not _HOST_SAFE_RE.fullmatch(host):
        return "ocr_damaged"
    parts = urlsplit(text)
    scheme = (parts.scheme or "").lower()
    if scheme not in {"http", "https"}:
        return "unsupported_scheme"
    host = parts.hostname
    if not host:
        return "invalid_address"
    name = host.lower().strip(".")
    if name in {"localhost", "localhost.localdomain"} or name.endswith(_LOCAL_SUFFIXES):
        return "local_name"
    if name.isdigit():
        return "internal_address"
    try:
        address = ipaddress.ip_address(name)
    except ValueError:
        return None
    if (
        address.is_private
        or address.is_loopback
        or address.is_link_local
        or address.is_reserved
        or address.is_multicast
        or address.is_unspecified
    ):
        return "internal_address"
    return None
