# Duux Fan Home Assistant Integration

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/custom-components/hacs)

A Home Assistant integration for controlling Duux smart fans through their cloud API.

## Features

- Turn fan on/off
- Control fan speed (1-30 levels, displayed as percentage)
- Enable/disable oscillation
- Real-time status updates

## Installation

### HACS (Recommended)

## Automated install 

Download and install directly through [HACS (Home Assistant Community Store)](https://hacs.xyz/): 

[![Open your Home Assistant instance and open the Duux Fan integration inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=basnijholt&repository=adaptive-lighting&category=integration) 

## Manual install 

1. Open HACS in your Home Assistant instance
2. Click on "Integrations"
3. Click the three dots in the top right corner and select "Custom repositories"
4. Add this repository URL and select "Integration" as the category
5. Click "Add"
6. Search for "Duux Fan" and install it
7. Restart Home Assistant

### Manual Installation

1. Download the `custom_components/duux` folder from this repository
2. Copy it to your `custom_components` directory in your Home Assistant configuration
3. Restart Home Assistant

## Configuration

1. Go to Settings → Devices & Services
2. Click "Add Integration"
3. Search for "Duux Fan"
4. Enter your device configuration:
   - **Device ID**: Your Duux fan's device ID (format: `xx:xx:xx:xx:xx:xx`)
   - **JWT Token**: Your authentication token for the Duux API

### Finding Your Device ID and JWT Token

You need to intercept HTTP requests from the Duux mobile app to obtain these values:

1. **Install a network proxy tool**:
   - **Proxyman** (macOS) - Recommended for ease of use
   - **Wireshark** (Cross-platform) - More advanced option
   - **Charles Proxy** (Cross-platform) - Alternative option

2. **Set up SSL proxying**:
   - Configure your proxy tool to intercept HTTPS traffic
   - Install the proxy's SSL certificate on your mobile device
   - Enable SSL proxying for `v5.api.cloudgarden.nl`

3. **Capture the requests**:
   - Connect your mobile device to the proxy
   - Open the Duux mobile app
   - Log into your account and interact with your fan (turn on/off, change speed, etc.)
   - Look for API requests to `v5.api.cloudgarden.nl`

4. **Extract the values**:
   - **Device ID**: Found in the URL path (format: `xx:xx:xx:xx:xx:xx`)
   - **JWT Token**: Found in the `Authorization` header (after "Bearer ")

## Supported Devices

This integration has been tested with Duux smart fans that use the cloudgarden.nl API. If your fan works with the Duux mobile app, it should work with this integration.

## Troubleshooting

- **Cannot connect**: Check that your JWT token is valid and hasn't expired
- **Device not found**: Verify your device ID is correct (should be in MAC address format)
- **API errors**: The Duux API may be temporarily unavailable

## Contributing

Contributions are welcome! Please submit issues and pull requests on GitHub.

## License

This project is licensed under the MIT License.