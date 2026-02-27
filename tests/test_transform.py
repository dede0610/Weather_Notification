"""Tests for transform module."""

from datetime import date

import polars as pl
import pytest

from src.transform.processors import clean_data, enrich_data, validate_data


@pytest.fixture
def sample_df():
    """Sample weather DataFrame."""
    return pl.DataFrame({
        "date": [date(2026, 2, 18), date(2026, 2, 19), date(2026, 2, 20)],
        "time": ["12:00 AM", "4:00 PM", "10:00 AM"],
        "temperature": [12.5, 15.0, 10.0],
        "precipitation": [0.0, 5.2, 12.5],
        "uv_index": [10.0, 5.0, 8.0],
        "location": ["Paris", "Paris", "Paris"],
    })


class TestCleanData:
    """Tests for clean_data function."""

    def test_clean_valid_data(self, sample_df):
        """Test cleaning valid data doesn't change row count."""
        cleaned = clean_data(sample_df)
        assert len(cleaned) == 3

    def test_clean_removes_null_time(self):
        """Test that rows with null times are removed."""
        df = pl.DataFrame({
            "date": [date(2026, 2, 18), None, date(2026, 2, 20)],
            "time": ["12:00 AM", None, "10:00 AM"],
            "temperature": [12.5, 15.0, 10.0],
            "uv_index": [5.0, 7.5, 2.0],
            "precipitation": [0.0, 5.2, 12.5],
            "location": ["Paris", "Paris", "Paris"],})
        cleaned = clean_data(df)
        assert len(cleaned) == 2


class TestEnrichData:
    """Tests for enrich_data function."""

    def test_enrich_adds_uv_category(self, sample_df):
        """Test that uv_category column is added."""
        enriched = enrich_data(sample_df)
        assert "uv_category" in enriched.columns
        assert enriched["uv_category"][0] == "Very High"

    def test_enrich_adds_temp_category(self, sample_df):
        """Test that temp_category column is added."""
        enriched = enrich_data(sample_df)
        assert "temp_category" in enriched.columns
        assert enriched["temp_category"][0] == "Moderate"

    def test_enrich_adds_precip_category(self, sample_df):
        """Test that precip_category column is added."""
        enriched = enrich_data(sample_df)
        assert "precip_category" in enriched.columns
        assert enriched["precip_category"][0] == "Dry"


class TestValidateData:
    """Tests for validate_data function."""

    def test_validate_valid_data(self, sample_df):
        """Test validation of valid data."""
        is_valid, errors = validate_data(sample_df)
        assert is_valid
        assert len(errors) == 0

    def test_validate_missing_columns(self):
        """Test validation with missing required columns."""
        df = pl.DataFrame({
            "date": [date(2026, 2, 18)],
            "temperature": [12.5],
        })
        is_valid, errors = validate_data(df)
        assert not is_valid

    def test_validate_negative_uv_index(self):
        """Test validation with negative UV index values."""
        df = pl.DataFrame({
            "date": [date(2026, 2, 18)],
            "time": ["12:00 AM"],
            "temperature": [12.5],
            "precipitation": [0.0],
            "uv_index": [-1.0],
            "location": ["Paris"],
        })
        is_valid, errors = validate_data(df)
        assert not is_valid
        assert "Negative UV index values" in errors
