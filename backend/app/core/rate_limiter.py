import time
import logging
from collections import defaultdict
from typing import Dict, List
from fastapi import HTTPException, status
import redis
from app.core.config import settings

logger = logging.getLogger(__name__)

class RedisRateLimiter:
    def __init__(self, redis_url: str = settings.REDIS_URL, limit_per_hour: int = settings.RATE_LIMIT_INVESTIGATIONS_PER_HOUR):
        self.limit_per_hour = limit_per_hour
        self.redis_url = redis_url
        self.fallback_requests: Dict[str, List[float]] = defaultdict(list)
        try:
            self.r = redis.Redis.from_url(redis_url, decode_responses=True)
        except Exception as e:
            logger.warning(f"Redis initialization warning: {e}. Falling back to local tracking.")
            self.r = None

    def check_rate_limit(self, user_id: str):
        now = time.time()
        one_hour_ago = now - 3600

        if self.r is not None:
            try:
                key = f"rate_limit:{user_id}"
                pipe = self.r.pipeline()
                pipe.zremrangebyscore(key, 0, one_hour_ago)
                pipe.zcard(key)
                pipe.zadd(key, {str(now): now})
                pipe.expire(key, 3600)
                res = pipe.execute()
                count = res[1]

                if count >= self.limit_per_hour:
                    raise HTTPException(
                        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                        detail=f"Rate limit exceeded: Maximum {self.limit_per_hour} investigations per hour allowed per user."
                    )
                return
            except redis.RedisError as e:
                logger.warning(f"Redis rate limiter unavailable ({e}). Using in-memory fallback.")

        # In-memory fallback if Redis is unreachable
        self.fallback_requests[user_id] = [t for t in self.fallback_requests[user_id] if t > one_hour_ago]
        if len(self.fallback_requests[user_id]) >= self.limit_per_hour:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded: Maximum {self.limit_per_hour} investigations per hour allowed per user."
            )
        self.fallback_requests[user_id].append(now)

rate_limiter = RedisRateLimiter()
