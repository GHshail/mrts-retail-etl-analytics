"""Load the processed MRTS CSV into MySQL through a staging table."""

from __future__ import annotations

import argparse
import re
from pathlib import Path
from time import perf_counter

import pandas as pd
from sqlalchemy import Engine, text

from src.utils.config import load_config
from src.utils.database import create_mysql_engine
from src.utils.logger import get_logger
from src.utils.paths import DEFAULT_CONFIG_FILE, SQL_DIR, resolve_project_path

LOGGER = get_logger("load_mrts")
MONTH_NUMBERS = {month: number for number, month in enumerate(
    ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"], start=1
)}


def safe_identifier(value: str) -> str:
    """Allow only safe SQL identifiers from configuration."""
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", value):
        raise ValueError(f"Unsafe SQL identifier: {value!r}")
    return value


def create_database(db: dict) -> None:
    database = safe_identifier(db["database"])
    engine = create_mysql_engine(db, include_database=False)
    try:
        with engine.begin() as connection:
            connection.execute(
                text(
                    f"CREATE DATABASE IF NOT EXISTS `{database}` "
                    "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
                )
            )
    finally:
        engine.dispose()


def install_schema(engine: Engine, database: str, target: str, staging: str) -> None:
    """Render and execute the version-controlled SQL installation script."""
    template = (SQL_DIR / "install.sql").read_text(encoding="utf-8")
    sql = template.format(
        database=safe_identifier(database),
        target_table=safe_identifier(target),
        staging_table=safe_identifier(staging),
    )
    statements = [statement.strip() for statement in sql.split(";") if statement.strip()]
    with engine.begin() as connection:
        for statement in statements:
            connection.execute(text(statement))


def prepare_load_dataframe(csv_file: Path) -> pd.DataFrame:
    """Validate and enrich the processed CSV for the database schema."""
    if not csv_file.exists():
        raise FileNotFoundError(f"Processed CSV not found: {csv_file}")
    df = pd.read_csv(
        csv_file,
        dtype={"Month": "string", "NAICS Code": "string", "Kind of Business": "string"},
        na_values=["NULL"],
        keep_default_na=True,
    )
    expected = {"Year", "Month", "NAICS Code", "Kind of Business", "Sales"}
    missing = expected.difference(df.columns)
    if missing:
        raise ValueError(f"Processed CSV is missing columns: {sorted(missing)}")

    df = df.rename(columns={
        "Year": "year",
        "Month": "month_name",
        "NAICS Code": "naics_code",
        "Kind of Business": "kind_of_business",
        "Sales": "sales",
    })
    df["year"] = pd.to_numeric(df["year"], errors="raise").astype("int16")
    df["month_name"] = df["month_name"].str.strip().str.title()
    df["month"] = df["month_name"].map(MONTH_NUMBERS)
    invalid = sorted(df.loc[df["month"].isna(), "month_name"].dropna().unique().tolist())
    if invalid:
        raise ValueError(f"Invalid month values: {invalid}")
    df["kind_of_business"] = df["kind_of_business"].str.strip()
    if df["kind_of_business"].isna().any() or (df["kind_of_business"] == "").any():
        raise ValueError("Blank business descriptions found")
    df["sales"] = pd.to_numeric(df["sales"], errors="coerce")
    df["sales_date"] = pd.to_datetime(
        {"year": df["year"], "month": df["month"], "day": 1}
    ).dt.date
    output = df[["sales_date", "year", "month", "month_name", "naics_code", "kind_of_business", "sales"]]
    duplicate_count = output.duplicated(
        subset=["sales_date", "naics_code", "kind_of_business"]
    ).sum()
    if duplicate_count:
        raise ValueError(f"Processed CSV contains {duplicate_count} duplicate target keys")
    return output


def stage_and_publish(engine: Engine, df: pd.DataFrame, target: str, staging: str, chunk_size: int) -> None:
    """Load staging, validate row counts, then replace the target in one transaction."""
    target = safe_identifier(target)
    staging = safe_identifier(staging)
    with engine.begin() as connection:
        connection.execute(text(f"TRUNCATE TABLE `{staging}`"))

    df.to_sql(staging, engine, if_exists="append", index=False, chunksize=chunk_size, method="multi")

    with engine.connect() as connection:
        staged_rows = connection.execute(text(f"SELECT COUNT(*) FROM `{staging}`")).scalar_one()
    if staged_rows != len(df):
        raise RuntimeError(f"Staging row-count mismatch: expected {len(df)}, found {staged_rows}")

    columns = "sales_date, year, month, month_name, naics_code, kind_of_business, sales"
    with engine.begin() as connection:
        connection.execute(text(f"DELETE FROM `{target}`"))
        connection.execute(text(f"INSERT INTO `{target}` ({columns}) SELECT {columns} FROM `{staging}`"))
        target_rows = connection.execute(text(f"SELECT COUNT(*) FROM `{target}`")).scalar_one()
    if target_rows != len(df):
        raise RuntimeError(f"Target row-count mismatch: expected {len(df)}, found {target_rows}")
    LOGGER.info("Published %s rows to %s", target_rows, target)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG_FILE)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    started = perf_counter()
    engine: Engine | None = None
    try:
        config = load_config(args.config)
        db, etl = config["database"], config["etl"]
        create_database(db)
        engine = create_mysql_engine(db)
        install_schema(engine, db["database"], etl["target_table"], etl["staging_table"])
        csv_file = resolve_project_path(config["files"]["processed_csv"])
        dataframe = prepare_load_dataframe(csv_file)
        LOGGER.info("Prepared %s rows; NULL sales=%s", len(dataframe), int(dataframe["sales"].isna().sum()))
        stage_and_publish(
            engine,
            dataframe,
            etl["target_table"],
            etl["staging_table"],
            int(etl["chunk_size"]),
        )
        LOGGER.info("Load completed in %.2f seconds", perf_counter() - started)
    except Exception:
        LOGGER.exception("MRTS load failed")
        raise
    finally:
        if engine is not None:
            engine.dispose()


if __name__ == "__main__":
    main()
