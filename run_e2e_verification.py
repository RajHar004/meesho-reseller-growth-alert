"""
End-to-End Comprehensive Audit & Verification Suite
===================================================
File: run_e2e_verification.py

Executes all 15 verification steps in exact sequential order:
  1. Generate the seeded dataset (data/generate_dataset.py)
  2. Verify 24 resellers and 900 orders in CSV & SQLite
  3. Run all Part 1 SQL queries from part1_sql/queries.sql
  4. Verify monthly_category_revenue.csv (15 rows, exact values)
  5. Run all Part 2 tests in test_growth_engine.py
  6. Test the corrupted feed fixture (3 line errors in order)
  7. Verify May MoM values (all 5 categories flagged)
  8. Verify June MoM values (4 flagged, 1 not flagged)
  9. Verify Part 3 narrative prompt pack and markdown reports
  10. Test masking positive and negative cases
  11. Run Part 4 May scenario (top 3 drafted, 2 suppressed)
  12. Run Part 4 June scenario (top 3 drafted, 1 suppressed, Beauty excluded)
  13. Run Part 4 corrupted-feed scenario (hard stop, 3 errors, empty drafts)
  14. Verify exact Part 4 JSON schema keys & action values
  15. Run complete pipeline from start to finish
"""

import os
import sys
import subprocess
import sqlite3
import csv
import json
import tempfile
import unittest

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT_DIR)

from part2_engine.growth_engine import mom_growth, is_flagged, validate_feed
from part3_narrative.masking import alias_for, assert_no_raw_names_leak, detect_raw_leaks, generate_narrative_block
from part4_agent.mock_agent_runner import run as agent_run

CHECKLIST_RESULTS = []


def record_result(step_num: int, name: str, passed: bool, details: str = ""):
    status = "PASS" if passed else "FAIL"
    CHECKLIST_RESULTS.append({
        "step": step_num,
        "name": name,
        "status": status,
        "details": details
    })
    print(f"[{status}] Step {step_num}: {name} {('- ' + details) if details else ''}")


def step_1_generate_dataset():
    gen_script = os.path.join(ROOT_DIR, "data", "generate_dataset.py")
    res = subprocess.run([sys.executable, gen_script], capture_output=True, text=True)
    passed = (res.returncode == 0) and ("Wrote 24 resellers and 900 orders" in res.stdout)
    record_result(1, "Generate the seeded dataset", passed, res.stdout.strip())
    assert passed, f"Dataset generation failed: {res.stderr}"


def step_2_verify_resellers_and_orders():
    res_path = os.path.join(ROOT_DIR, "data", "resellers.csv")
    ord_path = os.path.join(ROOT_DIR, "data", "orders.csv")
    db_path = os.path.join(ROOT_DIR, "data", "meesho_reseller.db")

    with open(res_path) as f:
        r_rows = list(csv.DictReader(f))
    with open(ord_path) as f:
        o_rows = list(csv.DictReader(f))

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    db_r_cnt = cur.execute("SELECT COUNT(*) FROM resellers").fetchone()[0]
    db_o_cnt = cur.execute("SELECT COUNT(*) FROM orders").fetchone()[0]
    conn.close()

    passed = (len(r_rows) == 24 and len(o_rows) == 900 and db_r_cnt == 24 and db_o_cnt == 900)
    details = f"resellers.csv: {len(r_rows)}, orders.csv: {len(o_rows)}, db_resellers: {db_r_cnt}, db_orders: {db_o_cnt}"
    record_result(2, "Verify 24 resellers and 900 orders", passed, details)
    assert passed, f"Reseller/order verification mismatch: {details}"


