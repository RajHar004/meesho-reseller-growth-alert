"""
Meesho Reseller Privacy & Masking Module
=========================================
File: part3_narrative/masking.py

Requirements Implemented:
  1. alias_for(reseller_id: str) -> str:
     - Returns f"ALIAS-{reseller_id[3:]}"
     - e.g. alias_for("RS019") == "ALIAS-19", alias_for("RS006") == "ALIAS-06"
  2. assert_no_raw_names_leak(text: str, reseller_names: list[str]) -> bool:
     - Returns False if any raw reseller_name string appears verbatim inside text.
  3. detect_raw_leaks(text: str, raw_names: list[str], raw_ids: list[str] | None = None) -> tuple[bool, list[str]]:
     - Detailed audit scanner detecting whether raw reseller names or raw IDs appear in external narrative.
  4. generate_narrative_block(...) -> str:
     - Deterministic offline template narrative generator with zero external API calls.
"""

from typing import Optional, List, Tuple


def alias_for(reseller_id: str) -> str:
    """
    Transforms a raw reseller ID into a privacy-safe alias.
    Requirement:
      alias_for("RS019") -> "ALIAS-19"
      alias_for("RS006") -> "ALIAS-06"
    """
    if str(reseller_id).startswith("RS"):
        return f"ALIAS-{reseller_id[3:]}"
    return f"ALIAS-{reseller_id}"


def assert_no_raw_names_leak(text: str, reseller_names: List[str]) -> bool:
    """
    Verifies that no raw reseller names appear verbatim in the target text.
    Returns:
      - False if any raw reseller name from the supplied list appears verbatim.
      - True if no leaks are detected.
    """
    if not text:
        return True
    for raw_name in reseller_names:
        if raw_name and raw_name in text:
            return False
    return True


def detect_raw_leaks(
    text: str,
    raw_names: List[str],
    raw_ids: Optional[List[str]] = None,
) -> Tuple[bool, List[str]]:
    """
    Scans an external narrative for any verbatim exposure of raw reseller names or IDs.
    Returns:
      (has_leaks: bool, detected_leaks: list[str])
    """
    detected: List[str] = []
    if not text:
        return (False, [])

    for name in raw_names:
        if name and name in text:
            detected.append(f"name:{name}")

    if raw_ids:
        for rid in raw_ids:
            if rid and rid in text:
                detected.append(f"id:{rid}")

    has_leaks = len(detected) > 0
    return (has_leaks, detected)


def generate_narrative_block(
    category: str,
    month: str,
    prev_month: str,
    prev_rev: float,
    curr_rev: float,
    mom_pct: float,
    n_orders: int,
    prev_n_orders: int = 0,
) -> str:
    """
    Deterministic, offline template-based narrative generator following
    the Context -> Insight -> Implication structure. Runs with zero API keys.
    """
    sign_str = "+" if mom_pct > 0 else ""
    direction = "expansion" if mom_pct > 0 else "contraction"

    hypotheses = {
        ("Ethnic Wear", True): "pre-festive regional wedding demand and festive catalog promotions",
        ("Ethnic Wear", False): "post-festive inventory normalization and selective stockouts in high-demand SKUs",
        ("Western Wear", True): "seasonal casualwear refresh and competitive fast-fashion pricing",
        ("Western Wear", False): "reseller margin compression and seasonal catalog churn",
        ("Kids Wear", True): "back-to-school purchasing cycles and active parent-network sharing",
        ("Kids Wear", False): "post-holiday order consolidation and lower repeat-order frequency",
        ("Home & Kitchen", True): "seasonal kitchen utility bundles and volume seller onboarding",
        ("Home & Kitchen", False): "category saturation following quarterly bulk procurement promotions",
        ("Beauty & Personal Care", True): "summer skincare campaign push and bundled personal care listings",
        ("Beauty & Personal Care", False): "reseller catalog rotation towards apparel categories",
    }

    hypo_reason = hypotheses.get(
        (category, mom_pct > 0),
        "shifts in regional reseller sharing activity and category catalog visibility",
    )

    action_items = {
        ("Ethnic Wear", True): "audit supplier stock levels in North and West hubs to maintain fulfillment SLA",
        ("Ethnic Wear", False): "inspect reseller catalog views and offer re-engagement incentive banners to active tier-1 sellers",
        ("Western Wear", True): "expand vendor partnerships in urban zones to support rising order volumes",
        ("Western Wear", False): "review pricing competitiveness against rival platforms and survey inactive apparel sellers",
        ("Kids Wear", True): "prioritize supplier fulfillment guarantees for bundle packs",
        ("Kids Wear", False): "re-engage inactive community resellers with curated value-pack catalogs",
        ("Home & Kitchen", True): "verify delivery logistics capacity for bulky cookware shipments",
        ("Home & Kitchen", False): "evaluate supplier minimum order quantities and discount thresholds",
        ("Beauty & Personal Care", True): "maintain fast-dispatch SLAs across top skincare assortments",
        ("Beauty & Personal Care", False): "review return rates and ensure freshness/expiry guidelines across active listings",
    }

    action_rec = action_items.get(
        (category, mom_pct > 0),
        "coordinate with regional category managers to evaluate catalog availability and reseller reorder rates",
    )

    narrative = (
        f"Context: Evaluation of {category} revenue for {month} 2026 benchmarked against {prev_month} 2026 baseline. "
        f"Insight: [Fact] {category} revenue moved from INR {prev_rev:.2f} ({prev_n_orders} orders) in {prev_month} "
        f"to INR {curr_rev:.2f} ({n_orders} orders) in {month}, recording an exact Month-on-Month growth of {sign_str}{mom_pct:.2f}%. "
        f"Implication: [Hypothesis] The observed {direction} is likely associated with {hypo_reason}. "
        f"Actionable Recommendation: Category managers should {action_rec}."
    )
    return narrative


if __name__ == "__main__":
    # Built-in verification tests
    assert alias_for("RS019") == "ALIAS-19"
    assert alias_for("RS006") == "ALIAS-06"
    assert alias_for("RS024") == "ALIAS-24"

    raw_test_names = ["Mumbai Reseller 1", "Mumbai Reseller 4"]
    raw_test_ids = ["RS019", "RS022"]

    # Positive test: masked text has no leaks
    clean_text = "Top seller ALIAS-19 located in West zone achieved INR 75295.09 in gross spend."
    assert assert_no_raw_names_leak(clean_text, raw_test_names) is True
    leaks_found, leak_list = detect_raw_leaks(clean_text, raw_test_names, raw_test_ids)
    assert leaks_found is False
    assert leak_list == []

    # Negative test: raw name leak detected
    leaked_name_text = "Top seller Mumbai Reseller 1 in West achieved INR 75295.09 in gross spend."
    assert assert_no_raw_names_leak(leaked_name_text, raw_test_names) is False
    leaks_found, leak_list = detect_raw_leaks(leaked_name_text, raw_test_names, raw_test_ids)
    assert leaks_found is True
    assert "name:Mumbai Reseller 1" in leak_list

    # Negative test: raw id leak detected
    leaked_id_text = "Top seller RS019 in West achieved INR 75295.09 in gross spend."
    leaks_found, leak_list = detect_raw_leaks(leaked_id_text, raw_test_names, raw_test_ids)
    assert leaks_found is True
    assert "id:RS019" in leak_list

    print("All masking assertions and leak detection tests passed successfully.")
