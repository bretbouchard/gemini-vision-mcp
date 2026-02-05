"""Domain models for Where's Waldo Rick.

All models use Pydantic for validation and serialization.
"""

from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field, field_validator


class Platform(str, Enum):
    """Screenshot capture platforms."""

    MACOS = "macos"
    IOS = "ios"
    WEB = "web"
    AUTO = "auto"


class Quality(str, Enum):
    """Screenshot resolution scaling."""

    X1 = "1x"  # Standard
    X2 = "2x"  # Retina
    X3 = "3x"  # Super high-res


class ImageFormat(str, Enum):
    """Screenshot file formats."""

    PNG = "png"  # Lossless
    JPEG = "jpeg"  # Compressed
    WEBP = "webp"  # Modern compressed


class Severity(str, Enum):
    """Regression severity levels."""

    CRITICAL = "critical"  # Center-stage layout breaks, text unreadability
    MAJOR = "major"  # Misalignment, overflow, spacing issues
    MINOR = "minor"  # 1px shifts, color variations


class Screenshot(BaseModel):
    """Screenshot metadata and storage information."""

    path: Path = Field(description="Absolute path to screenshot file")
    name: str = Field(description="Descriptive name for the screenshot")
    timestamp: datetime = Field(default_factory=datetime.now)
    platform: Platform = Field(default=Platform.AUTO)
    quality: Quality = Field(default=Quality.X2)
    format: ImageFormat = Field(default=ImageFormat.PNG)
    resolution: str | None = Field(default=None, description="Resolution as 'WxH' string")
    file_size_bytes: int | None = Field(default=None)

    @field_validator("path")
    @classmethod
    def validate_path_exists(cls, v: Path) -> Path:
        """Validate that screenshot file exists (optional for new screenshots)."""
        # Don't validate existence for new screenshots (created after capture)
        return v

    def get_relative_path(self, base_dir: Path) -> Path:
        """Get path relative to base directory."""
        try:
            return self.path.relative_to(base_dir)
        except ValueError:
            return self.path


class ExpectedChange(BaseModel):
    """Single expected change annotation."""

    description: str = Field(description="Natural language description of the change")
    bbox: list[int] | None = Field(
        default=None,
        description="Bounding box [x, y, width, height] if known",
    )
    element: str | None = Field(
        default=None,
        description="UI element identifier (e.g., 'card', 'button')",
    )


class Baseline(BaseModel):
    """Baseline screenshot with expected changes."""

    baseline_id: str = Field(description="Unique baseline identifier (timestamp-based)")
    screenshot: Screenshot = Field(description="Baseline screenshot metadata")
    phase: str = Field(description="Phase name or identifier")
    expected_changes: list[ExpectedChange] = Field(
        default_factory=list,
        description="List of expected changes for this baseline",
    )
    description: str | None = Field(
        default=None,
        description="Free-text description of the baseline",
    )
    created_at: datetime = Field(default_factory=datetime.now)


class ChangeRegion(BaseModel):
    """Detected change region with classification."""

    bbox: list[int] = Field(description="Bounding box [x, y, width, height]")
    description: str = Field(description="Natural language description of the change")
    confidence: float = Field(
        ge=0.0,
        le=1.0,
        description="Confidence score (0-1)",
    )
    intended: bool | None = Field(
        default=None,
        description="True if intended, False if unintended, None if unknown",
    )
    severity: Severity | None = Field(
        default=None,
        description="Severity level if unintended change",
    )


class ComparisonResult(BaseModel):
    """Result of comparing two screenshots."""

    before_path: Path = Field(description="Path to baseline screenshot")
    after_path: Path = Field(description="Path to current screenshot")
    threshold: int = Field(description="Pixel threshold used for comparison")

    # Pixel-level statistics
    changed_pixels: int = Field(description="Number of changed pixels")
    total_pixels: int = Field(description="Total pixels in image")
    changed_percentage: float = Field(description="Percentage of changed pixels")

    # Classification
    intended_changes: list[ChangeRegion] = Field(
        default_factory=list,
        description="Changes matching expected changes",
    )
    unintended_changes: list[ChangeRegion] = Field(
        default_factory=list,
        description="Changes not in expected list",
    )

    # Pass/fail determination
    passed: bool = Field(description="Overall pass/fail status")
    failure_reason: str | None = Field(
        default=None,
        description="Reason for failure if not passed",
    )

    # Output files
    heatmap_path: Path | None = Field(
        default=None,
        description="Path to heatmap visualization",
    )
    report_path: Path | None = Field(
        default=None,
        description="Path to markdown comparison report",
    )

    timestamp: datetime = Field(default_factory=datetime.now)


class ComparisonConfig(BaseModel):
    """Configuration for screenshot comparison."""

    pixel_threshold: int = Field(
        default=2,
        ge=1,
        le=3,
        description="Pixel threshold for change detection",
    )
    max_changed_regions: int = Field(
        default=10,
        ge=0,
        description="Maximum number of changed regions for pass",
    )
    max_changed_percentage: float = Field(
        default=0.5,
        ge=0.0,
        le=100.0,
        description="Maximum percentage of changed pixels for pass",
    )
    enable_anti_aliasing_filter: bool = Field(
        default=True,
        description="Enable Gaussian blur preprocessing",
    )
    anti_aliasing_kernel_size: int = Field(
        default=2,
        ge=1,
        le=5,
        description="Gaussian blur kernel size",
    )

    # Agentic vision settings
    enable_agentic_vision: bool = Field(
        default=True,
        description="Use Gemini agentic vision for analysis",
    )
    progressive_resolution: bool = Field(
        default=True,
        description="Start with low resolution, upgrade if needed",
    )
    min_confidence_threshold: float = Field(
        default=0.8,
        ge=0.0,
        le=1.0,
        description="Minimum confidence to stop resolution upgrades",
    )


class StorageConfig(BaseModel):
    """Configuration for screenshot storage."""

    base_dir: Path = Field(
        default=Path(".screenshots"),
        description="Base directory for all screenshot storage",
    )
    phases_dir: Path = Field(
        default=Path(".screenshots/phases"),
        description="Directory for phase screenshots",
    )
    cache_dir: Path = Field(
        default=Path(".screenshots/cache"),
        description="Directory for comparison cache",
    )
    reports_dir: Path = Field(
        default=Path(".screenshots/reports"),
        description="Directory for comparison reports",
    )
    conversations_dir: Path = Field(
        default=Path(".screenshots/conversations"),
        description="Directory for conversation history",
    )

    retention_days: int = Field(
        default=7,
        ge=1,
        description="Number of days to retain screenshots",
    )
    max_storage_mb: int | None = Field(
        default=None,
        description="Maximum storage in MB (None = unlimited)",
    )

    # Auto-cleanup settings
    enable_auto_cleanup: bool = Field(
        default=False,
        description="Automatically clean up old screenshots",
    )


class AppConfig(BaseModel):
    """Global application configuration."""

    comparison: ComparisonConfig = Field(
        default_factory=ComparisonConfig,
        description="Comparison settings",
    )
    storage: StorageConfig = Field(
        default_factory=StorageConfig,
        description="Storage settings",
    )

    # Platform settings
    default_platform: Platform = Field(
        default=Platform.AUTO,
        description="Default capture platform",
    )
    default_quality: Quality = Field(
        default=Quality.X2,
        description="Default screenshot quality",
    )
    default_format: ImageFormat = Field(
        default=ImageFormat.PNG,
        description="Default screenshot format",
    )

    # API keys
    gemini_api_key: str | None = Field(
        default=None,
        description="Gemini API key (from environment if not set)",
    )