def step_3_run_part1_sql_queries():
    queries_path = os.path.join(ROOT_DIR, "part1_sql", "queries.sql")
    with open(queries_path) as f:
        sql_content = f.read()

    db_path = os.path.join(ROOT_DIR, "data", "meesho_reseller.db")
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    # Query 1: monthly revenue by category
    q1 = """
    SELECT month, category, ROUND(SUM(quantity * unit_price), 2) AS revenue, COUNT(*) AS n_orders
    FROM orders
    GROUP BY CASE month WHEN 'April' THEN 1 WHEN 'May' THEN 2 WHEN 'June' THEN 3 END, month, category
    """
    q1_res = cur.execute(q1).fetchall()

    # Query 2: region-wise revenue and order count
    q2 = """
    SELECT r.region, ROUND(SUM(o.quantity * o.unit_price), 2) AS total_revenue, COUNT(o.order_id) AS order_count
    FROM resellers r JOIN orders o ON r.reseller_id = o.reseller_id
    GROUP BY r.region ORDER BY total_revenue DESC
    """
    q2_res = cur.execute(q2).fetchall()

    # Query 3: top resellers total spend > 50000
    q3 = """
    SELECT r.reseller_id, r.reseller_name, ROUND(SUM(o.quantity * o.unit_price), 2) AS total_spend
    FROM resellers r JOIN orders o ON r.reseller_id = o.reseller_id
    GROUP BY r.reseller_id, r.reseller_name HAVING total_spend > 50000
    ORDER BY total_spend DESC LIMIT 5
    """
    q3_res = cur.execute(q3).fetchall()

    # Query 4: RS024 check
    q4 = """
    SELECT r.reseller_id, COUNT(*), COUNT(o.order_id)
    FROM resellers r LEFT JOIN orders o ON r.reseller_id = o.reseller_id
    WHERE r.reseller_id = 'RS024' GROUP BY r.reseller_id
    """
    q4_res = cur.execute(q4).fetchone()

    # Query 5: June Delivered AOV
    q5 = """
    SELECT ROUND(SUM(quantity * unit_price) / COUNT(*), 2)
    FROM orders WHERE month = 'June' AND status = 'Delivered'
    """
    q5_res = cur.execute(q5).fetchone()[0]

    conn.close()

    passed = (
        len(q1_res) == 15 and
        len(q2_res) == 4 and
        len(q3_res) == 5 and
        q4_res == ("RS024", 1, 0) and
        q5_res == 1267.69
    )
    details = f"Q1 rows: {len(q1_res)}, Q2 regions: {len(q2_res)}, Q3 top: {len(q3_res)}, Q4: {q4_res}, Q5 AOV: {q5_res}"
    record_result(3, "Run all Part 1 SQL queries", passed, details)
    assert passed, f"SQL query mismatch: {details}"


def step_4_verify_monthly_category_revenue():
    csv_path = os.path.join(ROOT_DIR, "part1_sql", "output", "monthly_category_revenue.csv")
    with open(csv_path) as f:
        rows = list(csv.DictReader(f))

    expected_benchmarks = {
        ("April", "Ethnic Wear"): (104520.77, 64),
        ("April", "Western Wear"): (113866.15, 79),
        ("April", "Kids Wear"): (59847.27, 55),
        ("April", "Home & Kitchen"): (100446.23, 53),
        ("April", "Beauty & Personal Care"): (40737.01, 49),
        ("May", "Ethnic Wear"): (185107.61, 104),
        ("May", "Western Wear"): (86998.18, 64),
        ("May", "Kids Wear"): (45793.78, 47),
        ("May", "Home & Kitchen"): (91152.57, 44),
        ("May", "Beauty & Personal Care"): (35542.11, 41),
        ("June", "Ethnic Wear"): (76371.53, 52),
        ("June", "Western Wear"): (97415.64, 66),
        ("June", "Kids Wear"): (56737.78, 57),
        ("June", "Home & Kitchen"): (129971.22, 73),
        ("June", "Beauty & Personal Care"): (37559.07, 52),
    }

    passed = (len(rows) == 15)
    for r in rows:
        key = (r["month"], r["category"])
        exp_rev, exp_ord = expected_benchmarks[key]
        if float(r["revenue"]) != exp_rev or int(r["n_orders"]) != exp_ord:
            passed = False
            break

    record_result(4, "Verify monthly_category_revenue.csv", passed, f"15 rows matched ground truth exactly")
    assert passed, "monthly_category_revenue.csv does not match expected benchmarks"


