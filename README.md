# Meesho Reseller Growth & Alert Intelligence Pipeline

A code-first, reproducible intelligence pipeline designed to monitor reseller performance across high-velocity categories, enforce numeric guardrails, generate deterministic and auditable executive narratives, and drive agentic human-in-the-loop escalation workflows for Meesho's category operations.

---

## Overview

Modern e-commerce category operations require timely, auditable insights into category revenue movement without succumbing to alert flooding or unverified AI hallucinations. The **Meesho Reseller Growth & Alert Intelligence Pipeline** delivers an enterprise operational architecture divided into five stages:

$$\text{SQL Business Queries} \longrightarrow \text{Python Guardrails} \longrightarrow \text{AI Narrative Layer} \longrightarrow \text{Agent Planner} \longrightarrow \text{Human Approval Checkpoint}$$

1. **SQL Business Queries:** Ingests raw orders and reseller records into SQLite (`data/meesho_reseller.db`) to compute ground-truth aggregations, monthly category performance, regional contributions, zero-order inactive accounts, and Delivered Average Order Value (AOV).
2. **Python Guardrails:** Enforces row-level schema and non-negativity checks on incoming feeds (`validate_feed`), calculates exact Month-on-Month (MoM) growth percentages (`mom_growth`), and evaluates operational decision boundaries (`is_flagged`) using a tri-state classification (`"flagged"`, `"not_flagged"`, `"escalate_exact_boundary"`).
3. **AI Narrative Layer:** Translates flagged numerical variations into stakeholder updates structured around the **Context $\rightarrow$ Insight $\rightarrow$ Implication** framework. Strictly bifurcates ground-truth facts (`[Fact]`) from operational hypotheses (`[Hypothesis]`), masks merchant identities (`alias_for`), and asserts zero PII leaks (`assert_no_raw_names_leak`).
4. **Agent Workflow:** An 8-step guarded autonomous planner orchestrates feed intake, handles immediate hard stops on bad data, ranks flagged categories by absolute MoM growth magnitude, caps notification volume to the top 3 categories to prevent alert fatigue, logs suppressed items, and routes exact boundaries to escalation queues.
5. **Human Approval Checkpoint:** Every drafted alert payload is stamped with `action_taken: "drafted_and_held_for_approval"`. Zero notifications are dispatched autonomously to external channels.

---

## Repository Structure

```text
.
├── README.md                                 # Comprehensive pipeline documentation
├── run_e2e_verification.py                   # Automated 15-step end-to-end verification script
├── data/
│   ├── generate_dataset.py                   # Seeded deterministic dataset generator (PRNG seed 42)
│   ├── resellers.csv                         # Reseller directory (24 seeded resellers)
│   ├── orders.csv                            # Order transactions (900 orders across Apr, May, Jun 2026)
│   └── meesho_reseller.db                    # Relational SQLite database with resellers & orders tables
├── part1_sql/
│   ├── queries.sql                           # 5 analytical business SQL queries
│   └── output/
│       └── monthly_category_revenue.csv      # 15-row ground truth category revenue feed
├── part2_engine/
│   ├── growth_engine.py                      # Public engine: mom_growth, is_flagged, validate_feed
│   ├── test_growth_engine.py                 # Unit test suite verifying math, flags & fixtures
│   └── fixtures/
│       ├── corrupted_feed.csv                # Negative fixture containing 3 seeded line errors
│       └── monthly_category_revenue.csv      # Clean 15-row reference copy
├── part3_narrative/
│   ├── prompt_pack.md                        # Production prompt engineering specification (4 sections)
│   ├── narrative_report.md                   # Worked May & June narratives, self-evaluations & chart choices
│   └── masking.py                            # PII redaction (alias_for) & leak detection utilities
└── part4_agent/
    ├── agent_spec.md                         # 5-component agent architecture & guardrail specification
    └── mock_agent_runner.py                  # Guarded agent runner producing standardized JSON payloads
```

