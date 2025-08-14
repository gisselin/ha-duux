"""Tests for the Duux data update coordinator."""
from __future__ import annotations

from unittest.mock import AsyncMock, Mock, patch
import pytest
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import UpdateFailed

from custom_components.duux.coordinator import DuuxDataUpdateCoordinator
from custom_components.duux.api import DuuxApiError
from custom_components.duux.const import DOMAIN, REPAIR_ISSUE_AUTH_FAILED


@pytest.mark.unit
class TestDuuxDataUpdateCoordinator:
    """Test the DuuxDataUpdateCoordinator."""

    @pytest.fixture
    def mock_hass(self):
        """Mock Home Assistant."""
        hass = Mock(spec=HomeAssistant)
        hass.data = {}
        return hass

    @pytest.fixture
    def mock_session(self):
        """Mock aiohttp session."""
        return Mock()

    @pytest.fixture
    def coordinator(self, mock_hass, mock_session, mock_duux_api):
        """Create a coordinator for testing."""
        with patch("custom_components.duux.coordinator.DuuxApiClient") as mock_api_class:
            mock_api_class.return_value = mock_duux_api
            coord = DuuxDataUpdateCoordinator(
                mock_hass,
                mock_session,
                "34:5f:45:ec:b8:34",
                "test_token"
            )
            return coord

    async def test_init(self, coordinator):
        """Test coordinator initialization."""
        assert coordinator._device_id == "34:5f:45:ec:b8:34"
        assert coordinator._auth_failure_count == 0
        assert coordinator._repair_issue_created is False

    async def test_update_data_success(self, coordinator, mock_duux_api, mock_api_responses):
        """Test successful data update."""
        mock_duux_api.get_status.return_value = mock_api_responses["status_success"]
        
        result = await coordinator._async_update_data()
        
        assert result == mock_api_responses["status_success"]["data"]
        assert coordinator._auth_failure_count == 0

    async def test_update_data_success_after_auth_failures(self, coordinator, mock_duux_api, mock_api_responses):
        """Test successful data update after previous auth failures."""
        coordinator._auth_failure_count = 2
        coordinator._repair_issue_created = True
        mock_duux_api.get_status.return_value = mock_api_responses["status_success"]
        
        with patch("custom_components.duux.coordinator.ir.async_delete_issue") as mock_delete:
            result = await coordinator._async_update_data()
        
        assert result == mock_api_responses["status_success"]["data"]
        assert coordinator._auth_failure_count == 0
        assert coordinator._repair_issue_created is False
        mock_delete.assert_called_once_with(coordinator.hass, DOMAIN, REPAIR_ISSUE_AUTH_FAILED)

    async def test_update_data_invalid_response(self, coordinator, mock_duux_api):
        """Test data update with invalid response."""
        mock_duux_api.get_status.return_value = {"invalid": "response"}
        
        with pytest.raises(UpdateFailed, match="Invalid response from Duux API"):
            await coordinator._async_update_data()

    async def test_update_data_api_error_non_auth(self, coordinator, mock_duux_api):
        """Test data update with non-authentication API error."""
        mock_duux_api.get_status.side_effect = DuuxApiError("Network error")
        
        with pytest.raises(UpdateFailed, match="Error communicating with Duux API"):
            await coordinator._async_update_data()
        
        assert coordinator._auth_failure_count == 0

    async def test_update_data_auth_error_first_failure(self, coordinator, mock_duux_api):
        """Test data update with authentication error - first failure."""
        mock_duux_api.get_status.side_effect = DuuxApiError("401 Unauthorized")
        
        with pytest.raises(UpdateFailed):
            await coordinator._async_update_data()
        
        assert coordinator._auth_failure_count == 1
        assert coordinator._repair_issue_created is False

    async def test_update_data_auth_error_third_failure(self, coordinator, mock_duux_api):
        """Test data update with authentication error - third failure creates repair issue."""
        coordinator._auth_failure_count = 2
        mock_duux_api.get_status.side_effect = DuuxApiError("403 Forbidden")
        
        with patch("custom_components.duux.coordinator.ir.async_create_issue") as mock_create:
            with pytest.raises(UpdateFailed):
                await coordinator._async_update_data()
        
        assert coordinator._auth_failure_count == 3
        assert coordinator._repair_issue_created is True
        mock_create.assert_called_once()

    async def test_update_data_auth_error_no_duplicate_repair(self, coordinator, mock_duux_api):
        """Test that repair issue is not created twice."""
        coordinator._auth_failure_count = 5
        coordinator._repair_issue_created = True
        mock_duux_api.get_status.side_effect = DuuxApiError("Token expired")
        
        with patch("custom_components.duux.coordinator.ir.async_create_issue") as mock_create:
            with pytest.raises(UpdateFailed):
                await coordinator._async_update_data()
        
        assert coordinator._auth_failure_count == 6
        mock_create.assert_not_called()

    def test_is_auth_error_401(self, coordinator):
        """Test auth error detection for 401."""
        assert coordinator._is_auth_error("401 Unauthorized") is True

    def test_is_auth_error_403(self, coordinator):
        """Test auth error detection for 403."""
        assert coordinator._is_auth_error("403 Forbidden") is True

    def test_is_auth_error_unauthorized(self, coordinator):
        """Test auth error detection for unauthorized text."""
        assert coordinator._is_auth_error("Request unauthorized") is True

    def test_is_auth_error_token_expired(self, coordinator):
        """Test auth error detection for token expired."""
        assert coordinator._is_auth_error("Token expired") is True

    def test_is_auth_error_invalid_token(self, coordinator):
        """Test auth error detection for invalid token."""
        assert coordinator._is_auth_error("Invalid token provided") is True

    def test_is_auth_error_case_insensitive(self, coordinator):
        """Test auth error detection is case insensitive."""
        assert coordinator._is_auth_error("UNAUTHORIZED ACCESS") is True

    def test_is_auth_error_non_auth(self, coordinator):
        """Test non-auth error is not detected as auth error."""
        assert coordinator._is_auth_error("Network timeout") is False
        assert coordinator._is_auth_error("500 Internal Server Error") is False

    def test_create_auth_repair_issue(self, coordinator):
        """Test repair issue creation."""
        with patch("custom_components.duux.coordinator.ir.async_create_issue") as mock_create:
            coordinator._create_auth_repair_issue()
        
        mock_create.assert_called_once_with(
            coordinator.hass,
            DOMAIN,
            REPAIR_ISSUE_AUTH_FAILED,
            is_fixable=False,
            severity=mock_create.call_args[1]["severity"],
            translation_key="auth_failed",
            translation_placeholders={"device_id": "34:5f:45:ec:b8:34"},
        )