"""Alert conditions for weather data monitoring."""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import date

import polars as pl

logger = logging.getLogger("pipeline")


@dataclass
class AlertResult:
    """Result of an alert condition check."""

    triggered: bool
    condition_name: str
    message: str
    severity: str = "info"
    value: float | None = None
    threshold: float | None = None
    date: str | None = None
    data: dict = field(default_factory=dict)


class AlertCondition(ABC):
    """Abstract base class for alert conditions."""

    def __init__(self, name: str, severity: str = "info"):
        self.name = name
        self.severity = severity

    @abstractmethod
    def check(self, df: pl.DataFrame) -> AlertResult:
        """Check if condition is triggered."""
        pass


class ThresholdCondition(AlertCondition):
    """Alert when a value exceeds a threshold."""

    def __init__(
        self,
        name: str,
        column: str,
        threshold: float,
        comparison: str = "gt",
        severity: str = "warning",
    ):
        super().__init__(name, severity)
        self.column = column
        self.threshold = threshold
        self.comparison = comparison

    def check(self, df: pl.DataFrame) -> AlertResult:
        if df.is_empty() or self.column not in df.columns:
            return AlertResult(
                triggered=False,
                condition_name=self.name,
                message=f"Column {self.column} not found or data is empty",
            )

        value = df.select(pl.col(self.column).max()).item()

        comparison_map = {
            "gt": lambda v, t: v > t,
            "gte": lambda v, t: v >= t,
            "lt": lambda v, t: v < t,
            "lte": lambda v, t: v <= t,
            "eq": lambda v, t: v == t,
        }

        triggered = comparison_map.get(self.comparison, lambda v, t: False)(value, self.threshold)

        if triggered:
            message = (
                f"{self.name}: {self.column}={value} "
                f"({self.comparison} threshold {self.threshold})"
            )
            logger.warning(message)
        else:
            message = f"{self.name}: OK ({self.column}={value})"

        return AlertResult(
            triggered=triggered,
            condition_name=self.name,
            message=message,
            severity=self.severity if triggered else "info",
            value=value,
            threshold=self.threshold,
            date=date.today().isoformat(),
        )
    

def check_all_conditions(df: pl.DataFrame, conditions: list[AlertCondition]) -> list[AlertResult]:
    """Run all conditions and return results."""
    results = []
    for condition in conditions:
        result = condition.check(df)
        results.append(result)
        if result.triggered:
            logger.warning(f"Alert triggered: {result.message}")
    return results


def build_default_conditions(settings) -> list[AlertCondition]:
    """Build default alert conditions from settings."""
    return [
        ThresholdCondition(
            name="High Temperature",
            column="temperature",
            threshold=settings.temp_max_threshold,
            comparison="gt",
            severity="warning",
        ),
        ThresholdCondition(
            name="UV Index",
            column="uv_index",
            threshold=settings.uv_threshold,
            comparison="gt",
            severity="critical",
        ),
        ThresholdCondition(
            name="Heavy Precipitation",
            column="precipitation",
            threshold=settings.precipitation_threshold,
            comparison="gt",
            severity="warning",
        )
    ]
