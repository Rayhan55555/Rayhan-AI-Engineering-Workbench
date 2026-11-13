import time
from typing import Dict, List


class SlidingWindowRateLimiter:
    """
    Sliding window in-memory rate limiter per provider.
    Ensures provider quotas (RPM - requests per minute) are never exceeded.
    """
    def __init__(self, max_requests_per_window: int = 15, window_seconds: int = 60):
        self.max_requests = max_requests_per_window
        self.window_seconds = window_seconds
        self._provider_history: Dict[str, List[float]] = {}

    def is_allowed(self, provider: str) -> bool:
        now = time.time()
        timestamps = self._provider_history.get(provider, [])
        # Filter timestamps within current window
        valid = [t for t in timestamps if now - t < self.window_seconds]
        self._provider_history[provider] = valid
        return len(valid) < self.max_requests

    def record_request(self, provider: str):
        now = time.time()
        if provider not in self._provider_history:
            self._provider_history[provider] = []
        self._provider_history[provider].append(now)

    def remaining(self, provider: str) -> int:
        now = time.time()
        timestamps = self._provider_history.get(provider, [])
        valid = [t for t in timestamps if now - t < self.window_seconds]
        self._provider_history[provider] = valid
        return max(0, self.max_requests - len(valid))
