"""Rolling-window analysis for grocery stores and gasoline stations."""

import argparse
from pathlib import Path
import matplotlib.pyplot as plt
import pandas as pd
from src.analysis.common import analysis_engine, query_frame, save_chart
from src.utils.paths import DEFAULT_CONFIG_FILE

BUSINESSES = ["Grocery stores", "Gasoline stations"]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG_FILE)
    parser.add_argument("--show", action="store_true")
    args = parser.parse_args(); engine = analysis_engine(args.config)
    try:
        monthly = query_frame(engine, """
            SELECT sales_date, kind_of_business, sales FROM monthly_retail_sales
            WHERE kind_of_business IN (:b1,:b2) AND sales IS NOT NULL
            ORDER BY sales_date, kind_of_business
        """, {"b1": BUSINESSES[0], "b2": BUSINESSES[1]})
        yearly = query_frame(engine, """
            SELECT year, kind_of_business, SUM(sales) yearly_sales FROM monthly_retail_sales
            WHERE kind_of_business IN (:b1,:b2) AND sales IS NOT NULL
            GROUP BY year, kind_of_business ORDER BY year, kind_of_business
        """, {"b1": BUSINESSES[0], "b2": BUSINESSES[1]})
        monthly["sales_date"] = pd.to_datetime(monthly["sales_date"])
        pivot = monthly.pivot(index="sales_date", columns="kind_of_business", values="sales").sort_index()
        for business in BUSINESSES:
            if business not in pivot: raise ValueError(f"Category not found: {business}")
            plt.figure(figsize=(12,6)); plt.plot(pivot.index, pivot[business], alpha=.3, label="Monthly")
            for window in (3,6,12): plt.plot(pivot.index, pivot[business].rolling(window).mean(), label=f"{window}-month average")
            plt.title(f"{business}: Rolling Windows"); plt.xlabel("Year"); plt.ylabel("Sales"); plt.grid(alpha=.25); plt.legend()
            filename = business.lower().replace(" ", "_") + "_rolling_windows.png"
            print("Saved:", save_chart(filename, args.show))

        plt.figure(figsize=(12,6))
        for business in BUSINESSES: plt.plot(pivot.index, pivot[business].rolling(12).mean(), label=business)
        plt.title("12-Month Rolling Average Comparison"); plt.xlabel("Year"); plt.ylabel("Sales"); plt.grid(alpha=.25); plt.legend()
        print("Saved:", save_chart("rolling_12_month_comparison.png", args.show))

        annual = yearly.pivot(index="year", columns="kind_of_business", values="yearly_sales")
        plt.figure(figsize=(12,6))
        for column in annual: plt.plot(annual.index, annual[column], marker="o", label=column)
        plt.title("Annual Sales Comparison"); plt.xlabel("Year"); plt.ylabel("Annual sales"); plt.grid(alpha=.25); plt.legend()
        print("Saved:", save_chart("rolling_yearly_comparison.png", args.show))
    finally: engine.dispose()

if __name__ == "__main__": main()
