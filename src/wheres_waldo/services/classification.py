"""Classification service for intended vs unintended change detection.

Combines pixel diffing, Gemini analysis, and expected changes to classify
changes and determine pass/fail status.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from wheres_waldo.models.domain import (
    Baseline,
    ComparisonResult,
    ComparisonConfig,
    ChangeRegion,
    Severity,
)
from wheres_waldo.services.cache import CacheService
from wheres_waldo.services.comparison import ComparisonService
from wheres_waldo.services.gemini_integration import GeminiIntegrationService
from wheres_waldo.services.storage import StorageService
from wheres_waldo.utils.logging import get_logger

logger = get_logger(__name__)


class ClassificationService:
    """Classification service for intended vs unintended changes.

    Combines pixel-level comparison with Gemini agentic vision to:
    1. Detect all changes (pixel diffing)
    2. Interpret changes (Gemini natural language)
    3. Classify as intended/unintended (expected changes matching)
    4. Determine pass/fail (threshold-based)
    """

    def __init__(
        self,
        comparison_service: ComparisonService | None = None,
        gemini_service: GeminiIntegrationService | None = None,
        storage_service: StorageService | None = None,
        cache_service: CacheService | None = None,
        config: ComparisonConfig | None = None,
    ) -> None:
        """Initialize classification service.

        Args:
            comparison_service: Comparison service (creates if None)
            gemini_service: Gemini integration service (optional)
            storage_service: Storage service (creates if None)
            cache_service: Cache service (creates if None)
            config: Comparison configuration (uses defaults if None)
        """
        self.comparison_service = comparison_service or ComparisonService(config)
        self.gemini_service = gemini_service  # Optional (may not have API key)
        self.storage_service = storage_service or StorageService()
        self.cache_service = cache_service or CacheService(storage_service)
        self.config = config or ComparisonConfig()

        logger.info("ClassificationService initialized")

    async def compare_and_classify(
        self,
        before_path: Path,
        after_path: Path,
        baseline: Baseline | None = None,
        threshold: int | None = None,
        enable_gemini: bool | None = None,
    ) -> ComparisonResult:
        """Compare screenshots and classify changes.

        Args:
            before_path: Path to baseline screenshot
            after_path: Path to current screenshot
            baseline: Optional baseline with expected changes
            threshold: Pixel threshold (overrides config)
            enable_gemini: Enable Gemini analysis (overrides config)

        Returns:
            Complete comparison result with classification

        Raises:
            ValueError: If screenshots cannot be loaded
        """
        start_time = datetime.now()
        logger.info(f"Starting comparison: {before_path.name} vs {after_path.name}")

        # Step 0: Check cache first
        cache_key = self.cache_service.get_cache_key(
            before_path=before_path,
            after_path=after_path,
            threshold=threshold or self.config.pixel_threshold,
        )

        cached_result = self.cache_service.get(cache_key)
        if cached_result is not None:
            logger.info(f"Returning cached result from {cached_result.timestamp.isoformat()}")
            return cached_result

        # Determine if Gemini should be used
        use_gemini = enable_gemini if enable_gemini is not None else self.config.enable_agentic_vision

        # Step 1: Pixel-level comparison (always done)
        pixel_result = self.comparison_service.compare(
            before_path=before_path,
            after_path=after_path,
            threshold=threshold,
        )

        # Step 2: Gemini analysis (if enabled and available)
        gemini_changes = []
        overall_confidence = 0.0

        if use_gemini and self.gemini_service:
            logger.info("Running Gemini agentic vision analysis")

            expected_changes = baseline.expected_changes if baseline else None

            gemini_result = await self.gemini_service.analyze_changes(
                before_path=before_path,
                after_path=after_path,
                expected_changes=expected_changes,
                threshold=threshold or self.config.pixel_threshold,
                progressive_resolution=self.config.progressive_resolution,
                min_confidence=self.config.min_confidence_threshold,
            )

            if gemini_result.get("success"):
                gemini_changes = gemini_result.get("changes", [])
                overall_confidence = gemini_result.get("overall_confidence", 0.0)
                logger.info(f"Gemini analysis complete: {len(gemini_changes)} changes detected, confidence={overall_confidence:.2f}")
            else:
                logger.warning(f"Gemini analysis failed: {gemini_result.get('error')}")
        else:
            logger.info("Gemini analysis disabled or unavailable")

        # Step 3: Classify changes as intended/unintended
        intended_changes, unintended_changes = self._classify_changes(
            gemini_changes=gemini_changes,
            expected_changes=baseline.expected_changes if baseline else None,
        )

        # Step 4: Determine pass/fail
        passed, failure_reason = self._determine_pass_fail(
            pixel_result=pixel_result,
            intended_changes=intended_changes,
            unintended_changes=unintended_changes,
        )

        # Step 5: Create heatmap
        heatmap_path = None
        if pixel_result.changed_pixels > 0:
            try:
                from wheres_waldo.services.comparison import HeatmapColorScheme

                heatmap_dir = self.storage_service.config.base_dir / "reports"
                timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
                heatmap_path = heatmap_dir / f"{timestamp}-heatmap.png"

                self.comparison_service.create_heatmap(
                    before_path=before_path,
                    after_path=after_path,
                    output_path=heatmap_path,
                    threshold=threshold or self.config.pixel_threshold,
                    color_scheme=HeatmapColorScheme.YELLOW_ORANGE_RED,
                    opacity=0.6,
                )

                logger.info(f"Heatmap created: {heatmap_path}")

            except Exception as e:
                logger.error(f"Failed to create heatmap: {e}")

        # Step 6: Create comparison report
        report_path = None
        try:
            report_dir = self.storage_service.config.base_dir / "reports"
            timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            report_path = report_dir / f"{timestamp}-report.md"

            self._create_report(
                report_path=report_path,
                before_path=before_path,
                after_path=after_path,
                pixel_result=pixel_result,
                intended_changes=intended_changes,
                unintended_changes=unintended_changes,
                passed=passed,
                failure_reason=failure_reason,
                gemini_summary=gemini_result.get("summary") if use_gemini and self.gemini_service else None,
            )

            logger.info(f"Report created: {report_path}")

        except Exception as e:
            logger.error(f"Failed to create report: {e}")

        # Step 7: Build final result
        result = ComparisonResult(
            before_path=before_path,
            after_path=after_path,
            threshold=threshold or self.config.pixel_threshold,
            changed_pixels=pixel_result.changed_pixels,
            total_pixels=pixel_result.total_pixels,
            changed_percentage=pixel_result.changed_percentage,
            intended_changes=intended_changes,
            unintended_changes=unintended_changes,
            passed=passed,
            failure_reason=failure_reason,
            heatmap_path=heatmap_path,
            report_path=report_path,
            timestamp=start_time,
        )

        # Save to storage
        self.storage_service.save_comparison(result)

        # Cache the result
        self.cache_service.put(cache_key, result)

        logger.info(f"Comparison complete: passed={passed}, unintended_changes={len(unintended_changes)}")
        return result

    def _classify_changes(
        self,
        gemini_changes: list[ChangeRegion],
        expected_changes: list[Any] | None,
    ) -> tuple[list[ChangeRegion], list[ChangeRegion]]:
        """Classify changes as intended or unintended.

        Args:
            gemini_changes: Changes detected by Gemini
            expected_changes: Expected changes from baseline

        Returns:
            Tuple of (intended_changes, unintended_changes)
        """
        if not gemini_changes:
            return [], []

        # If no expected changes provided, all are unknown
        if not expected_changes:
            return [], gemini_changes

        intended = []
        unintended = []

        for change in gemini_changes:
            # Check if change matches any expected change
            match_found = False

            for expected in expected_changes:
                if self._change_matches_expected(change, expected):
                    change.intended = True
                    intended.append(change)
                    match_found = True
                    break

            if not match_found:
                # No match found - mark as unintended
                if change.intended is None:  # Only override if Gemini didn't classify
                    change.intended = False
                unintended.append(change)

        logger.info(f"Classified {len(intended)} intended, {len(unintended)} unintended changes")
        return intended, unintended

    def _change_matches_expected(self, change: ChangeRegion, expected: Any) -> bool:
        """Check if a change matches an expected change.

        Args:
            change: Detected change region
            expected: Expected change (ExpectedChange or dict)

        Returns:
            True if match found
        """
        expected_desc = expected.description.lower() if hasattr(expected, 'description') else str(expected).lower()
        change_desc = change.description.lower()

        # Simple substring matching
        if expected_desc in change_desc or change_desc in expected_desc:
            return True

        # TODO: Add more sophisticated matching (bbox proximity, element matching)
        return False

    def _determine_pass_fail(
        self,
        pixel_result: ComparisonResult,
        intended_changes: list[ChangeRegion],
        unintended_changes: list[ChangeRegion],
    ) -> tuple[bool, str | None]:
        """Determine if comparison passes or fails.

        Args:
            pixel_result: Pixel comparison result
            intended_changes: Intended changes list
            unintended_changes: Unintended changes list

        Returns:
            Tuple of (passed, failure_reason)
        """
        # Check 1: Too many changed regions
        total_changes = len(intended_changes) + len(unintended_changes)
        if total_changes > self.config.max_changed_regions:
            return False, f"Too many changed regions: {total_changes} > {self.config.max_changed_regions}"

        # Check 2: Too many changed pixels
        if pixel_result.changed_percentage > self.config.max_changed_percentage:
            return False, f"Too many changed pixels: {pixel_result.changed_percentage:.2f}% > {self.config.max_changed_percentage}%"

        # Check 3: Critical or major unintended changes
        critical_count = sum(1 for c in unintended_changes if c.severity == Severity.CRITICAL)
        major_count = sum(1 for c in unintended_changes if c.severity == Severity.MAJOR)

        if critical_count > 0:
            return False, f"{critical_count} critical unintended change(s) detected"

        if major_count > 0:
            return False, f"{major_count} major unintended change(s) detected"

        # All checks passed
        return True, None

    def _create_report(
        self,
        report_path: Path,
        before_path: Path,
        after_path: Path,
        pixel_result: ComparisonResult,
        intended_changes: list[ChangeRegion],
        unintended_changes: list[ChangeRegion],
        passed: bool,
        failure_reason: str | None,
        gemini_summary: str | None = None,
    ) -> None:
        """Create markdown comparison report.

        Args:
            report_path: Path to save report
            before_path: Before screenshot path
            after_path: After screenshot path
            pixel_result: Pixel comparison result
            intended_changes: Intended changes
            unintended_changes: Unintended changes
            passed: Pass/fail status
            failure_reason: Failure reason if failed
            gemini_summary: Optional Gemini summary
        """
        report = f"""# Visual Regression Comparison Report

