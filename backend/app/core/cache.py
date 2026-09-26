import hashlib
import json
import logging
from typing import Dict, Any, Optional
import redis
from app.core.config import settings

logger = logging.getLogger(__name__)

class RedisTTLCache:
    def __init__(self, redis_url: str = settings.REDIS_URL, ttl_seconds: int = 300):
        self.ttl = ttl_seconds
        self.redis_url = redis_url
        self.fallback_cache: Dict[str, Dict[str, Any]] = {}
        try:
            self.r = redis.Redis.from_url(redis_url, decode_responses=True)
        except Exception as e:
            logger.warning(f"Redis cache initialization warning: {e}")
            self.r = None

    def _generate_key(self, payload: Dict[str, Any]) -> str:
        serialized = json.dumps(payload, sort_keys=True)
        return "cache:inv:" + hashlib.sha256(serialized.encode("utf-8")).hexdigest()

    def get(self, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        key = self._generate_key(payload)
        if self.r is not None:
            try:
                val = self.r.get(key)
                if val:
                    return json.loads(val)
            except Exception as e:
                logger.warning(f"Redis get cache failed: {e}")

        # Fallback in-memory
        entry = self.fallback_cache.get(key)
        if entry:
            import time
            if time.time() - entry["timestamp"] < self.ttl:
                return entry["data"]
            else:
                del self.fallback_cache[key]
        return None

    def set(self, payload: Dict[str, Any], result: Dict[str, Any]):
        key = self._generate_key(payload)
        if self.r is not None:
            try:
                self.r.setex(key, self.ttl, json.dumps(result))
                return
            except Exception as e:
                logger.warning(f"Redis setex cache failed: {e}")

        import time
        self.fallback_cache[key] = {
            "timestamp": time.time(),
            "data": result
        }

investigation_cache = RedisTTLCache()
