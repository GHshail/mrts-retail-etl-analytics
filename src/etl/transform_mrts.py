"""Extract and transform the Census MRTS workbook into a long-format CSV."""

from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from pathlib import Path
from time import perf_counter

import pandas as pd

from src.utils.config import load_config
from src.utils.logger import get_logger
from src.utils.paths import DEFAULT_CONFIG_FILE, ensure_runtime_directories, resolve_project_path

LOGGER = get_logger("transform_mrts")
ALL_MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
MONTH_PATTERN = re.compile(
    r"^(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)"
    r"\.?\s*(\d{4})(?:\s*\([^)]*\))?$",
    re.IGNORECASE,
)
OUTPUT_COLUMNS = ["Year", "Month", "NAICS Code", "Kind of Business", "Sales"]


@dataclass(frozen=True)
class TransformStats:
    worksheets: int
    records: int
    null_sales: int
    earliest_year: int
    latest_year: int


def normalize_marker(value: object) -> str:
    """Normalize section markers while preserving exact semantic matching."""
    if pd.isna(value):
        return ""
    return re.sub(r"\s+", "", str(value).strip().upper())


def find_marker_row(df: pd.DataFrame, marker: str, start: int = 0) -> int | None:
    """Find an exact section marker in worksheet column B."""
    target = normalize_marker(marker)
    for index in range(start, len(df)):
        if normalize_marker(df.iloc[index, 1]) == target:
            return index
    return None


def detect_month_columns(header: pd.Series, worksheet_year: int) -> dict[str, int]:
    """Map month abbreviations to worksheet column positions."""
    columns: dict[str, int] = {}
    for index, value in enumerate(header):
        if pd.isna(value):
            continue
        match = MONTH_PATTERN.fullmatch(str(value).strip())
        if match and int(match.group(2)) == worksheet_year:
            columns[match.group(1).title()] = index
    return columns


def normalize_naics(value: object) -> str | None:
    """Preserve NAICS identifiers as strings without spreadsheet '.0' suffixes."""
    if pd.isna(value):
        return None
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value).strip() or None


def process_sheet(sheet_name: str, df: pd.DataFrame) -> pd.DataFrame:
    """Transform one year worksheet into twelve monthly rows per business."""
    year = int(sheet_name)
    if len(df) < 7 or df.shape[1] < 3:
        raise ValueError(f"Worksheet {sheet_name} has an unexpected structure")

    month_columns = detect_month_columns(df.iloc[4], year)
    if not month_columns:
        raise ValueError(f"No month headers detected in worksheet {sheet_name}")

    start = find_marker_row(df, "NOT ADJUSTED")
    if start is None:
        raise ValueError(f"NOT ADJUSTED marker not found in worksheet {sheet_name}")
    stop = find_marker_row(df, "ADJUSTED(2)", start=start + 1)
    if stop is None:
        raise ValueError(f"ADJUSTED(2) marker not found in worksheet {sheet_name}")

    records: list[dict[str, object]] = []
    for _, row in df.iloc[start + 1 : stop].iterrows():
        business = row.iloc[1]
        if pd.isna(business) or not str(business).strip():
            continue
        business_name = str(business).strip()
        naics_code = normalize_naics(row.iloc[0])
        for month in ALL_MONTHS:
            sales = pd.NA
            column = month_columns.get(month)
            if column is not None and column < len(row):
                sales = row.iloc[column]
            records.append(
                {
                    "Year": year,
                    "Month": month,
                    "NAICS Code": naics_code,
                    "Kind of Business": business_name,
                    "Sales": sales,
                }
            )

    LOGGER.info("Processed %s; detected months=%s", year, ",".join(month_columns))
    return pd.DataFrame.from_records(records, columns=OUTPUT_COLUMNS)


def transform_workbook(input_file: Path, output_file: Path) -> TransformStats:
    """Transform all year worksheets and write the canonical processed CSV."""
    if not input_file.exists():
        raise FileNotFoundError(f"Raw workbook not found: {input_file}")

    workbook = pd.ExcelFile(input_file, engine="openpyxl")
    frames: list[pd.DataFrame] = []
    processed_years: list[int] = []
    for sheet in workbook.sheet_names:
        if not re.fullmatch(r"\d{4}", str(sheet).strip()):
            LOGGER.warning("Skipping non-year worksheet: %s", sheet)
            continue
        raw = pd.read_excel(input_file, sheet_name=sheet, header=None, engine="openpyxl")
        frames.append(process_sheet(str(sheet), raw))
        processed_years.append(int(sheet))

    if not frames:
        raise ValueError("No year worksheets were transformed")

    result = pd.concat(frames, ignore_index=True)
    result["Sales"] = pd.to_numeric(result["Sales"], errors="coerce")
    duplicate_count = result.duplicated(
        subset=["Year", "Month", "NAICS Code", "Kind of Business"]
    ).sum()
    if duplicate_count:
        raise ValueError(f"Transformation produced {duplicate_count} duplicate business keys")

    output_file.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(output_file, index=False, na_rep="NULL")
    stats = TransformStats(
        worksheets=len(processed_years),
        records=len(result),
        null_sales=int(result["Sales"].isna().sum()),
        earliest_year=min(processed_years),
        latest_year=max(processed_years),
    )
    LOGGER.info("Wrote %s records to %s", stats.records, output_file)
    LOGGER.info("Year range=%s-%s; NULL sales=%s", stats.earliest_year, stats.latest_year, stats.null_sales)
    return stats


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG_FILE)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    ensure_runtime_directories()
    started = perf_counter()
    try:
        config = load_config(args.config)
        input_file = resolve_project_path(config["files"]["raw_excel"])
        output_file = resolve_project_path(config["files"]["processed_csv"])
        transform_workbook(input_file, output_file)
        LOGGER.info("Transformation completed in %.2f seconds", perf_counter() - started)
    except Exception:
        LOGGER.exception("MRTS transformation failed")
        raise


if __name__ == "__main__":
    main()