---

## Requirements

### Runtime & System Requirements
* **Python:** Standard Python 3.10+ (tested on Python 3.11 / 3.12).
* **Dependencies:** Zero third-party Python packages required. Uses standard library modules exclusively:
  * `sqlite3` for local relational queries.
  * `csv` for file intake, parsing, and serialization.
  * `json` for agent structured payload generation.
  * `unittest` for automated test execution.
  * `random` for seeded PRNG dataset creation.
* **Operating System:** Linux, macOS, or Windows (cross-platform path resolution via `os.path`).

---

## Part 1: Dataset Generation & SQL Queries

### Seeded Dataset Generator (`data/generate_dataset.py`)
Generates reproducible transaction data using `random.Random(42)`:
* **Resellers:** 24 resellers across 4 regions (`North`, `South`, `East`, `West`).
* **Orders:** 900 orders distributed equally across months:
  * April 2026: 300 orders
  * May 2026: 300 orders
  * June 2026: 300 orders
* **Category Price Ranges (INR):**
  * `Ethnic Wear`: 799.00 to 2499.00
  * `Western Wear`: 499.00 to 1899.00
  * `Kids Wear`: 299.00 to 1299.00
  * `Home & Kitchen`: 399.00 to 2999.00
  * `Beauty & Personal Care`: 199.00 to 999.00
* **Delivery Status Breakdown:** Delivered (75%), Shipped (15%), Cancelled (5%), Returned (5%).
* **Inactive Reseller Holdout:** `RS024` ("Ahmedabad Reseller 6", West) is strictly assigned 0 orders.
* **Database Target:** Automatically initializes schema and populates tables in `data/meesho_reseller.db`.

### Analytical SQL Queries (`part1_sql/queries.sql`)
1. **Monthly Revenue by Category:** Calculates `ROUND(SUM(quantity * unit_price), 2)` and `COUNT(*)` grouped by month and category. Exports to `part1_sql/output/monthly_category_revenue.csv` (15 rows).
2. **Region-Wise Revenue and Order Volume:** Joins orders to resellers, aggregating spend by geographic hub.
   * `North`: INR 337,125.46 (231 orders)
   * `West`: INR 333,106.33 (232 orders)
   * `South`: INR 316,736.68 (216 orders)
   * `East`: INR 275,098.45 (221 orders)
   * *Grand Total (All 900 Orders):* INR 1,262,066.92
3. **Top Resellers by Total Spend (`spend > 50,000`):**
   * `RS019` ("Mumbai Reseller 1"): INR 75,295.09
   * `RS022` ("Mumbai Reseller 4"): INR 73,882.33
   * `RS012` ("Hyderabad Reseller 6"): INR 69,936.46
   * `RS006` ("Lucknow Reseller 6"): INR 64,238.97
   * `RS005` ("Jaipur Reseller 5"): INR 61,825.02
4. **Resellers With Zero Orders (`LEFT JOIN` & `COUNT(*)` Demonstration):**
   * Unmatched record: `RS024` ("Ahmedabad Reseller 6").
   * Demonstrates why `COUNT(*)` returns `1` (counting the unmatched joined row) while `COUNT(o.order_id)` returns `0` (ignoring NULL values).
5. **June Delivered AOV:**
   * Filter: `month = 'June' AND status = 'Delivered'`.
   * Formula: `SUM(quantity * unit_price) / COUNT(*)`.
   * Result: **INR 1,267.69**.

---

## Part 2: Growth Engine, Flagging & Guardrails

Implemented in `part2_engine/growth_engine.py` with unit tests in `part2_engine/test_growth_engine.py`:

### Public Functions
1. `mom_growth(previous: float, current: float) -> float`
   * Computes: $\text{round}\left(\frac{\text{current} - \text{previous}}{\text{previous}} \times 100, 2\right)$
