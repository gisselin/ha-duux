"""Tests for the Duux integration initialization."""
from __future__ import annotations

from unittest.mock import AsyncMock, Mock, patch
import pytest
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_DEVICE_ID, Platform

from custom_components.duux import async_setup_entry, async_unload_entry
from custom_components.duux.const import DOMAIN


@pytest.mark.integration
class TestInit:
    """Test the integration initialization."""

    @pytest.fixture
    def mock_hass(self):
        """Mock Home Assistant."""
        hass = Mock(spec=HomeAssistant)
        hass.data = {}
        hass.config_entries = Mock()
        hass.config_entries.async_forward_entry_setups = AsyncMock(return_value=True)
        hass.config_entries.async_unload_platforms = AsyncMock(return_value=True)
        return hass

    @pytest.fixture
    def mock_entry(self):
        """Mock config entry."""
        entry = Mock(spec=ConfigEntry)
        entry.data = {
            CONF_DEVICE_ID: "34:5f:45:ec:b8:34",
            "jwt_token": "test_token_12345"
        }
        entry.entry_id = "test_entry_id"
        return entry

    async def test_setup_entry_success(self, mock_hass, mock_entry, mock_aiohttp_session):
        """Test successful setup of config entry."""
        with patch("custom_components.duux.async_get_clientsession") as mock_get_session:
            mock_get_session.return_value = mock_aiohttp_session
            
            with patch("custom_components.duux.DuuxDataUpdateCoordinator") as mock_coordinator_class:
                mock_coordinator = Mock()
                mock_coordinator.async_config_entry_first_refresh = AsyncMock()
                mock_coordinator_class.return_value = mock_coordinator
                
                result = await async_setup_entry(mock_hass, mock_entry)
        
        assert result is True
        assert DOMAIN in mock_hass.data
        assert mock_entry.entry_id in mock_hass.data[DOMAIN]
        assert mock_hass.data[DOMAIN][mock_entry.entry_id] == mock_coordinator
        
        # Verify coordinator was initialized correctly
        mock_coordinator_class.assert_called_once_with(
            mock_hass,
            mock_aiohttp_session,
            mock_entry.data[CONF_DEVICE_ID],
            mock_entry.data["jwt_token"]
        )
        
        # Verify first refresh was called
        mock_coordinator.async_config_entry_first_refresh.assert_called_once()
        
        # Verify platforms were set up
        mock_hass.config_entries.async_forward_entry_setups.assert_called_once_with(
            mock_entry, [Platform.FAN]
        )

    async def test_setup_entry_coordinator_error(self, mock_hass, mock_entry, mock_aiohttp_session):
        """Test setup with coordinator refresh error."""
        with patch("custom_components.duux.async_get_clientsession") as mock_get_session:
            mock_get_session.return_value = mock_aiohttp_session
            
            with patch("custom_components.duux.DuuxDataUpdateCoordinator") as mock_coordinator_class:
                mock_coordinator = Mock()
                mock_coordinator.async_config_entry_first_refresh = AsyncMock(
                    side_effect=Exception("Coordinator refresh failed")
                )
                mock_coordinator_class.return_value = mock_coordinator
                
                with pytest.raises(Exception, match="Coordinator refresh failed"):
                    await async_setup_entry(mock_hass, mock_entry)

    async def test_unload_entry_success(self, mock_hass, mock_entry):
        """Test successful unloading of config entry."""
        # Setup initial data
        mock_hass.data[DOMAIN] = {mock_entry.entry_id: Mock()}
        
        result = await async_unload_entry(mock_hass, mock_entry)
        
        assert result is True
        assert mock_entry.entry_id not in mock_hass.data[DOMAIN]
        mock_hass.config_entries.async_unload_platforms.assert_called_once_with(
            mock_entry, [Platform.FAN]
        )

    async def test_unload_entry_platform_failure(self, mock_hass, mock_entry):
        """Test unloading with platform unload failure."""
        # Setup initial data
        mock_hass.data[DOMAIN] = {mock_entry.entry_id: Mock()}
        mock_hass.config_entries.async_unload_platforms = AsyncMock(return_value=False)
        
        result = await async_unload_entry(mock_hass, mock_entry)
        
        assert result is False
        # Data should not be removed if unload failed
        assert mock_entry.entry_id in mock_hass.data[DOMAIN]

    async def test_setup_entry_data_structure(self, mock_hass, mock_entry, mock_aiohttp_session):
        """Test that data structure is properly initialized."""
        # Test when DOMAIN not in hass.data
        assert DOMAIN not in mock_hass.data
        
        with patch("custom_components.duux.async_get_clientsession") as mock_get_session:
            mock_get_session.return_value = mock_aiohttp_session
            
            with patch("custom_components.duux.DuuxDataUpdateCoordinator") as mock_coordinator_class:
                mock_coordinator = Mock()
                mock_coordinator.async_config_entry_first_refresh = AsyncMock()
                mock_coordinator_class.return_value = mock_coordinator
                
                await async_setup_entry(mock_hass, mock_entry)
        
        # Verify domain was added to hass.data
        assert DOMAIN in mock_hass.data
        assert isinstance(mock_hass.data[DOMAIN], dict)

    async def test_setup_entry_existing_domain_data(self, mock_hass, mock_entry, mock_aiohttp_session):
        """Test setup when domain data already exists."""
        # Pre-populate domain data
        existing_entry_id = "existing_entry"
        existing_coordinator = Mock()
        mock_hass.data[DOMAIN] = {existing_entry_id: existing_coordinator}
        
        with patch("custom_components.duux.async_get_clientsession") as mock_get_session:
            mock_get_session.return_value = mock_aiohttp_session
            
            with patch("custom_components.duux.DuuxDataUpdateCoordinator") as mock_coordinator_class:
                mock_coordinator = Mock()
                mock_coordinator.async_config_entry_first_refresh = AsyncMock()
                mock_coordinator_class.return_value = mock_coordinator
                
                await async_setup_entry(mock_hass, mock_entry)
        
        # Verify existing data is preserved
        assert existing_entry_id in mock_hass.data[DOMAIN]
        assert mock_hass.data[DOMAIN][existing_entry_id] == existing_coordinator
        
        # Verify new entry was added
        assert mock_entry.entry_id in mock_hass.data[DOMAIN]
        assert mock_hass.data[DOMAIN][mock_entry.entry_id] == mock_coordinator