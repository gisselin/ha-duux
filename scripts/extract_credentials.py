#!/usr/bin/env python3
"""
Duux Fan Credential Extractor

This script sets up a proxy server to capture Duux API credentials.
Run this script, configure your mobile device to use the proxy,
then use the Duux app to capture your device ID and JWT token.

Usage:
    python3 extract_credentials.py [--port PORT]

Requirements:
    pip install mitmproxy

Author: Duux Home Assistant Integration
"""

import argparse
import asyncio
import json
import logging
import re
import signal
import socket
import subprocess
import sys
from typing import Any, Dict

import aiohttp

# Configure logging - silence mitmproxy completely
logging.basicConfig(
    level=logging.ERROR,    # Only show errors
    format='%(message)s'    # Simplified format
)

# Silence specific mitmproxy loggers
logging.getLogger("mitmproxy").setLevel(logging.CRITICAL)
logging.getLogger("mitmproxy.master").setLevel(logging.CRITICAL)
logging.getLogger("mitmproxy.http").setLevel(logging.CRITICAL)
logging.getLogger("mitmproxy.net").setLevel(logging.CRITICAL)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)  # Allow our info messages

# Constants
DUUX_API_HOST = "v5.api.cloudgarden.nl"
DEVICE_ID_PATTERN = re.compile(r"/data/([a-fA-F0-9:]+)/status")
JWT_HEADER = "authorization"


def install_mitmproxy() -> bool:
    """Auto-install mitmproxy if not present."""
    print("📦 mitmproxy not found. Installing automatically...")
    
    try:
        # Try to install mitmproxy
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "mitmproxy"],
            capture_output=True,
            text=True,
            check=True
        )
        print("✅ mitmproxy installed successfully!")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install mitmproxy: {e}")
        print("📋 Please install manually with: pip install mitmproxy")
        return False
    except Exception as e:
        print(f"❌ Installation error: {e}")
        print("📋 Please install manually with: pip install mitmproxy")
        return False


def check_mitmproxy() -> bool:
    """Check if mitmproxy is available, install if not."""
    try:
        import mitmproxy
        return True
    except ImportError:
        # Try to auto-install
        if install_mitmproxy():
            try:
                import mitmproxy
                return True
            except ImportError:
                return False
        return False


class DuuxCredentialCapture:
    """Mitmproxy addon to capture Duux API credentials."""

    def __init__(self):
        self.captured_credentials: Dict[str, Any] = {}
        self.credentials_captured = False

    def request(self, flow) -> None:
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
        
        print(f"✅ Captured Device ID: {device_id}")

        self.captured_credentials = {
            "device_id": device_id,
            "jwt_token": jwt_token,
        }
        
        # Signal that credentials have been captured
        self.credentials_captured = True

    def get_credentials(self) -> Dict[str, Any]:
        """Get the captured credentials."""
        return self.captured_credentials.copy()

    def has_credentials(self) -> bool:
        """Check if credentials have been captured."""
        return self.credentials_captured