2. `is_flagged(mom_pct: float, threshold: float = 8.0) -> str`
   * Evaluates operational threshold using a tri-state decision rule:
     * `"flagged"` if $|mom\_pct| > 8.0$
     * `"not_flagged"` if $|mom\_pct| < 8.0$
     * `"escalate_exact_boundary"` if $|mom\_pct| == 8.0$ exactly (held for analyst review)
3. `validate_feed(csv_path: str) -> tuple[bool, list[str]]`
   * Row-level input guardrail reading line 2 onward (header = line 1).
   * Validates blank category, blank revenue, non-numeric revenue, and negative revenue values.
   * Preserves row encounter order in error strings. Returns `(True, [])` on clean feeds or `(False, errors)` on corrupted feeds.

### Corrupted Feed Fixture (`part2_engine/fixtures/corrupted_feed.csv`)
Produces exactly 3 ordered error lines:
1. `line 3: negative revenue (-4200.0) for category=Western Wear`
2. `line 4: missing category (month=July)`
3. `line 6: missing revenue (category=Home & Kitchen)`

### Benchmark MoM Growth Values
* **May 2026 vs. April 2026 (All 5 Categories Flagged):**
  * `Ethnic Wear`: $104,520.77 \rightarrow 185,107.61$ (**+77.10%**, `flagged`)
  * `Western Wear`: $113,866.15 \rightarrow 86,998.18$ (**-23.60%**, `flagged`)
  * `Kids Wear`: $59,847.27 \rightarrow 45,793.78$ (**-23.48%**, `flagged`)
  * `Beauty & Personal Care`: $40,737.01 \rightarrow 35,542.11$ (**-12.75%**, `flagged`)
  * `Home & Kitchen`: $100,446.23 \rightarrow 91,152.57$ (**-9.25%**, `flagged`)
* **June 2026 vs. May 2026 (4 of 5 Categories Flagged):**
  * `Ethnic Wear`: $185,107.61 \rightarrow 76,371.53$ (**-58.74%**, `flagged`)
  * `Home & Kitchen`: $91,152.57 \rightarrow 129,971.22$ (**+42.59%**, `flagged`)
  * `Kids Wear`: $45,793.78 \rightarrow 56,737.78$ (**+23.90%**, `flagged`)
  * `Western Wear`: $86,998.18 \rightarrow 97,415.64$ (**+11.97%**, `flagged`)
  * `Beauty & Personal Care`: $35,542.11 \rightarrow 37,559.07$ (**+5.67%**, `not_flagged`)

---

## Part 3: Narrative Layer, Epistemic Labeling & Masking

### Prompt Pack Architecture (`part3_narrative/prompt_pack.md`)
Structures executive summaries using 4 required sections:
1. **Trigger:** Activated strictly when `is_flagged(mom_pct) == "flagged"`.
2. **Input List:** Auditable bindings (`{category}`, `{month}`, `{prev_month}`, `{current_revenue}`, `{previous_revenue}`, `{mom_pct}`, `{n_orders}`, `{prev_n_orders}`).
3. **Prompt Template:** Demands the **Context $\rightarrow$ Insight $\rightarrow$ Implication** structure with zero invented figures.
4. **Refinement Checklist:** Evaluates Specificity, Audience Fit, Completeness, and Actionability.

### Epistemic Labeling Standards
* **`[Fact]`:** Explicitly tags database numbers, order volumes, and calculated growth rates.
* **`[Hypothesis]`:** Mandated for prospective operational causes (e.g., festive seasonality, catalog churn, wedding procurement).

### PII Redaction & Leakage Prevention (`part3_narrative/masking.py`)
* **Deterministic Alias Mapping:** `alias_for(reseller_id)` formats IDs as `ALIAS-{id[3:]}` (e.g., `RS019` $\rightarrow$ `ALIAS-19`, `RS006` $\rightarrow$ `ALIAS-06`).
* **Leak Detection:** `assert_no_raw_names_leak(text, reseller_names)` ensures zero raw merchant names appear verbatim in executive text.
* **Audit Scanner:** `detect_raw_leaks(text, names, ids)` returns line-level diagnostic tuples `(has_leaks, detected_tokens)`.

