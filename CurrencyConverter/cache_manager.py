import json
import os
from datetime import datetime, timedelta
from typing import Dict, Optional

class CacheManager:
    """Manages caching of exchange rates for offline fallback."""
    
    def __init__(self, cache_file: str = "exchange_cache.json"):
        self.cache_file = cache_file
        self.cache_duration = timedelta(hours=1)  # Cache expires after 1 hour
        self._cache_data = self._load_cache()
    
    def _load_cache(self) -> Dict:
        """Load cache data from file."""
        try:
            if os.path.exists(self.cache_file):
                with open(self.cache_file, 'r') as f:
                    cache_data = json.load(f)
                    # Validate cache format
                    if isinstance(cache_data, dict) and "rates" in cache_data:
                        return cache_data
            return {"rates": {}, "metadata": {}}
        except Exception:
            return {"rates": {}, "metadata": {}}
    
    def _save_cache(self):
        """Save cache data to file."""
        try:
            with open(self.cache_file, 'w') as f:
                json.dump(self._cache_data, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save cache: {e}")
    
    def _get_cache_key(self, from_currency: str, to_currency: str) -> str:
        """Generate cache key for currency pair."""
        return f"{from_currency}_{to_currency}"
    
    def cache_rate(self, from_currency: str, to_currency: str, exchange_rate: float):
        """
        Cache an exchange rate.
        
        Args:
            from_currency: Source currency code
            to_currency: Target currency code
            exchange_rate: Exchange rate to cache
        """
        cache_key = self._get_cache_key(from_currency, to_currency)
        timestamp = datetime.now().isoformat()
        
        self._cache_data["rates"][cache_key] = {
            "rate": exchange_rate,
            "timestamp": timestamp,
            "from_currency": from_currency,
            "to_currency": to_currency
        }
        
        # Update metadata
        self._cache_data["metadata"]["last_update"] = timestamp
        self._cache_data["metadata"]["total_cached"] = len(self._cache_data["rates"])
        
        self._save_cache()
    
    def get_cached_rate(self, from_currency: str, to_currency: str) -> Optional[float]:
        """
        Get cached exchange rate if available and not expired.
        
        Args:
            from_currency: Source currency code
            to_currency: Target currency code
            
        Returns:
            Cached exchange rate or None if not available/expired
        """
        cache_key = self._get_cache_key(from_currency, to_currency)
        
        if cache_key not in self._cache_data["rates"]:
            # Try reverse lookup
            reverse_key = self._get_cache_key(to_currency, from_currency)
            if reverse_key in self._cache_data["rates"]:
                cached_entry = self._cache_data["rates"][reverse_key]
                if self._is_cache_valid(cached_entry["timestamp"]):
                    # Return reciprocal of cached rate
                    return 1.0 / cached_entry["rate"]
            return None
        
        cached_entry = self._cache_data["rates"][cache_key]
        
        # Check if cache is still valid
        if self._is_cache_valid(cached_entry["timestamp"]):
            return cached_entry["rate"]
        else:
            # Remove expired entry
            del self._cache_data["rates"][cache_key]
            self._save_cache()
            return None
    
    def _is_cache_valid(self, timestamp_str: str) -> bool:
        """Check if cached data is still valid (not expired)."""
        try:
            cached_time = datetime.fromisoformat(timestamp_str)
            return datetime.now() - cached_time < self.cache_duration
        except Exception:
            return False
    
    def get_cache_info(self) -> Dict:
        """Get information about cached data."""
        total_cached = len(self._cache_data["rates"])
        valid_cached = 0
        
        for cache_key, cached_entry in self._cache_data["rates"].items():
            if self._is_cache_valid(cached_entry["timestamp"]):
                valid_cached += 1
        
        last_update = self._cache_data.get("metadata", {}).get("last_update", "Never")
        if last_update != "Never":
            try:
                last_update_dt = datetime.fromisoformat(last_update)
                last_update = last_update_dt.strftime("%Y-%m-%d %H:%M:%S")
            except:
                last_update = "Unknown"
        
        return {
            "count": f"{valid_cached}/{total_cached}",
            "last_update": last_update,
            "cache_file": self.cache_file
        }
    
    def clear_cache(self):
        """Clear all cached data."""
        self._cache_data = {"rates": {}, "metadata": {}}
        self._save_cache()
    
    def clear_expired_cache(self):
        """Remove expired cache entries."""
        expired_keys = []
        
        for cache_key, cached_entry in self._cache_data["rates"].items():
            if not self._is_cache_valid(cached_entry["timestamp"]):
                expired_keys.append(cache_key)
        
        for key in expired_keys:
            del self._cache_data["rates"][key]
        
        if expired_keys:
            self._save_cache()
        
        return len(expired_keys)
