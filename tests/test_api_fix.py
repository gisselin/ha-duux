"""Test to verify the API fix for JSON command structure."""
from __future__ import annotations

import json
from unittest.mock import AsyncMock, Mock
import pytest

from tests.test_api_standalone import DuuxApiClient


@pytest.mark.asyncio
class TestDuuxApiFix:
    """Test the specific API fix for command structure."""

    def setup_method(self):
        """Set up test fixtures."""
        self.session = Mock()
        self.api_client = DuuxApiClient(self.session, "34:5f:45:ec:b8:34", "test_token")

    async def test_command_json_serialization(self):
        """Test that commands are JSON serialized as strings."""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json = AsyncMock(return_value={"success": True})
        
        mock_context_manager = AsyncMock()
        mock_context_manager.__aenter__ = AsyncMock(return_value=mock_response)
        mock_context_manager.__aexit__ = AsyncMock(return_value=None)
        
        self.api_client._session.post = Mock(return_value=mock_context_manager)
        
        # Test with a power off command
        command = {"power": 0}
        await self.api_client.send_command(command)
        
        # Verify the exact structure sent to the API
        call_args = self.api_client._session.post.call_args
        json_data = call_args[1]["json"]
        
        # The command should be JSON serialized as a string
        expected_command_string = '{"power": 0}'
        assert json_data == {"command": expected_command_string}
        
        # Verify it's actually a string, not an object
        assert isinstance(json_data["command"], str)
        
        # Verify we can parse it back to the original command
        parsed_command = json.loads(json_data["command"])
        assert parsed_command == command

    async def test_complex_command_serialization(self):
        """Test serialization of complex commands."""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json = AsyncMock(return_value={"success": True})
        
        mock_context_manager = AsyncMock()
        mock_context_manager.__aenter__ = AsyncMock(return_value=mock_response)
        mock_context_manager.__aexit__ = AsyncMock(return_value=None)
        
        self.api_client._session.post = Mock(return_value=mock_context_manager)
        
        # Test with a complex command
        command = {
            "power": 1,
            "speed": 25,
            "horosc": 1,
            "mode": 2,
            "night": 0
        }
        await self.api_client.send_command(command)
        
        # Verify the structure
        call_args = self.api_client._session.post.call_args
        json_data = call_args[1]["json"]
        
        # Verify it's properly serialized
        assert isinstance(json_data["command"], str)
        parsed_command = json.loads(json_data["command"])
        assert parsed_command == command

    async def test_turn_off_command_structure(self):
        """Test the specific turn off command that was failing."""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json = AsyncMock(return_value={"success": True})
        
        mock_context_manager = AsyncMock()
        mock_context_manager.__aenter__ = AsyncMock(return_value=mock_response)
        mock_context_manager.__aexit__ = AsyncMock(return_value=None)
        
        self.api_client._session.post = Mock(return_value=mock_context_manager)
        
        # Test the turn_off method specifically
        await self.api_client.turn_off()
        
        # Verify the exact structure sent
        call_args = self.api_client._session.post.call_args
        json_data = call_args[1]["json"]
        
        # Should be: {"command": "{\"power\": 0}"}
        expected_command_string = '{"power": 0}'
        assert json_data == {"command": expected_command_string}
        
        # Double-check it's a string
        assert isinstance(json_data["command"], str)
        
        # Verify the parsed content
        parsed_command = json.loads(json_data["command"])
        assert parsed_command == {"power": 0}

    async def test_turn_on_command_structure(self):
        """Test the turn on command structure."""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json = AsyncMock(return_value={"success": True})
        
        mock_context_manager = AsyncMock()
        mock_context_manager.__aenter__ = AsyncMock(return_value=mock_response)
        mock_context_manager.__aexit__ = AsyncMock(return_value=None)
        
        self.api_client._session.post = Mock(return_value=mock_context_manager)
        
        # Test the turn_on method
        await self.api_client.turn_on()
        
        # Verify the structure
        call_args = self.api_client._session.post.call_args
        json_data = call_args[1]["json"]
        
        # Should be: {"command": "{\"power\": 1}"}
        expected_command_string = '{"power": 1}'
        assert json_data == {"command": expected_command_string}
        
        parsed_command = json.loads(json_data["command"])
        assert parsed_command == {"power": 1}


if __name__ == "__main__":
    pytest.main([__file__, "-v"])