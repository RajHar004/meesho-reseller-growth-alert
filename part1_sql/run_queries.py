import csv
import sqlite3
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATABASE_PATH = PROJECT_ROOT / "data" / "meesho_reseller.db"
QUERY_PATH = Path(__file__).resolve().with_name("queries.sql")
OUTPUT_PATH = Path(__file__).resolve().parent / "output" / "monthly_category_revenue.csv"
MONTHLY_COLUMNS = ["month", "category", "revenue", "n_orders"]


def main() -> None:
    connection = sqlite3.connect(DATABASE_PATH)
    try:
        statements = []
        pending_lines = []
        for line in QUERY_PATH.read_text(encoding="utf-8").splitlines(keepends=True):
            pending_lines.append(line)
            statement = "".join(pending_lines)
            if sqlite3.complete_statement(statement):
                if statement.strip():
                    statements.append(statement)
                pending_lines.clear()

        if any(
            line.strip() and not line.lstrip().startswith("--")
            for line in pending_lines
        ):
            raise ValueError(f"Incomplete SQL statement in {QUERY_PATH}")

        monthly_rows = None
        for statement in statements:
            cursor = connection.execute(statement)
            if cursor.description is None:
                continue

            columns = [column[0] for column in cursor.description]
            rows = cursor.fetchall()
            if columns == MONTHLY_COLUMNS:
                monthly_rows = rows

        if monthly_rows is None:
            raise RuntimeError(
                f"No query in {QUERY_PATH} returned columns {MONTHLY_COLUMNS}"
            )

        OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
        with OUTPUT_PATH.open("w", newline="", encoding="utf-8") as output_file:
            writer = csv.writer(output_file)
            writer.writerow(MONTHLY_COLUMNS)
            writer.writerows(
                (month, category, f"{revenue:.2f}", order_count)
                for month, category, revenue, order_count in monthly_rows
            )
    finally:
        connection.close()

    output_name = OUTPUT_PATH.relative_to(PROJECT_ROOT).as_posix()
    print(f"Wrote {len(monthly_rows)} rows to {output_name}")


if __name__ == "__main__":
    main()
