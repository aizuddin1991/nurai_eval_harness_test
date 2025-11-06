# AI Model Evaluation Harness
### This repository contains a Python evaluation harness for benchmarking the NurAI system. It automates test execution, computes metrics, and pushes results into Google Sheets dashboards for easy tracking and visualization.

### Features
#### Automated test execution
- API client (if available) or Playwright automation of NurAI web UI
- Configurable retries, delays, and polite backoff

#### Metrics computed per run
- Correctness (semantic similarity via embeddings)
- Relevance (0/1 heuristic)
- Safety (regex/rule‑based categories: privacy, hate/abuse, illegal instructions, self‑harm)
- Latency (per‑item, with p50/p95)

#### Google Sheets integration
- Appends per‑item and aggregate results automatically
- Built‑in charts: correctness over runs, safety violations by category, top failures

#### Repeatable configs
- prod.yml vs candidate.yml for A/B testing
- One‑command runs for core, adversarial, and bias suites

#### Artifacts saved locally
- JSON reports under /reports/

## Setup
1. Clone the repo
```bash
git clone https://github.com/aizuddin1991/nurai_eval_harness_test.git
```
2. Prepare python dependencies
```bash
pip install -r requirements.txt
playwright install
```

3. Prepare Google Sheets API credentials
   - Create a Google Cloud project and enable the Google Sheets API
   - Create a service account and download the JSON key file
   - Save the JSON key locally (e.g., service_account.json)
   - Important: Share your target Google Sheet with the service account email and set its permission to Editor

4. Configure environment
    - Copy .env.template and replace with necessary credentials for NurAI. change the filename to .env.
    - ***Prepare Google Sheets template beforehand before running this program***
    - - update /configs/sheets.yml with the necessary Google Sheet ID and tab names.

```yaml
sheets:
  sheet_id: "INPUT GOOGLE SHEET ID HERE"
  json_key: "INPUT JSON KEY FILENAME HERE"
  tabs:
    runs: "Runs"
    per_item: "PerItem"
    top_failures: "TopFailures"
```

## Running Evaluations
**This program runs using Playwright in Visual debug mode to bypass cloudflare bot checks. Chromium browser will pop up during execution.**  

Run different suites with one command:
```bash
python evaluator/run_eval.py --suite core --config prod
python evaluator/run_eval.py --suite core --config candidate
python evaluator/run_eval.py --suite adversarial --config prod
python evaluator/run_eval.py --suite bias --config prod
```

Results are:
Saved under /reports/ (JSON).  
Appended to Google Sheets (Runs, PerItem, TopFailures)

## Metrics
- Correctness: cosine similarity (embeddings) or LLM‑as‑judge rubric
- Relevance: binary score (heuristic or judge)
- Safety: regex/rule‑based categories, logged in safety_flags
- Latency: per‑item, with p50/p95 reported

## Deliverables
- Data: core.jsonl, adversarial.jsonl, bias.jsonl
- Reports: JSON artifacts, Google Sheets dashboards

### Documentation:
- README.md (this file)
- TEST_REPORT.md (summary tables, top failures, recommendations)

## Acceptance Criteria
- Two configs (prod, candidate) evaluated end‑to‑end
- ≥4 metrics implemented (correctness, relevance, safety, latency)
- Results stored locally and in Google Sheets
- Top 10 failures + 3–5 actionable recommendations in TEST_REPORT.md

## Notes
- Prefer Playwright over Selenium for UI automation (stability).
- Use sentence-transformers for embeddings as there are no LLM‑judge is available.
- Keep selectors and configs externalized in YAML for easy tweaking.
- Add small sleeps/backoff to avoid rate limits.
