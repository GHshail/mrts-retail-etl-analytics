"""Configuration loading and validation."""

from pathlib import Path
from typing import Any

import yaml

from src.utils.paths import DEFAULT_CONFIG_FILE


class ConfigError(ValueError):
    """Raised when project configuration is missing or invalid."""


def load_config(config_file: Path = DEFAULT_CONFIG_FILE) -> dict[str, Any]:
    """Load YAML configuration and validate required sections and keys."""
    if not config_file.exists():
        raise FileNotFoundError(
            f"Configuration not found: {config_file}. "
            "Copy config/database.example.yaml to config/database.yaml."
        )
    with config_file.open("r", encoding="utf-8") as stream:
        config = yaml.safe_load(stream) or {}

    required = {
        "database": ("host", "port", "database", "username", "password"),
        "files": ("raw_excel", "processed_csv"),
        "etl": ("target_table", "staging_table", "chunk_size"),
    }
    for section, keys in required.items():
        if section not in config:
            raise ConfigError(f"Missing configuration section: {section}")
        missing = [key for key in keys if key not in config[section]]
        if missing:
            raise ConfigError(f"Missing {section} settings: {', '.join(missing)}")
    return config
