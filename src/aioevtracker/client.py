"""Async API client for EV Tracker."""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any, cast

import aiohttp

from .exceptions import (
    EVTrackerApiError,
    EVTrackerAuthenticationError,
    EVTrackerConnectionError,
    EVTrackerRateLimitError,
)
from .models import Car, ChargingSession, HomeAssistantState

if TYPE_CHECKING:
    from aiohttp import ClientSession

_LOGGER = logging.getLogger(__name__)

DEFAULT_API_BASE_URL = "https://api.evtracker.cz/api/v1"

# API endpoints
ENDPOINT_CARS = "/cars"
ENDPOINT_CARS_DEFAULT = "/cars/default"
ENDPOINT_SESSIONS = "/sessions"
ENDPOINT_SESSIONS_SIMPLE = "/sessions/simple"
ENDPOINT_HA_STATE = "/homeassistant/state"


def _format_datetime_for_api(dt: datetime | str | None) -> str | None:
    """Format datetime for the backend API.

    The backend expects ISO format with Z suffix (UTC timezone).
    Example: 2025-11-26T22:00:00Z
    """
    if dt is None:
        return None

    if isinstance(dt, str):
        return dt

    # Convert to UTC and format with Z suffix
    if dt.tzinfo is None:
        dt = dt.astimezone(UTC)
    else:
        dt = dt.astimezone(UTC)

    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


