"""Percentage-change and contribution analysis for clothing-store categories."""

import argparse
from pathlib import Path
import matplotlib.pyplot as plt
import pandas as pd
from src.analysis.common import analysis_engine, query_frame, save_chart
from src.utils.paths import DEFAULT_CONFIG_FILE

MEN = "Men's clothing stores"
WOMEN = "Women's clothing stores"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG_FILE)
    parser.add_argument("--show", action="store_true")
    args = parser.parse_args(); engine = analysis_engine(args.config)
    try:
        df = query_frame(engine, """
            SELECT sales_date, kind_of_business, sales FROM monthly_retail_sales
            WHERE kind_of_business IN (:men,:women) AND sales IS NOT NULL
            ORDER BY sales_date, kind_of_business
        """, {"men": MEN, "women": WOMEN})
        df["sales_date"] = pd.to_datetime(df["sales_date"])
        pivot = df.pivot(index="sales_date", columns="kind_of_business", values="sales").sort_index()
        missing = {MEN, WOMEN}.difference(pivot.columns)
        if missing: raise ValueError(f"Missing business categories: {sorted(missing)}")
        changes = pivot.pct_change(fill_method=None).mul(100)
        contribution = pivot.div(pivot.sum(axis=1), axis=0).mul(100)

        plt.figure(figsize=(12,6))
        for column in pivot: plt.plot(pivot.index, pivot[column], label=column)
        plt.title("Men's and Women's Clothing Store Sales"); plt.xlabel("Year"); plt.ylabel("Sales"); plt.grid(alpha=.25); plt.legend()
        print("Saved:", save_chart("mens_womens_clothing_sales.png", args.show))

        plt.figure(figsize=(12,6))
        for column in changes: plt.plot(changes.index, changes[column], label=column)
        plt.axhline(0, linewidth=1); plt.title("Month-over-Month Percentage Change"); plt.xlabel("Year"); plt.ylabel("Percent"); plt.grid(alpha=.25); plt.legend()
        print("Saved:", save_chart("mens_womens_percentage_change.png", args.show))

        plt.figure(figsize=(12,6)); plt.stackplot(contribution.index, *[contribution[c] for c in contribution], labels=list(contribution.columns), alpha=.8)
        plt.title("Share of Combined Clothing Sales"); plt.xlabel("Year"); plt.ylabel("Contribution (%)"); plt.ylim(0,100); plt.legend(loc="upper left")
        print("Saved:", save_chart("mens_womens_percentage_contribution.png", args.show))
        print("\nSales correlation:", round(pivot.corr().iloc[0,1], 3))
        print("Average contribution (%)\n", contribution.mean().round(2).to_string())
    finally: engine.dispose()

if __name__ == "__main__": main()
