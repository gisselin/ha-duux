"""Config flow for Duux Fan integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_DEVICE_ID
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import DuuxApiClient, DuuxApiError
from .const import DOMAIN
from .proxy_manager import ProxyManager

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_DEVICE_ID): str,
        vol.Required("jwt_token"): str,
    }
)

STEP_SETUP_METHOD_SCHEMA = vol.Schema(
    {
        vol.Required("setup_method", default="automated"): vol.In(
            ["automated", "manual"]
        ),
    }
)


async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Validate the user input allows us to connect."""
    session = async_get_clientsession(hass)
    api = DuuxApiClient(session, data[CONF_DEVICE_ID], data["jwt_token"])

    try:
        await api.get_status()
    except DuuxApiError as err:
        raise InvalidAuth from err

    return {"title": f"Duux Fan ({data[CONF_DEVICE_ID]})"}


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Duux Fan."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        super().__init__()
        self.proxy_manager: ProxyManager | None = None
        self.captured_data: dict[str, Any] = {}

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step to choose setup method."""
        if user_input is None:
            return self.async_show_form(
                step_id="user", data_schema=STEP_SETUP_METHOD_SCHEMA
            )

        if user_input["setup_method"] == "automated":
            return await self.async_step_automated_setup()
        else:
            return await self.async_step_manual_setup()

    async def async_step_manual_setup(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle manual credential entry."""
        errors: dict[str, str] = {}
        if user_input is not None:
            await self.async_set_unique_id(user_input[CONF_DEVICE_ID])
            self._abort_if_unique_id_configured()

            try:
                info = await validate_input(self.hass, user_input)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                return self.async_create_entry(title=info["title"], data=user_input)

        return self.async_show_form(
            step_id="manual_setup", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )

    async def async_step_automated_setup(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Start the automated credential capture process."""
        try:
            self.proxy_manager = ProxyManager(self.hass)
            proxy_port = await self.proxy_manager.start_proxy()
            
            # Store the proxy port for later use
            self.captured_data["proxy_port"] = proxy_port
            
            return await self.async_step_proxy_instructions()
            
        except Exception as err:
            _LOGGER.error("Failed to start proxy: %s", err)
            return self.async_show_form(
                step_id="automated_setup",
                errors={"base": "proxy_start_failed"},
                description_placeholders={"error": str(err)},
            )

    async def async_step_proxy_instructions(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Show proxy configuration instructions and wait for credentials."""
        if user_input is not None:
            if user_input.get("action") == "cancel":
                await self._cleanup_proxy()
                return self.async_abort(reason="user_cancelled")
            
            return await self.async_step_credential_capture()

        proxy_port = self.captured_data.get("proxy_port")
        return self.async_show_form(
            step_id="proxy_instructions",
            data_schema=vol.Schema({
                vol.Optional("action"): vol.In(["continue", "cancel"])
            }),
            description_placeholders={
                "proxy_host": "127.0.0.1",
                "proxy_port": str(proxy_port),
            },
        )

    async def async_step_credential_capture(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Wait for credential capture from the proxy."""
        if self.proxy_manager is None:
            await self._cleanup_proxy()
            return self.async_abort(reason="proxy_error")

        try:
            # Wait for credentials with a 5-minute timeout
            credentials = await self.proxy_manager.wait_for_credentials(timeout=300)
            
            if not credentials:
                await self._cleanup_proxy()
                return self.async_show_form(
                    step_id="credential_capture",
                    errors={"base": "capture_timeout"},
                )

            await self._cleanup_proxy()

            if not credentials.get("device_id") or not credentials.get("jwt_token"):
                return self.async_show_form(
                    step_id="credential_capture",
                    errors={"base": "incomplete_credentials"},
                )

            # Validate the captured credentials
            await self.async_set_unique_id(credentials[CONF_DEVICE_ID])
            self._abort_if_unique_id_configured()

            try:
                info = await validate_input(self.hass, credentials)
            except (CannotConnect, InvalidAuth):
                return self.async_show_form(
                    step_id="credential_capture",
                    errors={"base": "invalid_captured_credentials"},
                )

            return self.async_create_entry(title=info["title"], data=credentials)

        except Exception as err:
            _LOGGER.exception("Error during credential capture")
            await self._cleanup_proxy()
            return self.async_show_form(
                step_id="credential_capture",
                errors={"base": "capture_error"},
                description_placeholders={"error": str(err)},
            )

    async def _cleanup_proxy(self) -> None:
        """Clean up the proxy manager."""
        if self.proxy_manager:
            try:
                await self.proxy_manager.stop_proxy()
            except Exception as err:
                _LOGGER.error("Error stopping proxy: %s", err)
            finally:
                self.proxy_manager = None


class CannotConnect(Exception):
    """Error to indicate we cannot connect."""


class InvalidAuth(Exception):
    """Error to indicate there is invalid auth."""