**Generated**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
**Status**: {'✅ PASSED' if passed else '❌ FAILED'}

---

## Comparison Details

- **Before**: `{before_path.name}`
- **After**: `{after_path.name}`
- **Threshold**: {pixel_result.threshold}px
- **Changed Pixels**: {pixel_result.changed_pixels:,} / {pixel_result.total_pixels:,} ({pixel_result.changed_percentage:.2f}%)

---

## Result

{'### ✅ PASSED' if passed else '### ❌ FAILED'}

{'All checks passed!' if passed else f'**Reason**: {failure_reason}'}

---

## Intended Changes ({len(intended_changes)})

{'No intended changes detected.' if not intended_changes else '\n'.join(f"1. **{c.description}** (confidence: {c.confidence:.2f})" for c in intended_changes)}

---

## Unintended Changes ({len(unintended_changes)})

{'No unintended changes detected - excellent!' if not unintended_changes else '\n'.join(f"1. **{c.description}** (severity: {c.severity.value if c.severity else 'unknown'}, confidence: {c.confidence:.2f})" for c in unintended_changes)}

---

## Summary

{'**Gemini Analysis**: ' + gemini_summary if gemini_summary else '**Pixel-level comparison only** (Gemini analysis disabled)'}

{'**Heatmap**: See ' + str(pixel_result.heatmap_path) if pixel_result.heatmap_path else ''}

---

*Generated by Where's Waldo Rick - Visual Regression MCP Server*
"""

        # Save report
        report_path.parent.mkdir(parents=True, exist_ok=True)
        with open(report_path, 'w') as f:
            f.write(report)

        logger.info(f"Report saved: {report_path}")
