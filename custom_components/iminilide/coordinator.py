from __future__ import annotations

from datetime import timedelta
import logging

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import IminilideApiClient
from .const import DOMAIN
from .exceptions import IminilideError
from .parser import VoieReading

_LOGGER = logging.getLogger(__name__)


class IminilideDataUpdateCoordinator(DataUpdateCoordinator[dict[int, VoieReading]]):
    """Coordinator that refreshes voie readings from the controller."""

    def __init__(
        self,
        hass: HomeAssistant,
        client: IminilideApiClient,
        update_interval: timedelta,
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_{client.host}",
            update_interval=update_interval,
        )
        self.client = client

    async def _async_update_data(self) -> dict[int, VoieReading]:
        try:
            return await self.client.async_fetch_readings()
        except IminilideError as exc:
            raise UpdateFailed(str(exc)) from exc
