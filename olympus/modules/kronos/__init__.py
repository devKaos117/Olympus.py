"""
Kronos - A python package to deal with time, analysis and logging

This package provides tools for
advanced logging, time reporting and
rate limiting, in both single and
multi-threaded/multi-process environments
"""

from .logger import Logger
from .rate_limiter import RateLimiter

__all__ = ["Logger", "RateLimiter"]