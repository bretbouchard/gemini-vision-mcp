"""Storage service for screenshots and metadata.

Provides CRUD operations for screenshots, baselines, and comparison results.
All operations use atomic writes to prevent corruption.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from wheres_waldo.models.domain import (
    Baseline,
    ComparisonResult,
    Screenshot,
    StorageConfig,
)
from wheres_waldo.utils.logging import get_logger

logger = get_logger(__name__)


class StorageService:
    """Storage service for screenshots and metadata.

    All file operations are atomic to prevent corruption.
    JSON index is updated after each write operation.
    """

    def __init__(self, config: StorageConfig | None = None) -> None:
        """Initialize storage service.

        Args:
            config: Storage configuration (uses defaults if not provided)
        """
        self.config = config or StorageConfig()
        self._ensure_directories()
        self._load_index()

    def _ensure_directories(self) -> None:
        """Create storage directories if they don't exist."""
        for dir_path in [
            self.config.base_dir,
            self.config.phases_dir,
            self.config.cache_dir,
            self.config.reports_dir,
            self.config.conversations_dir,
        ]:
            dir_path.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Ensured directory exists: {dir_path}")

    def _load_index(self) -> None:
        """Load JSON index from disk."""
        self.index_path = self.config.base_dir / "index.json"
        if self.index_path.exists():
            try:
                with open(self.index_path, "r") as f:
                    self._index = json.load(f)
                logger.debug(f"Loaded index with {len(self._index)} entries")
            except json.JSONDecodeError as e:
                logger.error(f"Failed to load index, creating new: {e}")
                self._index = {}
        else:
            self._index = {}
            logger.debug("Created new index")

    def _save_index(self) -> None:
        """Save JSON index to disk (atomic write)."""
        temp_path = self.index_path.with_suffix(".tmp")
        try:
            with open(temp_path, "w") as f:
                json.dump(self._index, f, indent=2, default=str)
            # Atomic rename
            temp_path.replace(self.index_path)
            logger.debug("Saved index to disk")
        except Exception as e:
            logger.error(f"Failed to save index: {e}")
            raise

    def _add_to_index(self, entry_type: str, entry_id: str, metadata: dict[str, Any]) -> None:
        """Add entry to JSON index.

        Args:
            entry_type: Type of entry (screenshot, baseline, comparison)
            entry_id: Unique identifier for the entry
            metadata: Metadata dictionary to store
        """
        if entry_type not in self._index:
            self._index[entry_type] = {}
        self._index[entry_type][entry_id] = metadata
        self._save_index()
        logger.debug(f"Added {entry_type} entry: {entry_id}")

    # Screenshot operations

    def save_screenshot(self, screenshot: Screenshot) -> Screenshot:
        """Save screenshot metadata to index.

        Note: The actual image file should already be saved by the capture service.

        Args:
            screenshot: Screenshot metadata to save

        Returns:
            The saved screenshot (with generated fields populated)
        """
        metadata = {
            "name": screenshot.name,
            "timestamp": screenshot.timestamp.isoformat(),
            "platform": screenshot.platform.value,
            "quality": screenshot.quality.value,
            "format": screenshot.format.value,
            "resolution": screenshot.resolution,
            "file_size_bytes": screenshot.file_size_bytes,
            "path": str(screenshot.path),
        }

        # Use name as ID for now (could be timestamp-based)
        entry_id = screenshot.name
        self._add_to_index("screenshots", entry_id, metadata)

        logger.info(f"Saved screenshot metadata: {entry_id}")
        return screenshot

    def get_screenshot(self, name: str) -> Screenshot | None:
        """Get screenshot metadata by name.

        Args:
            name: Screenshot name

        Returns:
            Screenshot metadata if found, None otherwise
        """
        screenshots = self._index.get("screenshots", {})
        if name in screenshots:
            metadata = screenshots[name]
            return Screenshot(
                path=Path(metadata["path"]),
                name=metadata["name"],
                timestamp=datetime.fromisoformat(metadata["timestamp"]),
                platform=metadata["platform"],
                quality=metadata["quality"],
                format=metadata["format"],
                resolution=metadata.get("resolution"),
                file_size_bytes=metadata.get("file_size_bytes"),
            )
        return None

    def list_screenshots(self, phase: str | None = None) -> list[Screenshot]:
        """List all screenshots, optionally filtered by phase.

        Args:
            phase: Optional phase name to filter by

        Returns:
            List of screenshot metadata
        """
        screenshots = self._index.get("screenshots", {})
        results = []

        for name, metadata in screenshots.items():
            if phase is None or phase in name:
                results.append(Screenshot(
                    path=Path(metadata["path"]),
                    name=metadata["name"],
                    timestamp=datetime.fromisoformat(metadata["timestamp"]),
                    platform=metadata["platform"],
                    quality=metadata["quality"],
                    format=metadata["format"],
                    resolution=metadata.get("resolution"),
                    file_size_bytes=metadata.get("file_size_bytes"),
                ))

        return sorted(results, key=lambda s: s.timestamp, reverse=True)

    # Baseline operations

    def save_baseline(self, baseline: Baseline) -> Baseline:
        """Save baseline metadata to index.

        Args:
            baseline: Baseline to save

        Returns:
            The saved baseline
        """
        metadata = {
            "baseline_id": baseline.baseline_id,
            "phase": baseline.phase,
            "description": baseline.description,
            "created_at": baseline.created_at.isoformat(),
            "screenshot_path": str(baseline.screenshot.path),
            "expected_changes": [
                {
                    "description": change.description,
                    "bbox": change.bbox,
                    "element": change.element,
                }
                for change in baseline.expected_changes
            ],
        }

        self._add_to_index("baselines", baseline.baseline_id, metadata)
        logger.info(f"Saved baseline: {baseline.baseline_id}")
        return baseline

    def get_baseline(self, baseline_id: str) -> Baseline | None:
        """Get baseline by ID.

        Args:
            baseline_id: Baseline identifier

        Returns:
            Baseline if found, None otherwise
        """
        baselines = self._index.get("baselines", {})
        if baseline_id in baselines:
            metadata = baselines[baseline_id]
            return Baseline(
                baseline_id=metadata["baseline_id"],
                phase=metadata["phase"],
                description=metadata.get("description"),
                created_at=datetime.fromisoformat(metadata["created_at"]),
                screenshot=Screenshot(path=Path(metadata["screenshot_path"]), name=""),
                expected_changes=[
                    ExpectedChange(
                        description=change["description"],
                        bbox=change.get("bbox"),
                        element=change.get("element"),
                    )
                    for change in metadata["expected_changes"]
                ],
            )
        return None

    def list_baselines(self, phase: str | None = None) -> list[Baseline]:
        """List all baselines, optionally filtered by phase.

        Args:
            phase: Optional phase name to filter by

        Returns:
            List of baselines
        """
        baselines = self._index.get("baselines", {})
        results = []

        for baseline_id, metadata in baselines.items():
            if phase is None or phase in metadata["phase"]:
                results.append(Baseline(
                    baseline_id=metadata["baseline_id"],
                    phase=metadata["phase"],
                    description=metadata.get("description"),
                    created_at=datetime.fromisoformat(metadata["created_at"]),
                    screenshot=Screenshot(path=Path(metadata["screenshot_path"]), name=""),
                    expected_changes=[
                        ExpectedChange(
                            description=change["description"],
                            bbox=change.get("bbox"),
                            element=change.get("element"),
                        )
                        for change in metadata["expected_changes"]
                    ],
                ))

        return sorted(results, key=lambda b: b.created_at, reverse=True)

    # Comparison operations

    def save_comparison(self, comparison: ComparisonResult) -> ComparisonResult:
        """Save comparison result to index.

        Args:
            comparison: Comparison result to save

        Returns:
            The saved comparison result
        """
        # Generate comparison ID from timestamp
        comparison_id = comparison.timestamp.strftime("%Y%m%d-%H%M%S")

        metadata = {
            "comparison_id": comparison_id,
            "timestamp": comparison.timestamp.isoformat(),
            "before_path": str(comparison.before_path),
            "after_path": str(comparison.after_path),
            "threshold": comparison.threshold,
            "changed_pixels": comparison.changed_pixels,
            "total_pixels": comparison.total_pixels,
            "changed_percentage": comparison.changed_percentage,
            "passed": comparison.passed,
            "failure_reason": comparison.failure_reason,
            "heatmap_path": str(comparison.heatmap_path) if comparison.heatmap_path else None,
            "report_path": str(comparison.report_path) if comparison.report_path else None,
        }

        self._add_to_index("comparisons", comparison_id, metadata)
        logger.info(f"Saved comparison: {comparison_id}")
        return comparison

    def get_comparison(self, comparison_id: str) -> ComparisonResult | None:
        """Get comparison result by ID.

        Args:
            comparison_id: Comparison identifier

        Returns:
            Comparison result if found, None otherwise
        """
        comparisons = self._index.get("comparisons", {})
        if comparison_id in comparisons:
            metadata = comparisons[comparison_id]
            return ComparisonResult(
                before_path=Path(metadata["before_path"]),
                after_path=Path(metadata["after_path"]),
                threshold=metadata["threshold"],
                changed_pixels=metadata["changed_pixels"],
                total_pixels=metadata["total_pixels"],
                changed_percentage=metadata["changed_percentage"],
                passed=metadata["passed"],
                failure_reason=metadata.get("failure_reason"),
                heatmap_path=Path(metadata["heatmap_path"]) if metadata.get("heatmap_path") else None,
                report_path=Path(metadata["report_path"]) if metadata.get("report_path") else None,
                timestamp=datetime.fromisoformat(metadata["timestamp"]),
            )
        return None

    # Cleanup operations

    def cleanup_old_screenshots(self, retention_days: int) -> dict[str, Any]:
        """Clean up screenshots older than retention period.

        Args:
            retention_days: Number of days to retain screenshots

        Returns:
            Dictionary with cleanup results
        """
        from datetime import timedelta

        cutoff = datetime.now() - timedelta(days=retention_days)
        screenshots = self.list_screenshots()
        deleted_count = 0
        freed_bytes = 0

        for screenshot in screenshots:
            if screenshot.timestamp < cutoff:
                try:
                    if screenshot.path.exists():
                        file_size = screenshot.path.stat().st_size
                        screenshot.path.unlink()
                        freed_bytes += file_size
                        deleted_count += 1
                        logger.info(f"Deleted old screenshot: {screenshot.path}")
                except Exception as e:
                    logger.error(f"Failed to delete {screenshot.path}: {e}")

        return {
            "deleted_screenshots": deleted_count,
            "freed_space_bytes": freed_bytes,
            "freed_space_mb": round(freed_bytes / (1024 * 1024), 2),
        }

    def get_storage_stats(self) -> dict[str, Any]:
        """Get storage statistics.

        Returns:
            Dictionary with storage usage statistics
        """
        screenshots = self.list_screenshots()
        total_bytes = 0

        for screenshot in screenshots:
            if screenshot.path.exists():
                total_bytes += screenshot.path.stat().st_size

        return {
            "total_screenshots": len(screenshots),
            "total_bytes": total_bytes,
            "total_mb": round(total_bytes / (1024 * 1024), 2),
            "base_dir": str(self.config.base_dir),
        }
