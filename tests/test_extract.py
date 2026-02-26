"""Tests for extract module."""


import pytest

from src.extract.api_client import OpenMeteoClient, parse_weather_response


@pytest.fixture
def sample_api_response():
    """Sample Open-Meteo API response."""
    return {
        "daily": {
            "time": ["2026-02-18", "2026-02-19", "2026-02-20"],
            "temperature_2m_max": [12.5, 15.0, 10.0],
            "temperature_2m_min": [5.0, 7.5, 2.0],
            "precipitation_sum": [0.0, 5.2, 12.5],
            "wind_speed_10m_max": [25.0, 45.0, 80.0],
        }
    }


class TestParseWeatherResponse:
    """Tests for parse_weather_response function."""

    def test_parse_valid_response(self, sample_api_response):
        """Test parsing a valid API response."""
        df = parse_weather_response(sample_api_response, "Paris")

        assert len(df) == 3
        assert "date" in df.columns
        assert "temp_max" in df.columns
        assert "temp_min" in df.columns
        assert "precipitation" in df.columns
        assert "wind_speed_max" in df.columns
        assert "location" in df.columns
        assert "temp_avg" in df.columns

    def test_parse_empty_response(self):
        """Test parsing an empty response."""
        df = parse_weather_response({}, "Paris")
        assert df.is_empty()

    def test_parse_missing_daily_key(self):
        """Test parsing response without daily key."""
        df = parse_weather_response({"hourly": {}}, "Paris")
        assert df.is_empty()

    def test_parse_calculates_avg_temp(self, sample_api_response):
        """Test that average temperature is calculated correctly."""
        df = parse_weather_response(sample_api_response, "Paris")

        expected_avg = (12.5 + 5.0) / 2
        assert df["temp_avg"][0] == expected_avg

    def test_parse_location_preserved(self, sample_api_response):
        """Test that location name is preserved."""
        df = parse_weather_response(sample_api_response, "Lyon")
        assert df["location"][0] == "Lyon"


class TestOpenMeteoClient:
    """Tests for OpenMeteoClient class."""

    def test_client_context_manager(self):
        """Test client works as context manager."""
        with OpenMeteoClient() as client:
            assert client.client is not None

    def test_client_close(self):
        """Test client can be closed explicitly."""
        client = OpenMeteoClient()
        client.close()

    @pytest.mark.integration
    def test_fetch_forecast_real_api(self):
        """Integration test: fetch from real API."""
        pytest.skip("Integration test - run manually")

        with OpenMeteoClient() as client:
            data = client.fetch_forecast(
                latitude=48.8566,
                longitude=2.3522,
                forecast_days=3,
            )

            assert "daily" in data
            assert len(data["daily"]["time"]) == 3
