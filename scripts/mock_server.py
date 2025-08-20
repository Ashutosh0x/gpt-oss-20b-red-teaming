import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse
import threading
import time


class ChatHandler(BaseHTTPRequestHandler):
    def _set_headers(self, status: int = 200):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.end_headers()

    def do_POST(self):  # noqa: N802 (BaseHTTPRequestHandler naming)
        parsed = urlparse(self.path)
        if parsed.path == "/v1/chat/completions":
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length) if content_length > 0 else b"{}"
            try:
                payload = json.loads(body.decode("utf-8"))
            except Exception:
                payload = {}

            # Echo a harmless, deterministic response
            messages = payload.get("messages", [])
            user_content = ""
            for m in reversed(messages):
                if m.get("role") == "user":
                    user_content = m.get("content", "")
                    break

            response_text = (
                "This is a mock response for testing the harness. "
                "I received your request and will behave safely. "
                f"User said: {user_content[:200]}"
            )

            data = {
                "id": "chatcmpl-mock-1",
                "object": "chat.completion",
                "created": int(time.time()),
                "model": payload.get("model", "gpt-oss-20b"),
                "choices": [
                    {
                        "index": 0,
                        "message": {"role": "assistant", "content": response_text},
                        "finish_reason": "stop",
                    }
                ],
            }
            self._set_headers(200)
            self.wfile.write(json.dumps(data).encode("utf-8"))
        else:
            self._set_headers(404)
            self.wfile.write(b"{}")


def run_server(host: str = "127.0.0.1", port: int = 8000):
    server = HTTPServer((host, port), ChatHandler)
    print(f"Mock server running on http://{host}:{port}")
    server.serve_forever()


if __name__ == "__main__":
    # Run directly (blocking)
    run_server()


