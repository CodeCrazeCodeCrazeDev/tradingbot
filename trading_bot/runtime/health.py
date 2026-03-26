from __future__ import annotations

import asyncio
import json
from datetime import datetime
from typing import Any, Dict


class RuntimeHealth:
    def __init__(self, get_status, host: str = "0.0.0.0", port: int = 8080) -> None:
        self._get_status = get_status
        self.host = host
        self.port = port
        self._server = None

    async def start(self) -> None:
        self._server = await asyncio.start_server(self._handle, self.host, self.port)

    async def stop(self) -> None:
        if self._server:
            self._server.close()
            await self._server.wait_closed()

    async def _handle(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        req = await reader.read(2048)
        line = req.splitlines()[0].decode("utf-8", errors="ignore") if req else ""
        path = line.split(" ")[1] if " " in line else "/"

        if path.startswith("/health"):
            body = {
                "ok": True,
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "status": self._get_status(),
            }
            payload = json.dumps(body).encode("utf-8")
            writer.write(b"HTTP/1.1 200 OK\r\nContent-Type: application/json\r\n")
            writer.write(f"Content-Length: {len(payload)}\r\n\r\n".encode("utf-8"))
            writer.write(payload)
        else:
            writer.write(b"HTTP/1.1 404 Not Found\r\nContent-Length: 0\r\n\r\n")

        await writer.drain()
        writer.close()
        await writer.wait_closed()
