# Duux Credential Extraction Scripts

This directory contains helper scripts for extracting Duux API credentials needed for the Home Assistant integration.

## Quick Start

Run this command to automatically extract your Duux credentials:

```bash
curl -sSL https://raw.githubusercontent.com/gisselin/ha-duux/main/scripts/extract_credentials.py | python3
```

## What it does

The script will:

1. **Install check**: Verify mitmproxy is installed (install with `pip install mitmproxy`)
2. **Start proxy**: Launch a proxy server on port 8080 (or find a free port)
3. **Show instructions**: Display mobile device configuration steps
4. **SSL certificate**: Guide you to install the mitmproxy certificate from `http://mitm.it`
5. **Capture credentials**: Monitor network traffic when you use the Duux app
6. **Display results**: Show your Device ID and JWT token for Home Assistant

## Manual Usage

You can also download and run the script directly:

```bash
# Download the script
curl -O https://raw.githubusercontent.com/gisselin/ha-duux/main/scripts/extract_credentials.py

# Make it executable
chmod +x extract_credentials.py

# Run with custom port
python3 extract_credentials.py --port 8888
```

## Requirements

- Python 3.7+
- mitmproxy: `pip install mitmproxy`
- Mobile device with Duux app installed

## How it works

1. The script creates a temporary mitmproxy addon that monitors HTTP traffic
2. When you use the Duux mobile app through the proxy, it captures:
   - **Device ID**: Extracted from the API URL path (`/data/{device_id}/status`)
   - **JWT Token**: Extracted from the `Authorization: Bearer {token}` header
3. Credentials are saved to `duux_credentials.json` in the current directory
4. The proxy automatically stops after capturing credentials

## Troubleshooting

**Port already in use**: The script will automatically find a free port if 8080 is busy.

**No credentials captured**: 
- Ensure your mobile device proxy is configured correctly
- Make sure you installed the SSL certificate from `http://mitm.it`
- Try controlling your fan in the Duux app (turn on/off, change speed)

**Certificate issues**: 
- On iOS: Settings → General → VPN & Device Management → Install certificate
- On Android: Settings → Security → Install from device storage

**mitmproxy not found**: Install it with `pip install mitmproxy`

## Security Note

This script only captures credentials locally on your machine. The proxy server:
- Only runs locally (127.0.0.1)
- Only captures Duux API traffic
- Automatically stops after finding credentials
- Does not send data anywhere external

Remember to remove proxy settings from your mobile device after setup!