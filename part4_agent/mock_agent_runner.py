"""
Meesho Reseller Growth & Alert Intelligence Agent - Mock Agent Runner
======================================================================
File: part4_agent/mock_agent_runner.py

This module executes the guarded 8-step agentic workflow:
  1. Validate incoming feed using Part 2's validate_feed
  2. Hard stop if feed is invalid, surfacing line errors
  3. Calculate MoM growth using Part 2's mom_growth (unmodified import)
  4. Apply flag rule using Part 2's is_flagged (unmodified import)
  5. Sort flagged categories by absolute MoM percentage descending
  6. Draft at most the top 3 flagged categories using Part 3 template
  7. Suppress additional flagged categories beyond the top-3 cap
  8. Separately record exact-boundary escalations (abs(mom_pct) == 8.0)
  9. Emit structured JSON adhering to the required schema

Required top-level JSON keys:
  - run_month
  - validation_status ("valid" | "invalid")
  - validation_errors (list[str])
  - flagged_categories (list[dict])
  - suppressed_categories (list[str])
  - escalated_categories (list[str])
  - action_taken ("drafted_and_held_for_approval" | "hard_stop")

Zero external APIs, zero emails, zero network calls.
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

# Critical requirement: import Part 2 and Part 3 functions unmodified
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
    # -------------------------------------------------------------------------
    # Subtask 1 & 2: Validate Feed & Hard Stop if Invalid
    # -------------------------------------------------------------------------
    is_valid, errors = validate_feed(current_month_csv)
    if not is_valid:
        # Immediate Hard Stop: no calculations attempted
        return {
            "run_month": month,
            "validation_status": "invalid",
            "validation_errors": errors,
            "flagged_categories": [],
            "suppressed_categories": [],
            "escalated_categories": [],
            "action_taken": "hard_stop",
        }

    # Also validate baseline feed if present
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

    # -------------------------------------------------------------------------
    # Subtask 3 & 4: Load Feeds, Compute MoM & Apply Tri-State Flag Rule
    # -------------------------------------------------------------------------
    prev_data = _load_category_data(previous_month_csv)
    curr_data = _load_category_data(current_month_csv)

    flagged_candidates: List[Dict[str, Any]] = []
    escalated_categories: List[str] = []

    # Get prev_month name from baseline data if available
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

            # Subtask 3: compute MoM growth via Part 2 function
            pct = mom_growth(prev_rev, curr_rev)

            # Subtask 4: apply tri-state flag rule via Part 2 function
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
                # Subtask 8: separately record exact-boundary escalations
                escalated_categories.append(cat)
            # "not_flagged" items (e.g. Beauty in June) are intentionally ignored

    # -------------------------------------------------------------------------
    # Subtask 5: Sort flagged categories by absolute MoM percentage descending
    # -------------------------------------------------------------------------
    flagged_candidates.sort(key=lambda x: x["abs_mom_pct"], reverse=True)

    # -------------------------------------------------------------------------
    # Subtask 6 & 7: Draft at most top 3, suppress additional flagged categories
    # -------------------------------------------------------------------------
    top_3_candidates = flagged_candidates[:3]
    suppressed_candidates = flagged_candidates[3:]

    flagged_categories: List[Dict[str, Any]] = []
    for item in top_3_candidates:
        # Generate drafted message using Part 3 template
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

    # -------------------------------------------------------------------------
    # Subtask 9: Emit structured JSON adhering to the required schema
    # -------------------------------------------------------------------------
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
    # Internal validation execution
    import tempfile

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
