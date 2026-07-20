"""Trend analysis for total retail sales and three selected businesses."""

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

from src.analysis.common import analysis_engine, query_frame, save_chart
from src.utils.paths import DEFAULT_CONFIG_FILE

TOTAL = "Retail and food services sales, total"
BUSINESSES = ["Book stores", "Sporting goods stores", "Hobby, toy, and game stores"]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG_FILE)
    parser.add_argument("--show", action="store_true")
    args = parser.parse_args()
    engine = analysis_engine(args.config)
    try:
        total = query_frame(engine, """
            SELECT sales_date, sales FROM monthly_retail_sales
            WHERE kind_of_business=:business AND sales IS NOT NULL ORDER BY sales_date
        """, {"business": TOTAL})
        comparison = query_frame(engine, """
            SELECT sales_date, kind_of_business, sales FROM monthly_retail_sales
            WHERE kind_of_business IN (:b1,:b2,:b3) AND sales IS NOT NULL
            ORDER BY sales_date, kind_of_business
        """, {"b1": BUSINESSES[0], "b2": BUSINESSES[1], "b3": BUSINESSES[2]})
        yearly = query_frame(engine, """
            SELECT year, kind_of_business, SUM(sales) yearly_sales FROM monthly_retail_sales
            WHERE kind_of_business IN (:b1,:b2,:b3) AND sales IS NOT NULL
            GROUP BY year, kind_of_business ORDER BY year, kind_of_business
        """, {"b1": BUSINESSES[0], "b2": BUSINESSES[1], "b3": BUSINESSES[2]})

        total["sales_date"] = pd.to_datetime(total["sales_date"])
        total["rolling_12"] = total["sales"].rolling(12, min_periods=12).mean()
        plt.figure(figsize=(12, 6)); plt.plot(total.sales_date, total.sales, alpha=.35, label="Monthly")
        plt.plot(total.sales_date, total.rolling_12, linewidth=2.3, label="12-month average")
        plt.title("Retail and Food Services Sales Trend"); plt.xlabel("Year"); plt.ylabel("Sales"); plt.grid(alpha=.25); plt.legend()
        print("Saved:", save_chart("retail_food_services_trend.png", args.show))

        comparison["sales_date"] = pd.to_datetime(comparison["sales_date"])
        pivot = comparison.pivot(index="sales_date", columns="kind_of_business", values="sales")
        plt.figure(figsize=(12, 6))
        for column in pivot: plt.plot(pivot.index, pivot[column], label=column)
        plt.title("Monthly Sales: Selected Businesses"); plt.xlabel("Year"); plt.ylabel("Sales"); plt.grid(alpha=.25); plt.legend()
        print("Saved:", save_chart("three_businesses_monthly.png", args.show))

        annual = yearly.pivot(index="year", columns="kind_of_business", values="yearly_sales")
        plt.figure(figsize=(12, 6))
        for column in annual: plt.plot(annual.index, annual[column], marker="o", label=column)
        plt.title("Annual Sales: Selected Businesses"); plt.xlabel("Year"); plt.ylabel("Annual sales"); plt.grid(alpha=.25); plt.legend()
        print("Saved:", save_chart("three_businesses_yearly.png", args.show))
        growth = ((annual.iloc[-1] / annual.iloc[0]) - 1).mul(100).sort_values(ascending=False)
        print("\nTotal growth over available period (%)\n", growth.to_string())
    finally:
        engine.dispose()

if __name__ == "__main__": main()
