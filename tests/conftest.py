"""Common fixtures for Duux Fan integration tests."""
from __future__ import annotations

from unittest.mock import AsyncMock, Mock, patch
import pytest

# Mock HomeAssistant imports for testing
class MockHomeAssistant:
    def __init__(self):
        self.data = {}

class MockConfigEntry:
    def __init__(self, **kwargs):
        self.version = kwargs.get('version', 1)
        self.minor_version = kwargs.get('minor_version', 0)
        self.domain = kwargs.get('domain')
        self.title = kwargs.get('title')
        self.data = kwargs.get('data', {})
        self.options = kwargs.get('options', {})
        self.entry_id = kwargs.get('entry_id')
        self.source = kwargs.get('source')
        self.state = kwargs.get('state')

CONF_DEVICE_ID = "device_id"
DOMAIN = "duux"


@pytest.fixture
def mock_duux_api():
    """Mock the DuuxApiClient."""
    with patch("custom_components.duux.api.DuuxApiClient") as mock:
        api = Mock()
        api.get_status = AsyncMock(return_value={
            "data": {
                "power": 1,
                "speed": 15,
                "mode": 0,
                "night": 0,
                "lock": 0,
                "horosc": 1,
                "verosc": 0
            }
        })
        api.turn_on = AsyncMock()
        api.turn_off = AsyncMock()
        api.set_speed = AsyncMock()
        api.set_oscillation = AsyncMock()
        api.set_mode = AsyncMock()
        api.set_night_mode = AsyncMock()
        mock.return_value = api
        yield api


@pytest.fixture
def mock_config_entry():
    """Mock a config entry for the integration."""
    return MockConfigEntry(
        version=1,
        minor_version=0,
        domain=DOMAIN,
        title="Duux Fan Test",
        data={
            CONF_DEVICE_ID: "34:5f:45:ec:b8:34",
            "jwt_token": "test_jwt_token_12345"
        },
        options={},
        entry_id="test_entry_id",
        source="user",
        state="loaded",
    )


@pytest.fixture
def mock_aiohttp_session():
    """Mock aiohttp session."""
    with patch("homeassistant.helpers.aiohttp_client.async_get_clientsession") as mock:
        session = Mock()
        mock.return_value = session
        yield session


@pytest.fixture
def mock_api_responses():
    """Mock API response data."""
    return {
        "status_success": {
            "data": {
                "power": 1,
                "speed": 15,
                "mode": 0,
                "night": 0,
                "lock": 0,
                "horosc": 1,
                "verosc": 0
            }
        },
        "status_off": {
            "data": {
                "power": 0,
                "speed": 1,
                "mode": 0,
                "night": 0,
                "lock": 0,
                "horosc": 0,
                "verosc": 0
            }
        },
        "command_success": {
            "success": True
        },
        "auth_error": {
            "error": "Unauthorized",
            "code": 401
        }
    }