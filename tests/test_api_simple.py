"""Simplified tests for the Duux API client without Home Assistant dependencies."""
from __future__ import annotations

import asyncio
import sys
import os
from unittest.mock import AsyncMock, Mock
import pytest

# Add the parent directory to the path so we can import our modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from custom_components.duux.api import DuuxApiClient, DuuxApiError


@pytest.mark.asyncio
class TestDuuxApiClientSimple:
    """Simplified test for the DuuxApiClient."""

    def setup_method(self):
        """Set up test fixtures."""
        self.session = Mock()
        self.api_client = DuuxApiClient(self.session, "34:5f:45:ec:b8:34", "test_token")

    async def test_init(self):
        """Test API client initialization."""
        assert self.api_client._device_id == "34:5f:45:ec:b8:34"
        assert self.api_client._jwt_token == "test_token"
        assert self.api_client._session is not None

    async def test_turn_on_calls_send_command(self):
        """Test turn on calls send_command with correct parameters."""
        self.api_client.send_command = AsyncMock()
        
        await self.api_client.turn_on()
        
        self.api_client.send_command.assert_called_once_with({"power": 1})

    async def test_turn_off_calls_send_command(self):
        """Test turn off calls send_command with correct parameters."""
        self.api_client.send_command = AsyncMock()
        
        await self.api_client.turn_off()
        
        self.api_client.send_command.assert_called_once_with({"power": 0})

    async def test_set_speed_valid(self):
        """Test setting valid speed."""
        self.api_client.send_command = AsyncMock()
        
        await self.api_client.set_speed(15)
        
        self.api_client.send_command.assert_called_once_with({"speed": 15})

    async def test_set_speed_invalid_low(self):
        """Test setting speed too low raises ValueError."""
        with pytest.raises(ValueError, match="Speed must be between 1 and 30"):
            await self.api_client.set_speed(0)

    async def test_set_speed_invalid_high(self):
        """Test setting speed too high raises ValueError."""
        with pytest.raises(ValueError, match="Speed must be between 1 and 30"):
            await self.api_client.set_speed(31)

    async def test_set_oscillation_on(self):
        """Test enabling oscillation."""
        self.api_client.send_command = AsyncMock()
        
        await self.api_client.set_oscillation(True)
        
        self.api_client.send_command.assert_called_once_with({"horosc": 1})

    async def test_set_oscillation_off(self):
        """Test disabling oscillation."""
        self.api_client.send_command = AsyncMock()
        
        await self.api_client.set_oscillation(False)
        
        self.api_client.send_command.assert_called_once_with({"horosc": 0})

    async def test_set_mode(self):
        """Test setting fan mode."""
        self.api_client.send_command = AsyncMock()
        
        await self.api_client.set_mode(2)
        
        self.api_client.send_command.assert_called_once_with({"mode": 2})

    async def test_set_night_mode_on(self):
        """Test enabling night mode."""
        self.api_client.send_command = AsyncMock()
        
        await self.api_client.set_night_mode(True)
        
        self.api_client.send_command.assert_called_once_with({"night": 1})

    async def test_set_night_mode_off(self):
        """Test disabling night mode."""
        self.api_client.send_command = AsyncMock()
        
        await self.api_client.set_night_mode(False)
        
        self.api_client.send_command.assert_called_once_with({"night": 0})

    async def test_get_status_success(self):
        """Test successful status request."""
        expected_response = {
            "data": {
                "power": 1,
                "speed": 15,
                "mode": 0,
                "horosc": 1
            }
        }
        
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json = AsyncMock(return_value=expected_response)
        
        self.api_client._session.get = AsyncMock()
        self.api_client._session.get.return_value.__aenter__ = AsyncMock(return_value=mock_response)
        self.api_client._session.get.return_value.__aexit__ = AsyncMock(return_value=None)

        result = await self.api_client.get_status()
        
        assert result == expected_response
        self.api_client._session.get.assert_called_once()

    async def test_send_command_success(self):
        """Test successful command sending."""
        expected_response = {"success": True}
        
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json = AsyncMock(return_value=expected_response)
        
        self.api_client._session.post = AsyncMock()
        self.api_client._session.post.return_value.__aenter__ = AsyncMock(return_value=mock_response)
        self.api_client._session.post.return_value.__aexit__ = AsyncMock(return_value=None)

        command = {"power": 1}
        result = await self.api_client.send_command(command)
        
        assert result == expected_response
        self.api_client._session.post.assert_called_once()


if __name__ == "__main__":
    # Run a simple test
    async def run_simple_test():
        test_instance = TestDuuxApiClientSimple()
        test_instance.setup_method()
        
        try:
            await test_instance.test_init()
            print("✓ test_init passed")
            
            await test_instance.test_turn_on_calls_send_command()
            print("✓ test_turn_on_calls_send_command passed")
            
            await test_instance.test_set_speed_valid()
            print("✓ test_set_speed_valid passed")
            
            try:
                await test_instance.test_set_speed_invalid_low()
                print("✗ test_set_speed_invalid_low failed - should have raised ValueError")
            except ValueError:
                print("✓ test_set_speed_invalid_low passed")
            
            print("\nAll basic tests passed!")
            
        except Exception as e:
            print(f"✗ Test failed: {e}")
            import traceback
            traceback.print_exc()

    # Run the simple test
    asyncio.run(run_simple_test())