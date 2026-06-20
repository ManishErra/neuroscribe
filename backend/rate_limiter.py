import time
from fastapi import Request, HTTPException, status
from collections import defaultdict
from typing import Dict, List

class RateLimiter:
    def __init__(self, limit: int, window_seconds: int):
        self.limit = limit
        self.window_seconds = window_seconds
        # Maps client IP key to a list of timestamps
        self.history: Dict[str, List[float]] = defaultdict(list)

    def check(self, request: Request):
        # Resolve client IP (supporting X-Forwarded-For proxies)
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            key = forwarded.split(",")[0].strip()
        else:
            key = request.client.host if request.client else "127.0.0.1"

        now = time.time()
        # Filter timestamps within current sliding window
        self.history[key] = [t for t in self.history[key] if now - t < self.window_seconds]
        
        if len(self.history[key]) >= self.limit:
            # Calculate remaining retry time
            retry_after = int(self.window_seconds - (now - self.history[key][0]))
            if retry_after <= 0:
                retry_after = 1
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Too many requests. Please try again in {retry_after} seconds.",
                headers={"Retry-After": str(retry_after)}
            )
        self.history[key].append(now)

# Instantiate rate limiters with designated rules
login_limiter = RateLimiter(limit=5, window_seconds=60)
register_limiter = RateLimiter(limit=5, window_seconds=60)
note_limiter = RateLimiter(limit=10, window_seconds=60)
audio_limiter = RateLimiter(limit=10, window_seconds=60)
rag_limiter = RateLimiter(limit=20, window_seconds=60)
