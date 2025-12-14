"""Exceptions for Earnings Feed API client."""

from __future__ import annotations


class EarningsFeedError(Exception):
    """Base exception for Earnings Feed API errors."""

    pass


class AuthenticationError(EarningsFeedError):
    """Raised when API key is missing or invalid."""

    pass


class RateLimitError(EarningsFeedError):
    """Raised when rate limit is exceeded."""

    def __init__(
        self,
        message: str = "Rate limit exceeded",
        reset_at: int | None = None,
    ):
        super().__init__(message)
        self.reset_at = reset_at


class NotFoundError(EarningsFeedError):
    """Raised when a resource is not found."""

    pass


class ValidationError(EarningsFeedError):
    """Raised when request parameters are invalid."""

    pass


class APIError(EarningsFeedError):
    """Raised for general API errors."""

    def __init__(
        self,
        message: str,
        status_code: int | None = None,
        code: str | None = None,
    ):
        super().__init__(message)
        self.status_code = status_code
        self.code = code
