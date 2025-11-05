# evaluator/run_eval.py
import argparse
import json
import time
from pathlib import Path
import yaml
from nurai_client import goto_from_home, login_if_needed, take_snapshot,wait_for_latest_answer
from metrics import compute_metrics, aggregate_metrics
from sheets_client import append_run, append_per_item, append_top_failures
from report import generate_test_report

def load_config(config_name: str):
    path = Path("configs") / f"{config_name}.yml"
    with open(path, "r") as f:
        return yaml.safe_load(f)

def load_suite(suite_name: str):
    path = Path("data") / f"{suite_name}.jsonl"
    items = []
    with open(path, "r") as f:
        for line in f:
            items.append(json.loads(line))
    return items

def run_suite(suite_name: str, config_name: str):
    config = load_config(config_name)
    items = load_suite(suite_name)
    sheets_config = load_config("sheets")

    # Start Playwright
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()

        # Navigate from home
        result = goto_from_home(context, config)
        if result["state"] == "login":
            result = login_if_needed(result["page"], config)
        chat_page = result["page"]

        run_id = f"{config_name}_{int(time.time())}"
        per_item_results = []

        is_first_prompt = True

        for item in items:
            qid = item["id"]
            question = item["question"]

            # Send prompt & measure latency
            start = time.time()

            if is_first_prompt:
                input_selector = config["selectors"]["chat_page"]["prompt_input"]["locator"]
            else:
                input_selector = config["selectors"]["chat_page"]["prompt_input_followup"]["locator"]
            chat_page.locator(input_selector).fill(question)
            chat_page.locator(config["selectors"]["chat_page"]["submit_button"]["locator"]).click()

            # Capture model answer
            answer = wait_for_latest_answer(chat_page)
            #dump_ai_answer_to_file(chat_page)

            latency_ms = int((time.time() - start) * 1000)

            # Compute metrics
            metrics = compute_metrics(item, answer, latency_ms, config)

            per_item_results.append({
                "run_id": run_id,
                "id": qid,
                "config": config_name,
                "model_answer": answer,
                "latency_ms": latency_ms,
                **metrics,
                "tags": item.get("tags", [])
            })
            is_first_prompt = False

        # Aggregate
        aggregates = aggregate_metrics(per_item_results)

        # Save artifacts locally
        reports_dir = Path(config["reports"]["output_dir"])
        reports_dir.mkdir(exist_ok=True)
        with open(reports_dir / f"{run_id}.json", "w") as f:
            json.dump(per_item_results, f, indent=2)

        # Push to Google Sheets
        # append_top_failures(per_item_results, config)
        append_run(run_id, config_name, suite_name, aggregates, sheets_config)
        append_per_item(per_item_results, sheets_config)
        append_top_failures(per_item_results, sheets_config)

        browser.close()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--suite", required=True, choices=["core", "adversarial", "bias"])
    parser.add_argument("--config", required=True, choices=["prod", "candidate"])
    args = parser.parse_args()

    run_suite(args.suite, args.config)

if __name__ == "__main__":
    main()

#report_file = generate_test_report(run_id, suite_name, config_name, aggregates, per_item_results, config["reports"]["output_dir"])
#print("Report written to", report_file)