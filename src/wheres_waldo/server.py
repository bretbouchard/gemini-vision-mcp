"""Where's Waldo Rick - MCP Server.

This module implements the MCP server with tools for visual regression testing
using Gemini 3 Flash's agentic vision capabilities.
"""

import sys
from typing import Any

from mcp.server.fastmcp import FastMCP

from wheres_waldo.utils.logging import get_logger, setup_logging

# Get logger (all logs go to stderr)
logger = get_logger(__name__)

# Create MCP server instance
mcp = FastMCP("wheres-waldo-rick")

# Set up exception handler
setup_logging(mcp)
logger.info("Where's Waldo Rick MCP server initialized")


@mcp.tool()
async def visual_capture(name: str, platform: str = "auto") -> dict[str, Any]:
    """Capture a screenshot and store it for visual regression testing.

    Args:
        name: Descriptive name for the screenshot (e.g., "Phase 3 - Before card update")
        platform: Platform to capture from (auto, macos, ios, web)

    Returns:
        Dictionary with screenshot path, metadata, and success status

    Example:
        >>> await visual_capture("Phase 3 - Before card update", "macos")
        {
            "success": true,
            "path": "/project/.screenshots/phases/3-before-card-update.png",
            "timestamp": "2025-02-04T20:00:00Z",
            "platform": "macos",
            "resolution": "2560x1440"
        }
    """
    # TODO: P1-PLAN-1: Implement tool stub
    # TODO: P2-PLAN-1: Add platform detection
    # TODO: P2-PLAN-2/3/4: Add platform-specific capture logic
    return {
        "success": False,
        "error": "Tool stub - not yet implemented",
        "path": None,
        "timestamp": None,
        "platform": platform,
    }


@mcp.tool()
async def visual_prepare(
    phase: str,
    expected_changes: str,
) -> dict[str, Any]:
    """Declare a baseline with expected changes before development work begins.

    Args:
        phase: Phase name or identifier (e.g., "Phase 3 - Card Layout Update")
        expected_changes: Description of expected changes (natural language or JSON)

    Returns:
        Dictionary with baseline ID and stored metadata

    Example:
        >>> await visual_prepare(
        ...     "Phase 3 - Card Layout Update",
        ...     "Card padding increases by 2px, button moves to right"
        ... )
        {
            "success": true,
            "baseline_id": "20250204-200000-3-card-layout-update",
            "phase": "Phase 3 - Card Layout Update",
            "expected_changes": "Card padding increases by 2px, button moves to right",
            "timestamp": "2025-02-04T20:00:00Z"
        }
    """
    # TODO: P1-PLAN-1: Implement tool stub
    # TODO: P2-PLAN-5: Add baseline declaration logic
    # TODO: P2-PLAN-5: Add expected changes parsing
    return {
        "success": False,
        "error": "Tool stub - not yet implemented",
        "baseline_id": None,
        "phase": phase,
        "expected_changes": expected_changes,
        "timestamp": None,
    }


@mcp.tool()
async def visual_compare(
    before_path: str,
    after_path: str,
    threshold: int = 2,
) -> dict[str, Any]:
    """Compare two screenshots with pixel-level precision and agentic vision analysis.

    Args:
        before_path: Path to baseline screenshot
        after_path: Path to current screenshot
        threshold: Pixel threshold for change detection (1, 2, or 3)

    Returns:
        Dictionary with comparison results, annotations, and pass/fail status

    Example:
        >>> await visual_compare(
        ...     "screenshots/phases/3-before.png",
        ...     "screenshots/phases/4-after.png",
        ...     threshold=2
        ... )
        {
            "success": true,
            "pass": false,
            "changed_pixels": 1523,
            "changed_percentage": 0.12,
            "intended_changes": [
                {"description": "Card padding increased by 2px", "bbox": [100, 200, 300, 400]}
            ],
            "unintended_changes": [
                {"description": "Title shifted 5px down", "severity": "major"}
            ],
            "heatmap_path": "screenshots/reports/20250204-200000-heatmap.png",
            "report_path": "screenshots/reports/20250204-200000-report.md"
        }
    """
    # TODO: P1-PLAN-1: Implement tool stub
    # TODO: P3-PLAN-1: Add OpenCV pixel diffing
    # TODO: P3-PLAN-2: Add anti-aliasing noise reduction
    # TODO: P3-PLAN-3: Add heatmap visualization
    # TODO: P3-PLAN-4: Add Gemini agentic vision integration
    # TODO: P3-PLAN-6: Add intelligent change interpretation
    # TODO: P3-PLAN-7: Add intended vs unintended classification
    return {
        "success": False,
        "error": "Tool stub - not yet implemented",
        "pass": None,
        "changed_pixels": None,
        "changed_percentage": None,
        "intended_changes": [],
        "unintended_changes": [],
        "heatmap_path": None,
        "report_path": None,
    }


@mcp.tool()
async def visual_cleanup(
    retention_days: int = 7,
) -> dict[str, Any]:
    """Clean up old screenshots and cache to free disk space.

    Args:
        retention_days: Number of days to retain screenshots (default: 7)

    Returns:
        Dictionary with cleanup results and storage statistics

    Example:
        >>> await visual_cleanup(retention_days=7)
        {
            "success": true,
            "deleted_screenshots": 23,
            "freed_space_mb": 45.2,
            "remaining_screenshots": 12,
            "storage_usage_mb": 23.1
        }
    """
    # TODO: P1-PLAN-1: Implement tool stub
    # TODO: P4-PLAN-4: Add cleanup logic
    return {
        "success": False,
        "error": "Tool stub - not yet implemented",
        "deleted_screenshots": 0,
        "freed_space_mb": 0.0,
        "remaining_screenshots": 0,
        "storage_usage_mb": 0.0,
    }


def main() -> None:
    """Start the MCP server.

    IMPORTANT: All logging must go to stderr to avoid polluting stdout,
    which must contain only valid JSON-RPC messages.
    """
    # Run the MCP server
    mcp.run()


if __name__ == "__main__":
    main()
