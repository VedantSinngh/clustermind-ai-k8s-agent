import hashlib
import json
import time
from typing import Dict, Any, Optional

class SimpleTTLCache:
    def __init__(self, ttl_seconds: int = 300):
        self.ttl = ttl_seconds
        self.cache: Dict[str, Dict[str, Any]] = {}

    def _generate_key(self, payload: Dict[str, Any]) -> str:
        serialized = json.dumps(payload, sort_keys=True)
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

    def get(self, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        key = self._generate_key(payload)
        entry = self.cache.get(key)
        if entry:
            if time.time() - entry["timestamp"] < self.ttl:
                return entry["data"]
            else:
                del self.cache[key]
        return None

    def set(self, payload: Dict[str, Any], result: Dict[str, Any]):
        key = self._generate_key(payload)
        self.cache[key] = {
            "timestamp": time.time(),
            "data": result
        }

investigation_cache = SimpleTTLCache(ttl_seconds=300) # 5-minute cache
