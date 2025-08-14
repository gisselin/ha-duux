"""Platform for Duux fan integration."""
from __future__ import annotations

import asyncio
import logging
from typing import Any

from homeassistant.components.fan import FanEntity, FanEntityFeature
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import issue_registry as ir
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util.percentage import (
    int_states_in_range,
    percentage_to_ranged_value,
    ranged_value_to_percentage,
)

from .api import DuuxApiError
from .const import DOMAIN, MAX_FAN_SPEED, MIN_FAN_SPEED, REPAIR_ISSUE_AUTH_FAILED
from .coordinator import DuuxDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

SPEED_RANGE = (MIN_FAN_SPEED, MAX_FAN_SPEED)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Duux fan from a config entry."""
    coordinator: DuuxDataUpdateCoordinator = hass.data[DOMAIN][config_entry.entry_id]
    
    async_add_entities([DuuxFan(coordinator, config_entry)])


class DuuxFan(CoordinatorEntity[DuuxDataUpdateCoordinator], FanEntity):
    """Representation of a Duux Fan."""

    _attr_has_entity_name = True
    _attr_name = None
    _attr_supported_features = (
        FanEntityFeature.SET_SPEED
        | FanEntityFeature.OSCILLATE
        | FanEntityFeature.TURN_OFF
        | FanEntityFeature.TURN_ON
    )

    def __init__(
        self,
        coordinator: DuuxDataUpdateCoordinator,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize the fan."""
        super().__init__(coordinator)
        self._attr_unique_id = config_entry.data["device_id"]
        self._attr_device_info = {
            "identifiers": {(DOMAIN, config_entry.data["device_id"])},
            "name": "Duux Fan",
            "manufacturer": "Duux",
            "model": "Smart Fan",
        }

    @property
    def is_on(self) -> bool | None:
        """Return true if the fan is on."""
        if self.coordinator.data is None:
            return None
        return bool(self.coordinator.data.get("power", 0))

    @property
    def percentage(self) -> int | None:
        """Return the current speed percentage."""
        if self.coordinator.data is None:
            return None
        
        speed = self.coordinator.data.get("speed")
        if speed is None:
            return None
        
        return ranged_value_to_percentage(SPEED_RANGE, int(speed))

    @property
    def speed_count(self) -> int:
        """Return the number of speeds the fan supports."""
        return int_states_in_range(SPEED_RANGE)

    @property
    def oscillating(self) -> bool | None:
        """Return true if the fan is oscillating."""
        if self.coordinator.data is None:
            return None
        return bool(self.coordinator.data.get("horosc", 0))

    async def async_turn_on(
        self,
        percentage: int | None = None,
        preset_mode: str | None = None,
        **kwargs: Any,
    ) -> None:
        """Turn on the fan."""
        try:
            await self.coordinator.api.turn_on()
            
            if percentage is not None:
                speed = percentage_to_ranged_value(SPEED_RANGE, percentage)
                await self.coordinator.api.set_speed(int(speed))
            
            # Wait for device to process command before refreshing
            await asyncio.sleep(1)
            await self.coordinator.async_request_refresh()
        except DuuxApiError as err:
            self._handle_api_error(err, "Failed to turn on fan")
            _LOGGER.error("Failed to turn on fan: %s", err)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off the fan."""
        try:
            await self.coordinator.api.turn_off()
            # Wait for device to process command before refreshing
            await asyncio.sleep(1)
            await self.coordinator.async_request_refresh()
        except DuuxApiError as err:
            self._handle_api_error(err, "Failed to turn off fan")
            _LOGGER.error("Failed to turn off fan: %s", err)

    async def async_set_percentage(self, percentage: int) -> None:
        """Set the speed of the fan, as a percentage."""
        try:
            speed = percentage_to_ranged_value(SPEED_RANGE, percentage)
            await self.coordinator.api.set_speed(int(speed))
            # Wait for device to process command before refreshing
            await asyncio.sleep(1)
            await self.coordinator.async_request_refresh()
        except DuuxApiError as err:
            self._handle_api_error(err, "Failed to set fan speed")
            _LOGGER.error("Failed to set fan speed: %s", err)

    async def async_oscillate(self, oscillating: bool) -> None:
        """Set oscillation."""
        try:
            await self.coordinator.api.set_oscillation(oscillating)
            # Wait for device to process command before refreshing
            await asyncio.sleep(1)
            await self.coordinator.async_request_refresh()
        except DuuxApiError as err:
            self._handle_api_error(err, "Failed to set fan oscillation")
            _LOGGER.error("Failed to set fan oscillation: %s", err)

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
                translation_placeholders={"device_id": self._attr_unique_id},
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