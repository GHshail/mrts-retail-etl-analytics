"""Centralized filesystem paths used by the MRTS project."""

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CONFIG_DIR = PROJECT_ROOT / "config"
DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
SAMPLE_DATA_DIR = DATA_DIR / "sample"
SQL_DIR = PROJECT_ROOT / "sql"
LOG_DIR = PROJECT_ROOT / "logs"
OUTPUT_DIR = PROJECT_ROOT / "output"
CHART_DIR = OUTPUT_DIR / "charts"
NOTEBOOK_DIR = PROJECT_ROOT / "notebooks"

DEFAULT_CONFIG_FILE = CONFIG_DIR / "database.yaml"
EXAMPLE_CONFIG_FILE = CONFIG_DIR / "database.example.yaml"


def resolve_project_path(value: str | Path) -> Path:
    """Resolve a configured path relative to the repository root."""
    path = Path(value).expanduser()
    return path if path.is_absolute() else PROJECT_ROOT / path


def ensure_runtime_directories() -> None:
    """Create directories written to during ETL and analysis runs."""
    for directory in (RAW_DATA_DIR, PROCESSED_DATA_DIR, LOG_DIR, CHART_DIR):
        directory.mkdir(parents=True, exist_ok=True)
