# Meesho Reseller Growth & Alert Intelligence Agent — Architecture & Workflow Specification

**File:** `part4_agent/agent_spec.md`  
**System Role:** Autonomous, guarded operations intelligence agent for Meesho Category Operations  
**Design Philosophy:** Code-first, fully deterministic, zero-API-key architecture with human-in-the-loop review.

---

## 1. Five Core Agent Components

### 1.1 Goal
Keep Meesho category managers proactively informed of any product category whose month-on-month revenue moves beyond the ±8.00% operational threshold, guaranteeing that every numeric figure traces to ground truth, alert fatigue is prevented via priority capping, and no external alert is ever released without explicit human approval.

### 1.2 Tools
The agent imports and directly executes verified domain tools from upstream pipeline modules without reimplementing mathematics or validation rules:
1. `validate_feed(csv_path: str) -> tuple[bool, list[str]]` *(from `part2_engine.growth_engine`)*: Enforces row-level schema, numeric integrity, and non-negativity checks on incoming data feeds.
2. `mom_growth(previous: float, current: float) -> float` *(from `part2_engine.growth_engine`)*: Computes exact Month-on-Month growth percentage rounded to 2 decimal places.
3. `is_flagged(mom_pct: float, threshold: float = 8.0) -> str` *(from `part2_engine.growth_engine`)*: Evaluates whether growth is `"flagged"`, `"not_flagged"`, or lands on the exact boundary requiring escalation (`"escalate_exact_boundary"`).
4. `generate_narrative_block(...) -> str` *(from `part3_narrative.masking`)*: Fills the deterministic, offline Context → Insight → Implication executive narrative template.
5. `assert_no_raw_names_leak(...) -> bool` *(from `part3_narrative.masking`)*: Confirms that zero raw merchant or reseller names leak into drafted summaries.

### 1.3 Memory / State
* **Cross-Run Historical Baseline:** The agent maintains state of the preceding month's category revenue and order volume (e.g., April baseline when evaluating May; May baseline when evaluating June).
* **Execution Session State:** Tracks feed validation status, line-numbered validation errors, classified categories, suppressed items, escalated items, and drafted messages awaiting human review.

### 1.4 Planner (8 Ordered Subtasks)
The agent executes an explicit, numbered sequence of subtasks per monthly run:
1. **Subtask 1 (Intake & Validation):** Load current month CSV feed and execute `validate_feed(current_month_csv)`.
2. **Subtask 2 (Input Gate / Branching):** 
   - If invalid: Immediately trigger a **Hard Stop**, populate `validation_errors`, set `action_taken = "hard_stop"`, and emit the error JSON payload without attempting any calculation.
   - If valid: Proceed to Subtask 3.
3. **Subtask 3 (Mathematical Transformation):** For each category present in both baseline and current feeds, compute `mom_pct = mom_growth(previous_revenue, current_revenue)`.
4. **Subtask 4 (Boundary Classification):** Evaluate each category with `status = is_flagged(mom_pct, threshold=8.0)`.
5. **Subtask 5 (Magnitude Ranking):** Filter categories where `status == "flagged"` and sort them in descending order by absolute growth magnitude: `abs(mom_pct)`.
6. **Subtask 6 (Draft Generation with Anti-Flooding Cap):** For at most the **top 3** flagged categories by magnitude, set `drafted = true` and generate the Context → Insight → Implication narrative block using Part 3 templates.
7. **Subtask 7 (Suppression Management):** Log any remaining flagged categories beyond the top-3 cap into `suppressed_categories` with `drafted = false` and no generated message (labeling them for manual analyst review).
8. **Subtask 7b (Exact Boundary Escalation):** Categorize any item where `status == "escalate_exact_boundary"` into `escalated_categories` without automated message generation, holding it for human review.
9. **Subtask 8 (JSON Serialization & Review Gateway):** Assemble and emit the standardized JSON output schema, tagging `action_taken = "drafted_and_held_for_approval"`.

### 1.5 Feedback Loop (Human Approval Gate)
Under no circumstances does the agent dispatch emails, webhooks, or push notifications autonomously:
* Every drafted message remains in the `drafted_and_held_for_approval` state.
* A human category manager must review each drafted text block, verify the `[Fact]` and `[Hypothesis]` labels, and approve or reject the notification before simulated release.

---

## 2. Guardrail System Architecture

