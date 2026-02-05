"""Business logic services for Where's Waldo Rick."""

from wheres_waldo.services.baseline import BaselineService
from wheres_waldo.services.capture import CaptureService, PlatformDetector, ScreenshotCaptureError
from wheres_waldo.services.config import ConfigService
from wheres_waldo.services.storage import StorageService

__all__ = [
    "BaselineService",
    "CaptureService",
    "PlatformDetector",
    "ScreenshotCaptureError",
    "ConfigService",
    "StorageService",
]
