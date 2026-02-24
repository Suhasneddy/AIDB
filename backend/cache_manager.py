import json
import time
from pathlib import Path

class DataCache:
    """Simple file-based cache to avoid repeated API calls"""
    
    def __init__(self, cache_dir="cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.cache_duration = 3600  # 1 hour in seconds
    
    def get(self, key):
        """Get cached data if it exists and is fresh"""
        cache_file = self.cache_dir / f"{key}.json"
        
        if not cache_file.exists():
            return None
        
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                cached = json.load(f)
            
            # Check if cache is still fresh
            if time.time() - cached['timestamp'] < self.cache_duration:
                print(f"✅ Using cached data for {key}")
                return cached['data']
            else:
                print(f"⏰ Cache expired for {key}")
                return None
                
        except Exception as e:
            print(f"⚠️ Cache read error: {e}")
            return None
    
    def set(self, key, data):
        """Store data in cache"""
        cache_file = self.cache_dir / f"{key}.json"
        
        try:
            cached = {
                'timestamp': time.time(),
                'data': data
            }
            
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(cached, f, ensure_ascii=False, indent=2)
            
            print(f"💾 Cached data for {key}")
            
        except Exception as e:
            print(f"⚠️ Cache write error: {e}")
    
    def clear(self):
        """Clear all cache"""
        for cache_file in self.cache_dir.glob("*.json"):
            cache_file.unlink()
        print("🗑️ Cache cleared")


# Global cache instance
cache = DataCache()