```
                    [ Incoming Monthly CSV Feed ]
                                  |
                                  v
        +---------------------------------------------------+
        |  INPUT GUARDRAIL: validate_feed(csv_path)        |
        +---------------------------------------------------+
               |                                     |
           [ Invalid ]                            [ Valid ]
               |                                     |
               v                                     v
     +-------------------+         +------------------------------------+
     |  HARD STOP        |         |  ACTION GUARDRAILS:                |
     |  action_taken:    |         |  1. Import Part 2 math unmodified  |
     |  "hard_stop"      |         |  2. Tri-state is_flagged(pct, 8.0) |
     |  Surfaces exact   |         |  3. Sort by abs(mom_pct) desc      |
     |  line errors      |         |  4. Cap drafts at Top 3            |
     +-------------------+         |  5. Suppress beyond Top 3          |
                                   |  6. Separate exact 8.00% boundary  |
                                   +------------------------------------+
                                                     |
                                                     v
                                   +------------------------------------+
                                   |  OUTPUT GUARDRAILS:                |
                                   |  1. Exact JSON Schema              |
                                   |  2. Zero auto-send                 |
                                   |  3. Held for Human Approval        |
                                   |  4. Zero invented numbers          |
                                   +------------------------------------+
```

### 2.1 Input Guardrail
* The feed file must be verified prior to parsing or metric calculation.
* Validates header structure (`month,category,revenue,n_orders`), missing categories, missing revenues, non-numeric revenue fields, and negative revenue values.
* If any violation is found, mathematical evaluation is skipped entirely.

### 2.2 Action Guardrails
* **No Mathematical Re-implementation:** The agent is forbidden from performing manual division or inline rounding; it must call `mom_growth` and `is_flagged` from `part2_engine.growth_engine`.
* **Eligibility Rule:** Only categories returning `is_flagged(mom_pct) == "flagged"` can be drafted. Unflagged categories (e.g., Beauty in June at `+5.67%`) are excluded from both drafts and suppression queues.
* **Notification-Flooding Cap:** In high-volatility months (such as May where all 5 categories are flagged), alert fatigue is prevented by drafting notifications for **at most 3 categories** sorted by `abs(mom_pct)` descending.
* **Suppression Logging:** Categories that qualify as flagged but rank 4th or 5th in magnitude are explicitly appended to `suppressed_categories`.
* **Exact Boundary Isolation:** Exactly `8.00%` transitions are placed into `escalated_categories` and never grouped with standard drafts or suppressed items.

### 2.3 Output Guardrails
* **Strict JSON Format:** The agent must always return the exact JSON schema defined in Section 4.
* **Zero Autonomous Transmission:** `action_taken` is set to `"drafted_and_held_for_approval"` (or `"hard_stop"`). No external communication API (Slack, Gmail, SMTP) is contacted.
* **Zero Numeric Invention:** Every number in the drafted message must originate from Part 1/Part 2 ground truth.

---

## 3. Success & Error Stopping Conditions

| Condition Type | Trigger Rule | Pipeline Behavior | Expected Action Taken |
| :--- | :--- | :--- | :--- |
| **Error Hard Stop** | `validate_feed() -> (False, errors)` | Halts pipeline immediately. No MoM math attempted. Emits line-level errors. | `"hard_stop"` |
| **Clean Success (Alerts Drafted)** | Valid feed; 1 to 5 categories flagged. | Computes MoM, ranks by magnitude, drafts top ≤ 3, logs remaining as suppressed. | `"drafted_and_held_for_approval"` |
| **Clean Success (Zero Alerts)** | Valid feed; 0 categories flagged. | Emits empty `flagged_categories` and `suppressed_categories`. | `"drafted_and_held_for_approval"` |
| **Boundary Escalation** | `abs(mom_pct) == 8.00` | Routes category to `escalated_categories`. No draft generated. | `"drafted_and_held_for_approval"` |

---

## 4. Structured JSON Output Schema

Every execution of the mock agent runner produces a JSON object conforming strictly to the following specification:

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
      "message": "Context: Evaluation of Ethnic Wear revenue for May 2026... Insight: [Fact]... Implication: [Hypothesis]..."
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

### Top-Level Key Definitions
* `run_month` (`string`): The current month under evaluation (`"May"`, `"June"`, or custom run month).
* `validation_status` (`string`): Either `"valid"` or `"invalid"`.
* `validation_errors` (`list[string]`): Empty on valid runs; contains line-indexed error strings upon validation failure.
* `flagged_categories` (`list[object]`): Sorted descending by `abs(mom_pct)`. Each entry contains `category`, `mom_pct`, `previous_revenue`, `current_revenue`, `drafted` (`true`), and the drafted `message`.
* `suppressed_categories` (`list[string]`): Names of flagged categories that exceeded the top-3 cap.
* `escalated_categories` (`list[string]`): Names of categories landing on exact boundary (`8.0%`).
* `action_taken` (`string`): Either `"drafted_and_held_for_approval"` or `"hard_stop"`.

