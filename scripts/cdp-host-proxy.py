"""Tiny Host-header-rewriting TCP proxy for reaching a host Chrome's CDP from a
Docker container (Docker Desktop / WSL2).

Why this exists: Chrome (66+) rejects the HTTP `/json` probe Playwright sends first
unless the `Host` header is an IP or `localhost` (DNS-rebinding protection). A Docker
container reaches the host via `host.docker.internal` (a hostname) -> rejected. A raw
TCP forwarder (netsh portproxy / socat) can't fix it. This proxy rewrites the first
request's `Host:` line to `localhost` and then pipes bytes transparently (covering both
the `/json` GET and the WebSocket upgrade), so the container can use a STABLE
`http://host.docker.internal:<LISTEN>` URL with no per-restart browser-id.

Run on the HOST next to Chrome:
    python scripts/cdp-host-proxy.py            # listens 0.0.0.0:9223 -> 127.0.0.1:18800
    CDP_LISTEN_PORT=9223 CDP_TARGET=127.0.0.1:18800 python scripts/cdp-host-proxy.py

Restrict exposure to the Docker subnet only (NOT the LAN) with a host firewall rule, e.g.
Windows:  New-NetFirewallRule -DisplayName cdp-9223 -Direction Inbound -Action Allow \
              -Protocol TCP -LocalPort 9223 -RemoteAddress 172.16.0.0/12
          (+ a Block rule for the rest of 9223). Then in the container set
          BROWSER_CDP_URL=http://host.docker.internal:9223
"""

import asyncio
import os
import re

LISTEN_HOST = "0.0.0.0"
LISTEN_PORT = int(os.getenv("CDP_LISTEN_PORT", "9223"))
_t_host, _, _t_port = os.getenv("CDP_TARGET", "127.0.0.1:18800").partition(":")
TARGET = (_t_host, int(_t_port or "18800"))
_HOST_LINE = re.compile(rb"(?im)^Host:[^\r\n]*")


async def _pipe(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
    try:
        while True:
            chunk = await reader.read(65536)
            if not chunk:
                break
            writer.write(chunk)
            await writer.drain()
    except Exception:
        pass
    finally:
        try:
            writer.close()
        except Exception:
            pass


async def _handle(client_r: asyncio.StreamReader, client_w: asyncio.StreamWriter) -> None:
    try:
        server_r, server_w = await asyncio.open_connection(*TARGET)
    except Exception:
        client_w.close()
        return
    # Rewrite the Host header on the first (HTTP request / WS upgrade) chunk only.
    first = await client_r.read(65536)
    if first:
        first = _HOST_LINE.sub(f"Host: localhost:{TARGET[1]}".encode(), first, count=1)
        server_w.write(first)
        await server_w.drain()
    await asyncio.gather(_pipe(server_r, client_w), _pipe(client_r, server_w))


async def main() -> None:
    server = await asyncio.start_server(_handle, LISTEN_HOST, LISTEN_PORT)
    print(f"cdp-host-proxy: {LISTEN_HOST}:{LISTEN_PORT} -> {TARGET[0]}:{TARGET[1]} "
          f"(Host header rewritten to localhost)")
    async with server:
        await server.serve_forever()


if __name__ == "__main__":
    asyncio.run(main())
