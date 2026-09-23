# Executive Narrative Report & Analytical Justification

**File:** `part3_narrative/narrative_report.md`  
**Pipeline Stage:** Part 3 — Reliable AI Narrative Layer  
**Objective:** Deliver fully auditable, grounded executive narratives for May and June category performance movements, accompanied by 4-criterion refinement evaluations and rigorous chart-choice justifications.

---

## 1. Worked Narrative Blocks (Context → Insight → Implication)

### 1.1 Scenario A: May 2026 Ethnic Wear (+77.10% MoM, Flagged)

* **Context:**  
  During May 2026, Meesho's category operations evaluated the month-on-month revenue trajectory of the Ethnic Wear category, benchmarked against April 2026 performance across all four regional operating hubs.

* **Insight:**  
  **[Fact]** Ethnic Wear gross revenue increased from INR 104,520.77 (64 orders) in April 2026 to INR 185,107.61 (104 orders) in May 2026, representing an exact Month-on-Month growth of **+77.10%**. This movement exceeds the operational alert threshold of 8.00% and is officially categorized as `flagged`.

* **Implication:**  
  **[Hypothesis]** The sharp 77.10% surge in order volume may be driven by pre-festive wedding season procurement and early regional reseller promotional campaigns.  
  **Actionable Recommendation:** Category managers should immediately conduct a supplier inventory availability audit across high-performing North and West hubs to secure fast-moving SKU inventory, while verifying that active reseller fulfillment rates and delivery timelines remain within SLA.

#### Self-Score Refinement Checklist (May Narrative)
1. **Specificity:** Passes. Uses exact verified figures (INR 104,520.77 to INR 185,107.61, 64 to 104 orders, and +77.10% growth) without rounding distortions or invented values.
2. **Audience Fit:** Passes. Targeted directly at regional category managers with an operational focus on catalog availability and reseller fulfillment SLAs rather than low-level database queries.
3. **Completeness:** Passes. Explicitly includes all three required architectural blocks: Context, Insight, and Implication.
4. **Actionability:** Passes. Proposes an immediate, concrete inventory availability audit and fulfillment SLA check rather than passive observation.

---

### 1.2 Scenario B: June 2026 Ethnic Wear (-58.74% MoM, Flagged)

* **Context:**  
  Following the significant expansion observed in May, category management conducted a performance review of Ethnic Wear for June 2026 compared to the preceding May 2026 baseline.

* **Insight:**  
  **[Fact]** Ethnic Wear gross revenue contracted from INR 185,107.61 (104 orders) in May 2026 to INR 76,371.53 (52 orders) in June 2026, recording an exact Month-on-Month decline of **-58.74%**. This sharp contraction crosses the 8.00% threshold in the negative direction and is categorized as `flagged`.

* **Implication:**  
  **[Hypothesis]** The 58.74% contraction is likely a post-surge normalization following heavy reseller stocking in May, potentially aggravated by stockouts in key catalog lines.  
  **Actionable Recommendation:** The category operations team should review reseller catalog views, re-contact top-tier Ethnic Wear resellers in the North and West zones to inspect reorder drop-offs, and run targeted working-capital incentive banners on the reseller feed.

#### Self-Score Refinement Checklist (June Narrative)
1. **Specificity:** Passes. Specifies the exact verified revenue decline from INR 185,107.61 to INR 76,371.53 and exact MoM decline of -58.74%.
2. **Audience Fit:** Passes. Formatted cleanly for category leads with clear distinction between observed metrics and managerial remedies.
3. **Completeness:** Passes. Fully satisfies the Context → Insight → Implication structure with complete temporal benchmarks.
4. **Actionability:** Passes. Recommends explicit operational next steps including catalog drop-off analysis and targeted reseller engagement campaigns.

---

## 2. Full Month-over-Month Movement Benchmark Tables

### May 2026 vs. April 2026 Summary
* **Ethnic Wear:** INR 104,520.77 → INR 185,107.61 (**+77.10%**, Status: `flagged`)
* **Western Wear:** INR 113,866.15 → INR 86,998.18 (**-23.60%**, Status: `flagged`)
* **Kids Wear:** INR 59,847.27 → INR 45,793.78 (**-23.48%**, Status: `flagged`)
* **Home & Kitchen:** INR 100,446.23 → INR 91,152.57 (**-9.25%**, Status: `flagged`)
* **Beauty & Personal Care:** INR 40,737.01 → INR 35,542.11 (**-12.75%**, Status: `flagged`)
* *Summary:* All 5 categories exhibited movements exceeding the ±8.00% threshold and were classified as `flagged`.

