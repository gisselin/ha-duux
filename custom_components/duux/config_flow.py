"""Config flow for Duux Fan integration."""
from __future__ import annotations

import asyncio
import json
import logging
import socket
from typing import Any

import voluptuous as vol
from aiohttp import web
from homeassistant import config_entries
from homeassistant.const import CONF_DEVICE_ID
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import DuuxApiClient, DuuxApiError
from .const import DOMAIN

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


def find_free_port() -> int:
    """Find a free port for the credential server."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("", 0))
        s.listen(1)
        port = s.getsockname()[1]
    return port


class CredentialServer:
    """HTTP server to receive credentials from the extraction script."""
    
    def __init__(self):
        self.port = find_free_port()
        self.app = web.Application()
        self.runner = None
        self.site = None
        self.credentials = None
        self.credential_event = asyncio.Event()
        
        # Setup routes
        self.app.router.add_post('/credentials', self.receive_credentials)
        self.app.router.add_options('/credentials', self.handle_options)
    
    async def receive_credentials(self, request):
        """Handle POST request with credentials."""
        try:
            data = await request.json()
            
            if "device_id" in data and "jwt_token" in data:
                self.credentials = data
                self.credential_event.set()
                _LOGGER.info("Received credentials from script")
                return web.json_response({"status": "success", "message": "Credentials received"})
            else:
                return web.json_response({"status": "error", "message": "Missing credentials"}, status=400)
                
        except json.JSONDecodeError:
            return web.json_response({"status": "error", "message": "Invalid JSON"}, status=400)
        except Exception as err:
            _LOGGER.error("Error receiving credentials: %s", err)
            return web.json_response({"status": "error", "message": str(err)}, status=500)
    
    async def handle_options(self, request):
        """Handle CORS preflight requests."""
        return web.Response(
            headers={
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "POST, OPTIONS",
                "Access-Control-Allow-Headers": "Content-Type",
            }
        )
    
    async def start(self):
        """Start the HTTP server."""
        self.runner = web.AppRunner(self.app)
        await self.runner.setup()
        self.site = web.TCPSite(self.runner, 'localhost', self.port)
        await self.site.start()
        _LOGGER.info("Credential server started on port %s", self.port)
    
    async def stop(self):
        """Stop the HTTP server."""
        if self.site:
            await self.site.stop()
        if self.runner:
            await self.runner.cleanup()
        _LOGGER.info("Credential server stopped")
    
    async def wait_for_credentials(self, timeout: float = 300) -> dict[str, Any] | None:
        """Wait for credentials with timeout."""
        try:
            await asyncio.wait_for(self.credential_event.wait(), timeout=timeout)
            return self.credentials
        except asyncio.TimeoutError:
            return None


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Duux Fan."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        super().__init__()
        self.credential_server: CredentialServer | None = None

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
            self.credential_server = CredentialServer()
            await self.credential_server.start()
            
            return self.async_show_progress(
                step_id="automated_setup",
                progress_action="waiting_for_script",
                description_placeholders={
                    "server_port": str(self.credential_server.port),
                    "script_command": f"curl -sSL https://raw.githubusercontent.com/gisselin/ha-duux/main/scripts/extract_credentials.py | python3 - --ha-endpoint http://localhost:{self.credential_server.port}",
                },
            )
            
        except Exception as err:
            _LOGGER.error("Failed to start credential server: %s", err)
            return self.async_show_form(
                step_id="automated_setup",
                errors={"base": "server_start_failed"},
                description_placeholders={"error": str(err)},
            )

    async def async_step_waiting_for_script(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Wait for the script to send credentials."""
        if self.credential_server is None:
            return self.async_abort(reason="server_error")

        try:
            # Wait for credentials with a 5-minute timeout
            credentials = await self.credential_server.wait_for_credentials(timeout=300)
            
            if not credentials:
                await self._cleanup_server()
                return self.async_show_progress_done(next_step_id="automated_setup")

            await self._cleanup_server()

            # Validate the received credentials
            await self.async_set_unique_id(credentials[CONF_DEVICE_ID])
            self._abort_if_unique_id_configured()

            try:
                info = await validate_input(self.hass, credentials)
            except (CannotConnect, InvalidAuth):
                return self.async_show_form(
                    step_id="manual_setup",
                    data_schema=STEP_USER_DATA_SCHEMA,
                    errors={"base": "invalid_captured_credentials"},
                    description_placeholders={
                        "device_id": credentials.get(CONF_DEVICE_ID, ""),
                        "jwt_token": credentials.get("jwt_token", "")[:50] + "...",
                    },
                )

            return self.async_create_entry(title=info["title"], data=credentials)

        except Exception as err:
            _LOGGER.exception("Error during automated setup")
            await self._cleanup_server()
            return self.async_show_form(
                step_id="manual_setup",
                data_schema=STEP_USER_DATA_SCHEMA,
                errors={"base": "automated_setup_failed"},
            )

    async def _cleanup_server(self) -> None:
        """Clean up the credential server."""
        if self.credential_server:
            try:
                await self.credential_server.stop()
            except Exception as err:
                _LOGGER.error("Error stopping credential server: %s", err)
            finally:
                self.credential_server = None


class CannotConnect(Exception):
    """Error to indicate we cannot connect."""


class InvalidAuth(Exception):
    """Error to indicate there is invalid auth."""