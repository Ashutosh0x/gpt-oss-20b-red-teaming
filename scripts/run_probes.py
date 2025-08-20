import argparse
import json
import os
import random
from datetime import datetime
from typing import Dict, List

from dotenv import load_dotenv
from rich.progress import track
import yaml

from src.rt_harness.adapter_openai import OpenAICompatClient
from src.rt_harness.adapter_ollama import OllamaClient


def load_prompts(path: str) -> List[Dict]:
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    assert isinstance(data, list), "YAML must be a list of prompt specs"
    return data


def build_messages(spec: Dict) -> List[Dict]:
    messages: List[Dict] = []
    system_msg = spec.get("system")
    if system_msg:
        messages.append({"role": "system", "content": system_msg})
    developer_msg = spec.get("developer")
    if developer_msg:
        messages.append({"role": "developer", "content": developer_msg})
    user_msg = spec.get("user")
    assert user_msg, "Prompt spec missing 'user'"
    messages.append({"role": "user", "content": user_msg})
    return messages


def main():
    load_dotenv()
    parser = argparse.ArgumentParser()
    parser.add_argument("--prompts", required=True, help="YAML file with prompt specs")
    parser.add_argument("--out", required=True, help="Output JSONL path")
    parser.add_argument("--temperature", type=float, default=0.7)
    parser.add_argument("--max-tokens", type=int, default=512)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--reasoning", type=str, default=None, choices=[None, "low", "medium", "high", "critical"])
    parser.add_argument("--log-stream", action="store_true", help="Print per-prompt progress to stdout")
    args = parser.parse_args()

    prompts = load_prompts(args.prompts)
    adapter = os.getenv("MODEL_ADAPTER", "openai").lower()
    if adapter == "ollama":
        client = OllamaClient()
    else:
        client = OpenAICompatClient()

    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as fout:
        iterator = range(len(prompts))
        if not args.log_stream:
            iterator = track(iterator, description="Running probes")
        for idx in iterator:
            spec = prompts[idx]
            messages = build_messages(spec)
            seed = args.seed if args.seed is not None else random.randint(1, 1_000_000)
            if args.log_stream:
                print(f"[probe {idx+1}/{len(prompts)}] id={spec.get('id','<no-id>')} seed={seed} ...", flush=True)
            try:
                result = client.chat(
                    messages=messages,
                    temperature=args.temperature,
                    max_tokens=args.max_tokens,
                    seed=seed,
                    reasoning=args.reasoning,
                )
                latency = result["latency_s"]
                assistant_text = result["raw"]["choices"][0]["message"].get("content", "")
            except Exception as e:
                if args.log_stream:
                    print(f"[probe {idx+1}] ERROR: {e}", flush=True)
                raise

            record = {
                "ts": datetime.utcnow().isoformat() + "Z",
                "spec": spec,
                "messages": messages,
                "response": result["raw"],
                "latency_s": latency,
                "params": {
                    "temperature": args.temperature,
                    "max_tokens": args.max_tokens,
                    "seed": seed,
                    "reasoning_level": args.reasoning,
                },
            }
            fout.write(json.dumps(record, ensure_ascii=False) + "\n")
            fout.flush()
            if args.log_stream:
                preview = assistant_text.replace("\n", " ")[:120]
                print(f"[probe {idx+1}] latency={latency:.2f}s reply='{preview}...'", flush=True)


if __name__ == "__main__":
    main()


