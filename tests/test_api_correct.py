"""Tests for the corrected Duux API client with text commands."""
from __future__ import annotations

from unittest.mock import AsyncMock, Mock
import pytest

# Inline the corrected API client for testing
class DuuxApiError(Exception):
    """Exception for Duux API errors."""


class DuuxApiClient:
    """API client for Duux Fan - corrected version."""

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
            # The API expects command as a text string in the format "tune set parameter value"
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

    async def set_speed(self, speed: int) -> None:
        """Set fan speed (1-30)."""
        if not 1 <= speed <= 30:
            raise ValueError("Speed must be between 1 and 30")
        await self.send_command(f"tune set speed {speed}")

    async def set_oscillation(self, oscillate: bool) -> None:
        """Set horizontal oscillation."""
        value = 1 if oscillate else 0
        await self.send_command(f"tune set horosc {value}")

    async def set_mode(self, mode: int) -> None:
        """Set fan mode."""
        await self.send_command(f"tune set mode {mode}")

    async def set_night_mode(self, night_mode: bool) -> None:
        """Set night mode."""
        value = 1 if night_mode else 0
        await self.send_command(f"tune set night {value}")


@pytest.mark.asyncio
class TestCorrectDuuxApiClient:
    """Test the corrected Duux API client with text commands."""

    def setup_method(self):
        """Set up test fixtures."""
        self.session = Mock()
        self.api_client = DuuxApiClient(self.session, "34:5f:45:ec:b8:34", "test_token")

    async def test_turn_on_command_format(self):
        """Test turn on sends the correct text command."""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json = AsyncMock(return_value={"success": True})
        
        mock_context_manager = AsyncMock()
        mock_context_manager.__aenter__ = AsyncMock(return_value=mock_response)
        mock_context_manager.__aexit__ = AsyncMock(return_value=None)
        
        self.api_client._session.post = Mock(return_value=mock_context_manager)
        
        await self.api_client.turn_on()
        
        # Verify the exact command format
        call_args = self.api_client._session.post.call_args
        json_data = call_args[1]["json"]
        assert json_data == {"command": "tune set power 1"}

    async def test_turn_off_command_format(self):
        """Test turn off sends the correct text command."""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json = AsyncMock(return_value={"success": True})
        
        mock_context_manager = AsyncMock()
        mock_context_manager.__aenter__ = AsyncMock(return_value=mock_response)
        mock_context_manager.__aexit__ = AsyncMock(return_value=None)
        
        self.api_client._session.post = Mock(return_value=mock_context_manager)
        
        await self.api_client.turn_off()
        
        # Verify the exact command format
        call_args = self.api_client._session.post.call_args
        json_data = call_args[1]["json"]
        assert json_data == {"command": "tune set power 0"}

    async def test_set_speed_command_format(self):
        """Test set speed sends the correct text command."""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json = AsyncMock(return_value={"success": True})
        
        mock_context_manager = AsyncMock()
        mock_context_manager.__aenter__ = AsyncMock(return_value=mock_response)
        mock_context_manager.__aexit__ = AsyncMock(return_value=None)
        
        self.api_client._session.post = Mock(return_value=mock_context_manager)
        
        await self.api_client.set_speed(15)
        
        # Verify the exact command format
        call_args = self.api_client._session.post.call_args
        json_data = call_args[1]["json"]
        assert json_data == {"command": "tune set speed 15"}

    async def test_set_oscillation_on_command_format(self):
        """Test oscillation on sends the correct text command."""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json = AsyncMock(return_value={"success": True})
        
        mock_context_manager = AsyncMock()
        mock_context_manager.__aenter__ = AsyncMock(return_value=mock_response)
        mock_context_manager.__aexit__ = AsyncMock(return_value=None)
        
        self.api_client._session.post = Mock(return_value=mock_context_manager)
        
        await self.api_client.set_oscillation(True)
        
        # Verify the exact command format
        call_args = self.api_client._session.post.call_args
        json_data = call_args[1]["json"]
        assert json_data == {"command": "tune set horosc 1"}

    async def test_set_oscillation_off_command_format(self):
        """Test oscillation off sends the correct text command."""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json = AsyncMock(return_value={"success": True})
        
        mock_context_manager = AsyncMock()
        mock_context_manager.__aenter__ = AsyncMock(return_value=mock_response)
        mock_context_manager.__aexit__ = AsyncMock(return_value=None)
        
        self.api_client._session.post = Mock(return_value=mock_context_manager)
        
        await self.api_client.set_oscillation(False)
        
        # Verify the exact command format
        call_args = self.api_client._session.post.call_args
        json_data = call_args[1]["json"]
        assert json_data == {"command": "tune set horosc 0"}

    async def test_set_mode_command_format(self):
        """Test mode setting sends the correct text command."""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json = AsyncMock(return_value={"success": True})
        
        mock_context_manager = AsyncMock()
        mock_context_manager.__aenter__ = AsyncMock(return_value=mock_response)
        mock_context_manager.__aexit__ = AsyncMock(return_value=None)
        
        self.api_client._session.post = Mock(return_value=mock_context_manager)
        
        await self.api_client.set_mode(2)
        
        # Verify the exact command format
        call_args = self.api_client._session.post.call_args
        json_data = call_args[1]["json"]
        assert json_data == {"command": "tune set mode 2"}

    async def test_set_night_mode_on_command_format(self):
        """Test night mode on sends the correct text command."""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json = AsyncMock(return_value={"success": True})
        
        mock_context_manager = AsyncMock()
        mock_context_manager.__aenter__ = AsyncMock(return_value=mock_response)
        mock_context_manager.__aexit__ = AsyncMock(return_value=None)
        
        self.api_client._session.post = Mock(return_value=mock_context_manager)
        
        await self.api_client.set_night_mode(True)
        
        # Verify the exact command format
        call_args = self.api_client._session.post.call_args
        json_data = call_args[1]["json"]
        assert json_data == {"command": "tune set night 1"}

    async def test_set_night_mode_off_command_format(self):
        """Test night mode off sends the correct text command."""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json = AsyncMock(return_value={"success": True})
        
        mock_context_manager = AsyncMock()
        mock_context_manager.__aenter__ = AsyncMock(return_value=mock_response)
        mock_context_manager.__aexit__ = AsyncMock(return_value=None)
        
        self.api_client._session.post = Mock(return_value=mock_context_manager)
        
        await self.api_client.set_night_mode(False)
        
        # Verify the exact command format
        call_args = self.api_client._session.post.call_args
        json_data = call_args[1]["json"]
        assert json_data == {"command": "tune set night 0"}

    async def test_speed_validation(self):
        """Test speed validation still works."""
        with pytest.raises(ValueError, match="Speed must be between 1 and 30"):
            await self.api_client.set_speed(0)
        
        with pytest.raises(ValueError, match="Speed must be between 1 and 30"):
            await self.api_client.set_speed(31)

    async def test_all_valid_speeds(self):
        """Test all valid speed values generate correct commands."""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json = AsyncMock(return_value={"success": True})
        
        mock_context_manager = AsyncMock()
        mock_context_manager.__aenter__ = AsyncMock(return_value=mock_response)
        mock_context_manager.__aexit__ = AsyncMock(return_value=None)
        
        self.api_client._session.post = Mock(return_value=mock_context_manager)
        
        # Test a few key speeds
        for speed in [1, 15, 30]:
            await self.api_client.set_speed(speed)
            call_args = self.api_client._session.post.call_args
            json_data = call_args[1]["json"]
            assert json_data == {"command": f"tune set speed {speed}"}


if __name__ == "__main__":
    pytest.main([__file__, "-v"])