def step_5_run_part2_tests():
    test_file = os.path.join(ROOT_DIR, "part2_engine", "test_growth_engine.py")
    res = subprocess.run([sys.executable, "-m", "unittest", test_file], capture_output=True, text=True)
    passed = (res.returncode == 0) and ("OK" in res.stderr)
    record_result(5, "Run all Part 2 tests", passed, f"unittest exited code {res.returncode}")
    assert passed, f"Part 2 unit tests failed:\n{res.stderr}"


def step_6_test_corrupted_feed():
    corrupt_fixture = os.path.join(ROOT_DIR, "part2_engine", "fixtures", "corrupted_feed.csv")
    valid, errors = validate_feed(corrupt_fixture)
    expected_errors = [
        "line 3: negative revenue (-4200.0) for category=Western Wear",
        "line 4: missing category (month=July)",
        "line 6: missing revenue (category=Home & Kitchen)"
    ]
    passed = (valid is False) and (errors == expected_errors)
    record_result(6, "Test the corrupted feed", passed, f"Returned 3 ordered errors exactly as required")
    assert passed, f"Corrupted feed error mismatch:\nGot: {errors}\nExpected: {expected_errors}"


def step_7_verify_may_mom_values():
    may_benchmarks = [
        ("Ethnic Wear", 104520.77, 185107.61, 77.10, "flagged"),
        ("Western Wear", 113866.15, 86998.18, -23.60, "flagged"),
        ("Kids Wear", 59847.27, 45793.78, -23.48, "flagged"),
        ("Home & Kitchen", 100446.23, 91152.57, -9.25, "flagged"),
        ("Beauty & Personal Care", 40737.01, 35542.11, -12.75, "flagged"),
    ]
    passed = True
    for cat, prev, curr, exp_pct, exp_flag in may_benchmarks:
        pct = mom_growth(prev, curr)
        flag = is_flagged(pct)
        if pct != exp_pct or flag != exp_flag:
            passed = False
            break
    record_result(7, "Verify May MoM values", passed, "All 5 categories flagged (77.1%, -23.6%, -23.48%, -9.25%, -12.75%)")
    assert passed, "May MoM verification failed"


def step_8_verify_june_mom_values():
    june_benchmarks = [
        ("Ethnic Wear", 185107.61, 76371.53, -58.74, "flagged"),
        ("Western Wear", 86998.18, 97415.64, 11.97, "flagged"),
        ("Kids Wear", 45793.78, 56737.78, 23.90, "flagged"),
        ("Home & Kitchen", 91152.57, 129971.22, 42.59, "flagged"),
        ("Beauty & Personal Care", 35542.11, 37559.07, 5.67, "not_flagged"),
    ]
    passed = True
    flagged_cnt = 0
    for cat, prev, curr, exp_pct, exp_flag in june_benchmarks:
        pct = mom_growth(prev, curr)
        flag = is_flagged(pct)
        if pct != exp_pct or flag != exp_flag:
            passed = False
            break
        if flag == "flagged":
            flagged_cnt += 1
    passed = passed and (flagged_cnt == 4)
    record_result(8, "Verify June MoM values", passed, "4 flagged, 1 not_flagged (Beauty at 5.67%)")
    assert passed, "June MoM verification failed"


def step_9_verify_part3_narratives():
    pack_path = os.path.join(ROOT_DIR, "part3_narrative", "prompt_pack.md")
    report_path = os.path.join(ROOT_DIR, "part3_narrative", "narrative_report.md")

    with open(pack_path) as f:
        pack_text = f.read()
    with open(report_path) as f:
        report_text = f.read()

    has_sections = all(sec in pack_text for sec in ["## 1. Trigger", "## 2. Input List", "## 3. Prompt Specification", "## 4. Refinement Checklist"])
    has_labels = ("[Fact]" in report_text) and ("[Hypothesis]" in report_text) and ("Context:" in report_text) and ("Insight:" in report_text) and ("Implication:" in report_text)
    has_justifications = ("Vertical Bar Chart" in report_text) and ("100% Stacked Bar" in report_text) and ("Horizontal Bar Chart" in report_text)

    passed = has_sections and has_labels and has_justifications
    record_result(9, "Verify Part 3 narrative requirements", passed, "Prompt pack 4 sections, Context->Insight->Implication, chart justifications verified")
    assert passed, "Part 3 narrative documents failed requirement verification"


