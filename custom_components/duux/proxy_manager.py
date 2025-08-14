"""Proxy manager for handling mitmproxy server lifecycle."""
from __future__ import annotations

import asyncio
import json
import logging
import os
import socket
from typing import Any

from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)

CREDENTIALS_FILE = "/tmp/duux_credentials.json"


def find_free_port() -> int:
    """Find a free port for the proxy server."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("", 0))
        s.listen(1)
        port = s.getsockname()[1]
    return port


class ProxyManager:
    """Manages the mitmproxy server for credential capture."""

    def __init__(self, hass: HomeAssistant) -> None:
        """Initialize the proxy manager."""
        self.hass = hass
        self.proxy_port: int | None = None
        self.proxy_process: asyncio.subprocess.Process | None = None
        self._running = False

    async def start_proxy(self) -> int:
        """Start the mitmproxy server and return port."""
        if self._running:
            raise RuntimeError("Proxy is already running")

        self.proxy_port = find_free_port()

        # Clean up any existing credentials file
        if os.path.exists(CREDENTIALS_FILE):
            os.remove(CREDENTIALS_FILE)

        try:
            # Get the path to the addon script
            addon_path = os.path.join(
                os.path.dirname(__file__), "proxy_addon.py"
            )

            # Start mitmproxy with our addon
            cmd = [
                "mitmdump",
                "--listen-port", str(self.proxy_port),
                "--set", "confdir=~/.mitmproxy",
                "--set", "ssl_insecure=true",
                "--scripts", addon_path,
            ]

            self.proxy_process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            # Wait a moment for the proxy to start
            await asyncio.sleep(3)

            if self.proxy_process.returncode is not None:
                # Process has already exited
                _, stderr = await self.proxy_process.communicate()
                error_msg = stderr.decode() if stderr else "Unknown error"
                raise RuntimeError(f"Failed to start proxy: {error_msg}")

            self._running = True
            _LOGGER.info("Started mitmproxy on port %s", self.proxy_port)
            
            return self.proxy_port

        except Exception as err:
            _LOGGER.error("Failed to start proxy: %s", err)
            await self.stop_proxy()
            raise

    async def stop_proxy(self) -> None:
        """Stop the mitmproxy server."""
        if self.proxy_process and self.proxy_process.returncode is None:
            self.proxy_process.terminate()
            try:
                await asyncio.wait_for(self.proxy_process.wait(), timeout=5)
            except asyncio.TimeoutError:
                self.proxy_process.kill()
                await self.proxy_process.wait()

        self.proxy_process = None
        self.proxy_port = None
        self._running = False
        
        # Clean up credentials file
        if os.path.exists(CREDENTIALS_FILE):
            try:
                os.remove(CREDENTIALS_FILE)
            except Exception as err:
                _LOGGER.warning("Failed to clean up credentials file: %s", err)
        
        _LOGGER.info("Stopped mitmproxy")

    async def wait_for_credentials(self, timeout: float = 300) -> dict[str, Any] | None:
        """Wait for credentials to be captured with timeout."""
        start_time = asyncio.get_event_loop().time()
        
        while asyncio.get_event_loop().time() - start_time < timeout:
            if os.path.exists(CREDENTIALS_FILE):
                try:
                    with open(CREDENTIALS_FILE, "r") as f:
                        credentials = json.load(f)
                    
                    if credentials.get("device_id") and credentials.get("jwt_token"):
                        _LOGGER.info("Successfully captured credentials")
                        return credentials
                except (json.JSONDecodeError, OSError) as err:
                    _LOGGER.warning("Error reading credentials file: %s", err)
            
            await asyncio.sleep(1)
        
        _LOGGER.warning("Timeout waiting for credentials")
        return None

    @property
    def is_running(self) -> bool:
        """Check if the proxy is running."""
        return self._running and self.proxy_process is not None

    def get_proxy_config(self) -> dict[str, Any]:
        """Get the proxy configuration for the user."""
        if not self.proxy_port:
            raise RuntimeError("Proxy is not running")

        return {
            "proxy_host": "127.0.0.1",
            "proxy_port": self.proxy_port,
            "ssl_verify": False,
        }