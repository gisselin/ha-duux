"""Standalone tests for the Duux API client logic."""
from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, Mock
import pytest
import aiohttp


class DuuxApiError(Exception):
    """Exception for Duux API errors."""


class DuuxApiClient:
    """API client for Duux Fan - standalone version for testing."""

    def __init__(self, session, device_id: str, jwt_token: str) -> None:
        """Initialize the API client."""
        self._session = session
        self._device_id = device_id
        self._jwt_token = jwt_token

    async def send_command(self, command: dict) -> dict:
        """Send a command to the Duux fan."""
        api_base_url = "https://v5.api.cloudgarden.nl"
        url = f"{api_base_url}/sensor/{self._device_id}/commands"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self._jwt_token}",
            "Host": "v5.api.cloudgarden.nl",
        }

        try:
            async with self._session.post(
                url, json={"command": command}, headers=headers
            ) as response:
                if not response.ok:
                    error_data = await response.json()
                    raise DuuxApiError(f"Command failed: {error_data}")
                
                return await response.json()
        except asyncio.TimeoutError as err:
            raise DuuxApiError("Timeout connecting to Duux API") from err
        except aiohttp.ClientError as err:
            raise DuuxApiError(f"Error connecting to Duux API: {err}") from err

    async def get_status(self) -> dict:
        """Get the current status of the Duux fan."""
        api_base_url = "https://v5.api.cloudgarden.nl"
        url = f"{api_base_url}/data/{self._device_id}/status"
        headers = {
            "Authorization": f"Bearer {self._jwt_token}",
            "Host": "v5.api.cloudgarden.nl",
        }

        try:
            async with self._session.get(url, headers=headers) as response:
                if not response.ok:
                    error_data = await response.json()
                    raise DuuxApiError(f"Status request failed: {error_data}")
                
                return await response.json()
        except asyncio.TimeoutError as err:
            raise DuuxApiError("Timeout connecting to Duux API") from err
        except aiohttp.ClientError as err:
            raise DuuxApiError(f"Error connecting to Duux API: {err}") from err

    async def turn_on(self) -> None:
        """Turn on the fan."""
        await self.send_command({"power": 1})

    async def turn_off(self) -> None:
        """Turn off the fan."""
        await self.send_command({"power": 0})

    async def set_speed(self, speed: int) -> None:
        """Set fan speed (1-30)."""
        if not 1 <= speed <= 30:
            raise ValueError("Speed must be between 1 and 30")
        await self.send_command({"speed": speed})

    async def set_oscillation(self, oscillate: bool) -> None:
        """Set horizontal oscillation."""
        await self.send_command({"horosc": 1 if oscillate else 0})

    async def set_mode(self, mode: int) -> None:
        """Set fan mode."""
        await self.send_command({"mode": mode})

    async def set_night_mode(self, night_mode: bool) -> None:
        """Set night mode."""
        await self.send_command({"night": 1 if night_mode else 0})


