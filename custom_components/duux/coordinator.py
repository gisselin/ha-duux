"""Data update coordinator for Duux Fan."""
from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any

import aiohttp
from homeassistant.core import HomeAssistant
from homeassistant.helpers import issue_registry as ir
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import DuuxApiClient, DuuxApiError
from .const import DEFAULT_SCAN_INTERVAL, DOMAIN, REPAIR_ISSUE_AUTH_FAILED

_LOGGER = logging.getLogger(__name__)


class DuuxDataUpdateCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Data update coordinator for Duux Fan."""

    def __init__(
        self,
        hass: HomeAssistant,
        session: aiohttp.ClientSession,
        device_id: str,
        jwt_token: str,
    ) -> None:
        """Initialize the coordinator."""
        self.api = DuuxApiClient(session, device_id, jwt_token)
        self._device_id = device_id
        self._auth_failure_count = 0
        self._repair_issue_created = False
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL),
        )

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from the Duux API."""
        try:
            response = await self.api.get_status()
            if "data" not in response:
                raise UpdateFailed("Invalid response from Duux API")
            
            # Reset auth failure count on successful request
            if self._auth_failure_count > 0:
                self._auth_failure_count = 0
                # Remove repair issue if it was created
                if self._repair_issue_created:
                    ir.async_delete_issue(self.hass, DOMAIN, REPAIR_ISSUE_AUTH_FAILED)
                    self._repair_issue_created = False
            
            return response["data"]
        except DuuxApiError as err:
            # Check if this is an authentication error
            if self._is_auth_error(str(err)):
                self._auth_failure_count += 1
                # Create repair issue after 3 consecutive auth failures
                if self._auth_failure_count >= 3 and not self._repair_issue_created:
                    self._create_auth_repair_issue()
                    self._repair_issue_created = True
            
            raise UpdateFailed(f"Error communicating with Duux API: {err}") from err

    def _is_auth_error(self, error_message: str) -> bool:
        """Check if the error is related to authentication."""
        auth_error_indicators = [
            "unauthorized",
            "invalid token",
            "authentication failed",
            "401",
            "403",
            "token expired"
        ]
        error_lower = error_message.lower()
        return any(indicator in error_lower for indicator in auth_error_indicators)

    def _create_auth_repair_issue(self) -> None:
        """Create a repair issue for authentication failures."""
        ir.async_create_issue(
            self.hass,
            DOMAIN,
            REPAIR_ISSUE_AUTH_FAILED,
            is_fixable=False,
            severity=ir.IssueSeverity.ERROR,
            translation_key="auth_failed",
            translation_placeholders={"device_id": self._device_id},
        )