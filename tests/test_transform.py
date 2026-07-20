import pandas as pd

from src.etl.transform_mrts import detect_month_columns, normalize_marker, normalize_naics


def test_month_header_variants():
    header = pd.Series(["NAICS Code", "Kind of Business", "Jan. 2026", "Apr. 2026(p)", "CY CUM"])
    assert detect_month_columns(header, 2026) == {"Jan": 2, "Apr": 3}


def test_adjusted_markers_are_not_confused():
    assert normalize_marker("NOT ADJUSTED") == "NOTADJUSTED"
    assert normalize_marker("ADJUSTED (2)") == "ADJUSTED(2)"
    assert normalize_marker("NOT ADJUSTED") != normalize_marker("ADJUSTED (2)")


def test_naics_normalization():
    assert normalize_naics(441.0) == "441"
    assert normalize_naics("44-45") == "44-45"
