"""Async Python client for EV Tracker API."""

from .client import DEFAULT_API_BASE_URL, EVTrackerClient
from .exceptions import (
    EVTrackerApiError,
    EVTrackerAuthenticationError,
    EVTrackerConnectionError,
    EVTrackerRateLimitError,
)
from .models import Car, ChargingSession, HomeAssistantState

__all__ = [
    "EVTrackerClient",
    "EVTrackerApiError",
    "EVTrackerAuthenticationError",
    "EVTrackerConnectionError",
    "EVTrackerRateLimitError",
    "Car",
    "ChargingSession",
    "HomeAssistantState",
    "DEFAULT_API_BASE_URL",
]

__version__ = "0.1.0"
