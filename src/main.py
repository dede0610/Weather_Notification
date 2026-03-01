"""Main pipeline orchestrator."""

import argparse
import sys
import time
from datetime import date
from pathlib import Path

from src.alerts.conditions import AlertResult, build_default_conditions, check_all_conditions
from src.alerts.notifiers import get_notifier
from src.config.settings import get_settings
from src.extract.api_client import OpenMeteoClient, parse_weather_response
from src.load.storage import DataStorage
from src.transform.processors import clean_data, enrich_data, validate_data
from src.utils.logging import log_execution_summary, setup_logger

logger = setup_logger("pipeline")


def run_pipeline(dry_run: bool = False) -> int:
    """Run the complete data pipeline.

    Args:
        dry_run: If True, don't save data or send real alerts.

    Returns:
        Exit code: 0 = success, 1 = error, 2 = alerts triggered
    """
    start_time = time.time()
    date_today = date.today()
    settings = get_settings()
    storage = DataStorage(Path(settings.data_dir))

    logger.info(f"🚀 Starting pipeline for {settings.location_name}")
    logger.info(f"🌏 Coordinates: ({settings.latitude}, {settings.longitude})")
    logger.info(f"Dry run: {dry_run}")

    records_processed = 0
    alerts_triggered = 0
    alert_results: list[AlertResult] = []

    try:
        with OpenMeteoClient() as client:
            raw_data = client.fetch_daily(
                latitude=settings.latitude,
                longitude=settings.longitude,
                date=date_today,
            )

        df = parse_weather_response(raw_data, settings.location_name, frequency="hourly")
        logger.info(f"Fetched {len(df)} records")

        if df.is_empty():
            logger.error("No data fetched from API")
            return 1

        df = clean_data(df)
        df = enrich_data(df)
        print(df.slice(8, 16))

        is_valid, errors = validate_data(df)
        if not is_valid:
            logger.error(f"Data validation failed: {errors}")
            return 1

        records_processed = len(df)

        if not dry_run:
            storage.save_raw(df, "weather_forecast")
            storage.save_processed(df, "weather_processed")
            logger.info("✅ Data saved successfully")
        else:
            logger.info("[DRY RUN] Skipping data save")

        # stats = compute_daily_stats(df)
        # logger.info(f"Stats: temp_max={stats.get('temp_max_overall')}°C, "
        #            f"precipitation_total={stats.get('precipitation_total')}mm")

        conditions = build_default_conditions(settings)
        alert_results = check_all_conditions(df, conditions)
        alerts_triggered = sum(1 for r in alert_results if r.triggered)

        if alerts_triggered > 0:
            logger.warning(f"{alerts_triggered} alert(s) triggered!")

        if settings.alert_enabled and alerts_triggered > 0:
            notifier = get_notifier(settings)
            if dry_run:
                from src.alerts.notifiers import ConsoleNotifier

                notifier = ConsoleNotifier()

            success = notifier.send(alert_results, settings.location_name, df)
            if not success:
                logger.error("❌ Failed to send notifications")
        elif not settings.alert_enabled:
            logger.info("Alerts disabled in configuration")

        if not dry_run:
            archived = storage.archive_old(days=30)
            if archived > 0:
                logger.info(f"Archived {archived} old files")

        duration = time.time() - start_time
        status = "ALERTS" if alerts_triggered > 0 else "SUCCESS"

        log_execution_summary(
            logger=logger,
            status=status,
            records_processed=records_processed,
            alerts_triggered=alerts_triggered,
            duration_seconds=duration,
        )

        return 0

    except Exception as e:
        logger.exception(f"❌ Pipeline failed with error: {e}")
        duration = time.time() - start_time
        log_execution_summary(
            logger=logger,
            status="ERROR",
            records_processed=records_processed,
            alerts_triggered=0,
            duration_seconds=duration,
        )
        return 1


def main() -> int:
    """Entry point for the pipeline."""
    parser = argparse.ArgumentParser(description="Weather data pipeline")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run without saving data or sending real alerts",
    )
    args = parser.parse_args()

    return run_pipeline(dry_run=args.dry_run)


if __name__ == "__main__":
    sys.exit(main())
