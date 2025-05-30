import time, threading, multiprocessing
from datetime import datetime, timedelta
from typing import List

from .logger import Logger

from ..utils.configuration import ConfigManager


class RateLimiter:
    """
    Rate limiter to ensure limits are respected in multithreading or multiprocessing
    Implements a token bucket algorithm for rate limiting
    """
    def __init__(self, logger: Logger = None):
        """
        Initialize rate limiter

        Args:
            logger: Logger instance for reporting rate limit events
        """
        # Load configurations
        self._config = ConfigManager.load()
        
        # Load logger
        self._logger = logger

        # Initialize either in multiprocessing or multithreading mode
        if self._config['multiprocessing_mode']:
            manager = multiprocessing.Manager()
            self._lock = manager.Lock()
            self._timestamps = manager.list()
            self._logger.debug("Multiprocessing RateLimiter config", self._config)
            self._logger.info(f"Multiprocessing RateLimiter initialized")
        else:
            self._lock = threading.Lock()
            self._timestamps: List[datetime] = []
            self._logger.debug("Multiprocessing RateLimiter config", self._config)
            self._logger.info(f"Multithreading RateLimiter initialized")

    def acquire(self) -> bool:
        """
        Wait until a request can be made without exceeding the rate limit

        Returns:
            True when the request can proceed
        """
        with self._lock:
            now = datetime.now()

            if isinstance(self._timestamps, list):
                # Regular list for threading mode
                self._timestamps = [ts for ts in self._timestamps if now - ts < timedelta(seconds=self._config['time_period'])]
            else:
                # Manager list for multiprocessing mode
                expired_indices = []
                for i, ts in enumerate(self._timestamps):
                    if now - ts >= timedelta(seconds=self._config['time_period']):
                        expired_indices.append(i)

                # Remove expired timestamps (in reverse order to not affect indices)
                for i in sorted(expired_indices, reverse=True):
                    self._timestamps.pop(i)

            # If we've reached the limit, wait
            if len(self._timestamps) >= self._config['limit']:
                if len(self._timestamps) > 0:  # Check if list is not empty
                    oldest = self._timestamps[0]
                    wait_time = (oldest + timedelta(seconds=self._config['time_period']) - now).total_seconds()
                    if wait_time > 0:
                        self._logger.debug(f"RateLimiter triggered for {wait_time:.2f} seconds")
                        time.sleep(wait_time)

            self._timestamps.append(now)
            return True

    def __enter__(self):
        """Context manager support"""
        self.acquire()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - no explicit release needed"""
        pass