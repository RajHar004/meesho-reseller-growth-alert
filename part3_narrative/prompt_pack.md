# Reusable AI Narrative Prompt Pack

**File:** `part3_narrative/prompt_pack.md`  
**Purpose:** Reusable prompt engineering specification to transform verified category revenue metrics into stakeholder-ready executive updates without numeric invention or hallucination.

---

## 1. Trigger

The prompt is invoked **only** when a category's automated growth status is evaluated as significant:
* **Trigger Condition:** `is_flagged(mom_pct) == "flagged"` (i.e. `abs(mom_pct) > 8.0%`).
* Categories with status `"not_flagged"` are skipped to prevent executive notification flooding.
* Categories with status `"escalate_exact_boundary"` (exactly `8.0%`) are routed directly to human analytics review without automated narrative drafting.

---

## 2. Input List

Every input variable is strictly derived from the validated outputs of Part 1 (SQL aggregation) and Part 2 (Growth Engine). No outside variables or arbitrary user inputs may be introduced:

| Variable | Type | Description | Example |
| :--- | :--- | :--- | :--- |
| `{category}` | `string` | The official Meesho product category name | `"Ethnic Wear"` |
| `{month}` | `string` | Current reporting month | `"May"` |
| `{prev_month}` | `string` | Preceding baseline month | `"April"` |
| `{current_revenue}` | `float` | Verified revenue for the current month (INR) | `185107.61` |
| `{previous_revenue}` | `float` | Verified revenue for previous month (INR) | `104520.77` |
| `{mom_pct}` | `float` | Exact MoM growth computed via `mom_growth()` | `77.10` |
| `{n_orders}` | `integer` | Number of orders in the current month | `104` |
| `{prev_n_orders}` | `integer` | Number of orders in the previous month | `64` |

---

## 3. Prompt Specification

Below is the production prompt template containing bracketed placeholders:

```text
You are an operations intelligence analyst drafting an executive performance update for Meesho category managers.

Generate a concise, auditable update for category "{category}" for {month} compared against {prev_month}.

STRICT GROUNDING & INTEGRITY CONSTRAINTS:
1. Use ONLY the verified numeric parameters supplied below.
2. NEVER invent, extrapolate, or estimate any financial or order figures.
3. Every numeric statement must trace exactly back to the supplied numbers:
   - Category: {category}
   - Reporting Period: {month} 2026 vs. {prev_month} 2026
   - Current Month Revenue: INR {current_revenue:,.2f} ({n_orders} orders)
   - Baseline Month Revenue: INR {previous_revenue:,.2f} ({prev_n_orders} orders)
   - Month-on-Month Growth: {mom_pct:+.2f}%
4. STRUCTURE REQUIREMENTS:
   You must produce exactly three labeled paragraphs following the Context -> Insight -> Implication framework:
   - **Context**: State what product category is being evaluated, the exact comparison months ({month} vs. {prev_month}), and the baseline numbers.
   - **Insight**: State the exact month-on-month percentage movement and revenue change. Label all verified numbers explicitly with the tag [Fact].
   - **Implication**: Provide a concrete, highly actionable recommendation for category operations (e.g. catalog availability, supplier onboarding, pricing audit). If you propose any operational cause not explicitly proven by the dataset, you MUST label that explanation with the tag [Hypothesis]. Never make unsupported causal claims as facts.
5. PII CONSTRAINTS:
   Do not reference individual reseller names. If specific resellers must be cited, use only their masked coded identifiers (e.g., ALIAS-XX).
```

---

## 4. Refinement Checklist (Validation Checks)

Before any drafted narrative is presented to human reviewers or stored as an executive alert, it must pass all 4 automated and audit criteria:

1. **Exact Numeric Verification:**
   - *Check:* Does every number in the draft (percentages, currency figures, order volumes) match a supplied placeholder value exactly, down to the decimal point?
   - *Enforcement:* Fails if any figure cannot be matched to `{mom_pct}`, `{current_revenue}`, `{previous_revenue}`, or order counts.

2. **Epistemic Labeling (Fact vs. Hypothesis):**
   - *Check:* Are mathematical outcomes and database numbers explicitly labeled as `[Fact]`, and are external explanations or prospective operational drivers explicitly labeled as `[Hypothesis]`?
   - *Enforcement:* Fails if causal explanations (e.g., "seasonal demand", "festive sales", "supply shortages") are presented as proven truths without qualification.

3. **Actionability & Audience Fit:**
   - *Check:* Does the **Implication** section offer a specific operational next step that a Meesho category manager can execute within 48 hours (e.g., vendor re-engagement, stock audits, regional promotions), rather than vague guidance like "monitor closely"?
   - *Enforcement:* Fails if recommendations lack clear ownership or concrete action items.

4. **Confidentiality & PII Masking:**
   - *Check:* Are all resellers and partners referenced solely by their regional affiliation and sanitized alias (`alias_for(reseller_id)`), with zero raw reseller names appearing verbatim?
   - *Enforcement:* Evaluated via `assert_no_raw_names_leak(text, reseller_names)`. Fails if any merchant name is exposed.

---

## 5. Reference Benchmark Scenarios (May & June MoM)

The prompt pack is designed to process the following verified MoM movements from Part 1 and Part 2:

### May 2026 vs. April 2026 (All 5 Categories Flagged)
* **Ethnic Wear:** INR `104520.77` → INR `185107.61` | **`+77.10%`** (`flagged`)
* **Western Wear:** INR `113866.15` → INR `86998.18` | **`-23.60%`** (`flagged`)
* **Kids Wear:** INR `59847.27` → INR `45793.78` | **`-23.48%`** (`flagged`)
* **Home & Kitchen:** INR `100446.23` → INR `91152.57` | **`-9.25%`** (`flagged`)
* **Beauty & Personal Care:** INR `40737.01` → INR `35542.11` | **`-12.75%`** (`flagged`)

### June 2026 vs. May 2026 (4 of 5 Categories Flagged)
* **Ethnic Wear:** INR `185107.61` → INR `76371.53` | **`-58.74%`** (`flagged`)
* **Western Wear:** INR `86998.18` → INR `97415.64` | **`+11.97%`** (`flagged`)
* **Kids Wear:** INR `45793.78` → INR `56737.78` | **`+23.90%`** (`flagged`)
* **Home & Kitchen:** INR `91152.57` → INR `129971.22` | **`+42.59%`** (`flagged`)
* **Beauty & Personal Care:** INR `35542.11` → INR `37559.07` | **`+5.67%`** (`not_flagged`)
