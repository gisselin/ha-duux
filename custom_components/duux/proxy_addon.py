"""Mitmproxy addon for capturing Duux API credentials."""
from __future__ import annotations

import json
import logging
import re
from typing import Any

from mitmproxy import http

# Configure logging
logging.basicConfig(level=logging.INFO)
_LOGGER = logging.getLogger(__name__)

DUUX_API_HOST = "v5.api.cloudgarden.nl"
DEVICE_ID_PATTERN = re.compile(r"/data/([a-fA-F0-9:]+)/status")
JWT_HEADER = "authorization"

# File to store captured credentials
CREDENTIALS_FILE = "/tmp/duux_credentials.json"


class DuuxCredentialCapture:
    """Mitmproxy addon to capture Duux API credentials."""

    def __init__(self) -> None:
        """Initialize the credential capture addon."""
        self.captured_credentials: dict[str, Any] = {}

    def request(self, flow: http.HTTPFlow) -> None:
        """Process HTTP requests to capture Duux API credentials."""
        if not flow.request.pretty_host == DUUX_API_HOST:
            return

        # Extract JWT token from Authorization header
        auth_header = flow.request.headers.get(JWT_HEADER)
        if not auth_header:
            return

        jwt_token = None
        if auth_header.startswith("Bearer "):
            jwt_token = auth_header[7:]  # Remove "Bearer " prefix
        
        if not jwt_token:
            return

        # Extract device ID from URL path
        match = DEVICE_ID_PATTERN.search(flow.request.path)
        if not match:
            return

        device_id = match.group(1)
        
        _LOGGER.info(
            "Captured Duux credentials - Device ID: %s, Token: %s...", 
            device_id, 
            jwt_token[:20] + "..." if len(jwt_token) > 20 else jwt_token
        )

        self.captured_credentials = {
            "device_id": device_id,
            "jwt_token": jwt_token,
        }
        
        # Write credentials to file for the config flow to read
        try:
            with open(CREDENTIALS_FILE, "w") as f:
                json.dump(self.captured_credentials, f)
            _LOGGER.info("Credentials saved to %s", CREDENTIALS_FILE)
        except Exception as err:
            _LOGGER.error("Failed to save credentials: %s", err)

    def get_credentials(self) -> dict[str, Any]:
        """Get the captured credentials."""
        return self.captured_credentials.copy()


# Global instance for mitmproxy
addons = [DuuxCredentialCapture()]