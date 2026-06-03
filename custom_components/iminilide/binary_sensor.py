from __future__ import annotations

import logging

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .alarm import is_alarm_triggered
from .entity import IminilideVoieEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up i-MINILide binary sensor entities."""

    runtime_data = entry.runtime_data
    entities: list[BinarySensorEntity] = []
    alarm_entities = 0

    for voie in sorted(runtime_data.description.voies.values(), key=lambda voie: voie.number):
        entities.append(IminilideSurveillanceBinarySensor(runtime_data, voie))
        if voie.alarm_surveillance_enabled and (
            voie.alarm_low_threshold is not None or voie.alarm_high_threshold is not None
        ):
            entities.append(IminilideAlarmBinarySensor(runtime_data, voie))
            alarm_entities += 1

    _LOGGER.debug(
        "Adding %d binary sensor entities for host %s across %d voies (%d alarm entities)",
        len(entities),
        runtime_data.host,
        len(runtime_data.description.voies),
        alarm_entities,
    )
    async_add_entities(entities)


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
    def extra_state_attributes(self) -> dict[str, bool | float | str] | None:
        attributes: dict[str, bool | float | str] = {"active": self.voie.active}
        if self.voie.unit:
            attributes["unite"] = self.voie.unit
        if self.voie.correction is not None:
            attributes["correction"] = self.voie.correction
        if self.voie.alarm_high_threshold is not None:
            attributes["seuil_alarme_haut"] = self.voie.alarm_high_threshold
        if self.voie.alarm_low_threshold is not None:
            attributes["seuil_alarme_bas"] = self.voie.alarm_low_threshold
        return attributes or None


class IminilideAlarmBinarySensor(IminilideVoieEntity, BinarySensorEntity):
    """Binary threshold sensor for one monitored voie."""

    def __init__(self, runtime_data, voie) -> None:
        super().__init__(runtime_data, voie, "alarm")
        self._attr_name = "Alarme"

    @property
    def is_on(self) -> bool:
        if self.reading is None or self.reading.numeric_value is None:
            return False

        return is_alarm_triggered(
            self.reading.numeric_value,
            self.voie.alarm_low_threshold,
            self.voie.alarm_high_threshold,
        )

    @property
    def extra_state_attributes(self) -> dict[str, str | float] | None:
        attributes: dict[str, str | float] = {}
        if self.voie.unit:
            attributes["unite"] = self.voie.unit
        if self.voie.correction is not None:
            attributes["correction"] = self.voie.correction
        if self.reading is not None and self.reading.numeric_value is not None:
            attributes["valeur"] = self.reading.numeric_value
        if self.voie.alarm_high_threshold is not None:
            attributes["seuil_alarme_haut"] = self.voie.alarm_high_threshold
        if self.voie.alarm_low_threshold is not None:
            attributes["seuil_alarme_bas"] = self.voie.alarm_low_threshold
        return attributes or None
