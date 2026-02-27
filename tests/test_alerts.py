"""Tests for alerts module."""

from datetime import date, timedelta

import polars as pl
import pytest

from src.alerts.conditions import (
    AlertResult,
    ThresholdCondition,
    build_default_conditions,
    check_all_conditions,
)
from src.alerts.notifiers import ConsoleNotifier


@pytest.fixture
def sample_df():
    """Sample weather DataFrame with extreme values on most recent date."""
    return pl.DataFrame({
        "date": [date.today(), date.today() - timedelta(days=1)],
        "temp_max": [38.0, 25.0],
        "temp_min": [-15.0, 5.0],
        "precipitation": [60.0, 0.0],
        "uv_index": [5.9, 9.0],
        "temp_avg": [11.5, 15.0],
        "location": ["Paris", "Paris"],
    })


class TestThresholdCondition:
    """Tests for ThresholdCondition."""

    def test_condition_triggered_gt(self, sample_df):
        """Test condition triggered when value > threshold."""
        condition = ThresholdCondition(
            name="High Temp",
            column="temp_max",
            threshold=35.0,
            comparison="gt",
        )
        result = condition.check(sample_df)

        assert result.triggered
        assert result.value == 38.0
        assert result.threshold == 35.0

    def test_condition_not_triggered(self, sample_df):
        """Test condition not triggered when value within limits."""
        condition = ThresholdCondition(
            name="High Temp",
            column="temp_max",
            threshold=50.0,
            comparison="gt",
        )
        result = condition.check(sample_df)

        assert not result.triggered

    def test_condition_triggered_lt(self, sample_df):
        """Test condition triggered when value < threshold."""
        condition = ThresholdCondition(
            name="Low Temp",
            column="temp_min",
            threshold=-10.0,
            comparison="lt",
        )
        result = condition.check(sample_df)

        assert result.triggered
        assert result.value == -15.0

    def test_condition_empty_dataframe(self):
        """Test condition with empty DataFrame."""
        condition = ThresholdCondition(
            name="High Temp",
            column="temp_max",
            threshold=35.0,
        )
        result = condition.check(pl.DataFrame())

        assert not result.triggered

    def test_condition_missing_column(self, sample_df):
        """Test condition with missing column."""
        condition = ThresholdCondition(
            name="Missing",
            column="nonexistent",
            threshold=35.0,
        )
        result = condition.check(sample_df)

        assert not result.triggered


class TestCheckAllConditions:
    """Tests for check_all_conditions function."""

    def test_check_multiple_conditions(self, sample_df):
        """Test checking multiple conditions."""
        conditions = [
            ThresholdCondition("High Temp", "temp_max", 35.0, "gt"),
            ThresholdCondition("Low Temp", "temp_min", -10.0, "lt"),
        ]
        results = check_all_conditions(sample_df, conditions)

        assert len(results) == 2
        assert results[0].triggered
        assert results[1].triggered

    def test_check_no_conditions_triggered(self, sample_df):
        """Test when no conditions are triggered."""
        conditions = [
            ThresholdCondition("High Temp", "temp_max", 50.0, "gt"),
        ]
        results = check_all_conditions(sample_df, conditions)

        assert len(results) == 1
        assert not results[0].triggered


class TestBuildDefaultConditions:
    """Tests for build_default_conditions function."""

    def test_build_conditions(self):
        """Test building default conditions from settings."""
        from unittest.mock import MagicMock

        settings = MagicMock()
        settings.temp_max_threshold = 35.0
        settings.temp_min_threshold = -10.0
        settings.precipitation_threshold = 50.0
        settings.uv_threshold = 6.0

        conditions = build_default_conditions(settings)

        assert len(conditions) == 3
        assert any(c.name == "High Temperature" for c in conditions)
        assert any(c.name == "UV Index" for c in conditions)


class TestConsoleNotifier:
    """Tests for ConsoleNotifier."""

    def test_notify_no_alerts(self, caplog):
        """Test notification when no alerts triggered."""
        notifier = ConsoleNotifier()
        results = [
            AlertResult(triggered=False, condition_name="Test", message="OK"),
        ]

        success = notifier.send(results, "Paris", sample_df)
        assert success

    def test_notify_with_alerts(self, caplog):
        """Test notification with triggered alerts."""
        notifier = ConsoleNotifier()
        results = [
            AlertResult(
                triggered=True,
                condition_name="High Temp",
                message="Temperature too high",
                severity="warning",
            ),
        ]

        success = notifier.send(results, "Paris", sample_df)
        assert success
