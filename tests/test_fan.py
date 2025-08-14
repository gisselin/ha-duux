"""Tests for the Duux fan entity."""
from __future__ import annotations

from unittest.mock import AsyncMock, Mock, patch
import pytest
from homeassistant.core import HomeAssistant
from homeassistant.components.fan import FanEntityFeature

from custom_components.duux.fan import DuuxFan
from custom_components.duux.api import DuuxApiError
from custom_components.duux.const import DOMAIN, REPAIR_ISSUE_AUTH_FAILED


@pytest.mark.unit
class TestDuuxFan:
    """Test the DuuxFan entity."""

    @pytest.fixture
    def mock_hass(self):
        """Mock Home Assistant."""
        hass = Mock(spec=HomeAssistant)
        hass.data = {DOMAIN: {}}
        return hass

    @pytest.fixture
    def mock_coordinator(self, mock_duux_api, mock_api_responses):
        """Mock coordinator."""
        coordinator = Mock()
        coordinator.data = mock_api_responses["status_success"]["data"]
        coordinator.api = mock_duux_api
        coordinator.async_request_refresh = AsyncMock()
        return coordinator

    @pytest.fixture
    def fan_entity(self, mock_coordinator, mock_config_entry):
        """Create a fan entity for testing."""
        return DuuxFan(mock_coordinator, mock_config_entry)

    def test_init(self, fan_entity, mock_config_entry):
        """Test fan entity initialization."""
        assert fan_entity._attr_unique_id == mock_config_entry.data["device_id"]
        assert fan_entity._attr_has_entity_name is True
        assert fan_entity._attr_name is None
        expected_features = (
            FanEntityFeature.SET_SPEED
            | FanEntityFeature.OSCILLATE
            | FanEntityFeature.TURN_OFF
            | FanEntityFeature.TURN_ON
        )
        assert fan_entity._attr_supported_features == expected_features

    def test_device_info(self, fan_entity, mock_config_entry):
        """Test device info."""
        device_info = fan_entity._attr_device_info
        assert device_info["identifiers"] == {(DOMAIN, mock_config_entry.data["device_id"])}
        assert device_info["name"] == "Duux Fan"
        assert device_info["manufacturer"] == "Duux"
        assert device_info["model"] == "Smart Fan"

    def test_is_on_true(self, fan_entity, mock_coordinator, mock_api_responses):
        """Test is_on when fan is on."""
        mock_coordinator.data = mock_api_responses["status_success"]["data"]
        assert fan_entity.is_on is True

    def test_is_on_false(self, fan_entity, mock_coordinator, mock_api_responses):
        """Test is_on when fan is off."""
        mock_coordinator.data = mock_api_responses["status_off"]["data"]
        assert fan_entity.is_on is False

    def test_is_on_none(self, fan_entity, mock_coordinator):
        """Test is_on when no data."""
        mock_coordinator.data = None
        assert fan_entity.is_on is None

    def test_percentage(self, fan_entity, mock_coordinator, mock_api_responses):
        """Test percentage calculation."""
        # Speed 15 out of 30 should be 50%
        mock_coordinator.data = mock_api_responses["status_success"]["data"]
        assert fan_entity.percentage == 50

    def test_percentage_min_speed(self, fan_entity, mock_coordinator):
        """Test percentage at minimum speed."""
        mock_coordinator.data = {"speed": 1}
        # Speed 1 out of 30 should be approximately 3%
        assert fan_entity.percentage == 3

    def test_percentage_max_speed(self, fan_entity, mock_coordinator):
        """Test percentage at maximum speed."""
        mock_coordinator.data = {"speed": 30}
        assert fan_entity.percentage == 100

    def test_percentage_none(self, fan_entity, mock_coordinator):
        """Test percentage when no data."""
        mock_coordinator.data = None
        assert fan_entity.percentage is None

    def test_percentage_no_speed(self, fan_entity, mock_coordinator):
        """Test percentage when speed is not in data."""
        mock_coordinator.data = {"power": 1}
        assert fan_entity.percentage is None

    def test_speed_count(self, fan_entity):
        """Test speed count."""
        assert fan_entity.speed_count == 30

    def test_oscillating_true(self, fan_entity, mock_coordinator, mock_api_responses):
        """Test oscillating when enabled."""
        mock_coordinator.data = mock_api_responses["status_success"]["data"]
        assert fan_entity.oscillating is True

    def test_oscillating_false(self, fan_entity, mock_coordinator, mock_api_responses):
        """Test oscillating when disabled."""
        mock_coordinator.data = mock_api_responses["status_off"]["data"]
        assert fan_entity.oscillating is False

    def test_oscillating_none(self, fan_entity, mock_coordinator):
        """Test oscillating when no data."""
        mock_coordinator.data = None
        assert fan_entity.oscillating is None

    async def test_turn_on_success(self, fan_entity, mock_coordinator, mock_duux_api):
        """Test successful turn on."""
        await fan_entity.async_turn_on()
        
        mock_duux_api.turn_on.assert_called_once()
        mock_coordinator.async_request_refresh.assert_called_once()

    async def test_turn_on_with_percentage(self, fan_entity, mock_coordinator, mock_duux_api):
        """Test turn on with specific percentage."""
        await fan_entity.async_turn_on(percentage=75)
        
        mock_duux_api.turn_on.assert_called_once()
        # 75% of 30 speeds = 22.5, rounded to 23
        mock_duux_api.set_speed.assert_called_once_with(23)
        mock_coordinator.async_request_refresh.assert_called_once()

    async def test_turn_on_api_error(self, fan_entity, mock_coordinator, mock_duux_api):
        """Test turn on with API error."""
        mock_duux_api.turn_on.side_effect = DuuxApiError("Connection failed")
        
        with patch.object(fan_entity, '_handle_api_error') as mock_handle_error:
            await fan_entity.async_turn_on()
        
        mock_handle_error.assert_called_once()

    async def test_turn_off_success(self, fan_entity, mock_coordinator, mock_duux_api):
        """Test successful turn off."""
        await fan_entity.async_turn_off()
        
        mock_duux_api.turn_off.assert_called_once()
        mock_coordinator.async_request_refresh.assert_called_once()

    async def test_turn_off_api_error(self, fan_entity, mock_coordinator, mock_duux_api):
        """Test turn off with API error."""
        mock_duux_api.turn_off.side_effect = DuuxApiError("Connection failed")
        
        with patch.object(fan_entity, '_handle_api_error') as mock_handle_error:
            await fan_entity.async_turn_off()
        
        mock_handle_error.assert_called_once()

    async def test_set_percentage_success(self, fan_entity, mock_coordinator, mock_duux_api):
        """Test successful set percentage."""
        await fan_entity.async_set_percentage(50)
        
        # 50% of 30 speeds = 15
        mock_duux_api.set_speed.assert_called_once_with(15)
        mock_coordinator.async_request_refresh.assert_called_once()

    async def test_set_percentage_api_error(self, fan_entity, mock_coordinator, mock_duux_api):
        """Test set percentage with API error."""
        mock_duux_api.set_speed.side_effect = DuuxApiError("Connection failed")
        
        with patch.object(fan_entity, '_handle_api_error') as mock_handle_error:
            await fan_entity.async_set_percentage(50)
        
        mock_handle_error.assert_called_once()

    async def test_oscillate_on_success(self, fan_entity, mock_coordinator, mock_duux_api):
        """Test successful oscillate on."""
        await fan_entity.async_oscillate(True)
        
        mock_duux_api.set_oscillation.assert_called_once_with(True)
        mock_coordinator.async_request_refresh.assert_called_once()

    async def test_oscillate_off_success(self, fan_entity, mock_coordinator, mock_duux_api):
        """Test successful oscillate off."""
        await fan_entity.async_oscillate(False)
        
        mock_duux_api.set_oscillation.assert_called_once_with(False)
        mock_coordinator.async_request_refresh.assert_called_once()

    async def test_oscillate_api_error(self, fan_entity, mock_coordinator, mock_duux_api):
        """Test oscillate with API error."""
        mock_duux_api.set_oscillation.side_effect = DuuxApiError("Connection failed")
        
        with patch.object(fan_entity, '_handle_api_error') as mock_handle_error:
            await fan_entity.async_oscillate(True)
        
        mock_handle_error.assert_called_once()

    def test_handle_api_error_auth_error(self, fan_entity, mock_config_entry):
        """Test handling authentication error."""
        error = DuuxApiError("401 Unauthorized")
        
        with patch("custom_components.duux.fan.ir.async_create_issue") as mock_create:
            fan_entity._handle_api_error(error, "Test operation")
        
        mock_create.assert_called_once_with(
            fan_entity.hass,
            DOMAIN,
            REPAIR_ISSUE_AUTH_FAILED,
            is_fixable=False,
            severity=mock_create.call_args[1]["severity"],
            translation_key="auth_failed",
            translation_placeholders={"device_id": mock_config_entry.data["device_id"]},
        )

    def test_handle_api_error_non_auth(self, fan_entity):
        """Test handling non-authentication error."""
        error = DuuxApiError("Network timeout")
        
        with patch("custom_components.duux.fan.ir.async_create_issue") as mock_create:
            fan_entity._handle_api_error(error, "Test operation")
        
        mock_create.assert_not_called()

    def test_is_auth_error_401(self, fan_entity):
        """Test auth error detection for 401."""
        assert fan_entity._is_auth_error("401 Unauthorized") is True

    def test_is_auth_error_403(self, fan_entity):
        """Test auth error detection for 403."""
        assert fan_entity._is_auth_error("403 Forbidden") is True

    def test_is_auth_error_unauthorized(self, fan_entity):
        """Test auth error detection for unauthorized text."""
        assert fan_entity._is_auth_error("Request unauthorized") is True

    def test_is_auth_error_token_expired(self, fan_entity):
        """Test auth error detection for token expired."""
        assert fan_entity._is_auth_error("Token expired") is True

    def test_is_auth_error_case_insensitive(self, fan_entity):
        """Test auth error detection is case insensitive."""
        assert fan_entity._is_auth_error("INVALID TOKEN") is True

    def test_is_auth_error_non_auth(self, fan_entity):
        """Test non-auth error is not detected as auth error."""
        assert fan_entity._is_auth_error("Network timeout") is False
        assert fan_entity._is_auth_error("500 Internal Server Error") is False