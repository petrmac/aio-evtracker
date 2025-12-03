"""Tests for EVTrackerClient."""

from __future__ import annotations

import pytest
from aioresponses import aioresponses

from aioevtracker import (
    DEFAULT_API_BASE_URL,
    EVTrackerAuthenticationError,
    EVTrackerClient,
    EVTrackerConnectionError,
    EVTrackerRateLimitError,
)


class TestEVTrackerClient:
    """Test EVTrackerClient initialization."""

    def test_init_defaults(self) -> None:
        """Test client initialization with defaults."""
        client = EVTrackerClient("test_key")
        assert client.api_key == "test_key"
        assert client.base_url == DEFAULT_API_BASE_URL

    def test_init_custom_base_url(self) -> None:
        """Test client with custom base URL."""
        client = EVTrackerClient("test_key", base_url="https://custom.api.com/")
        assert client.base_url == "https://custom.api.com"


class TestGetCars:
    """Test get_cars methods."""

    @pytest.mark.asyncio
    async def test_get_cars_raw_success(self) -> None:
        """Test successful get_cars_raw call."""
        with aioresponses() as m:
            m.get(
                f"{DEFAULT_API_BASE_URL}/cars",
                payload={"data": [{"id": 1, "name": "Tesla Model 3"}]},
            )

            async with EVTrackerClient("test_key") as client:
                result = await client.get_cars_raw()

            assert result == [{"id": 1, "name": "Tesla Model 3"}]

    @pytest.mark.asyncio
    async def test_get_cars_success(self) -> None:
        """Test successful get_cars call returns Car objects."""
        with aioresponses() as m:
            m.get(
                f"{DEFAULT_API_BASE_URL}/cars",
                payload={"data": [{"id": 1, "name": "Tesla Model 3"}]},
            )

            async with EVTrackerClient("test_key") as client:
                result = await client.get_cars()

            assert len(result) == 1
            assert result[0].id == 1
            assert result[0].name == "Tesla Model 3"


class TestAuthentication:
    """Test authentication error handling."""

    @pytest.mark.asyncio
    async def test_401_raises_auth_error(self) -> None:
        """Test 401 raises EVTrackerAuthenticationError."""
        with aioresponses() as m:
            m.get(f"{DEFAULT_API_BASE_URL}/cars", status=401)

            async with EVTrackerClient("bad_key") as client:
                with pytest.raises(EVTrackerAuthenticationError):
                    await client.get_cars_raw()

    @pytest.mark.asyncio
    async def test_403_raises_auth_error(self) -> None:
        """Test 403 raises EVTrackerAuthenticationError."""
        with aioresponses() as m:
            m.get(f"{DEFAULT_API_BASE_URL}/cars", status=403)

            async with EVTrackerClient("no_pro") as client:
                with pytest.raises(EVTrackerAuthenticationError):
                    await client.get_cars_raw()

    @pytest.mark.asyncio
    async def test_429_raises_rate_limit_error(self) -> None:
        """Test 429 raises EVTrackerRateLimitError."""
        with aioresponses() as m:
            m.get(
                f"{DEFAULT_API_BASE_URL}/cars",
                status=429,
                headers={"Retry-After": "60"},
            )

            async with EVTrackerClient("test_key") as client:
                with pytest.raises(EVTrackerRateLimitError):
                    await client.get_cars_raw()


class TestLogSession:
    """Test session logging."""

    @pytest.mark.asyncio
    async def test_log_session_simple(self) -> None:
        """Test log_session_simple."""
        with aioresponses() as m:
            m.post(
                f"{DEFAULT_API_BASE_URL}/sessions/simple",
                payload={"data": {"id": 100, "energyConsumedKwh": 25.5}},
            )

            async with EVTrackerClient("test_key") as client:
                result = await client.log_session_simple(energy_kwh=25.5)

            assert result.id == 100
            assert result.energy_kwh == 25.5

    @pytest.mark.asyncio
    async def test_log_session_full(self) -> None:
        """Test log_session with all parameters."""
        with aioresponses() as m:
            m.post(
                f"{DEFAULT_API_BASE_URL}/sessions",
                payload={"data": {"id": 101, "energyConsumedKwh": 45.0}},
            )

            async with EVTrackerClient("test_key") as client:
                result = await client.log_session(
                    energy_kwh=45.0,
                    location="Home",
                    energy_source="GRID",
                    rate_type="LOW",
                )

            assert result.id == 101


class TestValidateApiKey:
    """Test API key validation."""

    @pytest.mark.asyncio
    async def test_validate_success(self) -> None:
        """Test successful validation."""
        with aioresponses() as m:
            m.get(f"{DEFAULT_API_BASE_URL}/cars", payload={"data": []})

            async with EVTrackerClient("valid_key") as client:
                result = await client.validate_api_key()

            assert result is True

    @pytest.mark.asyncio
    async def test_validate_failure(self) -> None:
        """Test failed validation."""
        with aioresponses() as m:
            m.get(f"{DEFAULT_API_BASE_URL}/cars", status=401)

            async with EVTrackerClient("invalid_key") as client:
                result = await client.validate_api_key()

            assert result is False
