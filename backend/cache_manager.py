import json
import time
from pathlib import Path


class DataCache:
    """
    Dual cache: in-memory (primary, instant) + file-based (backup, survives restarts).
    On Render.com, file cache is ephemeral but in-memory works great.
    """

    def __init__(self, cache_dir="cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.cache_duration = 3600  # 1 hour in seconds

        # In-memory cache (FAST! No disk I/O)
        self._memory = {}

    def get(self, key):
        """Get cached data - checks memory first, then file"""
        # 1. Check in-memory cache (instant)
        if key in self._memory:
            entry = self._memory[key]
            if time.time() - entry["timestamp"] < self.cache_duration:
                return entry["data"]
            else:
                del self._memory[key]

        # 2. Check file cache (backup)
        cache_file = self.cache_dir / f"{key}.json"
        if cache_file.exists():
            try:
                with open(cache_file, "r", encoding="utf-8") as f:
                    cached = json.load(f)
                if time.time() - cached["timestamp"] < self.cache_duration:
                    # Promote to memory cache
                    self._memory[key] = cached
                    return cached["data"]
            except Exception:
                pass

        return None

    def set(self, key, data):
        """Store data in both memory and file cache"""
        entry = {"timestamp": time.time(), "data": data}

        # 1. Always set in memory (instant)
        self._memory[key] = entry

        # 2. Try to write to file (backup)
        try:
            cache_file = self.cache_dir / f"{key}.json"
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(entry, f, ensure_ascii=False, default=str)
        except Exception:
            pass  # File write failure is OK, memory cache still works

    def get_all_keys(self):
        """Get all valid cached keys"""
        return [k for k, v in self._memory.items()
                if time.time() - v["timestamp"] < self.cache_duration]

    def clear(self):
        """Clear all cache"""
        self._memory.clear()
        for cache_file in self.cache_dir.glob("*.json"):
            try:
                cache_file.unlink()
            except Exception:
                pass
        print("🗑️ Cache cleared")


# Global cache instance
cache = DataCache()