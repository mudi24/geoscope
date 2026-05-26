from __future__ import annotations

import ipaddress
import os
import socket
from urllib.parse import urlparse


class UrlSafetyError(ValueError):
    pass


def validate_public_url(url: str) -> None:
    """
    SSRF 基础防护（面试加分点）：
    - 只允许 http/https
    - 禁止访问 localhost/内网/保留地址（可通过环境变量放开）
    """
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        raise UrlSafetyError("only http/https is allowed")
    if not parsed.hostname:
        raise UrlSafetyError("missing hostname")

    allow_private = os.getenv("GEOSCOPE_ALLOW_PRIVATE_NETWORKS", "").lower() in {
        "1",
        "true",
        "yes",
    }
    if allow_private:
        return

    host = parsed.hostname
    try:
        infos = socket.getaddrinfo(host, parsed.port or (443 if parsed.scheme == "https" else 80))
    except OSError as e:
        raise UrlSafetyError(f"DNS resolve failed: {e}") from e

    for info in infos:
        ip_str = info[4][0]
        ip = ipaddress.ip_address(ip_str)
        if (
            ip.is_private
            or ip.is_loopback
            or ip.is_link_local
            or ip.is_multicast
            or ip.is_reserved
        ):
            raise UrlSafetyError(f"blocked non-public address: {ip_str}")

