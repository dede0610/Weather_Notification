"""Data storage module for Parquet files."""

import logging
import shutil
from datetime import datetime
from pathlib import Path

import polars as pl

logger = logging.getLogger("pipeline")


class DataStorage:
    """Handle data storage operations with Parquet files."""

    def __init__(self, base_path: Path):
        self.base_path = base_path
        self.raw_path = base_path / "raw"
        self.processed_path = base_path / "processed"
        self.archive_path = base_path / "archive"

        for path in [self.raw_path, self.processed_path, self.archive_path]:
            path.mkdir(parents=True, exist_ok=True)

    def save_raw(self, data: pl.DataFrame, source: str) -> Path:
        """Save raw data with timestamp in filename."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{source}_{timestamp}.parquet"
        filepath = self.raw_path / filename

        data.write_parquet(filepath, compression="snappy")
        logger.info(f"Saved raw data to {filepath}")

        return filepath

    def save_processed(self, data: pl.DataFrame, name: str) -> Path:
        """Save processed data."""
        filepath = self.processed_path / f"{name}.parquet"

        data.write_parquet(filepath, compression="snappy")
        logger.info(f"Saved processed data to {filepath}")

        return filepath

    def load_latest(self, name: str) -> pl.DataFrame | None:
        """Load the latest processed data file."""
        pattern = f"{name}*.parquet"
        files = list(self.processed_path.glob(pattern))

        if not files:
            logger.warning(f"No files found matching {pattern}")
            return None

        latest = max(files, key=lambda f: f.stat().st_mtime)
        logger.info(f"Loading {latest}")
        return pl.read_parquet(latest)

    def archive_old(self, days: int = 30) -> int:
        """Archive files older than specified days. Returns count of archived files."""
        cutoff = datetime.now().timestamp() - (days * 24 * 60 * 60)
        archived_count = 0

        for path in [self.raw_path, self.processed_path]:
            for file in path.glob("*.parquet"):
                if file.stat().st_mtime < cutoff:
                    dest = self.archive_path / file.name
                    shutil.move(str(file), str(dest))
                    archived_count += 1
                    logger.info(f"Archived {file.name}")

        return archived_count

    def get_storage_stats(self) -> dict[str, int | float]:
        """Get statistics about stored data."""
        stats: dict[str, int | float] = {
            "raw_files": len(list(self.raw_path.glob("*.parquet"))),
            "processed_files": len(list(self.processed_path.glob("*.parquet"))),
            "archive_files": len(list(self.archive_path.glob("*.parquet"))),
        }

        total_size = 0
        for path in [self.raw_path, self.processed_path, self.archive_path]:
            for file in path.glob("*.parquet"):
                total_size += file.stat().st_size

        stats["total_size_mb"] = round(total_size / (1024 * 1024), 2)
        return stats
