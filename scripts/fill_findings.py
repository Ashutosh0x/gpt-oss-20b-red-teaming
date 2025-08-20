import argparse
import json
from pathlib import Path
from typing import Any, Dict, List


def load_jsonl_n(path: Path, index: int) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        for i, line in enumerate(f):
            if i == index:
                return json.loads(line)
    raise IndexError(f"Index {index} out of range for {path}")


def short(text: str, limit: int = 200) -> str:
    t = (text or "").replace("\r", " ").replace("\n", " ")
    return t if len(t) <= limit else t[:limit] + "..."


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", required=True)
    parser.add_argument("--map", nargs="+", required=True, help="triples: idx findings_path title topic")
    args = parser.parse_args()

    run_path = Path(args.run)
    triples: List[str] = args.map
    if len(triples) % 4 != 0:
        raise SystemExit("--map must be groups of 4: idx findings_path title topic")

    for i in range(0, len(triples), 4):
        idx = int(triples[i])
        out_path = Path(triples[i + 1])
        title = triples[i + 2]
        topic = triples[i + 3]

        rec = load_jsonl_n(run_path, idx)
        spec = rec.get("spec") or {}
        prompt_id = spec.get("id", "unknown")
        assistant = (
            (rec.get("response") or {})
            .get("choices", [{}])[0]
            .get("message", {})
            .get("content", "")
        )

        if not out_path.exists():
            raise FileNotFoundError(out_path)
        data = json.loads(out_path.read_text(encoding="utf-8"))

        data["issue_title"] = title
        data["issue_summary"]["title"] = title
        data["issue_summary"]["topic_area"] = topic
        data["issue_summary"]["overview"] = f"Prompt id: {prompt_id}. Auto-filled from run {run_path.name}."
        data["issue_summary"]["observed_behavior"] = assistant

        out_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"Updated {out_path} (idx={idx}, prompt_id={prompt_id}, observed={short(assistant)})")


if __name__ == "__main__":
    main()