class TestDuuxApiClient:
    """Test the DuuxApiClient."""

    def setup_method(self):
        """Set up test fixtures."""
        self.session = Mock()
        self.api_client = DuuxApiClient(self.session, "34:5f:45:ec:b8:34", "test_token")

    @pytest.mark.asyncio
    async def test_init(self):
        """Test API client initialization."""
        assert self.api_client._device_id == "34:5f:45:ec:b8:34"
        assert self.api_client._jwt_token == "test_token"
        assert self.api_client._session is not None

    @pytest.mark.asyncio
    async def test_turn_on_calls_send_command(self):
        """Test turn on calls send_command with correct parameters."""
        self.api_client.send_command = AsyncMock()
        
        await self.api_client.turn_on()
        
        self.api_client.send_command.assert_called_once_with({"power": 1})

    @pytest.mark.asyncio
    async def test_turn_off_calls_send_command(self):
        """Test turn off calls send_command with correct parameters."""
        self.api_client.send_command = AsyncMock()
        
        await self.api_client.turn_off()
        
        self.api_client.send_command.assert_called_once_with({"power": 0})

    @pytest.mark.asyncio
    async def test_set_speed_valid(self):
        """Test setting valid speed."""
        self.api_client.send_command = AsyncMock()
        
        await self.api_client.set_speed(15)
        
        self.api_client.send_command.assert_called_once_with({"speed": 15})

    @pytest.mark.asyncio
    async def test_set_speed_invalid_low(self):
        """Test setting speed too low raises ValueError."""
        with pytest.raises(ValueError, match="Speed must be between 1 and 30"):
            await self.api_client.set_speed(0)

    @pytest.mark.asyncio
    async def test_set_speed_invalid_high(self):
        """Test setting speed too high raises ValueError."""
        with pytest.raises(ValueError, match="Speed must be between 1 and 30"):
            await self.api_client.set_speed(31)

    @pytest.mark.asyncio
    async def test_set_oscillation_on(self):
        """Test enabling oscillation."""
        self.api_client.send_command = AsyncMock()
        
        await self.api_client.set_oscillation(True)
        
        self.api_client.send_command.assert_called_once_with({"horosc": 1})

    @pytest.mark.asyncio
    async def test_set_oscillation_off(self):
        """Test disabling oscillation."""
        self.api_client.send_command = AsyncMock()
        
        await self.api_client.set_oscillation(False)
        
        self.api_client.send_command.assert_called_once_with({"horosc": 0})

    @pytest.mark.asyncio
    async def test_set_mode(self):
        """Test setting fan mode."""
        self.api_client.send_command = AsyncMock()
        
        await self.api_client.set_mode(2)
        
        self.api_client.send_command.assert_called_once_with({"mode": 2})

    @pytest.mark.asyncio
    async def test_set_night_mode_on(self):
        """Test enabling night mode."""
        self.api_client.send_command = AsyncMock()
        
        await self.api_client.set_night_mode(True)
        
        self.api_client.send_command.assert_called_once_with({"night": 1})

    @pytest.mark.asyncio
    async def test_set_night_mode_off(self):
        """Test disabling night mode."""
        self.api_client.send_command = AsyncMock()
        
        await self.api_client.set_night_mode(False)
        
        self.api_client.send_command.assert_called_once_with({"night": 0})

    @pytest.mark.asyncio
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
        
        # Create a proper async context manager mock
        mock_context_manager = AsyncMock()
        mock_context_manager.__aenter__ = AsyncMock(return_value=mock_response)
        mock_context_manager.__aexit__ = AsyncMock(return_value=None)
        
        self.api_client._session.get = Mock(return_value=mock_context_manager)

        result = await self.api_client.get_status()
        
        assert result == expected_response
        self.api_client._session.get.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_command_success(self):
        """Test successful command sending."""
        expected_response = {"success": True}
        
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json = AsyncMock(return_value=expected_response)
        
        # Create a proper async context manager mock
        mock_context_manager = AsyncMock()
        mock_context_manager.__aenter__ = AsyncMock(return_value=mock_response)
        mock_context_manager.__aexit__ = AsyncMock(return_value=None)
        
        self.api_client._session.post = Mock(return_value=mock_context_manager)

        command = {"power": 1}
        result = await self.api_client.send_command(command)
        
        assert result == expected_response
        self.api_client._session.post.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_command_error_response(self):
        """Test command sending with error response."""
        error_response = {"error": "Unauthorized", "code": 401}
        
        mock_response = Mock()
        mock_response.ok = False
        mock_response.json = AsyncMock(return_value=error_response)
        
        # Create a proper async context manager mock
        mock_context_manager = AsyncMock()
        mock_context_manager.__aenter__ = AsyncMock(return_value=mock_response)
        mock_context_manager.__aexit__ = AsyncMock(return_value=None)
        
        self.api_client._session.post = Mock(return_value=mock_context_manager)

        with pytest.raises(DuuxApiError, match="Command failed"):
            await self.api_client.send_command({"power": 1})


async def run_all_tests():
    """Run all tests manually."""
    test_instance = TestDuuxApiClient()
    
    tests = [
        test_instance.test_init,
        test_instance.test_turn_on_calls_send_command,
        test_instance.test_turn_off_calls_send_command,
        test_instance.test_set_speed_valid,
        test_instance.test_set_oscillation_on,
        test_instance.test_set_oscillation_off,
        test_instance.test_set_mode,
        test_instance.test_set_night_mode_on,
        test_instance.test_set_night_mode_off,
        test_instance.test_get_status_success,
        test_instance.test_send_command_success,
        test_instance.test_send_command_error_response,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        test_instance.setup_method()
        try:
            await test()
            print(f"✓ {test.__name__}")
            passed += 1
        except Exception as e:
            print(f"✗ {test.__name__}: {e}")
            failed += 1
    
    # Test error cases
    test_instance.setup_method()
    try:
        await test_instance.test_set_speed_invalid_low()
        print("✗ test_set_speed_invalid_low: Should have raised ValueError")
        failed += 1
    except ValueError:
        print("✓ test_set_speed_invalid_low")
        passed += 1
    except Exception as e:
        print(f"✗ test_set_speed_invalid_low: {e}")
        failed += 1
    
    test_instance.setup_method()
    try:
        await test_instance.test_set_speed_invalid_high()
        print("✗ test_set_speed_invalid_high: Should have raised ValueError")
        failed += 1
    except ValueError:
        print("✓ test_set_speed_invalid_high")
        passed += 1
    except Exception as e:
        print(f"✗ test_set_speed_invalid_high: {e}")
        failed += 1
    
    print(f"\nTest Results: {passed} passed, {failed} failed")
    return failed == 0


if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    exit(0 if success else 1)