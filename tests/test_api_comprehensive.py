"""Comprehensive tests for the Duux API client with additional error scenarios."""
from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, Mock
import pytest
import aiohttp

# Copy the DuuxApiClient and DuuxApiError from the standalone test
from tests.test_api_standalone import DuuxApiClient, DuuxApiError


@pytest.mark.asyncio
class TestDuuxApiClientComprehensive:
    """Comprehensive test suite for the DuuxApiClient."""

    def setup_method(self):
        """Set up test fixtures."""
        self.session = Mock()
        self.api_client = DuuxApiClient(self.session, "34:5f:45:ec:b8:34", "test_token")

    async def test_get_status_timeout_error(self):
        """Test status request timeout."""
        self.api_client._session.get.side_effect = asyncio.TimeoutError("Request timed out")
        
        with pytest.raises(DuuxApiError, match="Timeout connecting to Duux API"):
            await self.api_client.get_status()

    async def test_get_status_client_error(self):
        """Test status request with client error."""
        self.api_client._session.get.side_effect = aiohttp.ClientError("Connection failed")
        
        with pytest.raises(DuuxApiError, match="Error connecting to Duux API"):
            await self.api_client.get_status()

    async def test_send_command_timeout_error(self):
        """Test command sending timeout."""
        self.api_client._session.post.side_effect = asyncio.TimeoutError("Request timed out")
        
        with pytest.raises(DuuxApiError, match="Timeout connecting to Duux API"):
            await self.api_client.send_command({"power": 1})

    async def test_send_command_client_error(self):
        """Test command sending with client error."""
        self.api_client._session.post.side_effect = aiohttp.ClientError("Connection failed")
        
        with pytest.raises(DuuxApiError, match="Error connecting to Duux API"):
            await self.api_client.send_command({"power": 1})

    async def test_all_speed_values(self):
        """Test all valid speed values from 1 to 30."""
        self.api_client.send_command = AsyncMock()
        
        for speed in range(1, 31):
            await self.api_client.set_speed(speed)
            self.api_client.send_command.assert_called_with({"speed": speed})

    async def test_boundary_speed_values(self):
        """Test boundary values for speed."""
        self.api_client.send_command = AsyncMock()
        
        # Test minimum valid speed
        await self.api_client.set_speed(1)
        self.api_client.send_command.assert_called_with({"speed": 1})
        
        # Test maximum valid speed
        await self.api_client.set_speed(30)
        self.api_client.send_command.assert_called_with({"speed": 30})

    async def test_invalid_speed_zero(self):
        """Test speed value of 0."""
        with pytest.raises(ValueError, match="Speed must be between 1 and 30"):
            await self.api_client.set_speed(0)

    async def test_invalid_speed_negative(self):
        """Test negative speed value."""
        with pytest.raises(ValueError, match="Speed must be between 1 and 30"):
            await self.api_client.set_speed(-5)

    async def test_invalid_speed_too_high(self):
        """Test speed value above 30."""
        with pytest.raises(ValueError, match="Speed must be between 1 and 30"):
            await self.api_client.set_speed(31)

    async def test_invalid_speed_very_high(self):
        """Test very high speed value."""
        with pytest.raises(ValueError, match="Speed must be between 1 and 30"):
            await self.api_client.set_speed(100)

    async def test_device_id_in_urls(self):
        """Test that device ID is correctly included in URLs."""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json = AsyncMock(return_value={"data": {}})
        
        mock_context_manager = AsyncMock()
        mock_context_manager.__aenter__ = AsyncMock(return_value=mock_response)
        mock_context_manager.__aexit__ = AsyncMock(return_value=None)
        
        self.api_client._session.get = Mock(return_value=mock_context_manager)
        
        await self.api_client.get_status()
        
        # Check that the device ID is in the URL
        call_args = self.api_client._session.get.call_args
        url = call_args[0][0]  # First positional argument
        assert "34:5f:45:ec:b8:34" in url
        assert "/data/34:5f:45:ec:b8:34/status" in url

    async def test_jwt_token_in_headers(self):
        """Test that JWT token is correctly included in headers."""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json = AsyncMock(return_value={"data": {}})
        
        mock_context_manager = AsyncMock()
        mock_context_manager.__aenter__ = AsyncMock(return_value=mock_response)
        mock_context_manager.__aexit__ = AsyncMock(return_value=None)
        
        self.api_client._session.get = Mock(return_value=mock_context_manager)
        
        await self.api_client.get_status()
        
        # Check that the JWT token is in the headers
        call_args = self.api_client._session.get.call_args
        headers = call_args[1]["headers"]  # keyword arguments
        assert headers["Authorization"] == "Bearer test_token"

    async def test_host_header_included(self):
        """Test that Host header is correctly included."""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json = AsyncMock(return_value={"data": {}})
        
        mock_context_manager = AsyncMock()
        mock_context_manager.__aenter__ = AsyncMock(return_value=mock_response)
        mock_context_manager.__aexit__ = AsyncMock(return_value=None)
        
        self.api_client._session.get = Mock(return_value=mock_context_manager)
        
        await self.api_client.get_status()
        
        # Check that the Host header is included
        call_args = self.api_client._session.get.call_args
        headers = call_args[1]["headers"]
        assert headers["Host"] == "v5.api.cloudgarden.nl"

    async def test_command_structure(self):
        """Test that commands are properly structured."""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json = AsyncMock(return_value={"success": True})
        
        mock_context_manager = AsyncMock()
        mock_context_manager.__aenter__ = AsyncMock(return_value=mock_response)
        mock_context_manager.__aexit__ = AsyncMock(return_value=None)
        
        self.api_client._session.post = Mock(return_value=mock_context_manager)
        
        command = {"power": 1, "speed": 15}
        await self.api_client.send_command(command)
        
        # Check that the command is properly wrapped
        call_args = self.api_client._session.post.call_args
        json_data = call_args[1]["json"]
        assert json_data == {"command": command}

    async def test_boolean_conversion_oscillation(self):
        """Test boolean conversion for oscillation commands."""
        self.api_client.send_command = AsyncMock()
        
        # Test True -> 1
        await self.api_client.set_oscillation(True)
        self.api_client.send_command.assert_called_with({"horosc": 1})
        
        # Test False -> 0
        await self.api_client.set_oscillation(False)
        self.api_client.send_command.assert_called_with({"horosc": 0})

    async def test_boolean_conversion_night_mode(self):
        """Test boolean conversion for night mode commands."""
        self.api_client.send_command = AsyncMock()
        
        # Test True -> 1
        await self.api_client.set_night_mode(True)
        self.api_client.send_command.assert_called_with({"night": 1})
        
        # Test False -> 0
        await self.api_client.set_night_mode(False)
        self.api_client.send_command.assert_called_with({"night": 0})

    async def test_mode_values(self):
        """Test different mode values."""
        self.api_client.send_command = AsyncMock()
        
        for mode in [0, 1, 2, 3]:
            await self.api_client.set_mode(mode)
            self.api_client.send_command.assert_called_with({"mode": mode})


if __name__ == "__main__":
    pytest.main([__file__, "-v"])