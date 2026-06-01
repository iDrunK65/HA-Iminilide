from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, MANUFACTURER
from .models import IminilideRuntimeData
from .parser import VoieConfig, VoieReading


class IminilideVoieEntity(CoordinatorEntity, Entity):
    """Base entity for a single i-MINILide voie."""

    _attr_has_entity_name = True

    def __init__(
        self,
        runtime_data: IminilideRuntimeData,
        voie: VoieConfig,
        unique_suffix: str,
    ) -> None:
        super().__init__(runtime_data.coordinator)
        self._runtime_data = runtime_data
        self._voie = voie
        self._controller_device_identifier = f"controller_{runtime_data.controller_identifier}"
        self._voie_device_identifier = (
            f"{self._controller_device_identifier}_voie_{voie.number}"
        )
        self._attr_unique_id = f"{self._voie_device_identifier}_{unique_suffix}"

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, self._voie_device_identifier)},
            manufacturer=MANUFACTURER,
            model=self._voie.sensor_type,
            name=self._voie.name,
            via_device=(DOMAIN, self._controller_device_identifier),
        )

    @property
    def voie(self) -> VoieConfig:
        return self._voie

    @property
    def reading(self) -> VoieReading | None:
        return self.coordinator.data.get(self._voie.number)
