from __future__ import annotations

from homeassistant.const import Platform

DOMAIN = "iminilide"
MANUFACTURER = "Microlide"
DEFAULT_TIMEOUT = 10
MAX_CONCURRENT_VOIE_REQUESTS = 4
DEFAULT_SCAN_INTERVAL_SECONDS = 30
MIN_SCAN_INTERVAL_SECONDS = 5
MAX_SCAN_INTERVAL_SECONDS = 3600
PLATFORMS: list[Platform] = [Platform.SENSOR, Platform.BINARY_SENSOR]
