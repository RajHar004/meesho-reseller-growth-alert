"""
Unit Tests for Growth Engine & Guardrail Logic
==============================================
File: part2_engine/test_growth_engine.py

Verifies:
  1. April -> May Ethnic Wear growth & flagging
  2. May -> June Beauty & Personal Care growth & non-flagging
  3. Synthetic 8.00% exact boundary escalation
  4. Corrupted feed input guardrail error detection
  5. Full MoM tables for May vs April and June vs May
  6. Clean validation on genuine monthly_category_revenue.csv
"""

import os
import sys
import unittest

# Ensure current and parent directories are in sys.path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(BASE_DIR))
sys.path.insert(0, BASE_DIR)

from part2_engine.growth_engine import mom_growth, is_flagged, validate_feed


class TestGrowthEngine(unittest.TestCase):

    def test_case_1_april_to_may_ethnic_wear(self):
        """
        GIVEN April->May Ethnic Wear revenue moves from 104520.77 to 185107.61,
        WHEN mom_growth then is_flagged run on it,
        THEN mom_growth returns 77.1 and is_flagged returns 'flagged'.
        """
        previous = 104520.77
        current = 185107.61
        growth = mom_growth(previous, current)
        flag = is_flagged(growth)

        self.assertEqual(growth, 77.1, f"Expected 77.1, got {growth}")
        self.assertEqual(flag, "flagged", f"Expected 'flagged', got {flag}")

    def test_case_2_may_to_june_beauty_and_personal_care(self):
        """
        GIVEN May->June Beauty & Personal Care revenue moves from 35542.11 to 37559.07,
        WHEN evaluated,
        THEN mom_growth returns 5.67 and is_flagged returns 'not_flagged'.
        """
        previous = 35542.11
        current = 37559.07
        growth = mom_growth(previous, current)
        flag = is_flagged(growth)

        self.assertEqual(growth, 5.67, f"Expected 5.67, got {growth}")
        self.assertEqual(flag, "not_flagged", f"Expected 'not_flagged', got {flag}")

    def test_case_3_exact_boundary_escalation(self):
        """
        GIVEN a synthetic pair previous=100000, current=108000,
        WHEN evaluated,
        THEN mom_growth returns exactly 8.0 and is_flagged returns 'escalate_exact_boundary'.
        """
        previous = 100000.0
        current = 108000.0
        growth = mom_growth(previous, current)
        flag = is_flagged(growth)

        self.assertEqual(growth, 8.0, f"Expected 8.0, got {growth}")
        self.assertEqual(flag, "escalate_exact_boundary", f"Expected 'escalate_exact_boundary', got {flag}")

    def test_case_4_corrupted_feed_fixture(self):
        """
        GIVEN the corrupted feed fixture,
        WHEN validate_feed runs on it,
        THEN it returns (False, errors) where errors has exactly 3 entries matching required order.
        """
        fixture_path = os.path.join(BASE_DIR, "fixtures", "corrupted_feed.csv")
        valid, errors = validate_feed(fixture_path)

        self.assertFalse(valid, "Corrupted feed must return False.")
        expected_errors = [
            "line 3: negative revenue (-4200.0) for category=Western Wear",
            "line 4: missing category (month=July)",
            "line 6: missing revenue (category=Home & Kitchen)",
        ]
        self.assertEqual(errors, expected_errors, f"Error list mismatch.\nGot: {errors}\nExpected: {expected_errors}")

    def test_valid_feed_passes(self):
        """
        All 15 rows of monthly_category_revenue.csv pass validate_feed with zero errors.
        """
        fixture_path = os.path.join(BASE_DIR, "fixtures", "monthly_category_revenue.csv")
        valid, errors = validate_feed(fixture_path)
        self.assertTrue(valid, f"Expected valid feed, got errors: {errors}")
        self.assertEqual(errors, [], "Expected empty error list for valid feed.")

    def test_full_may_vs_april_mom_table(self):
        """
        Full May-vs-April MoM table verification:
          - Ethnic Wear: 77.1% (flagged)
          - Western Wear: -23.6% (flagged)
          - Kids Wear: -23.48% (flagged)
          - Home & Kitchen: -9.25% (flagged)
          - Beauty & Personal Care: -12.75% (flagged)
          -> every category is flagged in May.
        """
        may_vs_april = [
            ("Ethnic Wear", 104520.77, 185107.61, 77.1, "flagged"),
            ("Western Wear", 113866.15, 86998.18, -23.6, "flagged"),
            ("Kids Wear", 59847.27, 45793.78, -23.48, "flagged"),
            ("Home & Kitchen", 100446.23, 91152.57, -9.25, "flagged"),
            ("Beauty & Personal Care", 40737.01, 35542.11, -12.75, "flagged"),
        ]
        for cat, prev, curr, exp_pct, exp_flag in may_vs_april:
            pct = mom_growth(prev, curr)
            flag = is_flagged(pct)
            self.assertEqual(pct, exp_pct, f"{cat} MoM mismatch: {pct} vs {exp_pct}")
            self.assertEqual(flag, exp_flag, f"{cat} flag mismatch: {flag} vs {exp_flag}")

    def test_full_june_vs_may_mom_table(self):
        """
        Full June-vs-May MoM table verification:
          - Ethnic Wear: -58.74% (flagged)
          - Western Wear: 11.97% (flagged)
          - Kids Wear: 23.9% (flagged)
          - Home & Kitchen: 42.59% (flagged)
          - Beauty & Personal Care: 5.67% (not_flagged)
          -> exactly 4 of 5 categories flagged in June.
        """
        june_vs_may = [
            ("Ethnic Wear", 185107.61, 76371.53, -58.74, "flagged"),
            ("Western Wear", 86998.18, 97415.64, 11.97, "flagged"),
            ("Kids Wear", 45793.78, 56737.78, 23.9, "flagged"),
            ("Home & Kitchen", 91152.57, 129971.22, 42.59, "flagged"),
            ("Beauty & Personal Care", 35542.11, 37559.07, 5.67, "not_flagged"),
        ]
        flagged_count = 0
        for cat, prev, curr, exp_pct, exp_flag in june_vs_may:
            pct = mom_growth(prev, curr)
            flag = is_flagged(pct)
            self.assertEqual(pct, exp_pct, f"{cat} MoM mismatch: {pct} vs {exp_pct}")
            self.assertEqual(flag, exp_flag, f"{cat} flag mismatch: {flag} vs {exp_flag}")
            if flag == "flagged":
                flagged_count += 1
        self.assertEqual(flagged_count, 4, f"Expected exactly 4 flagged categories in June, got {flagged_count}")


if __name__ == "__main__":
    unittest.main()
