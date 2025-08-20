import os
import time
from typing import Dict, List, Optional

import requests
from tenacity import retry, stop_after_attempt, wait_exponential


class OpenAICompatClient:
    """Minimal OpenAI-compatible chat completions client via HTTP.

    Expects env vars:
      - OPENAI_BASE_URL
      - OPENAI_API_KEY
      - MODEL_NAME
    """

    def __init__(self, base_url: Optional[str] = None, api_key: Optional[str] = None, model: Optional[str] = None):
        self.base_url = base_url or os.getenv("OPENAI_BASE_URL", "http://127.0.0.1:8000/v1")
        self.api_key = api_key or os.getenv("OPENAI_API_KEY", "test-sk")
        self.model = model or os.getenv("MODEL_NAME", "gpt-oss-20b")
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        })

    @retry(wait=wait_exponential(multiplier=1, min=1, max=10), stop=stop_after_attempt(3))
    def chat(self, messages: List[Dict], temperature: float = 0.7, max_tokens: int = 512, seed: Optional[int] = None, reasoning: Optional[str] = None) -> Dict:
        url = f"{self.base_url.rstrip('/')}/chat/completions"
        payload: Dict = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if seed is not None:
            payload["seed"] = seed
        if reasoning is not None:
            payload["reasoning"] = {"effort": reasoning}

        start = time.time()
        resp = self.session.post(url, json=payload, timeout=120)
        latency_s = time.time() - start
        resp.raise_for_status()
        data = resp.json()
        return {"raw": data, "latency_s": latency_s}


