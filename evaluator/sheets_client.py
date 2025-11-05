# evaluator/sheets_client.py
import gspread
import yaml
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List

def _get_sheet(config: Dict[str, Any]):
    """
    Open the Google Sheet using gspread.
    Assumes you have already set up Google auth (service account or OAuth).
    """
    gc = gspread.service_account(filename="nuraitest-477116-e4f05a1d9e75.json")
    sheet_id = config["sheets"]["sheet_id"]
    return gc.open_by_key(sheet_id)

def append_run(run_id: str, config_name: str, suite_name: str, aggregates: Dict[str, Any], config: Dict[str, Any]):
    """
    Append one row to the Runs tab.
    """
    sh = _get_sheet(config)
    ws = sh.worksheet(config["sheets"]["tabs"]["runs"])

    # Define the expected header
    header = [
        "timestamp",
        "run_id",
        "config",
        "suite",
        "n_items",
        "correctness",
        "relevance",
        "safety_violations",
        "p50_ms",
        "p95_ms",
        "notes"
    ]

    # Check if sheet is empty or header missing
    existing_values = ws.get_all_values()
    if not existing_values:  # completely empty sheet
        ws.append_row(header, value_input_option="USER_ENTERED")
    else:
        first_row = existing_values[0]
        # If header mismatch (e.g. someone cleared it), re-add
        if first_row != header:
            ws.insert_row(header, 1, value_input_option="USER_ENTERED")

    row = [
        datetime.utcnow().isoformat(),
        run_id,
        config_name,
        suite_name,
        aggregates["n_items"],
        aggregates["correctness_avg"],
        aggregates["relevance_avg"],
        aggregates["safety_violations"],
        aggregates["p50_ms"],
        aggregates["p95_ms"],
        ""  # notes column
    ]
    ws.append_row(row, value_input_option="USER_ENTERED")

def append_per_item(per_item_results: List[Dict[str, Any]], config: Dict[str, Any]):
    """
    Append rows to the PerItem tab.
    """
    sh = _get_sheet(config)
    ws = sh.worksheet(config["sheets"]["tabs"]["per_item"])

    # Define expected header
    header = [
        "run_id",
        "id",
        "config",
        "correctness",
        "relevance",
        "safety_flags",
        "latency_ms",
        "model_answer",
        "tags"
    ]

    # Check if sheet is empty or header missing
    existing_values = ws.get_all_values()
    if not existing_values:  # completely empty sheet
        ws.append_row(header, value_input_option="USER_ENTERED")
    else:
        first_row = existing_values[0]
        if first_row != header:
            ws.insert_row(header, 1, value_input_option="USER_ENTERED")

    # Build rows to append
    rows = []
    for r in per_item_results:
        rows.append([
            r["run_id"],
            r["id"],
            r["config"],
            r["correctness"],
            r["relevance"],
            ",".join(r["safety_flags"]),
            r["latency_ms"],
            r["model_answer"],
            ",".join(r.get("tags", []))
        ])

    ws.append_rows(rows, value_input_option="USER_ENTERED",table_range= 'A1')

def append_top_failures(per_item_results: List[Dict[str, Any]], config: Dict[str, Any], top_n: int = 10):
    """
    Append rows to the TopFailures tab.
    """
    sh = _get_sheet(config)
    ws = sh.worksheet(config["sheets"]["tabs"]["top_failures"])

    # Define expected header
    header = [
        "run_id",
        "id",
        "snippet",
        "reason"
    ]

    # Check if sheet is empty or header missing
    existing_values = ws.get_all_values()
    if not existing_values:  # completely empty sheet
        ws.append_row(header, value_input_option="USER_ENTERED")
    else:
        first_row = existing_values[0]
        if first_row != header:
            ws.insert_row(header, 1, value_input_option="USER_ENTERED")

    # Sort by lowest correctness
    sorted_items = sorted(per_item_results, key=lambda r: r["correctness"])
    failures = sorted_items[:top_n]

    rows = []
    for r in failures:
        rows.append([
            r["run_id"],
            r["id"],
            r["model_answer"][:200],  # snippet
            "Low correctness"
        ])
    ws.append_rows(rows, value_input_option="USER_ENTERED",table_range='A1')
