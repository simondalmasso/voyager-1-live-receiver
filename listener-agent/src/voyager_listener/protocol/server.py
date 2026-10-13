from __future__ import annotations
import json
import os
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Callable
from urllib.parse import urlsplit


def _validated_origin(value: str) -> str:
    if any(ch in value for ch in "\r\n\x00"):
        raise ValueError("allowed origin contains control characters")
    parsed = urlsplit(value)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname or parsed.username or parsed.password:
        raise ValueError("allowed origin must be an http(s) origin")
    if parsed.path not in {"", "/"} or parsed.query or parsed.fragment:
        raise ValueError("allowed origin must not contain path, query or fragment")
    return f"{parsed.scheme}://{parsed.netloc}"


class SnapshotServer:
    def __init__(self, provider: Callable[[], dict[str, Any]], host: str = "127.0.0.1", port: int = 8765, allowed_origin: str = "http://127.0.0.1:4173") -> None:
        if host not in {"127.0.0.1", "localhost", "::1"} and os.getenv("VOYAGER_LISTENER_ALLOW_REMOTE") != "1":
            raise ValueError("remote bind requires VOYAGER_LISTENER_ALLOW_REMOTE=1")
        self.provider, self.host, self.port = provider, host, port
        self.allowed_origin = _validated_origin(allowed_origin)
        provider_ref = provider
        allowed = self.allowed_origin
        token = os.getenv("VOYAGER_LISTENER_TOKEN")
        class Handler(BaseHTTPRequestHandler):
            server_version = "VoyagerListener/1"
            def _auth(self) -> bool:
                if token and self.headers.get("authorization") != f"Bearer {token}":
                    self.send_response(401); self.end_headers(); return False
                return True
            def _headers(self, content_type: str) -> None:
                if self.headers.get("origin") == allowed:
                    self.send_header("Access-Control-Allow-Origin", allowed)
                    self.send_header("Vary", "Origin")
                self.send_header("Content-Type", content_type)
                self.send_header("Cache-Control", "no-store")
                self.send_header("X-Content-Type-Options", "nosniff")
            def do_GET(self) -> None:
                if not self._auth(): return
                if self.path == "/health":
                    body = json.dumps({"status":"ok","receiveOnly":True}).encode()
                    self.send_response(200); self._headers("application/json"); self.send_header("Content-Length", str(len(body))); self.end_headers(); self.wfile.write(body)
                elif self.path == "/snapshot":
                    body = json.dumps(provider_ref(), separators=(",", ":")).encode()
                    self.send_response(200); self._headers("application/json"); self.send_header("Content-Length", str(len(body))); self.end_headers(); self.wfile.write(body)
                elif self.path == "/events":
                    self.send_response(200); self._headers("text/event-stream"); self.send_header("Connection", "keep-alive"); self.end_headers()
                    try:
                        for _ in range(3600):
                            payload = json.dumps(provider_ref(), separators=(",", ":"))
                            self.wfile.write(f"data: {payload}\n\n".encode()); self.wfile.flush(); time.sleep(1)
                    except (BrokenPipeError, ConnectionResetError): pass
                else:
                    self.send_response(404); self.end_headers()
            def log_message(self, fmt: str, *args: object) -> None:
                return
        self._server = ThreadingHTTPServer((host, port), Handler)
    def serve_forever(self) -> None:
        self._server.serve_forever()
    def shutdown(self) -> None:
        self._server.shutdown()
