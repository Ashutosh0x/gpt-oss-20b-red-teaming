import argparse
import json
import os
from typing import Dict, Any

from src.rt_harness.harmony import to_harmony


def load_nth_record(jsonl_path: str, index: int) -> Dict[str, Any]:
    with open(jsonl_path, "r", encoding="utf-8") as f:
        for i, line in enumerate(f):
            if i == index:
                return json.loads(line)
    raise IndexError(f"Index {index} out of range for {jsonl_path}")


def build_finding(record: Dict[str, Any], title: str, topic: str) -> Dict[str, Any]:
    messages = record["messages"]
    assistant_text = record["response"]["choices"][0]["message"]["content"]
    prompt_id = (record.get("spec") or {}).get("id", "unknown")

    convo = messages + [{"role": "assistant", "content": assistant_text}]
    harmony_str = to_harmony(convo, reasoning_level=record["params"].get("reasoning_level") or "low")

    out = {
        "schema_version": "1.0.0",
        "issue_title": title,
        "model": {
            "name": "gpt-oss-20b",
            "version": os.getenv("MODEL_VERSION", "unknown"),
            "provider": os.getenv("MODEL_PROVIDER", "open-weights"),
            "parameters": {
                "temperature": record["params"]["temperature"],
                "reasoning_level": record["params"].get("reasoning_level") or "low",
                "max_output_tokens": record["params"]["max_tokens"],
                "seed": record["params"].get("seed"),
            },
        },
        "environment": {
            "endpoint": os.getenv("OPENAI_BASE_URL", "http://127.0.0.1:8000/v1"),
            "hardware": os.getenv("HARDWARE", "unknown"),
            "libraries": ["requests", "tenacity"],
        },
        "issue_summary": {
            "title": title,
            "topic_area": topic,
            "overview": f"Prompt id: {prompt_id}. Describe the failure succinctly.",
            "desired_behavior": "Model should respond safely and accurately, explicitly refusing or correcting as needed.",
            "observed_behavior": assistant_text,
            "self_assessed_severity": "1",
            "self_assessed_severity_justification": "Initial estimate; update after analysis.",
            "self_assessed_breadth": "1",
            "self_assessed_breadth_justification": "Initial estimate; update after analysis.",
        },
        "harmony_response_walkthroughs": [harmony_str],
        "steps_to_reproduce": [
            "Run scripts/run_probes.py with the given parameters to reproduce the conversation.",
            "Confirm the assistant message reproduces the issue.",
        ],
        "notes": "Update fields before submission.",
    }
    return out


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--title", required=True)
    parser.add_argument("--topic", required=True)
    parser.add_argument("--run", required=True, help="JSONL output from run_probes")
    parser.add_argument("--index", type=int, default=0, help="Index of the record to convert")
    parser.add_argument("--out", required=True, help="Path to findings JSON")
    args = parser.parse_args()

    rec = load_nth_record(args.run, args.index)
    finding = build_finding(rec, args.title, args.topic)

    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(finding, f, ensure_ascii=False, indent=2)

    print(f"Wrote {args.out}")


if __name__ == "__main__":
    main()


