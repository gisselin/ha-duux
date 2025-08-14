"""Tests for the Duux config flow."""
from __future__ import annotations

from unittest.mock import AsyncMock, Mock, patch
import pytest
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.const import CONF_DEVICE_ID

from custom_components.duux.config_flow import ConfigFlow, CannotConnect, InvalidAuth
from custom_components.duux.const import DOMAIN


@pytest.mark.unit
class TestConfigFlow:
    """Test the config flow."""

    @pytest.fixture
    def mock_hass(self):
        """Mock Home Assistant."""
        hass = Mock(spec=HomeAssistant)
        hass.data = {}
        return hass

    @pytest.fixture
    def config_flow(self, mock_hass):
        """Create a config flow for testing."""
        flow = ConfigFlow()
        flow.hass = mock_hass
        return flow

    async def test_form_user_step(self, config_flow):
        """Test the user step shows the form."""
        result = await config_flow.async_step_user()
        
        assert result["type"] == FlowResultType.FORM
        assert result["step_id"] == "user"
        assert result["errors"] == {}

    async def test_form_user_success(self, config_flow, mock_aiohttp_session):
        """Test successful configuration."""
        user_input = {
            CONF_DEVICE_ID: "34:5f:45:ec:b8:34",
            "jwt_token": "test_token_12345"
        }
        
        with patch("custom_components.duux.config_flow.validate_input") as mock_validate:
            mock_validate.return_value = {"title": "Duux Fan (34:5f:45:ec:b8:34)"}
            
            result = await config_flow.async_step_user(user_input)
        
        assert result["type"] == FlowResultType.CREATE_ENTRY
        assert result["title"] == "Duux Fan (34:5f:45:ec:b8:34)"
        assert result["data"] == user_input

    async def test_form_user_cannot_connect(self, config_flow):
        """Test cannot connect error."""
        user_input = {
            CONF_DEVICE_ID: "34:5f:45:ec:b8:34",
            "jwt_token": "test_token_12345"
        }
        
        with patch("custom_components.duux.config_flow.validate_input") as mock_validate:
            mock_validate.side_effect = CannotConnect()
            
            result = await config_flow.async_step_user(user_input)
        
        assert result["type"] == FlowResultType.FORM
        assert result["errors"] == {"base": "cannot_connect"}

    async def test_form_user_invalid_auth(self, config_flow):
        """Test invalid auth error."""
        user_input = {
            CONF_DEVICE_ID: "34:5f:45:ec:b8:34",
            "jwt_token": "invalid_token"
        }
        
        with patch("custom_components.duux.config_flow.validate_input") as mock_validate:
            mock_validate.side_effect = InvalidAuth()
            
            result = await config_flow.async_step_user(user_input)
        
        assert result["type"] == FlowResultType.FORM
        assert result["errors"] == {"base": "invalid_auth"}

    async def test_form_user_unknown_error(self, config_flow):
        """Test unknown error."""
        user_input = {
            CONF_DEVICE_ID: "34:5f:45:ec:b8:34",
            "jwt_token": "test_token_12345"
        }
        
        with patch("custom_components.duux.config_flow.validate_input") as mock_validate:
            mock_validate.side_effect = Exception("Unexpected error")
            
            result = await config_flow.async_step_user(user_input)
        
        assert result["type"] == FlowResultType.FORM
        assert result["errors"] == {"base": "unknown"}

    async def test_form_user_already_configured(self, config_flow):
        """Test device already configured."""
        user_input = {
            CONF_DEVICE_ID: "34:5f:45:ec:b8:34",
            "jwt_token": "test_token_12345"
        }
        
        # Mock that the device is already configured
        with patch.object(config_flow, "async_set_unique_id"):
            with patch.object(config_flow, "_abort_if_unique_id_configured") as mock_abort:
                mock_abort.side_effect = Exception("Already configured")
                
                with pytest.raises(Exception, match="Already configured"):
                    await config_flow.async_step_user(user_input)


@pytest.mark.unit
class TestValidateInput:
    """Test the validate_input function."""

    async def test_validate_input_success(self, mock_aiohttp_session, mock_api_responses):
        """Test successful validation."""
        from custom_components.duux.config_flow import validate_input
        
        data = {
            CONF_DEVICE_ID: "34:5f:45:ec:b8:34",
            "jwt_token": "test_token_12345"
        }
        
        mock_hass = Mock()
        
        with patch("custom_components.duux.config_flow.async_get_clientsession") as mock_session:
            mock_session.return_value = mock_aiohttp_session
            
            with patch("custom_components.duux.config_flow.DuuxApiClient") as mock_api_class:
                mock_api = Mock()
                mock_api.get_status = AsyncMock(return_value=mock_api_responses["status_success"])
                mock_api_class.return_value = mock_api
                
                result = await validate_input(mock_hass, data)
        
        assert result == {"title": f"Duux Fan ({data[CONF_DEVICE_ID]})"}

    async def test_validate_input_api_error(self, mock_aiohttp_session):
        """Test validation with API error."""
        from custom_components.duux.config_flow import validate_input, InvalidAuth
        from custom_components.duux.api import DuuxApiError
        
        data = {
            CONF_DEVICE_ID: "34:5f:45:ec:b8:34",
            "jwt_token": "invalid_token"
        }
        
        mock_hass = Mock()
        
        with patch("custom_components.duux.config_flow.async_get_clientsession") as mock_session:
            mock_session.return_value = mock_aiohttp_session
            
            with patch("custom_components.duux.config_flow.DuuxApiClient") as mock_api_class:
                mock_api = Mock()
                mock_api.get_status = AsyncMock(side_effect=DuuxApiError("401 Unauthorized"))
                mock_api_class.return_value = mock_api
                
                with pytest.raises(InvalidAuth):
                    await validate_input(mock_hass, data)