### June 2026 vs. May 2026 Summary
* **Ethnic Wear:** INR 185,107.61 → INR 76,371.53 (**-58.74%**, Status: `flagged`)
* **Western Wear:** INR 86,998.18 → INR 97,415.64 (**+11.97%**, Status: `flagged`)
* **Kids Wear:** INR 45,793.78 → INR 56,737.78 (**+23.90%**, Status: `flagged`)
* **Home & Kitchen:** INR 91,152.57 → INR 129,971.22 (**+42.59%**, Status: `flagged`)
* **Beauty & Personal Care:** INR 35,542.11 → INR 37,559.07 (**+5.67%**, Status: `not_flagged`)
* *Summary:* Exactly 4 of 5 categories exceeded the threshold and were flagged; Beauty & Personal Care remained within the acceptable boundary (+5.67%) and was not flagged.

---

## 3. Chart-Choice Justifications (Text-Only, No Rendered Images)

Each recommendation is strictly justified using the univariate/bivariate/multivariate analytical framework, cognitive load constraints (under 10-second comprehension), zero-baseline requirements, and non-redundancy rules.

### Question 1: "Which month had the highest total revenue?"
* **Data Context:** April = INR 419,417.43; May = INR 444,594.25; June = INR 398,055.24 (Total across all 900 orders = INR 1,262,066.92).
* **Recommended Chart Type:** **Vertical Bar Chart (Column Chart)**.
* **Justification:**  
  This question requires a **bivariate discrete comparison** evaluating a single continuous metric (Total Revenue) across an ordered categorical dimension (Months: April, May, June). A vertical bar chart is optimal because the human eye compares discrete heights with high accuracy within 10 seconds. In alignment with chart selection principles:
  - The vertical Y-axis strictly starts at zero (INR 0.00) to avoid exaggerating differences between INR 398k and INR 444k.
  - 3D perspective and unnecessary gradients are omitted to prevent visual distortion.
  - Legends are avoided because there is only one data series, with month names labeled directly on the horizontal axis.

### Question 2: "What percentage share does Ethnic Wear represent of April's total revenue?"
* **Data Context:** Ethnic Wear = INR 104,520.77 out of April Total = INR 419,417.43 (**24.92%**).
* **Recommended Chart Type:** **100% Stacked Bar (or Donut Chart with Direct Value Callouts)**.
* **Justification:**  
  This is a **part-to-whole univariate composition analysis** answering what fraction of total revenue belongs to one segment. A single horizontal 100% stacked bar chart or a clean 2D donut chart with direct percentage annotations (`24.92%`) is ideal. Key principles enforced:
  - Avoids multi-slice 3D pie charts that distort proportional visual area.
  - The focused slice (Ethnic Wear) is highlighted while remaining categories are grouped or neutrally shaded, allowing the stakeholder to identify the ~25% contribution in under 5 seconds.
  - Direct data labeling eliminates the need for separate legend scanning.

### Question 3: "How do the four regions compare on total revenue?"
* **Data Context:** North = INR 337,125.46 (231 orders), West = INR 333,106.33 (232 orders), South = INR 316,736.68 (216 orders), East = INR 275,098.45 (221 orders).
* **Recommended Chart Type:** **Horizontal Bar Chart (Sorted Descending)**.
* **Justification:**  
  This represents a **bivariate categorical ranking analysis** comparing regional performance across unordered geographic entities. A horizontal bar chart sorted descending (North → West → South → East) is superior because:
  - Geographic category names are readable along the vertical axis without slanted text.
  - Ranking North as the leading region (INR 337.1k) and East as the trailing region (INR 275.1k) is immediately perceptible within 5 seconds.
  - The horizontal X-axis starts strictly at zero, preventing misinterpretation of the relatively balanced revenue distribution across regions.
  - A legend is omitted as only a single metric (Revenue) is displayed.

---

## 4. Top Reseller Performance Summary (PII-Masked)

Under enterprise confidentiality guidelines, raw merchant names are redacted. Reseller identifiers are transformed using `alias_for(reseller_id)`:

* **ALIAS-19 (Region: West):** Total Spend = INR 75,295.09
* **ALIAS-22 (Region: West):** Total Spend = INR 73,882.33
* **ALIAS-12 (Region: South):** Total Spend = INR 69,936.46
* **ALIAS-06 (Region: North):** Total Spend = INR 64,238.97
* **ALIAS-05 (Region: North):** Total Spend = INR 61,825.02

All five resellers exceeded the INR 50,000 threshold. The summary contains zero raw names, conforming to `assert_no_raw_names_leak()`.
