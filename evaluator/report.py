# evaluator/report.py
from pathlib import Path
from typing import List, Dict
import statistics

def generate_test_report(run_id: str,
                         suite_name: str,
                         config_name: str,
                         aggregates: Dict[str, any],
                         per_item_results: List[Dict[str, any]],
                         output_dir: str = "./reports"):
    """
    Generate a TEST_REPORT.md summarizing the run.
    """
    report_path = Path(output_dir) / f"TEST_REPORT_{run_id}.md"

    # Top 10 failures by correctness
    sorted_items = sorted(per_item_results, key=lambda r: r["correctness"])
    top_failures = sorted_items[:10]

    # Recommendations (simple heuristics)
    recs = []
    if aggregates["correctness_avg"] < 0.8:
        recs.append("Improve model grounding: many answers fall below similarity threshold.")
    if aggregates["relevance_avg"] < 0.9:
        recs.append("Tighten prompt handling: some answers drift off-topic.")
    if aggregates["safety_violations"] > 0:
        recs.append("Strengthen safety filters: flagged unsafe content detected.")
    if aggregates["p95_ms"] and aggregates["p95_ms"] > 5000:
        recs.append("Optimize latency: 95th percentile response time is high.")

    with open(report_path, "w") as f:
        f.write(f"# Test Report for Run {run_id}\n\n")
        f.write(f"**Suite:** {suite_name}  \n")
        f.write(f"**Config:** {config_name}  \n\n")

        f.write("## Summary Metrics\n\n")
        f.write("| n_items | correctness_avg | relevance_avg | safety_violations | p50_ms | p95_ms |\n")
        f.write("|---------|-----------------|---------------|-------------------|--------|--------|\n")
        f.write(f"| {aggregates['n_items']} | {aggregates['correctness_avg']:.2f} | "
                f"{aggregates['relevance_avg']:.2f} | {aggregates['safety_violations']} | "
                f"{aggregates['p50_ms']} | {aggregates['p95_ms']} |\n\n")

        f.write("## Top 10 Failures\n\n")
        f.write("| id | correctness | snippet |\n")
        f.write("|----|-------------|---------|\n")
        for item in top_failures:
            snippet = item["model_answer"][:120].replace("\n", " ")
            f.write(f"| {item['id']} | {item['correctness']:.2f} | {snippet} |\n")

        f.write("\n## Recommendations\n\n")
        for rec in recs:
            f.write(f"- {rec}\n")

    return str(report_path)
