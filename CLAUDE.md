# Duux Fan Home Assistant Integration - Development Guide

This is a custom Home Assistant integration for controlling Duux smart fans through their cloud API.

## Project Structure

```
custom_components/duux/
├── __init__.py          # Integration setup and entry point
├── manifest.json        # Integration metadata and dependencies
├── const.py            # Constants and configuration values
├── config_flow.py      # Configuration flow for setup UI
├── coordinator.py      # Data update coordinator for API polling
├── api.py             # API client for Duux cloud service
├── fan.py             # Fan entity implementation
└── strings.json       # UI translations and repair issue messages
```

## Key Components

### API Client (`api.py`)
- Handles communication with Duux cloud API at `v5.api.cloudgarden.nl`
- Supports fan control operations: power, speed, oscillation, modes
- Uses JWT token authentication
- Speed range: 1-30 (mapped to 1-100% in Home Assistant)

### Data Coordinator (`coordinator.py`)
- Polls device status every 30 seconds
- Handles authentication failures with repair issue creation
- Manages API errors and connection issues

### Fan Entity (`fan.py`)
- Implements Home Assistant fan entity
- Supports: on/off, speed control (percentage), oscillation
- Handles API errors with repair warnings

### Repair System
- Monitors for authentication failures (expired JWT tokens)
- Creates repair issues after 3 consecutive auth failures
- Auto-resolves when authentication is restored
- Provides clear instructions for token renewal

## Development Commands

### Linting and Type Checking
```bash
# Run Python linting (if available)
ruff check custom_components/duux/
# or
flake8 custom_components/duux/

# Type checking (if available)
mypy custom_components/duux/
```

### Testing
```bash
# Install test dependencies
pip install -r requirements-test.txt

# Run all tests
pytest

# Run specific test categories
pytest -m unit          # Unit tests only
pytest -m integration   # Integration tests only

# Run tests with coverage
pytest --cov=custom_components.duux --cov-report=html

# Run specific test files
pytest tests/test_api.py
pytest tests/test_fan.py
pytest tests/test_coordinator.py
pytest tests/test_config_flow.py
pytest tests/test_init.py

# Manual testing with Home Assistant dev environment
hass --config /path/to/test/config
```

## Configuration

### Required Parameters
- **Device ID**: MAC address format (xx:xx:xx:xx:xx:xx)
- **JWT Token**: Bearer token from Duux mobile app

### Obtaining Credentials

**Option 1: Automated Script (Recommended)**

The easiest way to get your credentials is using our automated extraction script. 

📋 **See [scripts/README.md](scripts/README.md) for complete instructions and troubleshooting.**

**Quick Start:**
```bash
curl -sSL https://raw.githubusercontent.com/gisselin/ha-duux/main/scripts/extract_credentials.py | python3
```

**Features:**
- Auto-installs mitmproxy if needed
- Automatically detects your computer's IP address
- Guides you through mobile device setup
- Captures credentials when you use the Duux app
- Saves credentials to `duux_credentials.json`

**Option 2: Manual Method**
1. Install network proxy tool (Proxyman, Wireshark, Charles Proxy)
2. Configure SSL proxying for `v5.api.cloudgarden.nl`
3. Use Duux mobile app while monitoring network traffic
4. Extract Device ID from URL path and JWT token from Authorization header

## API Endpoints

### Status Polling
```
GET https://v5.api.cloudgarden.nl/data/{device_id}/status
Authorization: Bearer {jwt_token}
```

### Send Commands
```
POST https://v5.api.cloudgarden.nl/sensor/{device_id}/commands
Authorization: Bearer {jwt_token}
Content-Type: application/json

{
  "command": "tune set speed 15"
}
```

**Important**: The `command` field must be a text string in the format `"tune set [parameter] [value]"`. Examples:

```json
{"command": "tune set power 1"}     // Turn on
{"command": "tune set power 0"}     // Turn off
{"command": "tune set speed 8"}     // Set speed to 8
{"command": "tune set mode 1"}      // Set mode to 1
{"command": "tune set night 1"}     // Enable night mode
{"command": "tune set night 0"}     // Disable night mode
{"command": "tune set horosc 1"}    // Enable horizontal oscillation
{"command": "tune set horosc 0"}    // Disable horizontal oscillation
{"command": "tune set verosc 1"}    // Enable vertical oscillation
```

Command parameters:
- `power`: 0=off, 1=on
- `speed`: 1-30 (fan speed when on)
- `horosc`: 0-3 (horizontal oscillation levels)
- `verosc`: 0-2 (vertical oscillation levels)  
- `mode`: 0-3 (fan mode)
- `night`: 0=normal, 1=night mode
- `lock`: 0=unlocked, 1=locked

## Common Issues

### Authentication Failures
- JWT tokens expire periodically
- Repair system will alert users when tokens need refresh
- No automatic token renewal - requires manual intervention

### API Rate Limiting
- Current polling interval: 30 seconds
- Consider increasing if rate limiting occurs

### Network Connectivity
- Integration requires internet access
- Cloud-dependent (no local control)

## Future Enhancements

- [ ] Add support for additional fan modes
- [ ] Implement preset speeds
- [ ] Add temperature sensor support (if available)
- [ ] Consider adding night mode as separate entity
- [ ] Add device diagnostics

## HACS Installation

This integration is designed for HACS (Home Assistant Community Store):

1. Add custom repository: `https://github.com/gisselin/ha-duux`
2. Install through HACS interface
3. Restart Home Assistant
4. Add integration through UI: Settings → Devices & Services → Add Integration

## Security Notes

- JWT tokens should be treated as sensitive credentials
- Tokens are stored in Home Assistant's configuration
- No local API - all communication goes through Duux cloud
- Consider network security when using proxy tools for token extraction