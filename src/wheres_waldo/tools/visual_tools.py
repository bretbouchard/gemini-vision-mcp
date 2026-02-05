"""MCP tool implementations for visual regression testing.

Wires together capture, baseline, and storage services.
"""

from datetime import datetime
from pathlib import Path
from typing import Any

from mcp.server.fastmcp import FastMCP

from wheres_waldo.models.domain import Platform, Quality, ImageFormat
from wheres_waldo.services.baseline import BaselineService
from wheres_waldo.services.capture import CaptureService, ScreenshotCaptureError
from wheres_waldo.services.config import ConfigService
from wheres_waldo.services.storage import StorageService
from wheres_waldo.utils.logging import get_logger

logger = get_logger(__name__)


def register_visual_tools(mcp: FastMCP) -> None:
    """Register all visual tools with MCP server.

    Args:
        mcp: FastMCP server instance
    """

    # Initialize services
    config_service = ConfigService()
    storage_service = StorageService(config_service.get_config().storage)
    capture_service = CaptureService()
    baseline_service = BaselineService(capture_service, storage_service)

    @mcp.tool()
    async def visual_capture(
        name: str,
        platform: str = "auto",
        quality: str = "2x",
        format: str = "png",
    ) -> dict[str, Any]:
        """Capture a screenshot and store it for visual regression testing.

        Args:
            name: Descriptive name for the screenshot (e.g., "Phase 3 - Before card update")
            platform: Platform to capture from (auto, macos, ios, web)
            quality: Resolution quality (1x, 2x, 3x)
            format: Image format (png, jpeg, webp)

        Returns:
            Dictionary with screenshot path, metadata, and success status

        Example:
            >>> await visual_capture("Phase 3 - Before card update", "macos")
            {
                "success": true,
                "path": "/project/.screenshots/phases/current/20250204-200000-phase-3-before-card-update.png",
                "timestamp": "2025-02-04T20:00:00Z",
                "platform": "macos",
                "resolution": "2560x1440",
                "file_size_mb": 1.2
            }
        """
        try:
            # Parse enums
            platform_enum = Platform(platform.lower())
            quality_enum = Quality(quality.lower())
            format_enum = ImageFormat(format.lower())

            logger.info(f"Capturing screenshot: {name} from {platform_enum.value}")

            # Capture screenshot
            screenshot = capture_service.capture(
                name=name,
                platform=platform_enum,
                quality=quality_enum,
                format=format_enum,
            )

            # Save to storage
            storage_service.save_screenshot(screenshot)

            return {
                "success": True,
                "path": str(screenshot.path),
                "timestamp": screenshot.timestamp.isoformat(),
                "platform": screenshot.platform.value,
                "resolution": screenshot.resolution,
                "file_size_bytes": screenshot.file_size_bytes,
                "file_size_mb": round(screenshot.file_size_bytes / (1024 * 1024), 2) if screenshot.file_size_bytes else None,
            }

        except ScreenshotCaptureError as e:
            logger.error(f"Screenshot capture failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "platform": platform,
                "details": e.details,
            }
        except Exception as e:
            logger.exception(f"Unexpected error in visual_capture: {e}")
            return {
                "success": False,
                "error": f"Unexpected error: {e}",
                "platform": platform,
            }

    @mcp.tool()
    async def visual_prepare(
        phase: str,
        expected_changes: str,
        platform: str = "auto",
        quality: str = "2x",
        format: str = "png",
        description: str | None = None,
    ) -> dict[str, Any]:
        """Declare a baseline with expected changes before development work begins.

        Args:
            phase: Phase name or identifier (e.g., "Phase 3 - Card Layout Update")
            expected_changes: Description of expected changes (natural language or JSON)
            platform: Platform to capture from (auto, macos, ios, web)
            quality: Resolution quality (1x, 2x, 3x)
            format: Image format (png, jpeg, webp)
            description: Optional free-text description of the baseline

        Returns:
            Dictionary with baseline ID and stored metadata

        Example:
            >>> await visual_prepare(
            ...     phase="Phase 3 - Card Layout Update",
            ...     expected_changes="Card padding increases by 2px, button moves to right"
            ... )
            {
                "success": true,
                "baseline_id": "20250204-200000-phase-3-card-layout-update",
                "phase": "Phase 3 - Card Layout Update",
                "expected_changes_count": 2,
                "screenshot_path": "/project/.screenshots/phases/current/20250204-200000-baseline-phase-3.png",
                "timestamp": "2025-02-04T20:00:00Z"
            }
        """
        try:
            # Parse enums
            platform_enum = Platform(platform.lower())
            quality_enum = Quality(quality.lower())
            format_enum = ImageFormat(format.lower())

            logger.info(f"Creating baseline for phase: {phase}")

            # Create baseline
            baseline = baseline_service.create_baseline(
                phase=phase,
                expected_changes_input=expected_changes,
                platform=platform_enum,
                quality=quality_enum,
                format=format_enum,
                description=description,
            )

            return {
                "success": True,
                "baseline_id": baseline.baseline_id,
                "phase": baseline.phase,
                "expected_changes_count": len(baseline.expected_changes),
                "expected_changes": [
                    {
                        "description": change.description,
                        "element": change.element,
                        "bbox": change.bbox,
                    }
                    for change in baseline.expected_changes
                ],
                "screenshot_path": str(baseline.screenshot.path),
                "timestamp": baseline.created_at.isoformat(),
            }

        except ValueError as e:
            logger.error(f"Baseline creation failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "phase": phase,
            }
        except Exception as e:
            logger.exception(f"Unexpected error in visual_prepare: {e}")
            return {
                "success": False,
                "error": f"Unexpected error: {e}",
                "phase": phase,
            }

    @mcp.tool()
    async def visual_compare(
        before_path: str,
        after_path: str,
        threshold: int = 2,
        baseline_id: str | None = None,
        enable_gemini: bool = True,
    ) -> dict[str, Any]:
        """Compare two screenshots with pixel-level precision and agentic vision analysis.

        Args:
            before_path: Path to baseline screenshot
            after_path: Path to current screenshot
            threshold: Pixel threshold for change detection (1, 2, or 3)
            baseline_id: Optional baseline ID for expected changes
            enable_gemini: Enable Gemini agentic vision analysis (default: True)

        Returns:
            Dictionary with comparison results, annotations, and pass/fail status

        Example:
            >>> await visual_compare(
            ...     before_path="screenshots/phases/3-before.png",
            ...     after_path="screenshots/phases/4-after.png",
            ...     threshold=2,
            ...     baseline_id="20250204-200000-phase-3"
            ... )
            {
                "success": true,
                "passed": false,
                "changed_pixels": 1523,
                "changed_percentage": 0.12,
                "intended_changes": [
                    {"description": "Card padding increased by 2px", "confidence": 0.95}
                ],
                "unintended_changes": [
                    {"description": "Title shifted 5px down", "severity": "major", "confidence": 0.88}
                ],
                "heatmap_path": "screenshots/reports/20250204-200000-heatmap.png",
                "report_path": "screenshots/reports/20250204-200000-report.md"
            }
        """
        try:
            # Import services (late import to avoid circular dependency)
            from wheres_waldo.services.classification import ClassificationService
            from wheres_waldo.services.comparison import ComparisonService
            from wheres_waldo.services.gemini_integration import GeminiIntegrationService, GeminiRateLimiter
            import os

            # Validate paths
            before = Path(before_path)
            after = Path(after_path)

            if not before.exists():
                return {
                    "success": False,
                    "error": f"Before screenshot not found: {before_path}",
                }

            if not after.exists():
                return {
                    "success": False,
                    "error": f"After screenshot not found: {after_path}",
                }

            logger.info(f"Comparison requested: {before_path} vs {after_path}, enable_gemini={enable_gemini}")

            # Get baseline if provided
            baseline = None
            if baseline_id:
                baseline = storage_service.get_baseline(baseline_id)
                if not baseline:
                    return {
                        "success": False,
                        "error": f"Baseline not found: {baseline_id}",
                    }

            # Initialize comparison service
            comparison_service = ComparisonService(config_service.get_config().comparison)

            # Initialize Gemini service if enabled and API key available
            gemini_service = None
            if enable_gemini:
                api_key = os.getenv("GEMINI_API_KEY") or config_service.get_config().gemini_api_key
                if api_key:
                    rate_limiter = GeminiRateLimiter()
                    gemini_service = GeminiIntegrationService(api_key=api_key, rate_limiter=rate_limiter)
                    logger.info("Gemini agentic vision enabled")
                else:
                    logger.warning("Gemini API key not found, falling back to pixel-only comparison")
                    enable_gemini = False

            # Initialize classification service
            classification_service = ClassificationService(
                comparison_service=comparison_service,
                gemini_service=gemini_service,
                storage_service=storage_service,
                config=config_service.get_config().comparison,
            )

            # Run comparison
            result = await classification_service.compare_and_classify(
                before_path=before,
                after_path=after,
                baseline=baseline,
                threshold=threshold,
                enable_gemini=enable_gemini,
            )

            # Format response
            return {
                "success": True,
                "passed": result.passed,
                "failure_reason": result.failure_reason,
                "changed_pixels": result.changed_pixels,
                "total_pixels": result.total_pixels,
                "changed_percentage": result.changed_percentage,
                "threshold": result.threshold,
                "intended_changes": [
                    {
                        "description": c.description,
                        "bbox": c.bbox,
                        "confidence": c.confidence,
                    }
                    for c in result.intended_changes
                ],
                "unintended_changes": [
                    {
                        "description": c.description,
                        "bbox": c.bbox,
                        "severity": c.severity.value if c.severity else None,
                        "confidence": c.confidence,
                    }
                    for c in result.unintended_changes
                ],
                "heatmap_path": str(result.heatmap_path) if result.heatmap_path else None,
                "report_path": str(result.report_path) if result.report_path else None,
                "timestamp": result.timestamp.isoformat(),
            }

        except Exception as e:
            logger.exception(f"Unexpected error in visual_compare: {e}")
            return {
                "success": False,
                "error": f"Unexpected error: {e}",
                "before_path": before_path,
                "after_path": after_path,
            }

    @mcp.tool()
    async def visual_cleanup(
        retention_days: int = 7,
        dry_run: bool = False,
    ) -> dict[str, Any]:
        """Clean up old screenshots and cache to free disk space.

        Args:
            retention_days: Number of days to retain screenshots (default: 7)
            dry_run: If True, only report what would be deleted without actually deleting

        Returns:
            Dictionary with cleanup results and storage statistics

        Example:
            >>> await visual_cleanup(retention_days=7, dry_run=False)
            {
                "success": true,
                "deleted_screenshots": 23,
                "freed_space_mb": 45.2,
                "remaining_screenshots": 12,
                "storage_usage_mb": 23.1
            }
        """
        try:
            logger.info(f"Running cleanup: retention={retention_days} days, dry_run={dry_run}")

            # Get storage stats before cleanup
            stats_before = storage_service.get_storage_stats()

            # Run cleanup
            if dry_run:
                # Just report what would be deleted
                from datetime import timedelta

                cutoff = datetime.now() - timedelta(days=retention_days)
                old_screenshots = [
                    s for s in storage_service.list_screenshots()
                    if s.timestamp < cutoff
                ]

                result = {
                    "success": True,
                    "dry_run": True,
                    "would_delete_screenshots": len(old_screenshots),
                    "retention_days": retention_days,
                    "storage_usage": stats_before,
                }
            else:
                # Actually delete old screenshots
                cleanup_result = storage_service.cleanup_old_screenshots(retention_days)

                # Get storage stats after cleanup
                stats_after = storage_service.get_storage_stats()

                result = {
                    "success": True,
                    "dry_run": False,
                    "deleted_screenshots": cleanup_result["deleted_screenshots"],
                    "freed_space_mb": cleanup_result["freed_space_mb"],
                    "remaining_screenshots": stats_after["total_screenshots"],
                    "storage_usage_before_mb": stats_before["total_mb"],
                    "storage_usage_after_mb": stats_after["total_mb"],
                    "retention_days": retention_days,
                }

            return result

        except Exception as e:
            logger.exception(f"Unexpected error in visual_cleanup: {e}")
            return {
                "success": False,
                "error": f"Unexpected error: {e}",
            }

    @mcp.tool()
    async def visual_list(
        phase: str | None = None,
        limit: int = 50,
    ) -> dict[str, Any]:
        """List screenshots and baselines.

        Args:
            phase: Optional phase name to filter by
            limit: Maximum number of items to return (default: 50)

        Returns:
            Dictionary with lists of screenshots and baselines

        Example:
            >>> await visual_list(phase="Phase 3", limit=10)
            {
                "success": true,
                "screenshots": [
                    {
                        "name": "baseline-phase-3",
                        "path": "/project/.screenshots/phases/current/20250204-200000-baseline-phase-3.png",
                        "timestamp": "2025-02-04T20:00:00Z",
                        "platform": "macos"
                    }
                ],
                "baselines": [
                    {
                        "baseline_id": "20250204-200000-phase-3",
                        "phase": "Phase 3",
                        "expected_changes_count": 2
                    }
                ],
                "total_screenshots": 1,
                "total_baselines": 1
            }
        """
        try:
            logger.info(f"Listing items: phase={phase}, limit={limit}")

            # List screenshots
            screenshots = storage_service.list_screenshots(phase=phase)[:limit]

            # List baselines
            baselines = storage_service.list_baselines(phase=phase)[:limit]

            return {
                "success": True,
                "screenshots": [
                    {
                        "name": s.name,
                        "path": str(s.path),
                        "timestamp": s.timestamp.isoformat(),
                        "platform": s.platform.value,
                        "resolution": s.resolution,
                    }
                    for s in screenshots
                ],
                "baselines": [
                    {
                        "baseline_id": b.baseline_id,
                        "phase": b.phase,
                        "description": b.description,
                        "expected_changes_count": len(b.expected_changes),
                        "created_at": b.created_at.isoformat(),
                    }
                    for b in baselines
                ],
                "total_screenshots": len(screenshots),
                "total_baselines": len(baselines),
            }

        except Exception as e:
            logger.exception(f"Unexpected error in visual_list: {e}")
            return {
                "success": False,
                "error": f"Unexpected error: {e}",
            }
