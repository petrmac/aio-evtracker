"""Exceptions for EV Tracker API client."""

from __future__ import annotations


class EVTrackerApiError(Exception):
    """Base exception for EV Tracker API errors."""


class EVTrackerAuthenticationError(EVTrackerApiError):
    """Exception for authentication errors (401, 403)."""


class EVTrackerConnectionError(EVTrackerApiError):
    """Exception for connection errors."""


class EVTrackerRateLimitError(EVTrackerApiError):
    """Exception for rate limit errors (429)."""
