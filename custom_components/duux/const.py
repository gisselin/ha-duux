"""Constants for the Duux Fan integration."""

DOMAIN = "duux"

API_BASE_URL = "https://v5.api.cloudgarden.nl"

# Default device polling interval in seconds
DEFAULT_SCAN_INTERVAL = 30

# Fan speed mappings
MIN_FAN_SPEED = 1
MAX_FAN_SPEED = 30
MIN_PERCENTAGE = 1
MAX_PERCENTAGE = 100

# Repair issue identifiers
REPAIR_ISSUE_AUTH_FAILED = "auth_failed"