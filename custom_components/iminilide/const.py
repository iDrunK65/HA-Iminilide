from __future__ import annotations

from datetime import timedelta

from homeassistant.const import Platform

DOMAIN = "iminilide"
MANUFACTURER = "Microlide"
DEFAULT_TIMEOUT = 10
SCAN_INTERVAL = timedelta(seconds=30)
PLATFORMS: list[Platform] = [Platform.SENSOR, Platform.BINARY_SENSOR]
