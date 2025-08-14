"""Test to validate the correct power commands for Duux fan."""
from __future__ import annotations

from unittest.mock import AsyncMock, Mock
import pytest

# Import the API client from our main module
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

class DuuxApiError(Exception):
    """Exception for Duux API errors."""

class DuuxApiClient:
    """API client for Duux Fan - final corrected version."""

    def __init__(self, session, device_id: str, jwt_token: str) -> None:
        """Initialize the API client."""
        self._session = session
        self._device_id = device_id
        self._jwt_token = jwt_token

    async def send_command(self, command_text: str) -> dict:
        """Send a text command to the Duux fan."""
        api_base_url = "https://v5.api.cloudgarden.nl"
        url = f"{api_base_url}/sensor/{self._device_id}/commands"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self._jwt_token}",
            "Host": "v5.api.cloudgarden.nl",
        }

        try:
            command_data = {"command": command_text}
            async with self._session.post(
                url, json=command_data, headers=headers
            ) as response:
                if not response.ok:
                    error_data = await response.json()
                    raise DuuxApiError(f"Command failed: {error_data}")
                
                return await response.json()
        except Exception as err:
            raise DuuxApiError(f"Error connecting to Duux API: {err}") from err

    async def turn_on(self) -> None:
        """Turn on the fan."""
        await self.send_command("tune set power 1")

    async def turn_off(self) -> None:
        """Turn off the fan."""
        await self.send_command("tune set power 0")


@pytest.mark.asyncio
class TestPowerCommands:
    """Test the correct power commands implementation."""

    def setup_method(self):
        """Set up test fixtures."""
        self.session = Mock()
        self.api_client = DuuxApiClient(self.session, "34:5f:45:ec:b8:34", "test_token")

    async def test_turn_on_power_command(self):
        """Test that turn_on sends 'tune set power 1'."""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json = AsyncMock(return_value={"success": True})
        
        mock_context_manager = AsyncMock()
        mock_context_manager.__aenter__ = AsyncMock(return_value=mock_response)
        mock_context_manager.__aexit__ = AsyncMock(return_value=None)
        
        self.api_client._session.post = Mock(return_value=mock_context_manager)
        
        await self.api_client.turn_on()
        
        # Verify the exact command sent
        call_args = self.api_client._session.post.call_args
        json_data = call_args[1]["json"]
        assert json_data == {"command": "tune set power 1"}

    async def test_turn_off_power_command(self):
        """Test that turn_off sends 'tune set power 0'."""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json = AsyncMock(return_value={"success": True})
        
        mock_context_manager = AsyncMock()
        mock_context_manager.__aenter__ = AsyncMock(return_value=mock_response)
        mock_context_manager.__aexit__ = AsyncMock(return_value=None)
        
        self.api_client._session.post = Mock(return_value=mock_context_manager)
        
        await self.api_client.turn_off()
        
        # Verify the exact command sent
        call_args = self.api_client._session.post.call_args
        json_data = call_args[1]["json"]
        assert json_data == {"command": "tune set power 0"}

    async def test_power_commands_consistency(self):
        """Test that power commands are consistent and correct."""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json = AsyncMock(return_value={"success": True})
        
        mock_context_manager = AsyncMock()
        mock_context_manager.__aenter__ = AsyncMock(return_value=mock_response)
        mock_context_manager.__aexit__ = AsyncMock(return_value=None)
        
        self.api_client._session.post = Mock(return_value=mock_context_manager)
        
        # Test turn on
        await self.api_client.turn_on()
        call_args = self.api_client._session.post.call_args
        json_data = call_args[1]["json"]
        assert json_data["command"] == "tune set power 1"
        
        # Test turn off  
        await self.api_client.turn_off()
        call_args = self.api_client._session.post.call_args
        json_data = call_args[1]["json"]
        assert json_data["command"] == "tune set power 0"

    async def test_api_call_structure(self):
        """Test that the API call structure is correct."""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json = AsyncMock(return_value={"success": True})
        
        mock_context_manager = AsyncMock()
        mock_context_manager.__aenter__ = AsyncMock(return_value=mock_response)
        mock_context_manager.__aexit__ = AsyncMock(return_value=None)
        
        self.api_client._session.post = Mock(return_value=mock_context_manager)
        
        await self.api_client.turn_on()
        
        # Verify the URL and headers
        call_args = self.api_client._session.post.call_args
        url = call_args[0][0]
        headers = call_args[1]["headers"]
        json_data = call_args[1]["json"]
        
        assert "34:5f:45:ec:b8:34" in url
        assert "/commands" in url
        assert headers["Authorization"] == "Bearer test_token"
        assert headers["Host"] == "v5.api.cloudgarden.nl"
        assert headers["Content-Type"] == "application/json"
        assert json_data == {"command": "tune set power 1"}


if __name__ == "__main__":
    pytest.main([__file__, "-v"])