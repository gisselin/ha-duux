"""Tests for the Duux Natural Wind switch."""
from __future__ import annotations

from unittest.mock import AsyncMock, Mock, patch
import pytest

# Mock the necessary Home Assistant components
class MockSwitchEntity:
    _attr_has_entity_name = True
    _attr_name = None
    _attr_icon = None

class MockCoordinatorEntity:
    def __init__(self, coordinator):
        self.coordinator = coordinator

class MockConfigEntry:
    def __init__(self, **kwargs):
        self.data = kwargs.get('data', {})

class MockHomeAssistant:
    def __init__(self):
        self.data = {}

DOMAIN = "duux"
REPAIR_ISSUE_AUTH_FAILED = "auth_failed"

class DuuxApiError(Exception):
    """Exception for Duux API errors."""

# Inline the switch implementation for testing
class DuuxNaturalWindSwitch(MockCoordinatorEntity, MockSwitchEntity):
    """Test version of Duux Natural Wind switch."""

    _attr_has_entity_name = True
    _attr_name = "Natural Wind"
    _attr_icon = "mdi:weather-windy"

    def __init__(self, coordinator, config_entry) -> None:
        """Initialize the switch."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{config_entry.data['device_id']}_natural_wind"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, config_entry.data["device_id"])},
            "name": "Duux Fan",
            "manufacturer": "Duux",
            "model": "Smart Fan",
        }
        self.hass = MockHomeAssistant()

    @property
    def is_on(self) -> bool | None:
        """Return true if Natural Wind mode is on."""
        if self.coordinator.data is None:
            return None
        return bool(self.coordinator.data.get("mode", 0) == 1)

    async def async_turn_on(self, **kwargs) -> None:
        """Turn on Natural Wind mode."""
        await self.coordinator.api.send_command("tune set mode 1")
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs) -> None:
        """Turn off Natural Wind mode."""
        await self.coordinator.api.send_command("tune set mode 0")
        await self.coordinator.async_request_refresh()


@pytest.mark.asyncio
class TestDuuxNaturalWindSwitch:
    """Test the Duux Natural Wind switch."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_coordinator = Mock()
        self.mock_coordinator.data = {"mode": 0, "power": 1, "speed": 15}
        self.mock_coordinator.api = Mock()
        self.mock_coordinator.api.send_command = AsyncMock()
        self.mock_coordinator.async_request_refresh = AsyncMock()
        
        self.mock_config_entry = MockConfigEntry(
            data={"device_id": "34:5f:45:ec:b8:34", "jwt_token": "test_token"}
        )
        
        self.switch = DuuxNaturalWindSwitch(self.mock_coordinator, self.mock_config_entry)

    def test_init(self):
        """Test switch initialization."""
        assert self.switch._attr_name == "Natural Wind"
        assert self.switch._attr_icon == "mdi:weather-windy"
        assert self.switch._attr_unique_id == "34:5f:45:ec:b8:34_natural_wind"
        assert self.switch._attr_device_info["name"] == "Duux Fan"

    def test_is_on_false(self):
        """Test is_on when Natural Wind is off."""
        self.mock_coordinator.data = {"mode": 0}
        assert self.switch.is_on is False

    def test_is_on_true(self):
        """Test is_on when Natural Wind is on."""
        self.mock_coordinator.data = {"mode": 1}
        assert self.switch.is_on is True

    def test_is_on_none(self):
        """Test is_on when no data is available."""
        self.mock_coordinator.data = None
        assert self.switch.is_on is None

    def test_is_on_missing_mode(self):
        """Test is_on when mode is missing from data."""
        self.mock_coordinator.data = {"power": 1, "speed": 15}
        assert self.switch.is_on is False  # Default to 0 when missing

    async def test_turn_on_success(self):
        """Test successful turn on."""
        await self.switch.async_turn_on()
        
        self.mock_coordinator.api.send_command.assert_called_once_with("tune set mode 1")
        self.mock_coordinator.async_request_refresh.assert_called_once()

    async def test_turn_off_success(self):
        """Test successful turn off."""
        await self.switch.async_turn_off()
        
        self.mock_coordinator.api.send_command.assert_called_once_with("tune set mode 0")
        self.mock_coordinator.async_request_refresh.assert_called_once()

    async def test_turn_on_api_error(self):
        """Test turn on with API error."""
        self.mock_coordinator.api.send_command.side_effect = DuuxApiError("Connection failed")
        
        with pytest.raises(DuuxApiError):
            await self.switch.async_turn_on()

    async def test_turn_off_api_error(self):
        """Test turn off with API error."""
        self.mock_coordinator.api.send_command.side_effect = DuuxApiError("Connection failed")
        
        with pytest.raises(DuuxApiError):
            await self.switch.async_turn_off()

    def test_natural_wind_state_changes(self):
        """Test that switch state reflects mode changes correctly."""
        # Initially off
        self.mock_coordinator.data = {"mode": 0}
        assert self.switch.is_on is False
        
        # Turn on
        self.mock_coordinator.data = {"mode": 1}
        assert self.switch.is_on is True
        
        # Turn off again
        self.mock_coordinator.data = {"mode": 0}
        assert self.switch.is_on is False

    def test_device_info_structure(self):
        """Test device info structure is correct."""
        device_info = self.switch._attr_device_info
        assert device_info["identifiers"] == {(DOMAIN, "34:5f:45:ec:b8:34")}
        assert device_info["name"] == "Duux Fan"
        assert device_info["manufacturer"] == "Duux"
        assert device_info["model"] == "Smart Fan"

    async def test_command_format_turn_on(self):
        """Test that turn on sends correct command format."""
        await self.switch.async_turn_on()
        
        # Verify exact command format
        self.mock_coordinator.api.send_command.assert_called_once_with("tune set mode 1")

    async def test_command_format_turn_off(self):
        """Test that turn off sends correct command format."""
        await self.switch.async_turn_off()
        
        # Verify exact command format
        self.mock_coordinator.api.send_command.assert_called_once_with("tune set mode 0")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])