### Text-Only Chart Justifications
Documented in `part3_narrative/narrative_report.md`:
* **Highest Revenue Month:** Vertical Bar / Column Chart (bivariate discrete temporal comparison; Y-axis starts at zero; avoids 3D distortion).
* **Ethnic Wear Share of April Revenue (24.92%):** 100% Stacked Bar or 2D Donut Chart with direct callouts (part-to-whole univariate composition; reduces legend scanning).
* **Regional Revenue Comparison:** Sorted Horizontal Bar Chart (bivariate categorical ranking; legible labels; zero baseline).

---

## Part 4: Autonomous Agent Architecture & Guardrails

Documented in `part4_agent/agent_spec.md` and executed via `part4_agent/mock_agent_runner.py`:

### Five Core Components
1. **Goal:** Inform category managers of significant movements ($> \pm 8.00\%$) without alert fatigue.
2. **Tools:** Imports `validate_feed`, `mom_growth`, and `is_flagged` directly from `part2_engine.growth_engine` without reimplementing formulas. Imports `generate_narrative_block` from `part3_narrative.masking`.
3. **Memory / State:** Cross-month baseline tracking and intra-run execution state.
4. **Planner (8 Ordered Subtasks):**
   1. *Intake & Validation:* Run `validate_feed(current_month_csv)`.
   2. *Hard Stop Branch:* If invalid, halt immediately (`action_taken: "hard_stop"`).
   3. *Growth Computation:* Calculate `mom_growth(prev, curr)`.
   4. *Flag Classification:* Evaluate `is_flagged(pct, threshold=8.0)`.
   5. *Magnitude Sorting:* Sort flagged items descending by $|mom\_pct|$.
   6. *Draft Generation with Anti-Flooding Cap:* Draft narratives for at most the **top 3** items.
   7. *Suppression Logging:* Record remaining flagged categories beyond the top 3 in `suppressed_categories`.
   8. *Boundary Escalation:* Place exact 8.00% boundary cases in `escalated_categories`.
5. **Human Approval Gate:** All successful runs emit `action_taken: "drafted_and_held_for_approval"`. Zero notifications are sent automatically.

### Standardized JSON Output Schema
```json
{
  "run_month": "May",
  "validation_status": "valid",
  "validation_errors": [],
  "flagged_categories": [
    {
      "category": "Ethnic Wear",
      "mom_pct": 77.1,
      "previous_revenue": 104520.77,
      "current_revenue": 185107.61,
      "drafted": true,
      "message": "Context: ... Insight: [Fact] ... Implication: [Hypothesis] ..."
    }
  ],
  "suppressed_categories": [
    "Beauty & Personal Care",
    "Home & Kitchen"
  ],
  "escalated_categories": [],
  "action_taken": "drafted_and_held_for_approval"
}
```

---

## How to Run

Execute the pipeline in sequential order:

```bash
# 1. Generate the seeded dataset (data/resellers.csv, data/orders.csv, data/meesho_reseller.db)
python3 data/generate_dataset.py

# 2. Execute SQL analytical queries and create monthly_category_revenue.csv
python3 -c '
import sqlite3, csv
conn = sqlite3.connect("data/meesho_reseller.db")
cur = conn.cursor()
rows = cur.execute("""
SELECT month, category, ROUND(SUM(quantity * unit_price), 2) AS revenue, COUNT(*) AS n_orders
FROM orders
GROUP BY CASE month WHEN "April" THEN 1 WHEN "May" THEN 2 WHEN "June" THEN 3 END, month, category
""").fetchall()
with open("part1_sql/output/monthly_category_revenue.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["month", "category", "revenue", "n_orders"])
    for r in rows: w.writerow([r[0], r[1], f"{r[2]:.2f}", r[3]])
conn.close()
print("Generated part1_sql/output/monthly_category_revenue.csv")
'

# 3. Run Growth Engine unit tests
python3 -m unittest part2_engine/test_growth_engine.py -v

# 4. Verify Masking & Redaction assertions
python3 part3_narrative/masking.py

# 5. Run Mock Agent Runner for May, June, and Corrupted Feed scenarios
python3 part4_agent/mock_agent_runner.py
```

