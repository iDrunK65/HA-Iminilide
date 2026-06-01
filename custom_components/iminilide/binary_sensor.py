from __future__ import annotations

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .entity import IminilideVoieEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up i-MINILide binary sensor entities."""

    runtime_data = entry.runtime_data
    async_add_entities(
        IminilideSurveillanceBinarySensor(runtime_data, voie)
        for voie in sorted(runtime_data.description.voies.values(), key=lambda voie: voie.number)
    )


class IminilideSurveillanceBinarySensor(IminilideVoieEntity, BinarySensorEntity):
    """Expose whether alarm surveillance is enabled for one voie."""

    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, runtime_data, voie) -> None:
        super().__init__(runtime_data, voie, "surveillance")
        self._attr_name = "Surveillance"

    @property
    def is_on(self) -> bool:
        return self.voie.alarm_surveillance_enabled

    @property
    def extra_state_attributes(self) -> dict[str, bool]:
        return {"active": self.voie.active}
