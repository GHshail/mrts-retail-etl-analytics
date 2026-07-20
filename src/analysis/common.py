"""Shared helpers for MRTS analysis scripts."""

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
from sqlalchemy import Engine, text

from src.utils.config import load_config
from src.utils.database import create_mysql_engine
from src.utils.paths import CHART_DIR, DEFAULT_CONFIG_FILE, ensure_runtime_directories


def analysis_engine(config_file: Path = DEFAULT_CONFIG_FILE) -> Engine:
    config = load_config(config_file)
    return create_mysql_engine(config["database"])


def query_frame(engine: Engine, sql: str, params: dict | None = None) -> pd.DataFrame:
    with engine.connect() as connection:
        return pd.read_sql(text(sql), connection, params=params)


def save_chart(filename: str, show: bool = False) -> Path:
    ensure_runtime_directories()
    path = CHART_DIR / filename
    plt.tight_layout()
    plt.savefig(path, dpi=300, bbox_inches="tight")
    if show:
        plt.show()
    plt.close()
    return path
