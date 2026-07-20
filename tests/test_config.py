from pathlib import Path

import pytest

from src.utils.config import ConfigError, load_config


def test_missing_config(tmp_path: Path):
    with pytest.raises(FileNotFoundError):
        load_config(tmp_path / "missing.yaml")


def test_invalid_config(tmp_path: Path):
    config = tmp_path / "config.yaml"
    config.write_text("database: {}\n", encoding="utf-8")
    with pytest.raises(ConfigError):
        load_config(config)
