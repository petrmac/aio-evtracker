# aioevtracker

Async Python client for [EV Tracker](https://evtracker.cz) API.

## Installation

```bash
pip install aioevtracker
```

## Usage

```python
import asyncio
from aioevtracker import EVTrackerClient

async def main():
    async with EVTrackerClient(api_key="your-api-key") as client:
        # Get all cars
        cars = await client.get_cars()
        for car in cars:
            print(f"{car.name} (ID: {car.id})")

        # Get charging statistics
        state = await client.get_state()
        print(f"Monthly energy: {state.monthly_energy} kWh")
        print(f"Monthly cost: {state.monthly_cost} CZK")

        # Log a charging session
        session = await client.log_session_simple(
            energy_kwh=45.5,
            energy_source="GRID",
            rate_type="LOW",
        )
        print(f"Logged session ID: {session.id}")

asyncio.run(main())
```

## With existing aiohttp session

```python
import aiohttp
from aioevtracker import EVTrackerClient

async with aiohttp.ClientSession() as session:
    client = EVTrackerClient(
        api_key="your-api-key",
        session=session,
    )
    cars = await client.get_cars()
```

## API Reference

### EVTrackerClient

- `get_cars()` - Get list of user's cars
- `get_default_car()` - Get default car
- `get_state()` - Get Home Assistant state with statistics
- `log_session(...)` - Log a charging session with full control
- `log_session_simple(...)` - Log a charging session with smart defaults
- `validate_api_key()` - Validate the API key

### Models

- `Car` - Electric vehicle
- `ChargingSession` - Charging session
- `HomeAssistantState` - Statistics state

### Exceptions

- `EVTrackerApiError` - Base exception
- `EVTrackerAuthenticationError` - Invalid API key (401/403)
- `EVTrackerConnectionError` - Connection failed
- `EVTrackerRateLimitError` - Rate limit exceeded (429)

## License

MIT
