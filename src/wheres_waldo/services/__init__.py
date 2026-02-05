"""Business logic services for Where's Waldo Rick."""

from wheres_waldo.services.baseline import BaselineService
from wheres_waldo.services.capture import CaptureService, PlatformDetector, ScreenshotCaptureError
from wheres_waldo.services.classification import ClassificationService
from wheres_waldo.services.comparison import ComparisonService, HeatmapColorScheme
from wheres_waldo.services.config import ConfigService
from wheres_waldo.services.gemini_integration import GeminiIntegrationService, GeminiRateLimiter
from wheres_waldo.services.storage import StorageService

__all__ = [
    "BaselineService",
    "CaptureService",
    "PlatformDetector",
    "ScreenshotCaptureError",
    "ClassificationService",
    "ComparisonService",
    "HeatmapColorScheme",
    "ConfigService",
    "GeminiIntegrationService",
    "GeminiRateLimiter",
    "StorageService",
]
