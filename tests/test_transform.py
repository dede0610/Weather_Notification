"""Tests for transform module."""

from datetime import date

import polars as pl
import pytest

from src.transform.processors import clean_data, compute_daily_stats, enrich_data, validate_data


@pytest.fixture
def sample_df():
    """Sample weather DataFrame."""
    return pl.DataFrame({
        "date": [date(2026, 2, 18), date(2026, 2, 19), date(2026, 2, 20)],
        "temp_max": [12.5, 15.0, 10.0],
        "temp_min": [5.0, 7.5, 2.0],
        "precipitation": [0.0, 5.2, 12.5],
        "wind_speed_max": [25.0, 45.0, 80.0],
        "location": ["Paris", "Paris", "Paris"],
    })


@pytest.fixture
def sample_df_with_avg(sample_df):
    """Sample DataFrame with temp_avg column."""
    return sample_df.with_columns([
        ((pl.col("temp_max") + pl.col("temp_min")) / 2).alias("temp_avg"),
    ])


class TestCleanData:
    """Tests for clean_data function."""

    def test_clean_valid_data(self, sample_df):
        """Test cleaning valid data doesn't change row count."""
        df = sample_df.with_columns([
            ((pl.col("temp_max") + pl.col("temp_min")) / 2).alias("temp_avg"),
        ])
        cleaned = clean_data(df)
        assert len(cleaned) == 3

    def test_clean_empty_data(self):
        """Test cleaning empty DataFrame."""
        df = pl.DataFrame()
        cleaned = clean_data(df)
        assert cleaned.is_empty()

    def test_clean_removes_null_dates(self):
        """Test that rows with null dates are removed."""
        df = pl.DataFrame({
            "date": [date(2026, 2, 18), None, date(2026, 2, 20)],
            "temp_max": [12.5, 15.0, 10.0],
            "temp_min": [5.0, 7.5, 2.0],
            "precipitation": [0.0, 5.2, 12.5],
            "wind_speed_max": [25.0, 45.0, 80.0],
        })
        cleaned = clean_data(df)
        assert len(cleaned) == 2


class TestEnrichData:
    """Tests for enrich_data function."""

    def test_enrich_adds_temp_range(self, sample_df_with_avg):
        """Test that temp_range column is added."""
        enriched = enrich_data(sample_df_with_avg)
        assert "temp_range" in enriched.columns
        assert enriched["temp_range"][0] == 7.5

    def test_enrich_adds_temp_category(self, sample_df_with_avg):
        """Test that temp_category column is added."""
        enriched = enrich_data(sample_df_with_avg)
        assert "temp_category" in enriched.columns

    def test_enrich_adds_precip_category(self, sample_df_with_avg):
        """Test that precip_category column is added."""
        enriched = enrich_data(sample_df_with_avg)
        assert "precip_category" in enriched.columns

    def test_enrich_empty_data(self):
        """Test enriching empty DataFrame."""
        df = pl.DataFrame()
        enriched = enrich_data(df)
        assert enriched.is_empty()


class TestValidateData:
    """Tests for validate_data function."""

    def test_validate_valid_data(self, sample_df):
        """Test validation of valid data."""
        is_valid, errors = validate_data(sample_df)
        assert is_valid
        assert len(errors) == 0

    def test_validate_empty_data(self):
        """Test validation of empty DataFrame."""
        df = pl.DataFrame()
        is_valid, errors = validate_data(df)
        assert not is_valid
        assert "DataFrame is empty" in errors

    def test_validate_missing_columns(self):
        """Test validation with missing required columns."""
        df = pl.DataFrame({
            "date": [date(2026, 2, 18)],
            "temp_max": [12.5],
        })
        is_valid, errors = validate_data(df)
        assert not is_valid

    def test_validate_temp_min_greater_than_max(self):
        """Test validation when temp_min > temp_max."""
        df = pl.DataFrame({
            "date": [date(2026, 2, 18)],
            "temp_max": [5.0],
            "temp_min": [10.0],
            "precipitation": [0.0],
            "wind_speed_max": [25.0],
        })
        is_valid, errors = validate_data(df)
        assert not is_valid
        assert any("temp_min > temp_max" in e for e in errors)


class TestComputeDailyStats:
    """Tests for compute_daily_stats function."""

    def test_compute_stats(self, sample_df_with_avg):
        """Test computing statistics."""
        stats = compute_daily_stats(sample_df_with_avg)

        assert stats["record_count"] == 3
        assert stats["temp_max_overall"] == 15.0
        assert stats["temp_min_overall"] == 2.0
        assert stats["precipitation_total"] == 17.7

    def test_compute_stats_empty(self):
        """Test computing stats on empty DataFrame."""
        stats = compute_daily_stats(pl.DataFrame())
        assert stats == {}