---

## 5. Required Execution Scenarios (Given-When-Then Specs)

### Scenario 1: May 2026 Production Run (April → May Baseline)
* **GIVEN** April and May ground-truth revenue data where all 5 categories exceed the 8.0% threshold:
  - Ethnic Wear: `+77.10%`
  - Western Wear: `-23.60%`
  - Kids Wear: `-23.48%`
  - Beauty & Personal Care: `-12.75%`
  - Home & Kitchen: `-9.25%`
* **WHEN** the agent runner executes `run("May", "april_feed.csv", "may_feed.csv")`
* **THEN**:
  1. `validation_status` is `"valid"` and `validation_errors` is `[]`.
  2. `flagged_categories` contains exactly **3 drafted items** in strict order of `abs(mom_pct)`:
     1. Ethnic Wear (`77.1%`, `drafted = True`)
     2. Western Wear (`-23.6%`, `drafted = True`)
     3. Kids Wear (`-23.48%`, `drafted = True`)
  3. `suppressed_categories` contains exactly **2 items**:
     - `["Beauty & Personal Care", "Home & Kitchen"]` (or reverse order)
  4. `escalated_categories` is `[]`.
  5. `action_taken` is `"drafted_and_held_for_approval"`.

---

### Scenario 2: June 2026 Production Run (May → June Baseline)
* **GIVEN** May and June ground-truth revenue data where 4 categories exceed 8.0% and 1 category does not:
  - Ethnic Wear: `-58.74%` (flagged)
  - Home & Kitchen: `+42.59%` (flagged)
  - Kids Wear: `+23.90%` (flagged)
  - Western Wear: `+11.97%` (flagged)
  - Beauty & Personal Care: `+5.67%` (not flagged)
* **WHEN** the agent runner executes `run("June", "may_feed.csv", "june_feed.csv")`
* **THEN**:
  1. `validation_status` is `"valid"` and `validation_errors` is `[]`.
  2. `flagged_categories` contains exactly **3 drafted items** ordered by `abs(mom_pct)`:
     1. Ethnic Wear (`-58.74%`, `drafted = True`)
     2. Home & Kitchen (`42.59%`, `drafted = True`)
     3. Kids Wear (`23.9%`, `drafted = True`)
  3. `suppressed_categories` contains exactly **1 item**:
     - `["Western Wear"]`
  4. `Beauty & Personal Care` does not appear in `flagged_categories` or `suppressed_categories`.
  5. `escalated_categories` is `[]`.
  6. `action_taken` is `"drafted_and_held_for_approval"`.

---

### Scenario 3: Corrupted Feed Hard Stop
* **GIVEN** `part2_engine/fixtures/corrupted_feed.csv` as the current month feed:
  - Line 3: negative revenue (`-4200.0`) for Western Wear
  - Line 4: missing category for July
  - Line 6: missing revenue for Home & Kitchen
* **WHEN** the agent runner executes `run("July", "june_feed.csv", "corrupted_feed.csv")`
* **THEN**:
  1. `validation_status` is `"invalid"`.
  2. `action_taken` is `"hard_stop"`.
  3. `validation_errors` contains exactly the 3 ordered error strings:
     1. `"line 3: negative revenue (-4200.0) for category=Western Wear"`
     2. `"line 4: missing category (month=July)"`
     3. `"line 6: missing revenue (category=Home & Kitchen)"`
  4. `flagged_categories`, `suppressed_categories`, and `escalated_categories` are all empty `[]` (no calculations attempted on corrupted inputs).

---

### Scenario 4: Exact Boundary Synthetic Edge Case
* **GIVEN** a synthetic baseline feed where a category moves from INR 100,000.00 to INR 108,000.00 (exact +8.00% growth)
* **WHEN** the agent runner processes this transition
* **THEN**:
  1. `mom_growth` returns `8.0`.
  2. `is_flagged` returns `"escalate_exact_boundary"`.
  3. The category is routed directly to `escalated_categories`.
  4. No message is generated in `flagged_categories`, and it is not placed into `suppressed_categories`.
  5. `action_taken` is `"drafted_and_held_for_approval"`.
