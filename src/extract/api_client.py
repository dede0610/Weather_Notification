"""API client for Open-Meteo weather data."""

import logging
from datetime import date

import httpx
import polars as pl

logger = logging.getLogger("pipeline")


class OpenMeteoClient:
    """Client for Open-Meteo API (free, no auth required)."""

    BASE_URL = "https://api.open-meteo.com/v1"

    def __init__(self, timeout: float = 30.0):
        self.timeout = timeout
        self.client = httpx.Client(timeout=timeout, verify=False)

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.client.close()

    def fetch_daily(
        self,
        latitude: float,
        longitude: float,
        date: date,
    ) -> dict:
        """Fetch weather forecast for given coordinates."""
        url = f"{self.BASE_URL}/forecast"
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "hourly": "temperature_2m,precipitation,uv_index,uv_index_clear_sky",
            "timezone": "auto",
            "start_date": date.isoformat(),
            "end_date": date.isoformat(),
        }

        logger.info(f"Fetching Hourly weather data for ({latitude}, {longitude}) for today {date.isoformat()}")
        response = self.client.get(url, params=params)
        response.raise_for_status()
        return response.json()
    
    def fetch_forecast(
        self,
        latitude: float,
        longitude: float,
        forecast_days: int = 7,
    ) -> dict:
        """Fetch weather forecast for given coordinates."""
        url = f"{self.BASE_URL}/forecast"
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum,wind_speed_10m_max",
            "timezone": "auto",
            "forecast_days": forecast_days,
        }

        logger.info(f"Fetching forecast for ({latitude}, {longitude})")
        response = self.client.get(url, params=params)
        response.raise_for_status()
        return response.json()

    def fetch_historical(
        self,
        latitude: float,
        longitude: float,
        start_date: date,
        end_date: date,
    ) -> dict:
        """Fetch historical weather data."""
        url = f"{self.BASE_URL}/forecast"
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum,wind_speed_10m_max",
            "timezone": "auto",
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
        }

        logger.info(f"Fetching historical data from {start_date} to {end_date}")
        response = self.client.get(url, params=params)
        response.raise_for_status()
        return response.json()

    def close(self) -> None:
        """Close the HTTP client."""
        self.client.close()


def parse_weather_response(data: dict, location_name: str = "Unknown", frequency: str = "hourly") -> pl.DataFrame:
    """Parse Open-Meteo API response into a Polars DataFrame."""
    if frequency == "daily":
        daily = data.get("daily", {})

        df = pl.DataFrame({
            "date": daily.get("time", []),
            "temp_max": daily.get("temperature_2m_max", []),
            "temp_min": daily.get("temperature_2m_min", []),
            "precipitation": daily.get("precipitation_sum", []),
            "wind_speed_max": daily.get("wind_speed_10m_max", []),
            "location": location_name,
        })

        df = df.with_columns([
            pl.col("date").str.to_date("%Y-%m-%d").alias("date"),
            pl.col("temp_max").cast(pl.Float64),
            pl.col("temp_min").cast(pl.Float64),
            pl.col("precipitation").cast(pl.Float64),
            pl.col("wind_speed_max").cast(pl.Float64),
        ])

        df = df.with_columns([
            ((pl.col("temp_max") + pl.col("temp_min")) / 2).alias("temp_avg"),
        ])

    elif frequency == "hourly":
        hourly = data.get("hourly", {})

        df = pl.DataFrame({
            "date": date.today().isoformat(),
            "time": hourly.get("time", []),
            "temperature": hourly.get("temperature_2m", []),
            "precipitation": hourly.get("precipitation", []),
            "uv_index": hourly.get("uv_index", []),
            "uv_index_clear_sky": hourly.get("uv_index_clear_sky", []),
            "location": location_name,
        })

        df = df.with_columns([
            pl.col("time").str.to_datetime().dt.strftime("%I:%M %p").alias("time"),
            pl.col("temperature").cast(pl.Float64),
            pl.col("precipitation").cast(pl.Float64),
            pl.col("uv_index").cast(pl.Float64),
            pl.col("uv_index_clear_sky").cast(pl.Float64),
        ])

    else:
        logger.warning(f"Unknown frequency: {frequency}")
        return pl.DataFrame()

    return df
