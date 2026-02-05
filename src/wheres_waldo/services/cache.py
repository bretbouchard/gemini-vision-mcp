"""Aggressive caching service for comparison results.

Uses hash-based cache keys to minimize redundant Gemini API calls.
Target: >60% cache hit rate for repeated comparisons.
"""

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from wheres_waldo.models.domain import ComparisonResult
from wheres_waldo.services.storage import StorageService
from wheres_waldo.utils.helpers import hash_image_pair
from wheres_waldo.utils.logging import get_logger

logger = get_logger(__name__)


class CacheEntry:
    """Cache entry for comparison results."""

    def __init__(
        self,
        cache_key: str,
        result: ComparisonResult,
        timestamp: datetime,
    ) -> None:
        """Initialize cache entry.

        Args:
            cache_key: Hash-based cache key
            result: Comparison result to cache
            timestamp: Cache entry timestamp
        """
        self.cache_key = cache_key
        self.result = result
        self.timestamp = timestamp

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization.

        Returns:
            Dictionary representation
        """
        return {
            "cache_key": self.cache_key,
            "timestamp": self.timestamp.isoformat(),
            "result": {
                "before_path": str(self.result.before_path),
                "after_path": str(self.result.after_path),
                "threshold": self.result.threshold,
                "changed_pixels": self.result.changed_pixels,
                "total_pixels": self.result.total_pixels,
                "changed_percentage": self.result.changed_percentage,
                "passed": self.result.passed,
                "failure_reason": self.result.failure_reason,
                "intended_changes": [
                    {
                        "description": c.description,
                        "bbox": c.bbox,
                        "confidence": c.confidence,
                    }
                    for c in self.result.intended_changes
                ],
                "unintended_changes": [
                    {
                        "description": c.description,
                        "bbox": c.bbox,
                        "severity": c.severity.value if c.severity else None,
                        "confidence": c.confidence,
                    }
                    for c in self.result.unintended_changes
                ],
                "timestamp": self.result.timestamp.isoformat(),
            },
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CacheEntry":
        """Create cache entry from dictionary.

        Args:
            data: Dictionary from JSON file

        Returns:
            CacheEntry instance
        """
        from wheres_waldo.models.domain import ChangeRegion, Severity

        result_data = data["result"]

        # Reconstruct ChangeRegion objects
        intended_changes = [
            ChangeRegion(
                description=c["description"],
                bbox=c["bbox"],
                confidence=c["confidence"],
            )
            for c in result_data.get("intended_changes", [])
        ]

        unintended_changes = []
        for c in result_data.get("unintended_changes", []):
            change = ChangeRegion(
                description=c["description"],
                bbox=c["bbox"],
                confidence=c["confidence"],
            )
            if c.get("severity"):
                change.severity = Severity(c["severity"])
            unintended_changes.append(change)

        # Reconstruct ComparisonResult
        result = ComparisonResult(
            before_path=Path(result_data["before_path"]),
            after_path=Path(result_data["after_path"]),
            threshold=result_data["threshold"],
            changed_pixels=result_data["changed_pixels"],
            total_pixels=result_data["total_pixels"],
            changed_percentage=result_data["changed_percentage"],
            intended_changes=intended_changes,
            unintended_changes=unintended_changes,
            passed=result_data["passed"],
            failure_reason=result_data.get("failure_reason"),
            heatmap_path=None,  # Not cached to save space
            report_path=None,  # Not cached to save space
            timestamp=datetime.fromisoformat(result_data["timestamp"]),
        )

        return cls(
            cache_key=data["cache_key"],
            result=result,
            timestamp=datetime.fromisoformat(data["timestamp"]),
        )


class CacheService:
    """Aggressive caching service for comparison results.

    Minimizes redundant Gemini API calls through hash-based caching.
    """

    def __init__(
        self,
        storage_service: StorageService | None = None,
        cache_ttl_hours: int = 24,
    ) -> None:
        """Initialize cache service.

        Args:
            storage_service: Storage service (creates if None)
            cache_ttl_hours: Time-to-live for cache entries in hours
        """
        self.storage_service = storage_service or StorageService()
        self.cache_ttl = timedelta(hours=cache_ttl_hours)
        self.cache_dir = self.storage_service.config.base_dir / "cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # In-memory cache for faster access
        self._memory_cache: dict[str, CacheEntry] = {}

        # Statistics
        self._hits = 0
        self._misses = 0

        logger.info(f"CacheService initialized with TTL={cache_ttl_hours}h")

    def get_cache_key(
        self,
        before_path: Path,
        after_path: Path,
        threshold: int,
    ) -> str:
        """Generate cache key for image pair.

        Args:
            before_path: Path to before image
            after_path: Path to after image
            threshold: Pixel threshold used

        Returns:
            SHA256 hash-based cache key
        """
        return hash_image_pair(before_path, after_path, threshold)

    def get(self, cache_key: str) -> ComparisonResult | None:
        """Get cached comparison result.

        Args:
            cache_key: Cache key to look up

        Returns:
            Cached comparison result if found and valid, None otherwise
        """
        # Check memory cache first
        if cache_key in self._memory_cache:
            entry = self._memory_cache[cache_key]

            # Check if entry is still valid
            if datetime.now() - entry.timestamp < self.cache_ttl:
                self._hits += 1
                logger.info(f"Cache HIT (memory): {cache_key[:16]}...")
                return entry.result
            else:
                # Entry expired, remove from memory cache
                del self._memory_cache[cache_key]
                logger.debug(f"Cache entry expired: {cache_key[:16]}...")

        # Check disk cache
        cache_file = self.cache_dir / f"{cache_key}.json"
        if cache_file.exists():
            try:
                with open(cache_file, "r") as f:
                    data = json.load(f)

                entry = CacheEntry.from_dict(data)

                # Check if entry is still valid
                if datetime.now() - entry.timestamp < self.cache_ttl:
                    # Add to memory cache
                    self._memory_cache[cache_key] = entry
                    self._hits += 1
                    logger.info(f"Cache HIT (disk): {cache_key[:16]}...")
                    return entry.result
                else:
                    # Entry expired, remove from disk
                    cache_file.unlink()
                    logger.debug(f"Expired cache file removed: {cache_key[:16]}...")

            except Exception as e:
                logger.error(f"Failed to load cache file {cache_file}: {e}")

        # Cache miss
        self._misses += 1
        logger.info(f"Cache MISS: {cache_key[:16]}...")
        return None

    def put(
        self,
        cache_key: str,
        result: ComparisonResult,
    ) -> None:
        """Cache comparison result.

        Args:
            cache_key: Cache key
            result: Comparison result to cache
        """
        entry = CacheEntry(
            cache_key=cache_key,
            result=result,
            timestamp=datetime.now(),
        )

        # Add to memory cache
        self._memory_cache[cache_key] = entry

        # Write to disk cache
        cache_file = self.cache_dir / f"{cache_key}.json"
        try:
            with open(cache_file, "w") as f:
                json.dump(entry.to_dict(), f, indent=2)
            logger.debug(f"Cache entry saved: {cache_key[:16]}...")
        except Exception as e:
            logger.error(f"Failed to save cache file {cache_file}: {e}")

    def invalidate(self, cache_key: str) -> None:
        """Invalidate cache entry.

        Args:
            cache_key: Cache key to invalidate
        """
        # Remove from memory cache
        if cache_key in self._memory_cache:
            del self._memory_cache[cache_key]

        # Remove from disk cache
        cache_file = self.cache_dir / f"{cache_key}.json"
        if cache_file.exists():
            cache_file.unlink()
            logger.info(f"Cache entry invalidated: {cache_key[:16]}...")

    def clear(self) -> dict[str, Any]:
        """Clear all cache entries.

        Returns:
            Dictionary with clear results
        """
        # Clear memory cache
        memory_count = len(self._memory_cache)
        self._memory_cache.clear()

        # Clear disk cache
        disk_count = 0
        freed_bytes = 0

        for cache_file in self.cache_dir.glob("*.json"):
            file_size = cache_file.stat().st_size
            cache_file.unlink()
            disk_count += 1
            freed_bytes += file_size

        logger.info(f"Cache cleared: {memory_count} memory entries, {disk_count} disk entries")

        return {
            "memory_entries_cleared": memory_count,
            "disk_entries_cleared": disk_count,
            "freed_bytes": freed_bytes,
            "freed_mb": round(freed_bytes / (1024 * 1024), 2),
        }

    def cleanup_expired(self) -> dict[str, Any]:
        """Clean up expired cache entries.

        Returns:
            Dictionary with cleanup results
        """
        now = datetime.now()
        expired_count = 0
        freed_bytes = 0

        # Check disk cache files
        for cache_file in self.cache_dir.glob("*.json"):
            try:
                # Check file modification time
                mtime = datetime.fromtimestamp(cache_file.stat().st_mtime)

                if now - mtime > self.cache_ttl:
                    file_size = cache_file.stat().st_size
                    cache_file.unlink()
                    expired_count += 1
                    freed_bytes += file_size
            except Exception as e:
                logger.error(f"Failed to process cache file {cache_file}: {e}")

        # Also clean up memory cache
        expired_keys = [
            key
            for key, entry in self._memory_cache.items()
            if now - entry.timestamp > self.cache_ttl
        ]

        for key in expired_keys:
            del self._memory_cache[key]

        logger.info(f"Cleaned up {expired_count} expired cache entries")

        return {
            "expired_entries_removed": expired_count,
            "freed_bytes": freed_bytes,
            "freed_mb": round(freed_bytes / (1024 * 1024), 2),
        }

    def get_stats(self) -> dict[str, Any]:
        """Get cache statistics.

        Returns:
            Dictionary with cache statistics
        """
        total_requests = self._hits + self._misses
        hit_rate = (self._hits / total_requests) if total_requests > 0 else 0.0

        # Count disk cache files
        disk_count = len(list(self.cache_dir.glob("*.json")))
        memory_count = len(self._memory_cache)

        # Calculate disk usage
        disk_bytes = sum(
            cache_file.stat().st_size
            for cache_file in self.cache_dir.glob("*.json")
        )

        return {
            "hits": self._hits,
            "misses": self._misses,
            "total_requests": total_requests,
            "hit_rate": round(hit_rate * 100, 2),  # Percentage
            "memory_entries": memory_count,
            "disk_entries": disk_count,
            "total_entries": memory_count + disk_count,
            "disk_usage_bytes": disk_bytes,
            "disk_usage_mb": round(disk_bytes / (1024 * 1024), 2),
            "target_hit_rate": 60.0,  # 60% target
            "target_met": hit_rate >= 0.6,
        ]