class EVTrackerClient:
    """Async API client for EV Tracker.

    Args:
        api_key: API key from EV Tracker settings.
        session: Optional aiohttp ClientSession. If not provided, a new session
            will be created and managed internally.
        base_url: Base URL for the API. Defaults to production URL.
        user_agent: User-Agent header value.
    """

    def __init__(
        self,
        api_key: str,
        session: ClientSession | None = None,
        base_url: str = DEFAULT_API_BASE_URL,
        user_agent: str | None = None,
    ) -> None:
        """Initialize the API client."""
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self._session = session
        self._owned_session = False
        self._user_agent = user_agent or "aioevtracker"

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create an aiohttp session."""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
            self._owned_session = True
        return self._session

    async def close(self) -> None:
        """Close the session if we own it."""
        if self._owned_session and self._session and not self._session.closed:
            await self._session.close()

    async def __aenter__(self) -> EVTrackerClient:
        """Async context manager entry."""
        return self

    async def __aexit__(self, *args: Any) -> None:
        """Async context manager exit."""
        await self.close()

    def _get_headers(self) -> dict[str, str]:
        """Get headers for API requests."""
        return {
            "x-api-key": self.api_key,
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": self._user_agent,
        }

    async def _request(
        self,
        method: str,
        endpoint: str,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Make an API request."""
        session = await self._get_session()
        url = f"{self.base_url}{endpoint}"
        headers = self._get_headers()

        _LOGGER.debug("API request: %s %s", method, url)

        try:
            async with session.request(
                method,
                url,
                headers=headers,
                **kwargs,
            ) as response:
                _LOGGER.debug("API response status: %s", response.status)

                if response.status == 401:
                    raise EVTrackerAuthenticationError("Invalid API key")

                if response.status == 403:
                    raise EVTrackerAuthenticationError(
                        "API key lacks permissions or PRO subscription required"
                    )

                if response.status == 429:
                    retry_after = response.headers.get("Retry-After", "60")
                    raise EVTrackerRateLimitError(
                        f"Rate limit exceeded. Retry after {retry_after} seconds"
                    )

                if response.status >= 500:
                    text = await response.text()
                    raise EVTrackerApiError(f"Server error: {response.status} - {text}")

                if response.status >= 400:
                    try:
                        error_data = await response.json()
                        error_msg = error_data.get("error", {}).get(
                            "message", "Unknown error"
                        )
                    except Exception:
                        error_msg = await response.text()
                    raise EVTrackerApiError(
                        f"API error: {response.status} - {error_msg}"
                    )

                return cast(dict[str, Any], await response.json())

        except aiohttp.ClientError as err:
            _LOGGER.error("Connection error: %s", err)
            raise EVTrackerConnectionError(f"Connection error: {err}") from err

    async def get_cars(self) -> list[Car]:
        """Get user's cars.

        Returns:
            List of Car objects.
        """
        response = await self._request("GET", ENDPOINT_CARS)
        return [Car.from_dict(car) for car in response.get("data", [])]

    async def get_cars_raw(self) -> list[dict[str, Any]]:
        """Get user's cars as raw dictionaries.

        Returns:
            List of car dictionaries.
        """
        response = await self._request("GET", ENDPOINT_CARS)
        return cast(list[dict[str, Any]], response.get("data", []))

    async def get_default_car(self) -> Car | None:
        """Get user's default car.

        Returns:
            Default Car or None if not set.
        """
        response = await self._request("GET", ENDPOINT_CARS_DEFAULT)
        data = response.get("data")
        return Car.from_dict(data) if data else None

    async def get_state(self) -> HomeAssistantState:
        """Get Home Assistant state with all statistics.

        Returns:
            HomeAssistantState with monthly/yearly statistics.
        """
        response = await self._request("GET", ENDPOINT_HA_STATE)
        return HomeAssistantState.from_dict(response.get("data", {}))

    async def get_state_raw(self) -> dict[str, Any]:
        """Get Home Assistant state as raw dictionary.

        Returns:
            State dictionary.
        """
        response = await self._request("GET", ENDPOINT_HA_STATE)
        return cast(dict[str, Any], response.get("data", {}))

    async def log_session(
        self,
        energy_kwh: float,
        *,
        start_time: datetime | str | None = None,
        end_time: datetime | str | None = None,
        car_id: int | None = None,
        location: str | None = None,
        external_id: str | None = None,
        provider: str | None = None,
        energy_source: str | None = None,
        rate_type: str | None = None,
        price_per_kwh: float | None = None,
        vat_percentage: float | None = None,
        notes: str | None = None,
    ) -> ChargingSession:
        """Log a charging session with full control.

        Args:
            energy_kwh: Energy consumed in kWh.
            start_time: When charging started.
            end_time: When charging ended.
            car_id: Car ID to associate with session.
            location: Charging location.
            external_id: External ID for idempotency.
            provider: Charging provider (HOME, CEZ, EOON, etc.).
            energy_source: Energy source (GRID or SOLAR).
            rate_type: Tariff rate type (HIGH or LOW).
            price_per_kwh: Price per kWh without VAT.
            vat_percentage: VAT percentage.
            notes: Additional notes.

        Returns:
            Created ChargingSession.
        """
        payload: dict[str, Any] = {"energyConsumedKwh": energy_kwh}

        if start_time is not None:
            formatted = _format_datetime_for_api(start_time)
            if formatted:
                payload["startTime"] = formatted

        if end_time is not None:
            formatted = _format_datetime_for_api(end_time)
            if formatted:
                payload["endTime"] = formatted

        if car_id is not None:
            payload["carId"] = car_id
        if location:
            payload["location"] = location
        if external_id:
            payload["externalId"] = external_id
        if provider:
            payload["provider"] = provider
        if energy_source:
            payload["energySource"] = energy_source.upper()
        if rate_type:
            payload["rateType"] = rate_type.upper()
        if price_per_kwh is not None:
            payload["pricePerKwhWithoutVat"] = price_per_kwh
        if vat_percentage is not None:
            payload["vatPercentage"] = vat_percentage
        if notes:
            payload["notes"] = notes

        _LOGGER.debug("Logging session: %s", payload)

        response = await self._request("POST", ENDPOINT_SESSIONS, json=payload)
        return ChargingSession.from_dict(response.get("data", {}))

    async def log_session_simple(
        self,
        energy_kwh: float,
        *,
        start_time: datetime | str | None = None,
        end_time: datetime | str | None = None,
        car_id: int | None = None,
        location: str | None = None,
        external_id: str | None = None,
        energy_source: str | None = None,
        rate_type: str | None = None,
    ) -> ChargingSession:
        """Log a charging session with smart defaults.

        Args:
            energy_kwh: Energy consumed in kWh (only required field).
            start_time: When charging started (estimated if not provided).
            end_time: When charging ended (defaults to now).
            car_id: Car ID (uses default car if not specified).
            location: Charging location (defaults to "Home").
            external_id: External ID for idempotency.
            energy_source: Energy source (GRID or SOLAR).
            rate_type: Tariff rate type (HIGH or LOW).

        Returns:
            Created ChargingSession.
        """
        payload: dict[str, Any] = {"energyConsumedKwh": energy_kwh}

        if start_time is not None:
            formatted = _format_datetime_for_api(start_time)
            if formatted:
                payload["startTime"] = formatted

        if end_time is not None:
            formatted = _format_datetime_for_api(end_time)
            if formatted:
                payload["endTime"] = formatted

        if car_id is not None:
            payload["carId"] = car_id
        if location:
            payload["location"] = location
        if external_id:
            payload["externalId"] = external_id
        if energy_source:
            payload["energySource"] = energy_source.upper()
        if rate_type:
            payload["rateType"] = rate_type.upper()

        _LOGGER.debug("Logging simple session: %s", payload)

        response = await self._request("POST", ENDPOINT_SESSIONS_SIMPLE, json=payload)
        return ChargingSession.from_dict(response.get("data", {}))

    async def validate_api_key(self) -> bool:
        """Validate the API key by fetching cars.

        Returns:
            True if valid, False otherwise.
        """
        try:
            await self.get_cars()
            return True
        except EVTrackerAuthenticationError:
            return False
        except EVTrackerApiError as err:
            _LOGGER.warning("API key validation error: %s", err)
            return False
