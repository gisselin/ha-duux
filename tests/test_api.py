"""Tests for the Duux API client."""
from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, Mock, patch
import pytest
import aiohttp

from custom_components.duux.api import DuuxApiClient, DuuxApiError


@pytest.mark.unit
class TestDuuxApiClient:
    """Test the DuuxApiClient."""

    @pytest.fixture
    def api_client(self):
        """Create a DuuxApiClient for testing."""
        session = Mock()
        return DuuxApiClient(session, "34:5f:45:ec:b8:34", "test_token")

    async def test_init(self, api_client):
        """Test API client initialization."""
        assert api_client._device_id == "34:5f:45:ec:b8:34"
        assert api_client._jwt_token == "test_token"
        assert api_client._session is not None

    async def test_get_status_success(self, api_client, mock_api_responses):
        """Test successful status request."""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json = AsyncMock(return_value=mock_api_responses["status_success"])
        
        api_client._session.get = AsyncMock()
        api_client._session.get.return_value.__aenter__ = AsyncMock(return_value=mock_response)
        api_client._session.get.return_value.__aexit__ = AsyncMock(return_value=None)

        result = await api_client.get_status()
        
        assert result == mock_api_responses["status_success"]
        api_client._session.get.assert_called_once()

    async def test_get_status_auth_error(self, api_client, mock_api_responses):
        """Test status request with authentication error."""
        mock_response = Mock()
        mock_response.ok = False
        mock_response.json = AsyncMock(return_value=mock_api_responses["auth_error"])
        
        api_client._session.get = AsyncMock()
        api_client._session.get.return_value.__aenter__ = AsyncMock(return_value=mock_response)
        api_client._session.get.return_value.__aexit__ = AsyncMock(return_value=None)

        with pytest.raises(DuuxApiError, match="Status request failed"):
            await api_client.get_status()

    async def test_get_status_timeout(self, api_client):
        """Test status request timeout."""
        api_client._session.get = AsyncMock(side_effect=asyncio.TimeoutError())

        with pytest.raises(DuuxApiError, match="Timeout connecting to Duux API"):
            await api_client.get_status()

    async def test_get_status_client_error(self, api_client):
        """Test status request with client error."""
        api_client._session.get = AsyncMock(side_effect=aiohttp.ClientError("Connection failed"))

        with pytest.raises(DuuxApiError, match="Error connecting to Duux API"):
            await api_client.get_status()

    async def test_send_command_success(self, api_client, mock_api_responses):
        """Test successful command sending."""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json = AsyncMock(return_value=mock_api_responses["command_success"])
        
        api_client._session.post = AsyncMock()
        api_client._session.post.return_value.__aenter__ = AsyncMock(return_value=mock_response)
        api_client._session.post.return_value.__aexit__ = AsyncMock(return_value=None)

        command = {"power": 1}
        result = await api_client.send_command(command)
        
        assert result == mock_api_responses["command_success"]
        api_client._session.post.assert_called_once()

    async def test_send_command_error(self, api_client, mock_api_responses):
        """Test command sending with error response."""
        mock_response = Mock()
        mock_response.ok = False
        mock_response.json = AsyncMock(return_value=mock_api_responses["auth_error"])
        
        api_client._session.post = AsyncMock()
        api_client._session.post.return_value.__aenter__ = AsyncMock(return_value=mock_response)
        api_client._session.post.return_value.__aexit__ = AsyncMock(return_value=None)

        with pytest.raises(DuuxApiError, match="Command failed"):
            await api_client.send_command({"power": 1})

    async def test_turn_on(self, api_client):
        """Test turn on command."""
        api_client.send_command = AsyncMock()
        
        await api_client.turn_on()
        
        api_client.send_command.assert_called_once_with({"power": 1})

    async def test_turn_off(self, api_client):
        """Test turn off command."""
        api_client.send_command = AsyncMock()
        
        await api_client.turn_off()
        
        api_client.send_command.assert_called_once_with({"power": 0})

    async def test_set_speed_valid(self, api_client):
        """Test setting valid speed."""
        api_client.send_command = AsyncMock()
        
        await api_client.set_speed(15)
        
        api_client.send_command.assert_called_once_with({"speed": 15})

    async def test_set_speed_invalid_low(self, api_client):
        """Test setting speed too low."""
        with pytest.raises(ValueError, match="Speed must be between 1 and 30"):
            await api_client.set_speed(0)

    async def test_set_speed_invalid_high(self, api_client):
        """Test setting speed too high."""
        with pytest.raises(ValueError, match="Speed must be between 1 and 30"):
            await api_client.set_speed(31)

    async def test_set_oscillation_on(self, api_client):
        """Test enabling oscillation."""
        api_client.send_command = AsyncMock()
        
        await api_client.set_oscillation(True)
        
        api_client.send_command.assert_called_once_with({"horosc": 1})

    async def test_set_oscillation_off(self, api_client):
        """Test disabling oscillation."""
        api_client.send_command = AsyncMock()
        
        await api_client.set_oscillation(False)
        
        api_client.send_command.assert_called_once_with({"horosc": 0})

    async def test_set_mode(self, api_client):
        """Test setting fan mode."""
        api_client.send_command = AsyncMock()
        
        await api_client.set_mode(2)
        
        api_client.send_command.assert_called_once_with({"mode": 2})

    async def test_set_night_mode_on(self, api_client):
        """Test enabling night mode."""
        api_client.send_command = AsyncMock()
        
        await api_client.set_night_mode(True)
        
        api_client.send_command.assert_called_once_with({"night": 1})

    async def test_set_night_mode_off(self, api_client):
        """Test disabling night mode."""
        api_client.send_command = AsyncMock()
        
        await api_client.set_night_mode(False)
        
        api_client.send_command.assert_called_once_with({"night": 0})