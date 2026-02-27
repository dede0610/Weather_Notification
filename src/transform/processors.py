"""Data transformation and validation processors."""

import logging

import polars as pl

logger = logging.getLogger("pipeline")


def clean_data(df: pl.DataFrame) -> pl.DataFrame:
    """Clean raw weather data."""
    if df.is_empty():
        return df

    initial_rows = len(df)

    df = df.with_row_index()
    df = df.filter(pl.col("time").is_not_null())
    df = df.filter(pl.col("temperature").is_not_null())

    df = df.fill_null(strategy="zero")

    if "location" in df.columns:
        df = df.unique(subset=["time", "location"])
    else:
        df = df.unique(subset=["time"])

    final_rows = len(df)
    if initial_rows != final_rows:
        logger.info(f"Cleaned data: {initial_rows} -> {final_rows} rows")

    print(df.sort("index", descending=False))

    return df.sort("index", descending=False)


def enrich_data(df: pl.DataFrame) -> pl.DataFrame:
    """Add derived columns and enrich data."""
    if df.is_empty():
        return df

    df = df.with_columns([
        pl.when(pl.col("temperature") > 30)
        .then(pl.lit("Hot"))
        .when(pl.col("temperature") < 10)
        .then(pl.lit("Cold"))
        .otherwise(pl.lit("Moderate"))
        .alias("temp_category"),
        pl.when(pl.col("precipitation") > 10)
        .then(pl.lit("Rainy"))
        .when(pl.col("precipitation") > 0)
        .then(pl.lit("Light_rain"))
        .otherwise(pl.lit("Dry"))
        .alias("precip_category"),
        pl.when(pl.col("uv_index") >= 11)
        .then(pl.lit("Extreme"))
        .when(pl.col("uv_index") >= 8)
        .then(pl.lit("Very High"))
        .when(pl.col("uv_index") >= 6)
        .then(pl.lit("High"))
        .when(pl.col("uv_index") >= 3)
        .then(pl.lit("Moderate"))
        .otherwise(pl.lit("Low"))
        .alias("uv_category"),
    ])

    return df


def validate_data(df: pl.DataFrame) -> tuple[bool, list[str]]:
    """Validate data quality. Returns (is_valid, list of errors)."""
    errors = []

    if df.is_empty():
        errors.append("DataFrame is empty")
        return False, errors

    required_columns = ["temperature", "precipitation", "uv_index"]
    missing = [col for col in required_columns if col not in df.columns]
    if missing:
        errors.append(f"Missing required columns: {missing}")
        return False, errors

    if df.filter(pl.col("temperature") > 60).height > 0:
        errors.append("Invalid temperature values (> 60°C)")

    if df.filter(pl.col("precipitation") < 0).height > 0:
        errors.append("Negative precipitation values")

    if df.filter(pl.col("uv_index") < 0).height > 0:
        errors.append("Negative UV index values")

    if df.filter(pl.col("uv_index") > 15).height > 0:
        errors.append("InvalidUV index values > 15")

    is_valid = len(errors) == 0
    if not is_valid:
        logger.error(f"Data validation failed: {errors}")
    else:
        logger.info("✅ Data validation passed")

    return is_valid, errors


def compute_daily_stats(df: pl.DataFrame) -> dict:
    """Compute summary statistics for the data."""
    if df.is_empty():
        return {}

    stats = {
        "record_count": len(df),
        "date_min": df["date"].min().isoformat() if df["date"].min() else None,
        "date_max": df["date"].max().isoformat() if df["date"].max() else None,
        "temp_max_overall": (
            float(df["temp_max"].max()) if df["temp_max"].max() is not None else None
        ),
        "temp_min_overall": (
            float(df["temp_min"].min()) if df["temp_min"].min() is not None else None
        ),
        "temp_avg_mean": (
            float(df["temp_avg"].mean()) if "temp_avg" in df.columns else None
        ),
        "precipitation_total": (
            float(df["precipitation"].sum())
            if df["precipitation"].sum() is not None
            else None
        ),
        "wind_speed_max": (
            float(df["wind_speed_max"].max())
            if df["wind_speed_max"].max() is not None
            else None
        ),
    }

    return stats
