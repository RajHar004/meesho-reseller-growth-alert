"""
Meesho Reseller Growth & Alert Intelligence Agent - Agent Runner & Execution Engine
===================================================================================
File: part4_agent/mock_agent_runner.py

Orchestrates the category performance monitoring workflow:
  1. Validates input feeds with fail-fast schema checks (validate_feed).
  2. Applies tri-state threshold evaluation (is_flagged).
  3. Ranks volatile categories by absolute growth percentage.
  4. Enforces an anti-fatigue policy (caps drafted notifications to the top 3).
  5. Formats structured JSON payloads held for human review.

Schema:
  - run_month (str)
  - validation_status ("valid" | "invalid")
  - validation_errors (list[str])
  - flagged_categories (list[dict])
  - suppressed_categories (list[str])
  - escalated_categories (list[str])
  - action_taken ("drafted_and_held_for_approval" | "hard_stop")
"""

import os
import sys
import csv
import json
from typing import Dict, Any, List

# Ensure project root is accessible in import path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Core engine and narrative formatters
from part2_engine.growth_engine import validate_feed, mom_growth, is_flagged
from part3_narrative.masking import generate_narrative_block



def _load_category_data(csv_path: str) -> Dict[str, Dict[str, Any]]:
    """
    Helper to parse a validated monthly category CSV into a lookup dictionary:
      category -> {"revenue": float, "n_orders": int, "month": str}
    """
    category_map: Dict[str, Dict[str, Any]] = {}
    with open(csv_path, mode="r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            cat = row["category"].strip()
            rev = float(row["revenue"].strip())
            orders = int(row["n_orders"].strip()) if "n_orders" in row else 0
            m = row["month"].strip() if "month" in row else ""
            category_map[cat] = {
                "revenue": rev,
                "n_orders": orders,
                "month": m,
            }
    return category_map


def run(month: str, previous_month_csv: str, current_month_csv: str) -> Dict[str, Any]:
    """
    Executes the 8-step agentic workflow for a given reporting month.
    
    Args:
      month: Reporting month name (e.g. "May", "June")
      previous_month_csv: Path to baseline month CSV feed
      current_month_csv: Path to current month CSV feed
      
    Returns:
      Structured JSON object conforming to the specification.
    """
    # 1. Validate Input Feeds (Fail-fast guardrail before metric computation)
    is_valid, errors = validate_feed(current_month_csv)
    if not is_valid:
        # Immediate hard stop on invalid feed
        return {
            "run_month": month,
            "validation_status": "invalid",
            "validation_errors": errors,
            "flagged_categories": [],
            "suppressed_categories": [],
            "escalated_categories": [],
            "action_taken": "hard_stop",
        }

    # Validate baseline feed
    is_prev_valid, prev_errors = validate_feed(previous_month_csv)
    if not is_prev_valid:
        return {
            "run_month": month,
            "validation_status": "invalid",
            "validation_errors": [f"Baseline feed error: {e}" for e in prev_errors],
            "flagged_categories": [],
            "suppressed_categories": [],
            "escalated_categories": [],
            "action_taken": "hard_stop",
        }

    # 2. Ingest Category Revenue & Evaluate Threshold Rules
    prev_data = _load_category_data(previous_month_csv)
    curr_data = _load_category_data(current_month_csv)

    flagged_candidates: List[Dict[str, Any]] = []
    escalated_categories: List[str] = []

    # Extract previous month label if present
    prev_month_name = "Previous Month"
    for item in prev_data.values():
        if item.get("month"):
            prev_month_name = item["month"]
            break

    for cat, curr_info in curr_data.items():
        if cat in prev_data:
            prev_info = prev_data[cat]
            prev_rev = prev_info["revenue"]
            curr_rev = curr_info["revenue"]

            # Compute Month-over-Month growth
            pct = mom_growth(prev_rev, curr_rev)

            # Evaluate against 8.00% operational boundary
            status = is_flagged(pct, threshold=8.0)

            if status == "flagged":
                flagged_candidates.append({
                    "category": cat,
                    "mom_pct": pct,
                    "abs_mom_pct": abs(pct),
                    "previous_revenue": prev_rev,
                    "current_revenue": curr_rev,
                    "n_orders": curr_info["n_orders"],
                    "prev_n_orders": prev_info["n_orders"],
                })
            elif status == "escalate_exact_boundary":
                # Route exact 8.00% boundary cases to analyst escalation queue
                escalated_categories.append(cat)
            # Normal variance categories (< 8.0%) remain unflagged

    # 3. Sort flagged categories by absolute volatility magnitude descending
    flagged_candidates.sort(key=lambda x: x["abs_mom_pct"], reverse=True)

    # 4. Anti-fatigue notification policy: draft top 3, suppress remaining
    top_3_candidates = flagged_candidates[:3]
    suppressed_candidates = flagged_candidates[3:]

    flagged_categories: List[Dict[str, Any]] = []
    for item in top_3_candidates:
        msg = generate_narrative_block(
            category=item["category"],
            month=month,
            prev_month=prev_month_name,
            prev_rev=item["previous_revenue"],
            curr_rev=item["current_revenue"],
            mom_pct=item["mom_pct"],
            n_orders=item["n_orders"],
            prev_n_orders=item["prev_n_orders"],
        )
        flagged_categories.append({
            "category": item["category"],
            "mom_pct": item["mom_pct"],
            "previous_revenue": item["previous_revenue"],
            "current_revenue": item["current_revenue"],
            "drafted": True,
            "message": msg,
        })

    suppressed_categories = [item["category"] for item in suppressed_candidates]

    # 5. Build structured payload held for human category manager approval
    output_payload: Dict[str, Any] = {
        "run_month": month,
        "validation_status": "valid",
        "validation_errors": [],
        "flagged_categories": flagged_categories,
        "suppressed_categories": suppressed_categories,
        "escalated_categories": escalated_categories,
        "action_taken": "drafted_and_held_for_approval",

    }

    return output_payload


if __name__ == "__main__":
    import tempfile

    # Flexible CLI invocation:
    # Usage: python3 part4_agent/mock_agent_runner.py [month] [prev_csv] [curr_csv]
    if len(sys.argv) == 4:
        run_m = sys.argv[1]
        p_csv = sys.argv[2]
        c_csv = sys.argv[3]
        result = run(run_m, p_csv, c_csv)
        print(json.dumps(result, indent=2))
        sys.exit(0)

    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    full_csv = os.path.join(base_dir, "part1_sql", "output", "monthly_category_revenue.csv")
    corrupt_csv = os.path.join(base_dir, "part2_engine", "fixtures", "corrupted_feed.csv")

    # Split full 15-row feed into monthly files for agent runs
    april_rows, may_rows, june_rows = [], [], []
    with open(full_csv, "r", encoding="utf-8") as f:
        reader = list(csv.DictReader(f))
        for r in reader:
            if r["month"] == "April":
                april_rows.append(r)
            elif r["month"] == "May":
                may_rows.append(r)
            elif r["month"] == "June":
                june_rows.append(r)

    def write_temp_csv(rows):
        tf = tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".csv", newline="")
        writer = csv.DictWriter(tf, fieldnames=["month", "category", "revenue", "n_orders"])
        writer.writeheader()
        writer.writerows(rows)
        tf.close()
        return tf.name

    april_csv = write_temp_csv(april_rows)
    may_csv = write_temp_csv(may_rows)
    june_csv = write_temp_csv(june_rows)

    try:
        # Run May scenario
        print("\n================== MAY SCENARIO (April -> May) ==================")
        may_result = run("May", april_csv, may_csv)
        print(json.dumps(may_result, indent=2))

        # Run June scenario
        print("\n================== JUNE SCENARIO (May -> June) ==================")
        june_result = run("June", may_csv, june_csv)
        print(json.dumps(june_result, indent=2))

        # Run Corrupted Feed scenario
        print("\n================== CORRUPTED FEED SCENARIO ==================")
        corrupt_result = run("July", june_csv, corrupt_csv)
        print(json.dumps(corrupt_result, indent=2))

    finally:
        os.remove(april_csv)
        os.remove(may_csv)
        os.remove(june_csv)

