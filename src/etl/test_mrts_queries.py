"""Run database validation queries after the MRTS load."""

import argparse
from pathlib import Path

import pandas as pd
from sqlalchemy import text

from src.utils.config import load_config
from src.utils.database import create_mysql_engine
from src.utils.paths import DEFAULT_CONFIG_FILE

QUERIES = {
    "Load summary": """
        SELECT COUNT(*) AS total_records, MIN(year) AS earliest_year,
               MAX(year) AS latest_year,
               COUNT(DISTINCT kind_of_business) AS business_categories,
               SUM(sales IS NULL) AS null_sales_records
        FROM monthly_retail_sales
    """,
    "Latest-year month coverage": """
        SELECT year, month, month_name, COUNT(*) AS rows_total,
               COUNT(sales) AS rows_with_sales, SUM(sales IS NULL) AS null_sales_rows
        FROM monthly_retail_sales
        WHERE year = (SELECT MAX(year) FROM monthly_retail_sales)
        GROUP BY year, month, month_name
        ORDER BY month
    """,
}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG_FILE)
    args = parser.parse_args()
    config = load_config(args.config)
    engine = create_mysql_engine(config["database"])
    try:
        for title, sql in QUERIES.items():
            print(f"\n{title}\n{'=' * len(title)}")
            with engine.connect() as connection:
                frame = pd.read_sql(text(sql), connection)
            print(frame.to_string(index=False))
    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
