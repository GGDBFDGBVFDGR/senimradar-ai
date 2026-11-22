"""Registrable-domain helper used to keep one site inside a single split."""

from __future__ import annotations

_MULTI = {
    "co.uk",
    "org.uk",
    "ac.uk",
    "gov.uk",
    "com.au",
    "net.au",
    "org.au",
    "co.nz",
    "com.br",
    "co.jp",
    "co.kr",
    "com.tr",
    "com.mx",
    "co.za",
    "com.kz",
    "org.kz",
    "net.kz",
    "co.kz",
    "com.ua",
    "com.ru",
    "net.ru",
    "org.ru",
    "com.cn",
    "com.tw",
    "com.hk",
    "co.in",
    "com.sg",
    "com.ar",
}


def registrable_domain(host: str) -> str:
    name = host.lower().strip(".")
    if name.startswith("www."):
        name = name[4:]
    labels = [part for part in name.split(".") if part]
    if len(labels) <= 2:
        return ".".join(labels)
    tail = ".".join(labels[-2:])
    if tail in _MULTI:
        return ".".join(labels[-3:])
    return tail