---

## Testing & Complete Verification

To run the automated 15-step end-to-end verification suite:

```bash
python3 run_e2e_verification.py
```

This script verifies every layer against the exact capstone acceptance criteria.

---

## End-to-End Pipeline Integration

$$\text{Part 1 (SQL)} \longrightarrow \text{Part 2 (Engine)} \longrightarrow \text{Part 3 (Narrative)} \longrightarrow \text{Part 4 (Agent)}$$

1. **Part 1 $\rightarrow$ Part 2:** Analytical SQL queries aggregate raw orders into `monthly_category_revenue.csv`. This CSV is passed directly to Part 2's `validate_feed()` before growth calculations begin.
2. **Part 2 $\rightarrow$ Part 3:** Part 2's `mom_growth()` and `is_flagged()` identify candidates that require narrative summaries. Ground-truth numbers are passed to Part 3's Context $\rightarrow$ Insight $\rightarrow$ Implication template, with merchant names sanitized via `alias_for()`.
3. **Part 3 $\rightarrow$ Part 4:** The agent uses Part 3's templating functions to generate draft messages for the top 3 flagged categories, ensuring that generated text contains zero unverified figures or raw merchant names.
4. **Part 4 (Guarded Completion):** The agent ranks categories by absolute magnitude, applies the top-3 cap, suppresses lower-priority alerts, isolates boundary cases, and outputs a structured JSON payload held for human approval.

---

## Zero API Key & Deterministic Execution Guarantee

* **100% Offline Operation:** This pipeline requires **zero external API keys**, paid credits, or third-party cloud services.
* **Deterministic Narrative Path:** All narrative generation runs through template-based slot filling and deterministic rule engines. Every test produces repeatable results across environments.

---

## Acceptance Criteria Checklist

All criteria have been executed and verified in the automated test suite:

- [x] **24 Resellers:** Generated in `data/resellers.csv` and `data/meesho_reseller.db`.
- [x] **900 Orders:** Exactly 300 orders in April, 300 in May, and 300 in June 2026.
- [x] **Five SQL Questions:** Implemented in `part1_sql/queries.sql` and verified against database output.
- [x] **Three Python Functions:** `mom_growth`, `is_flagged`, and `validate_feed` implemented in `growth_engine.py`.
- [x] **Corrupted Feed with 3 Errors:** `part2_engine/fixtures/corrupted_feed.csv` triggers lines 3, 4, and 6 in exact order.
- [x] **May & June Narratives:** Worked examples using Context $\rightarrow$ Insight $\rightarrow$ Implication with `[Fact]` and `[Hypothesis]` labels.
- [x] **Masking Tests:** `alias_for("RS019") == "ALIAS-19"`; positive test passes; negative test catches verbatim leaks.
- [x] **May Agent Scenario:** Top 3 drafted (Ethnic, Western, Kids), 2 suppressed (Beauty, Home).
- [x] **June Agent Scenario:** Top 3 drafted (Ethnic, Home, Kids), 1 suppressed (Western), Beauty omitted.
- [x] **Corrupted-Feed Hard Stop:** Returns `validation_status: "invalid"`, `action_taken: "hard_stop"`, and empty draft arrays.
- [x] **Exact JSON Schema:** Adheres to all 7 required top-level keys.
- [x] **Top-3 Notification Cap:** Enforces alert limits in high-volatility months to prevent fatigue.
- [x] **Exact-Boundary Escalation:** Routes exact 8.00% boundaries to `escalated_categories` for human review.
