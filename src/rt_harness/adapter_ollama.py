import os
import time
from typing import Dict, List, Optional

import requests
from tenacity import retry, stop_after_attempt, wait_exponential


class OllamaClient:
    """Minimal client for Ollama's chat API.

    Env vars:
      - OLLAMA_BASE_URL (default http://127.0.0.1:11434)
      - MODEL_NAME (Ollama model tag)
    """

    def __init__(self, base_url: Optional[str] = None, model: Optional[str] = None):
        self.base_url = base_url or os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
        self.model = model or os.getenv("MODEL_NAME", "")
        if not self.model:
            raise ValueError("MODEL_NAME must be set for OllamaClient")
        self.session = requests.Session()

    @retry(wait=wait_exponential(multiplier=1, min=1, max=10), stop=stop_after_attempt(3))
    def chat(self, messages: List[Dict], temperature: float = 0.7, max_tokens: int = 512, seed: Optional[int] = None, reasoning: Optional[str] = None) -> Dict:
        url = f"{self.base_url.rstrip('/')}/api/chat"
        # Map OpenAI-style messages to Ollama chat format
        payload: Dict = {
            "model": self.model,
            "messages": messages,
            "options": {
                "temperature": temperature,
                # Ollama uses num_predict; None means default
                "num_predict": max_tokens,
            },
            "stream": False,
        }
        if seed is not None:
            payload["options"]["seed"] = seed

        start = time.time()
        resp = self.session.post(url, json=payload, timeout=120)
        latency_s = time.time() - start
        resp.raise_for_status()
        data = resp.json()
        # Normalize to OpenAI-like structure expected by the harness
        # Some reasoning models return content in `thinking` and leave `content` empty.
        # Prefer content; if empty, fall back to thinking.
        try:
            message_obj = data.get("message", {})
        except Exception:
            message_obj = {}
        content = message_obj.get("content") or message_obj.get("thinking") or ""
        normalized = {
            "choices": [
                {
                    "index": 0,
                    "message": {"role": "assistant", "content": content},
                    "finish_reason": data.get("done_reason", "stop"),
                }
            ]
        }
        return {"raw": normalized, "latency_s": latency_s}