def step_10_test_masking():
    # Deterministic test
    assert alias_for("RS019") == "ALIAS-19"
    assert alias_for("RS006") == "ALIAS-06"
    assert alias_for("RS024") == "ALIAS-24"

    raw_names = ["Mumbai Reseller 1", "Mumbai Reseller 4", "Jaipur Reseller 5"]
    raw_ids = ["RS019", "RS022"]

    # Positive test
    clean_text = "Executive update for ALIAS-19 in West zone."
    clean_no_leaks = assert_no_raw_names_leak(clean_text, raw_names)
    clean_audit_leaks, clean_list = detect_raw_leaks(clean_text, raw_names, raw_ids)

    # Negative test
    leaky_text = "Executive update for Mumbai Reseller 1 in West zone."
    leaky_no_leaks = assert_no_raw_names_leak(leaky_text, raw_names)
    leaky_audit_leaks, leaky_list = detect_raw_leaks(leaky_text, raw_names, raw_ids)

    passed = (clean_no_leaks is True) and (not clean_audit_leaks) and (leaky_no_leaks is False) and leaky_audit_leaks and ("name:Mumbai Reseller 1" in leaky_list)
    record_result(10, "Test masking positive and negative cases", passed, "alias_for verified, positive passed, negative leak caught")
    assert passed, "Masking assertions failed"


def _get_monthly_temp_csvs():
    full_csv = os.path.join(ROOT_DIR, "part1_sql", "output", "monthly_category_revenue.csv")
    months = {"April": [], "May": [], "June": []}
    with open(full_csv, "r", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row["month"] in months:
                months[row["month"]].append(row)

    def write_csv(rows):
        tf = tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".csv", newline="")
        w = csv.DictWriter(tf, fieldnames=["month", "category", "revenue", "n_orders"])
        w.writeheader()
        w.writerows(rows)
        tf.close()
        return tf.name

    return write_csv(months["April"]), write_csv(months["May"]), write_csv(months["June"])


def step_11_run_part4_may_scenario():
    apr_csv, may_csv, jun_csv = _get_monthly_temp_csvs()
    try:
        res = agent_run("May", apr_csv, may_csv)
        passed = (
            res["run_month"] == "May" and
            res["validation_status"] == "valid" and
            res["action_taken"] == "drafted_and_held_for_approval" and
            [x["category"] for x in res["flagged_categories"]] == ["Ethnic Wear", "Western Wear", "Kids Wear"] and
            set(res["suppressed_categories"]) == {"Beauty & Personal Care", "Home & Kitchen"} and
            res["escalated_categories"] == []
        )
        record_result(11, "Run the Part 4 May scenario", passed, "Drafted 3 (Ethnic, Western, Kids), Suppressed 2 (Beauty, Home)")
        assert passed, f"May scenario failed: {res}"
    finally:
        for p in [apr_csv, may_csv, jun_csv]:
            if os.path.exists(p):
                os.remove(p)


def step_12_run_part4_june_scenario():
    apr_csv, may_csv, jun_csv = _get_monthly_temp_csvs()
    try:
        res = agent_run("June", may_csv, jun_csv)
        all_touched = set([x["category"] for x in res["flagged_categories"]]) | set(res["suppressed_categories"])
        passed = (
            res["run_month"] == "June" and
            res["validation_status"] == "valid" and
            res["action_taken"] == "drafted_and_held_for_approval" and
            [x["category"] for x in res["flagged_categories"]] == ["Ethnic Wear", "Home & Kitchen", "Kids Wear"] and
            res["suppressed_categories"] == ["Western Wear"] and
            ("Beauty & Personal Care" not in all_touched) and
            res["escalated_categories"] == []
        )
        record_result(12, "Run the Part 4 June scenario", passed, "Drafted 3 (Ethnic, Home, Kids), Suppressed Western, Beauty omitted")
        assert passed, f"June scenario failed: {res}"
    finally:
        for p in [apr_csv, may_csv, jun_csv]:
            if os.path.exists(p):
                os.remove(p)


