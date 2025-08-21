## OpenAI gpt-oss-20b Red-Teaming Harness

This repo contains a lightweight, reproducible workflow to probe `gpt-oss-20b`, capture adversarial conversations, and generate Kaggle‑compliant findings JSON files.

### What’s included
- Prompts: `data/prompts/{advanced.yaml, novel.yaml, covert.yaml}`
- Harness: `scripts/run_probes.py` (OpenAI‑compatible + Ollama)
- Adapters: `src/rt_harness/{adapter_openai.py, adapter_ollama.py}`
- Generators/Validators: `scripts/{make_finding.py, validate_finding.py, enrich_findings.py}`
- Analysis/Detectors: `scripts/{analyze_runs.py, detect_failures.py}`
- Reproduction: `notebooks/submit_repro.ipynb`

### Quick start
1) Prereqs
- Python 3.8+
- Local model server (Ollama) with a `gpt-oss-20b` tag

2) Install
```powershell
python -m pip install -r requirements.txt
```

3) Set env (Ollama)
```powershell
$env:MODEL_ADAPTER="ollama"
$env:OLLAMA_BASE_URL="http://127.0.0.1:11434"
$env:MODEL_NAME="gpt-oss:20b"
```

4) Run probes (examples)
```powershell
python -m scripts.run_probes --prompts data/prompts/novel.yaml --out outputs/run-novel.t0.s222.jsonl --temperature 0 --max-tokens 96 --seed 222 --log-stream
python -m scripts.run_probes --prompts data/prompts/advanced.yaml --out outputs/run-advanced.jsonl --temperature 0.7 --max-tokens 96 --log-stream
```

5) Create and validate findings
```powershell
python -m scripts.make_finding --title "Evaluation awareness signaling" --topic "evaluation awareness" --run outputs/run-novel.t0.s111.jsonl --index 2 --out findings/final.2.json
python -m scripts.validate_finding findings/final.2.json findings.schema
```

6) Reproduce in notebook
Open `notebooks/submit_repro.ipynb` and run all cells. It re‑runs the prompts and asserts that observed behavior matches the stored finding(s).



### Safety
- Prompts are designed to demonstrate behavior without enabling harm. Avoid adding actionable instructions.

