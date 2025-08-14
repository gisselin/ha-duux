"""API client for Duux Fan."""
from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

import aiohttp

from .const import API_BASE_URL

_LOGGER = logging.getLogger(__name__)


class DuuxApiError(Exception):
    """Exception for Duux API errors."""


class DuuxApiClient:
    """API client for Duux Fan."""

    def __init__(self, session: aiohttp.ClientSession, device_id: str, jwt_token: str) -> None:
        """Initialize the API client."""
        self._session = session
        self._device_id = device_id
        self._jwt_token = jwt_token

    async def send_command(self, command_text: str) -> dict[str, Any]:
        """Send a text command to the Duux fan."""
        url = f"{API_BASE_URL}/sensor/{self._device_id}/commands"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self._jwt_token}",
            "Host": API_BASE_URL.replace("https://", ""),
        }

        try:
            # The API expects command as a text string in the format "tune set parameter value"
            command_data = {"command": command_text}
            async with self._session.post(
                url, json=command_data, headers=headers
            ) as response:
                if not response.ok:
                    error_data = await response.json()
                    raise DuuxApiError(f"Command failed: {error_data}")
                
                return await response.json()
        except asyncio.TimeoutError as err:
            raise DuuxApiError("Timeout connecting to Duux API") from err
        except aiohttp.ClientError as err:
            raise DuuxApiError(f"Error connecting to Duux API: {err}") from err

    async def get_status(self) -> dict[str, Any]:
        """Get the current status of the Duux fan."""
        url = f"{API_BASE_URL}/data/{self._device_id}/status"
        headers = {
            "Authorization": f"Bearer {self._jwt_token}",
            "Host": API_BASE_URL.replace("https://", ""),
        }

        try:
            async with self._session.get(url, headers=headers) as response:
                if not response.ok:
                    error_data = await response.json()
                    raise DuuxApiError(f"Status request failed: {error_data}")
                
                return await response.json()
        except asyncio.TimeoutError as err:
            raise DuuxApiError("Timeout connecting to Duux API") from err
        except aiohttp.ClientError as err:
            raise DuuxApiError(f"Error connecting to Duux API: {err}") from err

    async def turn_on(self) -> None:
        """Turn on the fan."""
        await self.send_command("tune set power 1")

    async def turn_off(self) -> None:
        """Turn off the fan."""
        await self.send_command("tune set power 0")

    async def set_speed(self, speed: int) -> None:
        """Set fan speed (1-30)."""
        if not 1 <= speed <= 30:
            raise ValueError("Speed must be between 1 and 30")
        await self.send_command(f"tune set speed {speed}")

    async def set_oscillation(self, oscillate: bool) -> None:
        """Set horizontal oscillation."""
        value = 1 if oscillate else 0
        await self.send_command(f"tune set horosc {value}")

    async def set_night_mode(self, night_mode: bool) -> None:
        """Set night mode."""
        value = 1 if night_mode else 0
        await self.send_command(f"tune set night {value}")