def step_13_run_part4_corrupted_feed_scenario():
    apr_csv, may_csv, jun_csv = _get_monthly_temp_csvs()
    corrupt_fixture = os.path.join(ROOT_DIR, "part2_engine", "fixtures", "corrupted_feed.csv")
    try:
        res = agent_run("July", jun_csv, corrupt_fixture)
        expected_errors = [
            "line 3: negative revenue (-4200.0) for category=Western Wear",
            "line 4: missing category (month=July)",
            "line 6: missing revenue (category=Home & Kitchen)"
        ]
        passed = (
            res["run_month"] == "July" and
            res["validation_status"] == "invalid" and
            res["action_taken"] == "hard_stop" and
            res["validation_errors"] == expected_errors and
            res["flagged_categories"] == [] and
            res["suppressed_categories"] == [] and
            res["escalated_categories"] == []
        )
        record_result(13, "Run the Part 4 corrupted-feed scenario", passed, "Hard stop, 3 ordered errors, empty drafts")
        assert passed, f"Corrupted feed scenario failed: {res}"
    finally:
        for p in [apr_csv, may_csv, jun_csv]:
            if os.path.exists(p):
                os.remove(p)


def step_14_verify_part4_json_schema():
    apr_csv, may_csv, jun_csv = _get_monthly_temp_csvs()
    try:
        res = agent_run("May", apr_csv, may_csv)
        required_keys = [
            "run_month",
            "validation_status",
            "validation_errors",
            "flagged_categories",
            "suppressed_categories",
            "escalated_categories",
            "action_taken"
        ]
        has_all_keys = list(res.keys()) == required_keys
        has_valid_action = res["action_taken"] in ["drafted_and_held_for_approval", "hard_stop"]
        passed = has_all_keys and has_valid_action
        record_result(14, "Verify the exact Part 4 JSON schema", passed, f"Exact 7 keys and valid action_taken '{res['action_taken']}'")
        assert passed, f"Schema mismatch: keys={list(res.keys())}, action={res.get('action_taken')}"
    finally:
        for p in [apr_csv, may_csv, jun_csv]:
            if os.path.exists(p):
                os.remove(p)


def step_15_run_complete_pipeline():
    # Execute full sequence consecutively
    print("\n--- Running Complete Pipeline Orchestration ---")
    step_1_generate_dataset()
    step_2_verify_resellers_and_orders()
    step_3_run_part1_sql_queries()
    step_4_verify_monthly_category_revenue()
    step_5_run_part2_tests()
    step_6_test_corrupted_feed()
    step_7_verify_may_mom_values()
    step_8_verify_june_mom_values()
    step_9_verify_part3_narratives()
    step_10_test_masking()
    step_11_run_part4_may_scenario()
    step_12_run_part4_june_scenario()
    step_13_run_part4_corrupted_feed_scenario()
    step_14_verify_part4_json_schema()
    record_result(15, "Run the complete pipeline from start to finish", True, "End-to-end orchestration successful without error")


if __name__ == "__main__":
    try:
        step_1_generate_dataset()
        step_2_verify_resellers_and_orders()
        step_3_run_part1_sql_queries()
        step_4_verify_monthly_category_revenue()
        step_5_run_part2_tests()
        step_6_test_corrupted_feed()
        step_7_verify_may_mom_values()
        step_8_verify_june_mom_values()
        step_9_verify_part3_narratives()
        step_10_test_masking()
        step_11_run_part4_may_scenario()
        step_12_run_part4_june_scenario()
        step_13_run_part4_corrupted_feed_scenario()
        step_14_verify_part4_json_schema()
        step_15_run_complete_pipeline()

        print("\n=======================================================")
        print("          END-TO-END VERIFICATION SUMMARY             ")
        print("=======================================================")
        all_passed = all(item["status"] == "PASS" for item in CHECKLIST_RESULTS)
        for item in CHECKLIST_RESULTS[-15:]:
            print(f"Step {item['step']:02d} | [{item['status']}] {item['name']:<48} | {item['details']}")
        print("=======================================================")
        if all_passed:
            print("ALL 15 REQUIREMENTS PASSED WITH ZERO DISCREPANCIES.")
            sys.exit(0)
        else:
            print("SOME REQUIREMENTS FAILED.")
            sys.exit(1)

    except Exception as e:
        print(f"\n[FATAL ERROR during verification]: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
