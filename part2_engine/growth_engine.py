"""
Meesho Reseller Growth & Alert Intelligence Pipeline - Growth Engine & Guardrail Module
========================================================================================
File: part2_engine/growth_engine.py

Public Functions:
  1. mom_growth(previous: float, current: float) -> float
  2. is_flagged(mom_pct: float, threshold: float = 8.0) -> str
  3. validate_feed(csv_path: str) -> tuple[bool, list[str]]
"""

import csv


def mom_growth(previous: float, current: float) -> float:
    """
    Computes Month-on-Month growth percentage:
    round((current - previous) / previous * 100, 2)
    """
    if previous == 0:
        raise ValueError("previous revenue cannot be zero for MoM calculation.")
    return round((current - previous) / previous * 100, 2)


def is_flagged(mom_pct: float, threshold: float = 8.0) -> str:
    """
    Evaluates whether a Month-on-Month growth percentage represents a significant change:
      - "flagged" if abs(mom_pct) > threshold
      - "not_flagged" if abs(mom_pct) < threshold
      - "escalate_exact_boundary" if abs(mom_pct) == threshold exactly
    """
    abs_pct = abs(mom_pct)
    # Using a small tolerance for floating point exact equality comparison
    if abs(abs_pct - threshold) < 1e-9:
        return "escalate_exact_boundary"
    elif abs_pct > threshold:
        return "flagged"
    else:
        return "not_flagged"


def validate_feed(csv_path: str) -> tuple[bool, list[str]]:
    """
    Input guardrail over a month,category,revenue,n_orders CSV.
    For every data row (line 2 onward, 1-indexed with the header as line 1):
      - if category is blank: append "line {N}: missing category (month={month})"
      - if revenue is blank: append "line {N}: missing revenue (category={category})"
      - if revenue is present but not parseable as a float: append "line {N}: revenue not numeric: {revenue!r}"
      - if revenue parses but is negative: append "line {N}: negative revenue ({parsed_val}) for category={category}"

    Returns (True, []) only if there are zero errors, else (False, errors).
    Preserves row encounter order in validation errors.
    """
    errors: list[str] = []

    with open(csv_path, mode="r", newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        try:
            header = next(reader)
        except StopIteration:
            return (False, ["Feed file is empty."])

        # Find column indices if standard header, or default to 0, 1, 2, 3
        # Standard columns: month, category, revenue, n_orders
        col_map = {col.strip().lower(): idx for idx, col in enumerate(header)}
        month_idx = col_map.get("month", 0)
        cat_idx = col_map.get("category", 1)
        rev_idx = col_map.get("revenue", 2)

        for line_num, row in enumerate(reader, start=2):
            if not row or not any(field.strip() for field in row):
                continue

            month = row[month_idx].strip() if len(row) > month_idx else ""
            category = row[cat_idx].strip() if len(row) > cat_idx else ""
            rev_str = row[rev_idx].strip() if len(row) > rev_idx else ""

            # Check 1: blank category
            if not category:
                errors.append(f"line {line_num}: missing category (month={month})")

            # Check 2: blank revenue
            if not rev_str:
                errors.append(f"line {line_num}: missing revenue (category={category})")
            else:
                # Check 3: not parseable as float
                try:
                    rev_val = float(rev_str)
                    # Check 4: negative revenue
                    if rev_val < 0:
                        errors.append(f"line {line_num}: negative revenue ({rev_val}) for category={category}")
                except ValueError:
                    errors.append(f"line {line_num}: revenue not numeric: {rev_str!r}")

    if len(errors) == 0:
        return (True, [])
    return (False, errors)
