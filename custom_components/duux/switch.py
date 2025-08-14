"""Platform for Duux switch integration."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import issue_registry as ir
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .api import DuuxApiError
from .const import DOMAIN, REPAIR_ISSUE_AUTH_FAILED
from .coordinator import DuuxDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Duux switch from a config entry."""
    coordinator: DuuxDataUpdateCoordinator = hass.data[DOMAIN][config_entry.entry_id]
    
    async_add_entities([DuuxNaturalWindSwitch(coordinator, config_entry)])


class DuuxNaturalWindSwitch(CoordinatorEntity[DuuxDataUpdateCoordinator], SwitchEntity):
    """Representation of a Duux Natural Wind switch."""

    _attr_has_entity_name = True
    _attr_name = "Natural Wind"
    _attr_icon = "mdi:weather-windy"

    def __init__(
        self,
        coordinator: DuuxDataUpdateCoordinator,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize the switch."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{config_entry.data['device_id']}_natural_wind"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, config_entry.data["device_id"])},
            "name": "Duux Fan",
            "manufacturer": "Duux",
            "model": "Smart Fan",
        }

    @property
    def is_on(self) -> bool | None:
        """Return true if Natural Wind mode is on."""
        if self.coordinator.data is None:
            return None
        # mode 1 = Natural Wind on, mode 0 = Natural Wind off
        return bool(self.coordinator.data.get("mode", 0) == 1)

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn on Natural Wind mode."""
        try:
            await self.coordinator.api.send_command("tune set mode 1")
            await self.coordinator.async_request_refresh()
        except DuuxApiError as err:
            self._handle_api_error(err, "Failed to turn on Natural Wind mode")
            _LOGGER.error("Failed to turn on Natural Wind mode: %s", err)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off Natural Wind mode."""
        try:
            await self.coordinator.api.send_command("tune set mode 0")
            await self.coordinator.async_request_refresh()
        except DuuxApiError as err:
            self._handle_api_error(err, "Failed to turn off Natural Wind mode")
            _LOGGER.error("Failed to turn off Natural Wind mode: %s", err)

    def _handle_api_error(self, error: DuuxApiError, context: str) -> None:
        """Handle API errors and create repair issues for auth failures."""
        error_message = str(error)
        # Check if this is an authentication error
        if self._is_auth_error(error_message):
            ir.async_create_issue(
                self.hass,
                DOMAIN,
                REPAIR_ISSUE_AUTH_FAILED,
                is_fixable=False,
                severity=ir.IssueSeverity.ERROR,
                translation_key="auth_failed",
                translation_placeholders={"device_id": self._attr_unique_id.split("_")[0]},
            )

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