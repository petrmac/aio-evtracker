"""Data models for EV Tracker API."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass
class Car:
    """Represents an EV in the user's account."""

    id: int
    name: str
    make: str | None = None
    model: str | None = None
    year: int | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Car:
        """Create a Car from API response data."""
        return cls(
            id=data["id"],
            name=data["name"],
            make=data.get("make"),
            model=data.get("model"),
            year=data.get("year"),
        )


@dataclass
class ChargingSession:
    """Represents a charging session."""

    id: int
    energy_kwh: float
    cost: float | None = None
    start_time: datetime | None = None
    end_time: datetime | None = None
    location: str | None = None
    energy_source: str | None = None
    rate_type: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ChargingSession:
        """Create a ChargingSession from API response data."""
        return cls(
            id=data["id"],
            energy_kwh=data.get("energyConsumedKwh", 0.0),
            cost=data.get("totalCost"),
            start_time=_parse_datetime(data.get("startTime")),
            end_time=_parse_datetime(data.get("endTime")),
            location=data.get("location"),
            energy_source=data.get("energySource"),
            rate_type=data.get("rateType"),
        )


@dataclass
class HomeAssistantState:
    """Represents the Home Assistant state response."""

    monthly_energy: float
    monthly_cost: float
    monthly_sessions: int
    yearly_energy: float
    yearly_cost: float
    last_session_energy: float | None
    last_session_cost: float | None
    avg_cost_per_kwh: float | None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> HomeAssistantState:
        """Create HomeAssistantState from API response data."""
        return cls(
            monthly_energy=data.get("monthlyEnergy", 0.0),
            monthly_cost=data.get("monthlyCost", 0.0),
            monthly_sessions=data.get("monthlySessions", 0),
            yearly_energy=data.get("yearlyEnergy", 0.0),
            yearly_cost=data.get("yearlyCost", 0.0),
            last_session_energy=data.get("lastSessionEnergy"),
            last_session_cost=data.get("lastSessionCost"),
            avg_cost_per_kwh=data.get("avgCostPerKwh"),
        )


def _parse_datetime(value: str | None) -> datetime | None:
    """Parse an ISO datetime string."""
    if value is None:
        return None
    try:
        # Handle Z suffix
        if value.endswith("Z"):
            value = value[:-1] + "+00:00"
        return datetime.fromisoformat(value)
    except (ValueError, TypeError):
        return None
