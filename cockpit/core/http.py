"""HTTP-Verbindungen für alle Adapter.

- Zertifikate kommen aus dem Windows-Zertifikatsspeicher (Bibliothek truststore). So klappt es auch
  in Firmennetzen, die eigene Zertifikate einsetzen (Konzept 6.2).
- Proxy-Einstellungen aus Windows bzw. den Umgebungsvariablen werden übernommen.
- Wartezeiten: kurz für den Verbindungsaufbau, länger für die Antwort.
"""
from __future__ import annotations

import ssl

import httpx

from cockpit import APP_NAME, __version__

USER_AGENT = f"{APP_NAME}/{__version__}"
CONNECT_TIMEOUT = 10
READ_TIMEOUT = 30


def ssl_context() -> ssl.SSLContext:
    try:
        import truststore
        return truststore.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    except Exception:                                   # ohne truststore: Standard von Python
        return ssl.create_default_context()


def make_client(base_url: str = "", headers: dict[str, str] | None = None,
                transport: httpx.BaseTransport | None = None) -> httpx.Client:
    """Neuer HTTP-Client. transport ersetzen Tests durch httpx.MockTransport."""
    all_headers = {"User-Agent": USER_AGENT}
    all_headers.update(headers or {})
    return httpx.Client(base_url=base_url, headers=all_headers,
                        timeout=httpx.Timeout(READ_TIMEOUT, connect=CONNECT_TIMEOUT),
                        verify=ssl_context() if transport is None else True,
                        transport=transport, follow_redirects=True)