class DuuxCredentialExtractor:
    """Main credential extraction coordinator."""
    
    def __init__(self, port: int = 8080, ha_endpoint: str = None):
        self.port = port
        self.ha_endpoint = ha_endpoint
        self.proxy_master = None
        self.capture_addon = DuuxCredentialCapture()
        self.running = False
        
    def find_free_port(self) -> int:
        """Find a free port if the specified one is in use."""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(("", self.port))
                return self.port
        except OSError:
            # Port in use, find a free one
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(("", 0))
                s.listen(1)
                port = s.getsockname()[1]
                return port

    def get_local_ip(self) -> str:
        """Get the local IP address of this machine."""
        try:
            # Connect to a remote address to determine local IP
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                # Use Google DNS (doesn't actually connect)
                s.connect(("8.8.8.8", 80))
                local_ip = s.getsockname()[0]
                return local_ip
        except Exception:
            # Fallback to localhost if unable to determine
            return "127.0.0.1"

    async def start_proxy(self) -> None:
        """Start the mitmproxy server using Python API."""
        from mitmproxy import options
        from mitmproxy.tools.dump import DumpMaster
        
        # Find a free port and get local IP
        self.port = self.find_free_port()
        local_ip = self.get_local_ip()
        
        print(f"🚀 Proxy started on port {self.port}")
        print(f"📱 Configure mobile proxy: {local_ip}:{self.port}")
        print("🔒 Install certificate: http://mitm.it")
        print("📲 Use Duux app → credentials will be captured automatically")
        print("⏹️  Press Ctrl+C to stop\n")
        
        # Configure mitmproxy options
        opts = options.Options(
            listen_port=self.port, 
            ssl_insecure=True
        )
        
        # Create proxy master within async context
        self.proxy_master = DumpMaster(opts)
        self.proxy_master.addons.add(self.capture_addon)
        self.running = True
        
        # Create tasks for proxy and credential monitoring
        proxy_task = asyncio.create_task(self.proxy_master.run())
        monitor_task = asyncio.create_task(self._monitor_capture())
        
        try:
            # Wait for either proxy to finish or credentials to be captured
            done, pending = await asyncio.wait(
                [proxy_task, monitor_task],
                return_when=asyncio.FIRST_COMPLETED
            )
            
            # Cancel pending tasks
            for task in pending:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
                    
        except KeyboardInterrupt:
            print("🛑 Stopped by user")
            # Cancel tasks
            proxy_task.cancel()
            monitor_task.cancel()
            try:
                await proxy_task
            except asyncio.CancelledError:
                pass
            try:
                await monitor_task
            except asyncio.CancelledError:
                pass

    async def _monitor_capture(self) -> None:
        """Monitor for credential capture in async context."""
        while self.running:
            if self.capture_addon.has_credentials():
                self.running = False
                if self.proxy_master:
                    self.proxy_master.shutdown()
                
                # Send credentials to HA if endpoint provided
                if self.ha_endpoint:
                    credentials = self.capture_addon.get_credentials()
                    await self.send_to_ha(credentials)
                
                break
            await asyncio.sleep(1.0)  # Check every second

    async def send_to_ha(self, credentials: Dict[str, Any]) -> None:
        """Send credentials to Home Assistant endpoint."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.ha_endpoint}/credentials",
                    json=credentials,
                    headers={"Content-Type": "application/json"},
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        print("✅ Credentials sent to Home Assistant successfully!")
                        print("🎉 Setup completed! Check your Home Assistant integration.")
                    else:
                        print(f"⚠️  Failed to send credentials to HA: {response.status}")
                        print("📋 Please enter them manually in Home Assistant")
                        
        except asyncio.TimeoutError:
            print("⚠️  Timeout sending credentials to Home Assistant")
            print("📋 Please enter them manually in Home Assistant")
        except Exception as err:
            print(f"⚠️  Error sending credentials to HA: {err}")
            print("📋 Please enter them manually in Home Assistant")

    def stop_proxy(self) -> None:
        """Stop the proxy server."""
        self.running = False
        if self.proxy_master:
            self.proxy_master.shutdown()

    def display_results(self) -> None:
        """Display the captured credentials."""
        credentials = self.capture_addon.get_credentials()
        
        if not credentials:
            print("⚠️  No credentials were captured")
            return
            
        try:
            print()
            print("=" * 60)
            print("🎉 CREDENTIALS CAPTURED SUCCESSFULLY!")
            print("=" * 60)
            print(f"Device ID:  {credentials['device_id']}")
            print(f"JWT Token:  {credentials['jwt_token']}")
            print()
            print("📋 Copy these values into your Home Assistant integration:")
            print("   1. Go to Settings → Devices & Services")
            print("   2. Click 'Add Integration'")
            print("   3. Search for 'Duux Fan'")
            print("   4. Enter the Device ID and JWT Token above")
            print("=" * 60)
            
            # Save to a permanent file
            output_file = "duux_credentials.json"
            with open(output_file, 'w') as f:
                json.dump(credentials, f, indent=2)
            print(f"💾 Credentials saved to: {output_file}")
            
        except Exception as err:
            print(f"❌ Error displaying credentials: {err}")


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Extract Duux API credentials using mitmproxy"
    )
    parser.add_argument(
        "--port", 
        type=int, 
        default=8080,
        help="Proxy port (default: 8080)"
    )
    parser.add_argument(
        "--ha-endpoint",
        type=str,
        help="Home Assistant endpoint to send credentials to (e.g., http://localhost:8123)"
    )
    
    args = parser.parse_args()
    
    # Check if mitmproxy is installed (auto-install if not)
    if not check_mitmproxy():
        print("❌ Could not install mitmproxy!")
        sys.exit(1)
    
    extractor = DuuxCredentialExtractor(args.port, args.ha_endpoint)
    
    # Handle Ctrl+C gracefully
    def signal_handler(sig, frame):
        extractor.stop_proxy()
    
    signal.signal(signal.SIGINT, signal_handler)
    
    try:
        await extractor.start_proxy()
    except Exception as err:
        print(f"❌ Error: {err}")
    finally:
        extractor.display_results()


if __name__ == "__main__":
    asyncio.run(main())