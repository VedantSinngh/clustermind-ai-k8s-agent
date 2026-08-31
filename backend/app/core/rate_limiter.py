import time
from collections import defaultdict
from typing import Dict, List
from fastapi import HTTPException, status
from app.core.config import settings

class RateLimiter:
    def __init__(self, limit_per_hour: int = settings.RATE_LIMIT_INVESTIGATIONS_PER_HOUR):
        self.limit_per_hour = limit_per_hour
        self.requests: Dict[str, List[float]] = defaultdict(list)

    def check_rate_limit(self, user_id: str):
        now = time.time()
        one_hour_ago = now - 3600

        # Filter timestamps older than 1 hour
        self.requests[user_id] = [t for t in self.requests[user_id] if t > one_hour_ago]

        if len(self.requests[user_id]) >= self.limit_per_hour:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded: Maximum {self.limit_per_hour} investigations per hour allowed per user. Please wait before running another investigation."
            )

        self.requests[user_id].append(now)

rate_limiter = RateLimiter()
